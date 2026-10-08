import json, re, unicodedata, numpy as np, soundfile as sf, torch, librosa
from transformers import Wav2Vec2ForCTC, AutoProcessor
res = json.load(open('out/synth.json'))
CODE = {'sw': 'swh', 'ha': 'hau', 'yo': 'yor', 'ig': 'ibo', 'ar': 'ara'}
proc = AutoProcessor.from_pretrained('facebook/mms-1b-all'); model = Wav2Vec2ForCTC.from_pretrained('facebook/mms-1b-all')
def norm(s):
    s = unicodedata.normalize('NFD', s.lower()); s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return re.sub(r'[^\w ]+', ' ', s).split()
def cer(a, b):
    a = ' '.join(norm(a)); b = ' '.join(norm(b))
    d = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        p, d[0] = d[0], i
        for j, cb in enumerate(b, 1): p, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, p + (ca != cb))
    return d[len(b)] / max(1, len(a))
out = []; cur = None
for lang, tag, path, text in sorted(res):
    if cur != lang:
        proc.tokenizer.set_target_lang(CODE[lang]); model.load_adapter(CODE[lang]); cur = lang
    w, sr = sf.read(path); w = librosa.resample(np.asarray(w, dtype=np.float32), orig_sr=sr, target_sr=16000)
    with torch.no_grad(): ids = torch.argmax(model(**proc(w, sampling_rate=16000, return_tensors='pt')).logits, -1)[0]
    hyp = proc.decode(ids)
    f0 = librosa.yin(w, fmin=70, fmax=400, sr=16000); f0 = f0[(f0 > 75) & (f0 < 390)]
    out.append({'lang': lang, 'tag': tag, 'file': path, 'cer': round(cer(text, hyp), 3), 'dur': round(len(w) / 16000, 2), 'f0_mean': round(float(np.median(f0)), 1) if len(f0) else 0, 'f0_std_st': round(float(np.std(12 * np.log2(f0 / np.median(f0)))), 2) if len(f0) else 0, 'hyp': hyp, 'ref': text})
    print(out[-1]['lang'], out[-1]['tag'], out[-1]['cer'], out[-1]['f0_mean'], out[-1]['f0_std_st'], flush=True)
json.dump(out, open('out/asr.json', 'w'), ensure_ascii=False, indent=1)
import collections
agg = collections.defaultdict(list)
for o in out: agg[(o['lang'], o['tag'])].append(o)
for k, v in sorted(agg.items()): print('SUMMARY', k, 'cer', round(np.mean([x['cer'] for x in v]), 3), 'f0', round(np.mean([x['f0_mean'] for x in v])), 'pitchvar', round(np.mean([x['f0_std_st'] for x in v]), 2))
