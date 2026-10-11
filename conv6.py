import json, os, time, numpy as np, torch, scipy.io.wavfile as wf, librosa, onnx, onnxruntime as ort, shutil, traceback
from onnx import numpy_helper, helper, TensorProto
from transformers import VitsModel, AutoTokenizer
from huggingface_hub import hf_hub_download
from onnxsim import simplify
os.makedirs('res', exist_ok=True); os.makedirs('voices', exist_ok=True); os.makedirs('/tmp/big', exist_ok=True)
M = {'ig-a': 'nexusbert/igbo-mms-tts', 'yo-a': 'davidguzmanr/mms-tts-yor-finetuned'}
T = {'yo': 'báwo ni craig bí owó tí ń wọlé kò bá pọ̀ a máa ń nira láti fi pamọ́ àmọ́ ó ṣeé ṣe',
     'ig': 'ndewo craig ọ na-esi ike ichekwa ego mgbe ego batara dị ntakịrị mana ọ ga-ekwe omume'}
def strip_wn(model):
    from torch.nn.utils import parametrize
    for mod in model.modules():
        try: torch.nn.utils.remove_weight_norm(mod)
        except Exception: pass
        try:
            if parametrize.is_parametrized(mod):
                for name in list(mod.parametrizations.keys()): parametrize.remove_parametrizations(mod, name, leave_parametrized=True)
        except Exception: pass
def compress(src, dst, use8):
    m = onnx.load(src); g = m.graph
    consumers = {}
    for nd in g.node:
        for i in nd.input: consumers.setdefault(i, []).append(nd.name)
    new_init, nodes, st = [], [], {'q8': 0, 'f16': 0}
    for init in list(g.initializer):
        a = numpy_helper.to_array(init); nm = init.name
        if a.dtype != np.float32 or a.size < 4096 or a.ndim < 2: new_init.append(init); continue
        where = ' '.join(consumers.get(nm, [])) + ' ' + nm
        if use8(where):
            ch = a.reshape(a.shape[0], -1); lo = np.minimum(ch.min(1), 0); hi = np.maximum(ch.max(1), 0)
            sc = ((hi - lo) / 255.0).astype(np.float32); sc[sc == 0] = 1e-8; zp = np.clip(np.round(-lo / sc), 0, 255).astype(np.uint8)
            q = np.clip(np.round(ch / sc[:, None]) + zp[:, None], 0, 255).astype(np.uint8).reshape(a.shape)
            new_init += [numpy_helper.from_array(q, nm + '_q8'), numpy_helper.from_array(sc, nm + '_sc'), numpy_helper.from_array(zp, nm + '_zp')]
            nodes.append(helper.make_node('DequantizeLinear', [nm + '_q8', nm + '_sc', nm + '_zp'], [nm], axis=0, name=nm + '_dq')); st['q8'] += 1
        else:
            new_init.append(numpy_helper.from_array(a.astype(np.float16), nm + '_h'))
            nodes.append(helper.make_node('Cast', [nm + '_h'], [nm], to=TensorProto.FLOAT, name=nm + '_cast')); st['f16'] += 1
    del g.initializer[:]; g.initializer.extend(new_init); old = list(g.node); del g.node[:]; g.node.extend(nodes + old)
    onnx.save(m, dst); return st
class Wrap(torch.nn.Module):
    def __init__(s, m): super().__init__(); s.m = m
    def forward(s, input_ids, attention_mask): return s.m(input_ids=input_ids, attention_mask=attention_mask).waveform
def export(model, ids, path):
    torch.onnx.export(Wrap(model), (ids['input_ids'], ids['attention_mask']), path, input_names=['input_ids', 'attention_mask'], output_names=['waveform'],
                      dynamic_axes={'input_ids': {1: 'n'}, 'attention_mask': {1: 'n'}, 'waveform': {1: 's'}}, opset_version=17, dynamo=False)
    ms, ok = simplify(onnx.load(path)); onnx.save(ms, path)
