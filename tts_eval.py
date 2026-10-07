"""Synthesize sample sentences with candidate TTS models, then transcribe them back with ASR to measure intelligibility."""
import json, os, re, sys, unicodedata, time, traceback
import torch, numpy as np, soundfile as sf
from transformers import VitsModel, AutoTokenizer, pipeline
torch.set_num_threads(4)
S = json.load(open('samples.json'))
S['yo'].append('Ẹ wọn 1658 gíráàmù.'); S['ha'].append('Ki auna gram 1658.'); S['ig'].append('Tụọ gram 1658.'); S['sw'].append('Pima gramu 1658.'); S['ar'].append('زِنِي 1658 غْرَامًا.')
CANDS = {
 'yo': ['facebook/mms-tts-yor', 'multilingual-tts/VITS-OpenBible-Yoruba'],
 'ha': ['facebook/mms-tts-hau', 'multilingual-tts/VITS-OpenBible-Hausa'],
 'ig': ['alsonNifemi/mms-tts-ibo', 'waxal-benchmarking/mms-tts-ibo-rnjema101', 'rnjema-unima/mms-tts-ibo-baseline', 'multilingual-tts/VITS-OpenBible-Igbo'],
 'sw': ['facebook/mms-tts-swh'],
 'ar': ['facebook/mms-tts-ara'],
}
try:
    from uroman import Uroman; U = Uroman()
except Exception as e:
    U = None; print('no uroman', e)
os.makedirs('out', exist_ok=True)
res = {}
for lang, models in CANDS.items():
    for mid in models:
        tag = mid.split('/')[-1]
        try:
            tok = AutoTokenizer.from_pretrained(mid); model = VitsModel.from_pretrained(mid); model.eval()
            uro = getattr(tok, 'is_uroman', False)
            for i, t in enumerate(S[lang]):
                txt = U.romanize_string(t) if (uro and U) else t
                inp = tok(txt, return_tensors='pt')
                t0 = time.time()
                with torch.no_grad(): wav = model(**inp).waveform[0].numpy()
                sf.write(f'out/{lang}_{tag}_{i}.wav', wav, model.config.sampling_rate)
                res.setdefault(lang, {}).setdefault(tag, []).append({'i': i, 'uroman': uro, 'sec': round(len(wav) / model.config.sampling_rate, 2), 'gen': round(time.time() - t0, 2)})
            print('OK', mid, flush=True)
        except Exception as e:
            print('FAIL', mid, e); res.setdefault(lang, {})[tag] = str(e)[:300]
json.dump(res, open('out/synth.json', 'w'), indent=1)
# ASR back-transcription
WL = {'yo': 'yoruba', 'ha': 'hausa', 'sw': 'swahili', 'ar': 'arabic'}
asr = pipeline('automatic-speech-recognition', model='openai/whisper-small', device=-1)
mms = None
out = {}
import glob
for f in sorted(glob.glob('out/*.wav')):
    lang = os.path.basename(f).split('_')[0]
    try:
        if lang in WL:
            r = asr(f, generate_kwargs={'language': WL[lang], 'task': 'transcribe'})['text']
        else:
            if mms is None:
                from transformers import Wav2Vec2ForCTC, AutoProcessor
                proc = AutoProcessor.from_pretrained('facebook/mms-1b-all', target_lang='ibo'); mm = Wav2Vec2ForCTC.from_pretrained('facebook/mms-1b-all', target_lang='ibo', ignore_mismatched_sizes=True)
                mms = (proc, mm)
            proc, mm = mms
            import librosa
            a, sr = librosa.load(f, sr=16000)
            iv = proc(a, sampling_rate=16000, return_tensors='pt')
            with torch.no_grad(): lg = mm(**iv).logits
            r = proc.decode(torch.argmax(lg, dim=-1)[0])
        out[os.path.basename(f)] = r
        print(os.path.basename(f), '=>', r, flush=True)
    except Exception as e:
        out[os.path.basename(f)] = 'ERR ' + str(e)[:200]
json.dump(out, open('out/asr.json', 'w'), ensure_ascii=False, indent=1)
