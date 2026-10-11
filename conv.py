import json, os, time, numpy as np, torch, scipy.io.wavfile as wf, librosa, onnx, onnxruntime as ort, shutil, traceback
from transformers import VitsModel, AutoTokenizer
from huggingface_hub import hf_hub_download
from onnxsim import simplify
from onnxruntime.quantization import quantize_dynamic, QuantType
os.makedirs('res', exist_ok=True); os.makedirs('voices', exist_ok=True)
M = {'yo-a': 'davidguzmanr/mms-tts-yor-finetuned', 'yo-b': 'Toadoum/yoruba-mms-tts-moz', 'ig-a': 'nexusbert/igbo-mms-tts'}
T = {'yo': 'báwo ni, craig. bí owó tí ń wọlé kò bá pọ̀, a máa ń nira láti fi pamọ́, àmọ́ ó ṣeé ṣe',
     'ig': 'ndewo craig. ọ na-esi ike ichekwa ego mgbe ego batara dị ntakịrị, mana ọ ga-ekwe omume'}
out = {}
def strip_wn(model):
    n = 0
    for mod in model.modules():
        try:
            torch.nn.utils.remove_weight_norm(mod); n += 1
        except Exception: pass
        try:
            from torch.nn.utils import parametrize
            if parametrize.is_parametrized(mod):
                for name in list(mod.parametrizations.keys()): parametrize.remove_parametrizations(mod, name, leave_parametrized=True); n += 1
        except Exception: pass
    return n
for key, mid in M.items():
    r = {'model': mid}
    try:
        tok = AutoTokenizer.from_pretrained(mid); model = VitsModel.from_pretrained(mid); model.eval()
        r['weight_norm_removed'] = strip_wn(model)
        d = f'voices/{key}'; os.makedirs(d, exist_ok=True)
        for f in ['vocab.json', 'tokenizer_config.json', 'config.json', 'special_tokens_map.json']:
            try: shutil.copy(hf_hub_download(mid, f), f'{d}/{f}')
            except Exception as e: r['missing_' + f] = str(e)[:80]
        text = T[key[:2]]; ids = tok(text, return_tensors='pt')
        class W(torch.nn.Module):
            def __init__(s, m): super().__init__(); s.m = m
            def forward(s, input_ids, attention_mask): return s.m(input_ids=input_ids, attention_mask=attention_mask).waveform
        torch.onnx.export(W(model), (ids['input_ids'], ids['attention_mask']), f'{d}/fp32.onnx', input_names=['input_ids', 'attention_mask'], output_names=['waveform'],
                          dynamic_axes={'input_ids': {1: 'n'}, 'attention_mask': {1: 'n'}, 'waveform': {1: 's'}}, opset_version=17, dynamo=False)
        ms, ok = simplify(onnx.load(f'{d}/fp32.onnx')); onnx.save(ms, f'{d}/sim.onnx'); r['simplified'] = ok
        quantize_dynamic(f'{d}/sim.onnx', f'{d}/model_q8.onnx', weight_type=QuantType.QUInt8)
        r['size_fp32_mb'] = round(os.path.getsize(f'{d}/fp32.onnx') / 1e6, 1); r['size_q8_mb'] = round(os.path.getsize(f'{d}/model_q8.onnx') / 1e6, 1)
        sr = model.config.sampling_rate; r['rate'] = sr
        for tag, f in [('fp32', f'{d}/sim.onnx'), ('q8', f'{d}/model_q8.onnx')]:
            s = ort.InferenceSession(f, providers=['CPUExecutionProvider']); t0 = time.time()
            wav = s.run(None, {'input_ids': ids['input_ids'].numpy(), 'attention_mask': ids['attention_mask'].numpy()})[0][0]
            r[tag + '_ms'] = int((time.time() - t0) * 1000); r[tag + '_sec'] = round(len(wav) / sr, 2)
            f0, _, _ = librosa.pyin(wav.astype(np.float64), fmin=60, fmax=450, sr=sr); f0 = f0[~np.isnan(f0)]
            r[tag + '_pitch'] = round(float(np.median(f0)), 1) if len(f0) else None
            r[tag + '_rms'] = round(float(np.sqrt(np.mean(wav ** 2))), 4)
            wf.write(f'res/{key}_{tag}.wav', sr, (np.clip(wav, -1, 1) * 32767).astype(np.int16))
        r['ids_sample'] = ids['input_ids'][0][:24].tolist()
        for f in ['fp32.onnx', 'sim.onnx']: os.remove(f'{d}/{f}')
    except Exception as e:
        r['err'] = traceback.format_exc()[-600:]
    out[key] = r; print(key, json.dumps(r)[:500])
json.dump(out, open('res/conv.json', 'w'), indent=1, ensure_ascii=False)
