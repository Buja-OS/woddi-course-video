"""Narrate v2 scripts with a VITS/MMS voice for one language (runs on GitHub Actions).
Usage: python3 voice_mms.py <lang> <model_id> <scripts_dir> <out_dir>
Writes <out_dir>/<course>/<module>/s<shot>_<k>.opus"""
import json, os, sys, glob, re, subprocess
import torch, numpy as np, soundfile as sf
from transformers import VitsModel, AutoTokenizer
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from numwords import spell
torch.set_num_threads(4)
lang, mid, sdir, odir = sys.argv[1:5]
UNITS = {
 'sw': [('%', ' asilimia'), ('₦', 'naira ')], 'ha': [('%', ' kashi cikin ɗari'), ('₦', 'naira ')],
 'ig': [('%', ' pasentị'), ('₦', 'naira ')], 'yo': [('%', ' pásẹ́ǹtì'), ('₦', 'náírà ')], 'ar': [('%', ' بالمئة'), ('₦', 'نيرة ')],
}
tok = AutoTokenizer.from_pretrained(mid); model = VitsModel.from_pretrained(mid); model.eval()
uro = getattr(tok, 'is_uroman', False)
U = None
if uro:
    from uroman import Uroman; U = Uroman()
sr = model.config.sampling_rate
def clean(t):
    for a, b in UNITS[lang]: t = t.replace(a, b)
    t = re.sub(r'\b(kg|g|ml|L)\b', '', t) if False else t
    t = spell(t, lang)
    t = re.sub(r'[“”"«»()\[\]]', '', t)
    return re.sub(r'\s+', ' ', t).strip()
for sp in sorted(glob.glob(os.path.join(sdir, '*', 'm?.%s.json' % lang))):
    course = os.path.basename(os.path.dirname(sp)); mod = os.path.basename(sp).split('.')[0]
    S = json.load(open(sp)); od = os.path.join(odir, course, mod); os.makedirs(od, exist_ok=True)
    for i, sh in enumerate(S['shots']):
        for j, s in enumerate(sh['say']):
            txt = clean(s)
            if U: txt = U.romanize_string(txt)
            # long sentences: synthesize clause by clause so the voice does not drift, join with short pauses
            parts = [p for p in re.split(r'(?<=[,;:،])\s+', txt) if p.strip()] if len(txt) > 160 else [txt]
            audio = []
            for k, p in enumerate(parts):
                torch.manual_seed(1)
                inp = tok(p, return_tensors='pt')
                if inp['input_ids'].shape[1] < 2: continue
                with torch.no_grad(): w = model(**inp).waveform[0].numpy()
                audio.append(w); audio.append(np.zeros(int(0.12 * sr), dtype=np.float32))
            a = np.concatenate(audio) if audio else np.zeros(int(0.3 * sr), dtype=np.float32)
            nz = np.where(np.abs(a) > 0.01)[0]
            if len(nz): a = a[max(0, nz[0] - 400): nz[-1] + 1200]
            wav = os.path.join(od, 's%02d_%d.wav' % (i, j)); sf.write(wav, a, sr)
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', wav, '-c:a', 'libopus', '-b:a', '40k', wav[:-4] + '.opus'], check=True); os.remove(wav)
    print('voiced', lang, course, mod, flush=True)
