import json, time, os, urllib.request, numpy as np, torch, scipy.io.wavfile as wf, librosa, traceback
from transformers import VitsModel, AutoTokenizer
os.makedirs('res', exist_ok=True); out = {}
T = {'yo': 'Báwo ni, Craig. Bí owó tí ń wọlé kò bá pọ̀, a máa ń nira láti fi pamọ́, àmọ́ ó ṣeé ṣe. Kọ gbogbo ohun tí o ná sílẹ̀.',
     'ig': 'Ndewo Craig. Ọ na-esi ike ichekwa ego mgbe ego batara dị ntakịrị, mana ọ ga-ekwe omume. Dee ihe niile ị na-emefu kwa ụbọchị.'}
C = {'yo': ['facebook/mms-tts-yor', 'Owos/mms-tts-yor', 'Toadoum/yoruba-mms-tts-moz', 'offiongbassey/mms-tts-yoruba-finetuned-new', 'davidguzmanr/mms-tts-yor-finetuned', 'alexgichamba/mms-tts-yor-finetuned', 'oyemade/mms-tts-yor-fine-tuned'],
     'ig': ['nexusbert/igbo-mms-tts', 'alsonNifemi/mms-tts-ibo', 'rnjema-unima/mms-tts-ibo-baseline', 'waxal-benchmarking/mms-tts-ibo-rnjema101', 'multilingual-tts/VITS-OpenBible-Igbo']}
for lang, ids in C.items():
    for mid in ids:
        r = {}
        try:
            info = json.load(urllib.request.urlopen('https://huggingface.co/api/models/' + mid))
            r['license'] = (info.get('cardData') or {}).get('license'); r['files'] = [s['rfilename'] for s in info.get('siblings', [])][:25]; r['downloads'] = info.get('downloads')
            tok = AutoTokenizer.from_pretrained(mid); model = VitsModel.from_pretrained(mid); model.eval()
            vocab = tok.get_vocab(); norm = T[lang].lower()
            r['not_in_vocab'] = sorted(set(c for c in norm if c not in vocab and c != ' '))
            r['speakers'] = getattr(model.config, 'num_speakers', 1)
            ids_ = tok(norm, return_tensors='pt'); torch.manual_seed(1); t0 = time.time()
            with torch.no_grad(): wav = model(**ids_).waveform[0].numpy()
            r['cpu_ms'] = int((time.time() - t0) * 1000); sr = model.config.sampling_rate; r['seconds'] = round(len(wav) / sr, 2)
            f = 'res/c_' + lang + '_' + mid.replace('/', '__') + '.wav'; wf.write(f, sr, (np.clip(wav, -1, 1) * 32767).astype(np.int16))
            f0, _, _ = librosa.pyin(wav.astype(np.float64), fmin=60, fmax=450, sr=sr); f0 = f0[~np.isnan(f0)]
            r['median_pitch_hz'] = round(float(np.median(f0)), 1) if len(f0) else None
            r['params_m'] = round(sum(p.numel() for p in model.parameters()) / 1e6, 1)
        except Exception as e:
            r['err'] = repr(e)[:250]
        out[lang + ':' + mid] = r; print(mid, r)
json.dump(out, open('res/cand.json', 'w'), indent=1, ensure_ascii=False)
