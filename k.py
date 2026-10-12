import json, sys, os, re, subprocess, urllib.parse, urllib.request, time
S = json.load(open('script.json')); L = sys.argv[1]; os.makedirs('out/' + L, exist_ok=True)
log = open(f'out/log-{L}.txt', 'w')
def P(*a): print(*a, flush=True); print(*a, file=log, flush=True)
if L in ('en', 'fr', 'pt'):
    from kokoro import KPipeline
    import soundfile as sf, numpy as np
    code, voice = {'en': ('a', 'af_heart'), 'fr': ('f', 'ff_siwis'), 'pt': ('p', 'pf_dora')}[L]
    pipe = KPipeline(lang_code=code)
    for b in S['beats']:
        t = b['voice'][L]; parts = []
        for gs, ps, audio in pipe(t, voice=voice, speed=0.95):
            parts.append(np.asarray(audio)); parts.append(np.zeros(int(24000 * 0.12), dtype=np.float32))
        y = np.concatenate(parts) if parts else np.zeros(2400, dtype=np.float32)
        sf.write(f'out/{L}/{b["id"]}.wav', y, 24000); P(b['id'], 'ok', round(len(y) / 24000, 2))
else:
    tl = {'ar': 'ar', 'sw': 'sw'}[L]
    def chunks(t):
        out, cur = [], ''
        for piece in re.split(r'(?<=[.!?؟،,:;])\s+', t):
            if len(cur) + len(piece) + 1 <= 180: cur = (cur + ' ' + piece).strip()
            else:
                if cur: out.append(cur)
                while len(piece) > 180:
                    cut = piece.rfind(' ', 0, 180); out.append(piece[:cut]); piece = piece[cut + 1:]
                cur = piece
        if cur: out.append(cur)
        return out
    for b in S['beats']:
        files = []
        for i, c in enumerate(chunks(b['voice'][L])):
            url = 'https://translate.google.com/translate_tts?ie=UTF-8&client=tw-ob&tl=' + tl + '&q=' + urllib.parse.quote(c)
            f = f'out/{L}/_{b["id"]}_{i}.mp3'
            for k in range(4):
                try:
                    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Chrome/120 Mobile Safari/537.36', 'Referer': 'https://translate.google.com/'})
                    open(f, 'wb').write(urllib.request.urlopen(req, timeout=20).read()); break
                except Exception as e: P('retry', b['id'], e); time.sleep(3)
            files.append(f); time.sleep(0.4)
        lst = f'out/{L}/_l.txt'; open(lst, 'w').write(''.join(f"file '{os.path.basename(x)}'\n" for x in files))
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c:a', 'libmp3lame', '-b:a', '64k', f'out/{L}/{b["id"]}.mp3'])
        for x in files: os.remove(x)
        P(b['id'], 'ok', len(files), 'parts')
    os.remove(f'out/{L}/_l.txt')
