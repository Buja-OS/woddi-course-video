#!/usr/bin/env python3
"""Translate WODDI course strings with Google's public translate endpoint. Resumable: skips strings already done."""
import json, os, re, sys, time, html, random, glob, urllib.request, urllib.parse
LANG, SHARD, NSHARD = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
GL = {'fr': 'fr', 'pt': 'pt-PT', 'ar': 'ar', 'yo': 'yo', 'ha': 'ha', 'ig': 'ig', 'sw': 'sw'}[LANG]
ids = sorted(os.path.basename(f)[:-5] for f in glob.glob('src/*.json'))
mine = [c for i, c in enumerate(ids) if i % NSHARD == SHARD]
os.makedirs(f'out/{LANG}', exist_ok=True)
URL = f'https://translate.googleapis.com/translate_a/t?client=gtx&sl=en&tl={GL}&format=html'
UA = ['Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36',
      'Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15']
stats = {'req': 0, 'retry': 0, 'fail': 0, 'done': 0}

def enc(s):  # protect markdown bold and literal html
    e = html.escape(s, quote=False)
    return re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', e)

def dec(s):
    s = re.sub(r'\s*<b>\s*', ' **', s); s = re.sub(r'\s*</b>\s*', '** ', s)
    s = html.unescape(s)
    s = re.sub(r'\s+', ' ', s).strip()
    s = re.sub(r'\*\* ([.,;:!?)])', r'**\1', s)
    return s

def call(batch):
    body = urllib.parse.urlencode([('q', enc(x)) for x in batch]).encode()
    for attempt in range(8):
        stats['req'] += 1
        try:
            req = urllib.request.Request(URL, data=body, headers={'User-Agent': random.choice(UA), 'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8'})
            with urllib.request.urlopen(req, timeout=30) as r:
                j = json.loads(r.read().decode('utf-8'))
            if isinstance(j, str): j = [j]
            j = [x[0] if isinstance(x, list) else x for x in j]
            if len(j) != len(batch): raise ValueError('count %d != %d' % (len(j), len(batch)))
            return [dec(x) for x in j]
        except Exception as e:
            stats['retry'] += 1
            code = getattr(e, 'code', 0)
            wait = (30 if code == 429 else 3) * (attempt + 1)
            print(f'  retry {attempt+1} after {wait}s: {code or type(e).__name__} {str(e)[:80]}', flush=True)
            time.sleep(wait)
    stats['fail'] += 1
    return None

blocked = 0
for cid in mine:
    src = json.load(open(f'src/{cid}.json'))
    path = f'out/{LANG}/{cid}.json'
    prev = {}
    if os.path.exists(path): prev = json.load(open(path)).get('t', {})
    todo = [s for s in src if s not in prev]
    t = dict(prev)
    i = 0
    while i < len(todo):
        batch, size = [], 0
        while i < len(todo) and len(batch) < 60 and size + len(todo[i]) < 3800:
            batch.append(todo[i]); size += len(todo[i]); i += 1
        if not batch: batch = [todo[i]]; i += 1
        res = call(batch)
        if res is None:
            blocked += 1
            if blocked >= 3: break
            continue
        blocked = 0
        for en, tr in zip(batch, res):
            if tr: t[en] = tr
        time.sleep(0.4 + random.random() * 0.4)
    json.dump({'v': 2, 'lang': LANG, 'course': cid, 't': t}, open(path, 'w'), ensure_ascii=False, separators=(',', ':'))
    stats['done'] += 1
    print(f'{LANG} {cid}: {len(t)}/{len(src)}', flush=True)
    if blocked >= 3:
        print('BLOCKED: stopping this shard early; rerun picks up the rest', flush=True); break
print('STATS', json.dumps(stats))
