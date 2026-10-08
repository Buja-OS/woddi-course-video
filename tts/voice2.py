"""Narrate v2 scripts for one language and a list of courses (runs on GitHub Actions).
Engines, chosen by a listening test scored with speech recognition (lower error = clearer speech):
  en, fr, pt  Kokoro (af_heart, ff_siwis, pf_dora)
  sw, ha, ar  Meta MMS-TTS with calmer settings (less wobble, slightly slower)
  yo, ig      VITS OpenBible voices (multilingual-tts, CC BY-SA 4.0): clearer than MMS for these two
Usage: python3 voice2.py <lang> <scripts_dir> <out_dir> <course> [<course> ...]
Writes <out_dir>/<course>/<module>/s<shot>_<k>.opus"""
import json, os, sys, glob, re, subprocess, random
import numpy as np, soundfile as sf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
lang, sdir, odir = sys.argv[1:4]; courses = sys.argv[4:]

UNITS = {
 'sw': [('%', ' asilimia'), ('₦', 'naira ')], 'ha': [('%', ' kashi cikin ɗari'), ('₦', 'naira ')],
 'ig': [('%', ' pasentị'), ('₦', 'naira ')], 'yo': [('%', ' pásẹ́ǹtì'), ('₦', 'náírà ')], 'ar': [('%', ' بالمئة'), ('₦', 'نيرة ')],
}
KUNITS = {
 'en': [(r'(\d)\s?kg\b', r'\1 kilograms'), (r'(\d)\s?g\b', r'\1 grams'), (r'(\d)\s?ml\b', r'\1 millilitres'), (r'(\d)\s?L\b', r'\1 litres'), (r'(\d)\s?%', r'\1 percent'), (r'₦\s?([\d,\.]+)', r'\1 naira'), (r'(\d)\s?°C', r'\1 degrees Celsius'), (r'\bpH\b', 'P H')],
 'fr': [(r'(\d)\s?kg\b', r'\1 kilos'), (r'(\d)\s?g\b', r'\1 grammes'), (r'(\d)\s?ml\b', r'\1 millilitres'), (r'(\d)\s?L\b', r'\1 litres'), (r'(\d)\s?%', r'\1 pour cent'), (r'₦\s?([\d,\.  ]+)', r'\1 nairas'), (r'(\d)\s?°C', r'\1 degrés'), (r'\bpH\b', 'pé ache')],
 'pt': [(r'(\d)\s?kg\b', r'\1 quilos'), (r'(\d)\s?g\b', r'\1 gramas'), (r'(\d)\s?ml\b', r'\1 mililitros'), (r'(\d)\s?L\b', r'\1 litros'), (r'(\d)\s?%', r'\1 por cento'), (r'₦\s?([\d,\.  ]+)', r'\1 nairas'), (r'(\d)\s?°C', r'\1 graus'), (r'\bpH\b', 'pê agá')],
}


def knorm(t):
    t = t.replace('’', "'").replace(' ', ' ').replace(' ', ' ')
    for a, b in KUNITS[lang]: t = re.sub(a, b, t)
    t = re.sub(r'(\d)[,  ](\d{3})\b', r'\1\2', t); t = re.sub(r'(\d)[,  ](\d{3})\b', r'\1\2', t)
    if lang in ('fr', 'pt'):
        t = re.sub(r'(\d)\.(\d)', r'\1,\2', t)
        t = re.sub(r'(\d+):(\d+)', lambda m: m.group(1) + (' pour ' if lang == 'fr' else ' para ') + m.group(2), t)
    else:
        t = re.sub(r'(\d+):(\d+)', r'\1 to \2', t)
    return re.sub(r'\*\*', '', t)


def vnorm(t):
    from numwords import spell
    t = t.replace(' ', ' ').replace(' ', ' ')
    for a, b in UNITS[lang]: t = t.replace(a, b)
    t = spell(t, lang)
    t = re.sub(r'[“”"«»()\[\]*]', '', t)
    return re.sub(r'\s+', ' ', t).strip()


def trim(a, sr):
    nz = np.where(np.abs(a) > 0.01)[0]
    return a[max(0, nz[0] - int(0.02 * sr)): nz[-1] + int(0.05 * sr)] if len(nz) else a


if lang in ('en', 'fr', 'pt'):
    from kokoro_onnx import Kokoro
    K = Kokoro('kokoro-v1.0.onnx', 'voices-v1.0.bin')
    VOICE = {'en': 'af_heart', 'fr': 'ff_siwis', 'pt': 'pf_dora'}; KL = {'en': 'en-us', 'fr': 'fr-fr', 'pt': 'pt-br'}; SP = {'en': 0.96, 'fr': 0.98, 'pt': 0.98}
    def synth(text):
        a, sr = K.create(knorm(text), voice=VOICE[lang], speed=SP[lang] * random.uniform(0.98, 1.02), lang=KL[lang])
        return np.asarray(a, dtype=np.float32), sr
