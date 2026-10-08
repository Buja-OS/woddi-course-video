"""Translate the work units assigned to one runner. Each unit: [lang, course, start, end] over mtin/<course>.json.
Stops early when Google starts refusing (the next run picks up what is left). Output: out/<lang>/<course>.<start>.json"""
import json, os, sys, time, urllib.request, urllib.parse, random, re
SEP = '\n⁂\n'
class Blocked(Exception): pass
def call(text, tl):
    data = urllib.parse.urlencode({'client': 'gtx', 'sl': 'en', 'tl': tl, 'dt': 't', 'q': text}).encode()
    err = None
    for i in range(4):
        try:
            req = urllib.request.Request('https://translate.googleapis.com/translate_a/single', data=data, headers={'User-Agent': 'Mozilla/5.0', 'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'})
            j = json.loads(urllib.request.urlopen(req, timeout=30).read().decode())
            return ''.join(p[0] for p in j[0] if p and p[0])
        except urllib.error.HTTPError as e:
            err = e
            if e.code == 429 and i >= 1: raise Blocked(str(e))
            time.sleep(3 * (i + 1))
        except Exception as e:
            err = e; time.sleep(3 * (i + 1))
    raise err
def run(items, tl, maxc=4200):
    out = {}; i = 0
    while i < len(items):
        batch = []; size = 0
        while i < len(items) and (not batch or size + len(items[i]) < maxc):
            batch.append(i); size += len(items[i]) + 5; i += 1
        res = call(SEP.join(items[k].replace('**', '') for k in batch), tl)
        parts = re.split(r'\s*⁂\s*', res)
        if len(parts) != len(batch): parts = [call(items[k].replace('**', ''), tl) for k in batch]
        for k, p in zip(batch, parts): out[items[k]] = p.strip()
        time.sleep(0.15)
    return out
units = json.load(open('units.json'))[int(sys.argv[1])]
from concurrent.futures import ThreadPoolExecutor
def do(u):
    lang, cid, a, b = u
    items = json.load(open('mtin/%s.json' % cid))[a:b]
    os.makedirs('out/' + lang, exist_ok=True)
    t0 = time.time()
    try:
        d = run(items, lang); json.dump(d, open('out/%s/%s.%d.json' % (lang, cid, a), 'w'), ensure_ascii=False)
        return 'ok %s %s %d %d %ds' % (lang, cid, a, b, time.time() - t0)
    except Exception as e:
        return 'FAIL %s %s %d %r' % (lang, cid, a, e)
with ThreadPoolExecutor(4) as ex:
    for r in ex.map(do, units): print(r, flush=True)