def run(f, ids):
    s = ort.InferenceSession(f, providers=['CPUExecutionProvider'])
    return s.run(None, {'input_ids': ids['input_ids'].numpy(), 'attention_mask': ids['attention_mask'].numpy()})[0][0]
def score(a, b, sr):
    A = librosa.power_to_db(librosa.feature.melspectrogram(y=a, sr=sr, n_mels=80)); B = librosa.power_to_db(librosa.feature.melspectrogram(y=b, sr=sr, n_mels=80))
    n = min(A.shape[1], B.shape[1]); A = A[:, :n]; B = B[:, :n]; mask = A.max(0) > A.max() - 50
    fa, _, _ = librosa.pyin(a.astype(np.float64), fmin=60, fmax=450, sr=sr); fb, _, _ = librosa.pyin(b.astype(np.float64), fmin=60, fmax=450, sr=sr)
    n2 = min(len(fa), len(fb)); fa = fa[:n2]; fb = fb[:n2]; m = ~np.isnan(fa) & ~np.isnan(fb)
    return round(float(np.mean(np.abs(A[:, mask] - B[:, mask]))), 2), round(float(np.corrcoef(fa[m], fb[m])[0, 1]), 3) if m.sum() > 5 else None
V = {
 'all8': lambda w: True,
 'dec16': lambda w: 'decoder' not in w,
 'flowdec16': lambda w: 'decoder' not in w and '/flow' not in w,
 'all16': lambda w: False,
}
out = {}
for key, mid in M.items():
    r = {'model': mid}
    try:
        tok = AutoTokenizer.from_pretrained(mid); model = VitsModel.from_pretrained(mid); model.eval(); strip_wn(model)
        ids = tok(T[key[:2]], return_tensors='pt'); sr = model.config.sampling_rate
        ns, nsd = model.noise_scale, model.noise_scale_duration
        model.noise_scale = 0.0; model.noise_scale_duration = 0.0; export(model, ids, '/tmp/big/det.onnx'); ref = run('/tmp/big/det.onnx', ids)
        for vn, fn in V.items():
            st = compress('/tmp/big/det.onnx', f'/tmp/big/det_{vn}.onnx', fn); x = run(f'/tmp/big/det_{vn}.onnx', ids)
            r[vn] = {'mb': round(os.path.getsize(f'/tmp/big/det_{vn}.onnx') / 1e6, 1), 'mel_l1': None, 'pitch_corr': None, 'st': st}
            r[vn]['mel_l1'], r[vn]['pitch_corr'] = score(ref, x, sr)
            wf.write(f'res/{key}_det_{vn}.wav', sr, (np.clip(x, -1, 1) * 32767).astype(np.int16))
        # choose: smallest with mel_l1 <= 3.5 and pitch_corr >= 0.95
        ok = [v for v in V if r[v]['mel_l1'] is not None and r[v]['mel_l1'] <= 3.5 and (r[v]['pitch_corr'] or 0) >= 0.95]
        best = min(ok, key=lambda v: r[v]['mb']) if ok else 'all16'; r['chosen'] = best
        model.noise_scale = ns; model.noise_scale_duration = nsd; export(model, ids, '/tmp/big/full.onnx')
        d = f'voices/{key}'; os.makedirs(d, exist_ok=True)
        for f in ['vocab.json', 'tokenizer_config.json', 'config.json']:
            try: shutil.copy(hf_hub_download(mid, f), f'{d}/{f}')
            except Exception: pass
        compress('/tmp/big/full.onnx', f'{d}/model_q8.onnx', V[best]); r['published_mb'] = round(os.path.getsize(f'{d}/model_q8.onnx') / 1e6, 1)
        w = run(f'{d}/model_q8.onnx', ids); wf.write(f'res/{key}_final.wav', sr, (np.clip(w, -1, 1) * 32767).astype(np.int16))
    except Exception:
        r['err'] = traceback.format_exc()[-900:]
    out[key] = r; print(key, json.dumps(r))
json.dump(out, open('res/conv6.json', 'w'), indent=1)
