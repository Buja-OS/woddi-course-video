import json, os, asyncio, sys, unicodedata, re, time
S = json.load(open('script.json')); L = sys.argv[1]
EDGE = {'en': 'en-NG-EzinneNeural', 'fr': 'fr-FR-DeniseNeural', 'pt': 'pt-PT-RaquelNeural', 'ar': 'ar-SA-ZariyahNeural', 'sw': 'sw-KE-ZuriNeural'}
MMS = {'ha': 'facebook/mms-tts-hau', 'yo': 'facebook/mms-tts-yor', 'ig': 'facebook/mms-tts-ibo'}
os.makedirs('out/' + L, exist_ok=True); log = open('out/log-%s.txt' % L, 'w')
def P(*a): print(*a, file=log, flush=True); print(*a, flush=True)
if L in EDGE:
    import edge_tts
    async def one(t, f):
        for k in range(5):
            try:
                await asyncio.wait_for(edge_tts.Communicate(t, EDGE[L], rate='-4%').save(f), 45); return True
            except Exception as e:
                P('retry', f, repr(e)[:120]); await asyncio.sleep(4)
        return False
    async def main():
        for b in S['beats']:
            t0 = time.time(); ok = await one(b['voice'][L], 'out/%s/%s.mp3' % (L, b['id'])); P(b['id'], ok, round(time.time() - t0, 1))
    asyncio.run(main())
else:
    import torch, numpy as np, scipy.io.wavfile as wf
    from transformers import VitsModel, AutoTokenizer
    m = MMS[L]; tok = AutoTokenizer.from_pretrained(m); model = VitsModel.from_pretrained(m); model.eval()
    vocab = set(tok.get_vocab().keys()); P('vocab', ''.join(sorted(vocab)))
    model.speaking_rate = 0.92
    for b in S['beats']:
        t = unicodedata.normalize('NFC', b['voice'][L])
        miss = sorted(set(c for c in unicodedata.normalize('NFD', t.lower()) if c not in vocab and c != ' '))
        parts = [p.strip() for p in re.split(r'(?<=[.!?:,;])\s+', t) if p.strip()]
        audio = []
        for p in parts:
            inp = tok(p, return_tensors='pt')
            with torch.no_grad():
                torch.manual_seed(7); y = model(**inp).waveform[0].numpy()
            audio.append(y); audio.append(np.zeros(int(16000 * (0.3 if p[-1] in '.!?:' else 0.15)), dtype=np.float32))
        y = np.concatenate(audio[:-1]); y = y / max(1e-6, np.abs(y).max()) * 0.92
        wf.write('out/%s/%s.wav' % (L, b['id']), 16000, (y * 32767).astype(np.int16))
        P(b['id'], 'ok', len(y) / 16000, 'missing:', ''.join(miss))
