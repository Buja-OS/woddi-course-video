import json, os, sys, traceback, time, re, unicodedata
import numpy as np, soundfile as sf, torch
S = json.load(open('sents.json')); os.makedirs('out/wav', exist_ok=True)
res = []
def save(name, lang, i, wav, sr):
    p = 'out/wav/%s_%s_%d.wav' % (lang, name, i); sf.write(p, np.asarray(wav, dtype=np.float32), sr); return p
def mms(repo, lang, tag, **kw):
    from transformers import VitsModel, AutoTokenizer
    tok = AutoTokenizer.from_pretrained(repo); m = VitsModel.from_pretrained(repo)
    for k, v in kw.items(): setattr(m, k, v)
    for i, t in enumerate(S[lang]):
        x = tok(t, return_tensors='pt')
        with torch.no_grad(): w = m(**x).waveform[0].numpy()
        res.append((lang, tag, save(tag, lang, i, w, m.config.sampling_rate), t))
def speecht5(repo, lang, tag):
    from transformers import SpeechT5Processor, SpeechT5ForTextToSpeech, SpeechT5HifiGan
    from huggingface_hub import hf_hub_download
    pr = SpeechT5Processor.from_pretrained(repo); m = SpeechT5ForTextToSpeech.from_pretrained(repo); voc = SpeechT5HifiGan.from_pretrained('microsoft/speecht5_hifigan')
    emb = torch.load(hf_hub_download(repo, 'speaker_embeddings.pt'), weights_only=False)
    if isinstance(emb, dict): emb = list(emb.values())[0]
    emb = torch.as_tensor(emb).float()
    if emb.dim() == 1: emb = emb[None]
    emb = emb[:1]
    for i, t in enumerate(S[lang]):
        x = pr(text=t, return_tensors='pt')
        with torch.no_grad(): w = m.generate_speech(x['input_ids'], emb, vocoder=voc).numpy()
        res.append((lang, tag, save(tag, lang, i, w, 16000), t))
def coqui(repo, lang, tag, files):
    from huggingface_hub import snapshot_download
    from TTS.api import TTS
    d = snapshot_download(repo, allow_patterns=files)
    cfg = os.path.join(d, 'config.json')
    mp = [os.path.join(d, f) for f in files if f.endswith('.pth') and 'speaker' not in f and 'd_vector' not in f][0]
    # point speaker files in the config at the downloaded copies
    c = json.load(open(cfg))
    def fix(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if isinstance(v, str) and (v.endswith('.pth') or v.endswith('.json')) and os.path.exists(os.path.join(d, os.path.basename(v))): o[k] = os.path.join(d, os.path.basename(v))
                else: fix(v)
        elif isinstance(o, list):
            for v in o: fix(v)
    fix(c); cfg2 = os.path.join(d, 'config_fixed.json'); json.dump(c, open(cfg2, 'w'))
    tts = TTS(model_path=mp, config_path=cfg2)
    spk = None
    try:
        sp = tts.speakers
        print(tag, 'speakers', sp[:20] if sp else sp, flush=True)
        if sp: spk = sp[0]
    except Exception as e: print(tag, 'no speakers', e)
    for i, t in enumerate(S[lang]):
        w = tts.tts(text=t, speaker=spk) if spk else tts.tts(text=t)
        res.append((lang, tag, save(tag, lang, i, w, tts.synthesizer.output_sample_rate), t))
def piper(lang, tag, voice):
    from huggingface_hub import hf_hub_download
    from piper import PiperVoice
    on = hf_hub_download('rhasspy/piper-voices', voice + '.onnx'); hf_hub_download('rhasspy/piper-voices', voice + '.onnx.json')
    v = PiperVoice.load(on)
    for i, t in enumerate(S[lang]):
        chunks = list(v.synthesize(t))
        w = np.concatenate([c.audio_float_array for c in chunks])
        res.append((lang, tag, save(tag, lang, i, w, v.config.sample_rate), t))
JOBS = [
 ('sw', 'mms', lambda: mms('facebook/mms-tts-swh', 'sw', 'mms')),
 ('sw', 'mmstuned', lambda: mms('facebook/mms-tts-swh', 'sw', 'mmstuned', noise_scale=0.45, speaking_rate=0.92, noise_scale_duration=0.6)),
 ('sw', 'mussa', lambda: mms('mussacharles60/swahili-tts-female-voice', 'sw', 'mussa')),
 ('sw', 'openbible', lambda: coqui('multilingual-tts/VITS-OpenBible-Swahili', 'sw', 'openbible', ['config.json', 'model_last.pth', 'speakers.pth'])),
 ('ha', 'mms', lambda: mms('facebook/mms-tts-hau', 'ha', 'mms')),
 ('ha', 'mmstuned', lambda: mms('facebook/mms-tts-hau', 'ha', 'mmstuned', noise_scale=0.45, speaking_rate=0.92, noise_scale_duration=0.6)),
 ('ha', 'twb', lambda: coqui('CLEAR-Global/TWB-Voice-Hausa-TTS-1.0', 'ha', 'twb', ['config.json', 'config_se.json', 'best_model_498283.pth', 'd_vector.pth', 'speakers.pth', 'speakers.json', 'model_se.pth', 'language_ids.json'])),
 ('yo', 'mms', lambda: mms('facebook/mms-tts-yor', 'yo', 'mms')),
 ('yo', 'mmstuned', lambda: mms('facebook/mms-tts-yor', 'yo', 'mmstuned', noise_scale=0.45, speaking_rate=0.92, noise_scale_duration=0.6)),
 ('yo', 'imhotep', lambda: speecht5('ImhotepAI/yoruba-tts', 'yo', 'imhotep')),
 ('yo', 'openbible', lambda: coqui('multilingual-tts/VITS-OpenBible-Yoruba', 'yo', 'openbible', ['config.json', 'model_last.pth', 'speakers.pth'])),
 ('ig', 'mms', lambda: mms('rnjema-unima/mms-tts-ibo-baseline', 'ig', 'mms')),
 ('ig', 'openbible', lambda: coqui('multilingual-tts/VITS-OpenBible-Igbo', 'ig', 'openbible', ['config.json', 'model_last.pth', 'speakers.pth'])),
 ('ar', 'mms', lambda: mms('facebook/mms-tts-ara', 'ar', 'mms')),
 ('ar', 'openbible', lambda: coqui('multilingual-tts/VITS-OpenBible-Arabic-Standard', 'ar', 'openbible', ['config.json', 'model_last.pth', 'speakers.pth'])),
 ('ar', 'piper', lambda: piper('ar', 'piper', 'ar/ar_JO/kareem/medium/ar_JO-kareem-medium')),
]
only = sys.argv[1:] 
for lang, tag, fn in JOBS:
    if only and lang not in only: continue
    t0 = time.time()
    try: fn(); print('OK', lang, tag, round(time.time() - t0, 1), 's', flush=True)
    except Exception as e: print('FAIL', lang, tag, repr(e)[:300], flush=True); traceback.print_exc(limit=3)
json.dump(res, open('out/synth.json', 'w'), ensure_ascii=False)
