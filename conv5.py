import json, os, time, numpy as np, torch, scipy.io.wavfile as wf, librosa, onnx, onnxruntime as ort, shutil, traceback
from onnx import numpy_helper, helper, TensorProto
from transformers import VitsModel, AutoTokenizer
from huggingface_hub import hf_hub_download
from onnxsim import simplify
os.makedirs('res', exist_ok=True); os.makedirs('voices', exist_ok=True); os.makedirs('/tmp/big', exist_ok=True)
M = {'yo-a': 'davidguzmanr/mms-tts-yor-finetuned', 'yo-b': 'Toadoum/yoruba-mms-tts-moz', 'ig-a': 'nexusbert/igbo-mms-tts'}
T = {'yo': 'báwo ni craig bí owó tí ń wọlé kò bá pọ̀ a máa ń nira láti fi pamọ́ àmọ́ ó ṣeé ṣe',
     'ig': 'ndewo craig ọ na-esi ike ichekwa ego mgbe ego batara dị ntakịrị mana ọ ga-ekwe omume'}
def strip_wn(model):
    from torch.nn.utils import parametrize
    n = 0
    for mod in model.modules():
        try: torch.nn.utils.remove_weight_norm(mod); n += 1
        except Exception: pass
        try:
            if parametrize.is_parametrized(mod):
                for name in list(mod.parametrizations.keys()): parametrize.remove_parametrizations(mod, name, leave_parametrized=True); n += 1
        except Exception: pass
    return n
def wq8(src, dst):
    """weight-only 8-bit: big float weights stored as uint8 + per-channel scale, turned back into floats by DequantizeLinear"""
    m = onnx.load(src); g = m.graph; new_init = []; nodes = []; n = 0
    for init in list(g.initializer):
        a = numpy_helper.to_array(init)
        if a.dtype != np.float32 or a.size < 4096 or a.ndim < 2: new_init.append(init); continue
        ch = a.reshape(a.shape[0], -1); lo = ch.min(1); hi = ch.max(1)
        lo = np.minimum(lo, 0); hi = np.maximum(hi, 0)
        scale = ((hi - lo) / 255.0).astype(np.float32); scale[scale == 0] = 1e-8
        zp = np.clip(np.round(-lo / scale), 0, 255).astype(np.uint8)
        q = np.clip(np.round(ch / scale[:, None]) + zp[:, None], 0, 255).astype(np.uint8).reshape(a.shape)
        nm = init.name
        new_init += [numpy_helper.from_array(q, nm + '_q8'), numpy_helper.from_array(scale, nm + '_sc'), numpy_helper.from_array(zp, nm + '_zp')]
        nodes.append(helper.make_node('DequantizeLinear', [nm + '_q8', nm + '_sc', nm + '_zp'], [nm], axis=0, name=nm + '_dq')); n += 1
    del g.initializer[:]; g.initializer.extend(new_init)
    old = list(g.node); del g.node[:]; g.node.extend(nodes + old)
    onnx.save(m, dst); return n
def snr(ref, x):
    k = min(len(ref), len(x)); ref = ref[:k]; x = x[:k]
    return round(float(10 * np.log10(np.sum(ref ** 2) / (np.sum((ref - x) ** 2) + 1e-12))), 1), len(ref) == len(x)
def run(f, ids):
    s = ort.InferenceSession(f, providers=['CPUExecutionProvider']); t0 = time.time()
    w = s.run(None, {'input_ids': ids['input_ids'].numpy(), 'attention_mask': ids['attention_mask'].numpy()})[0][0]
    return w, int((time.time() - t0) * 1000)
class Wrap(torch.nn.Module):
    def __init__(s, m): super().__init__(); s.m = m
    def forward(s, input_ids, attention_mask): return s.m(input_ids=input_ids, attention_mask=attention_mask).waveform
def export(model, ids, path):
    torch.onnx.export(Wrap(model), (ids['input_ids'], ids['attention_mask']), path, input_names=['input_ids', 'attention_mask'], output_names=['waveform'],
                      dynamic_axes={'input_ids': {1: 'n'}, 'attention_mask': {1: 'n'}, 'waveform': {1: 's'}}, opset_version=17, dynamo=False)
    ms, ok = simplify(onnx.load(path)); onnx.save(ms, path); return ok
out = {}
for key, mid in M.items():
    r = {'model': mid}
    try:
        tok = AutoTokenizer.from_pretrained(mid); model = VitsModel.from_pretrained(mid); model.eval(); r['wn'] = strip_wn(model)
        d = f'voices/{key}'; os.makedirs(d, exist_ok=True)
        for f in ['vocab.json', 'tokenizer_config.json', 'config.json']:
            try: shutil.copy(hf_hub_download(mid, f), f'{d}/{f}')
            except Exception as e: r['missing_' + f] = str(e)[:80]
        ids = tok(T[key[:2]], return_tensors='pt'); sr = model.config.sampling_rate
        r['noise_scale'] = model.config.noise_scale if hasattr(model.config, 'noise_scale') else None
        # 1) deterministic check (no randomness): fp32 vs 8-bit
        ns, nsd = model.noise_scale, model.noise_scale_duration
        model.noise_scale = 0.0; model.noise_scale_duration = 0.0
        export(model, ids, '/tmp/big/det.onnx'); n = wq8('/tmp/big/det.onnx', '/tmp/big/det_q8.onnx')
        a, _ = run('/tmp/big/det.onnx', ids); b, _ = run('/tmp/big/det_q8.onnx', ids)
        r['det_snr_db'], r['det_same_length'] = snr(a, b); r['tensors_quantized'] = n
        wf.write(f'res/{key}_det_fp32.wav', sr, (np.clip(a, -1, 1) * 32767).astype(np.int16)); wf.write(f'res/{key}_det_q8.wav', sr, (np.clip(b, -1, 1) * 32767).astype(np.int16))
        # 2) the real voice (natural variation on), 8-bit, published
        model.noise_scale = ns; model.noise_scale_duration = nsd
        export(model, ids, '/tmp/big/full.onnx'); wq8('/tmp/big/full.onnx', f'{d}/model_q8.onnx')
        r['size_q8_mb'] = round(os.path.getsize(f'{d}/model_q8.onnx') / 1e6, 1)
        w, ms_ = run(f'{d}/model_q8.onnx', ids); r['q8_ms'] = ms_; r['q8_sec'] = round(len(w) / sr, 2)
        f0, _, _ = librosa.pyin(w.astype(np.float64), fmin=60, fmax=450, sr=sr); f0 = f0[~np.isnan(f0)]; r['q8_pitch'] = round(float(np.median(f0)), 1) if len(f0) else None
        wf.write(f'res/{key}_q8.wav', sr, (np.clip(w, -1, 1) * 32767).astype(np.int16))
        r['ids_head'] = ids['input_ids'][0][:20].tolist()
    except Exception:
        r['err'] = traceback.format_exc()[-900:]
    out[key] = r; print(key, json.dumps(r))
json.dump(out, open('res/conv5.json', 'w'), indent=1, ensure_ascii=False)
