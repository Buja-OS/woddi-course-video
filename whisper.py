import json,glob,os
from faster_whisper import WhisperModel
m=WhisperModel('small',device='cpu',compute_type='int8')
r={}
for f in sorted(glob.glob('res/live_*.mp3')):
    segs,info=m.transcribe(f,beam_size=1)
    r[os.path.basename(f)]={'detected':info.language,'prob':round(info.language_probability,2),'duration':round(info.duration,1),'heard':' '.join(s.text for s in segs)[:300]}
json.dump(r,open('res/whisper.json','w'),indent=1,ensure_ascii=False)
print(json.dumps(r,indent=1,ensure_ascii=False))
