"""Machine-translate a list of English strings with Google's public translate endpoint (same one the site already uses),
batching many strings per request. Usage: python3 mt.py in.json out.json lang"""
import json, sys, time, urllib.request, urllib.parse, random, re
SEP = '\n⁂\n'
def call(text, tl, tries=6):
    data = urllib.parse.urlencode({'client': 'gtx', 'sl': 'en', 'tl': tl, 'dt': 't', 'q': text}).encode()
    for i in range(tries):
        try:
            req = urllib.request.Request('https://translate.googleapis.com/translate_a/single', data=data, headers={'User-Agent': 'Mozilla/5.0', 'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'})
            j = json.loads(urllib.request.urlopen(req, timeout=30).read().decode())
            return ''.join(p[0] for p in j[0] if p and p[0])
        except Exception as e:
            time.sleep(min(60, 2 ** i + random.random())); err = e
    raise err
def translate_all(items, tl, maxc=4200):
    out = [None] * len(items); i = 0
    while i < len(items):
        batch = []; size = 0
        while i < len(items) and (not batch or size + len(items[i]) < maxc):
            batch.append(i); size += len(items[i]) + 5; i += 1
        src = SEP.join(items[k].replace('**', '') for k in batch)
        res = call(src, tl)
        parts = re.split(r'\s*⁂\s*', res)
        if len(parts) != len(batch):      # separator lost: translate one by one
            parts = [call(items[k].replace('**', ''), tl) for k in batch]
        for k, p in zip(batch, parts): out[k] = p.strip()
        time.sleep(0.3)
    return out
if __name__ == '__main__':
    items = json.load(open(sys.argv[1])); tl = sys.argv[3]
    t0 = time.time(); tr = translate_all(items, tl)
    json.dump(dict(zip(items, tr)), open(sys.argv[2], 'w'), ensure_ascii=False)
    print('translated', len(items), 'strings to', tl, 'in', round(time.time() - t0), 's')
