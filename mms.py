import json, time, os, urllib.request, numpy as np, torch, scipy.io.wavfile as wf
from transformers import VitsModel, AutoTokenizer
out = {}
os.makedirs('res', exist_ok=True)
for q in ['mms-tts-yor', 'mms-tts-ibo', 'mms-tts-hau', 'yoruba tts', 'igbo tts']:
    try:
        d = json.load(urllib.request.urlopen('https://huggingface.co/api/models?search=' + q.replace(' ', '%20') + '&limit=40'))
        out['search:' + q] = [m['id'] for m in d]
    except Exception as e: out['search:' + q] = str(e)
T = {
 'yor': ['Báwo ni, Craig. Bí owó tí ń wọlé kò bá pọ̀, a máa ń nira láti fi pamọ́, àmọ́ ó ṣeé ṣe.', 'Kọ gbogbo ohun tí o ná lójoojúmọ́ sílẹ̀, kí o sì fi díẹ̀ pamọ́ ní gbogbo ìgbà tí owó bá wọlé.'],
 'ibo': ['Ndewo Craig. Ọ na-esi ike ichekwa ego mgbe ego batara dị ntakịrị, mana ọ ga-ekwe omume.', 'Dee ihe niile ị na-emefu kwa ụbọchị, ma chekwaa ntakịrị ego oge ọ bụla ego batara.'],
}
import librosa
for lang, texts in T.items():
    mid = 'facebook/mms-tts-' + lang
    try:
        tok = AutoTokenizer.from_pretrained(mid); model = VitsModel.from_pretrained(mid); model.eval()
        r = {'uroman': getattr(tok, 'is_uroman', None), 'rate': model.config.sampling_rate, 'samples': []}
        vocab = tok.get_vocab()
        for i, t in enumerate(texts):
            norm = t.lower()
            unk = sorted(set(c for c in norm if c not in vocab and c != ' '))
            ids = tok(norm, return_tensors='pt')
            for seed in [1]:
                torch.manual_seed(seed); t0 = time.time()
                with torch.no_grad(): wav = model(**ids).waveform[0].numpy()
                ms = int((time.time() - t0) * 1000)
            f = f'res/mms_{lang}_{i}.wav'; wf.write(f, model.config.sampling_rate, (wav * 32767).astype(np.int16))
            f0, vf, _ = librosa.pyin(wav.astype(np.float64), fmin=60, fmax=400, sr=model.config.sampling_rate)
            f0 = f0[~np.isnan(f0)]
            r['samples'].append({'text': t, 'chars_not_in_vocab': unk, 'seconds': round(len(wav) / model.config.sampling_rate, 2), 'cpu_ms': ms, 'median_pitch_hz': round(float(np.median(f0)), 1) if len(f0) else None})
        # also: NFD form (tone marks as separate characters) to see which form the vocab expects
        import unicodedata
        r['vocab_has_combining'] = [c for c in vocab if unicodedata.combining(c)]
        r['vocab_size'] = len(vocab); r['vocab_sample'] = ''.join(sorted(vocab))[:200]
        out[lang] = r
    except Exception as e:
        out[lang] = 'ERR ' + repr(e)[:300]
json.dump(out, open('res/mms.json', 'w'), indent=1, ensure_ascii=False)
print(json.dumps(out, indent=1, ensure_ascii=False))
