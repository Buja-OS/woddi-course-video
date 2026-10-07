import json, glob, os, torch
from transformers import pipeline
torch.set_num_threads(4)
asr = pipeline('automatic-speech-recognition', model='openai/whisper-small', device=-1)
WL = {'ar': 'arabic', 'ha': 'hausa', 'sw': 'swahili', 'yo': 'yoruba'}
out = {}
for f in sorted(glob.glob('wavs/*.wav')):
    L = os.path.basename(f).split('_')[0]
    if L not in WL: continue
    out[os.path.basename(f)] = asr(f, generate_kwargs={'language': WL[L], 'task': 'transcribe'})['text']
    print(os.path.basename(f), '=>', out[os.path.basename(f)], flush=True)
json.dump(out, open('out/asr2.json', 'w'), ensure_ascii=False, indent=1)