elif lang in ('sw', 'ha', 'ar'):
    import torch
    from transformers import VitsModel, AutoTokenizer
    torch.set_num_threads(4)
    mid = {'sw': 'facebook/mms-tts-swh', 'ha': 'facebook/mms-tts-hau', 'ar': 'facebook/mms-tts-ara'}[lang]
    tok = AutoTokenizer.from_pretrained(mid); M = VitsModel.from_pretrained(mid); M.eval()
    M.noise_scale = 0.45; M.noise_scale_duration = 0.6; M.speaking_rate = 0.92
    U = None
    if getattr(tok, 'is_uroman', False):
        from uroman import Uroman; U = Uroman()
    def synth(text):
        t = vnorm(text)
        if U: t = U.romanize_string(t)
        parts = [p for p in re.split(r'(?<=[,;:،.!?])\s+', t) if p.strip()] if len(t) > 160 else [t]
        out = []; sr = M.config.sampling_rate
        for p in parts:
            torch.manual_seed(1); x = tok(p, return_tensors='pt')
            if x['input_ids'].shape[1] < 2: continue
            with torch.no_grad(): w = M(**x).waveform[0].numpy()
            out += [trim(w, sr), np.zeros(int(0.14 * sr), dtype=np.float32)]
        return (np.concatenate(out) if out else np.zeros(int(0.3 * sr), dtype=np.float32)), sr
else:
    from huggingface_hub import snapshot_download
    from TTS.api import TTS
    repo = {'yo': 'multilingual-tts/VITS-OpenBible-Yoruba', 'ig': 'multilingual-tts/VITS-OpenBible-Igbo'}[lang]
    d = snapshot_download(repo, allow_patterns=['config.json', 'model_last.pth', 'speakers.pth'])
    c = json.load(open(os.path.join(d, 'config.json')))
    def fix(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if isinstance(v, str) and v.endswith(('.pth', '.json')) and os.path.exists(os.path.join(d, os.path.basename(v))): o[k] = os.path.join(d, os.path.basename(v))
                else: fix(v)
        elif isinstance(o, list):
            for v in o: fix(v)
    fix(c); cf = os.path.join(d, 'config_fixed.json'); json.dump(c, open(cf, 'w'))
    T = TTS(model_path=os.path.join(d, 'model_last.pth'), config_path=cf); SR = T.synthesizer.output_sample_rate
    # Yoruba: the translations come without tone marks; restore them (kenny0bi/ami-yoruba-diacritics, about 86%
    # of words right) so the voice, trained on fully marked text, reads the tones. Falls back to plain text.
    RESTORE = None
    if lang == 'yo':
        try:
            rd = snapshot_download('kenny0bi/ami-yoruba-diacritics'); sys.path.insert(0, rd)
            from restore import load_restorer
            RESTORE = load_restorer(rd)
            print('tone restore sample:', RESTORE.restore('bawo ni oko re se n lo'), flush=True)
        except Exception as e:
            print('tone restore unavailable', repr(e)[:200], flush=True)
    def synth(text):
        t = vnorm(text)
        if RESTORE:
            try: t = RESTORE.restore(t)
            except Exception: pass
        parts = [p for p in re.split(r'(?<=[,;:.!?])\s+', t) if p.strip()] if len(t) > 180 else [t]
        out = []
        for p in parts:
            w = np.asarray(T.tts(text=p), dtype=np.float32)
            out += [trim(w, SR), np.zeros(int(0.14 * SR), dtype=np.float32)]
        return np.concatenate(out), SR

random.seed(7)
for course in courses:
    for sp in sorted(glob.glob(os.path.join(sdir, course, 'm*.json'))):
        parts = os.path.basename(sp).split('.')
        if (lang == 'en' and len(parts) != 2) or (lang != 'en' and (len(parts) != 3 or parts[1] != lang)): continue
        mod = parts[0]; S = json.load(open(sp)); od = os.path.join(odir, course, mod); os.makedirs(od, exist_ok=True)
        for i, sh in enumerate(S['shots']):
            for j, s in enumerate(sh['say']):
                out = os.path.join(od, 's%02d_%d.opus' % (i, j))
                if os.path.exists(out): continue
                try:
                    a, sr = synth(s)
                except Exception as e:
                    print('TTS error', course, mod, i, j, repr(e)[:200], flush=True); a, sr = np.zeros(8000, dtype=np.float32), 16000
                a = trim(a, sr); peak = np.max(np.abs(a)) or 1.0; a = a * min(1.0, 0.95 / peak)
                wav = out[:-5] + '.wav'; sf.write(wav, a, sr)
                subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-i', wav, '-c:a', 'libopus', '-b:a', '40k', out], check=True); os.remove(wav)
        print('voiced', lang, course, mod, flush=True)
