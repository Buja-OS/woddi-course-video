import json, os, sys, glob, time
sys.path.insert(0, '.')
from mt import translate_all
lang, g, n = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
files = sorted(glob.glob('mtin/*.json'))[g::n]
os.makedirs('out/%s' % lang, exist_ok=True)
for f in files:
    cid = os.path.basename(f)[:-5]; items = json.load(open(f)); t0 = time.time()
    try:
        tr = translate_all(items, lang)
        json.dump(dict(zip(items, tr)), open('out/%s/%s.json' % (lang, cid), 'w'), ensure_ascii=False)
        print('ok', lang, cid, len(items), round(time.time() - t0), flush=True)
    except Exception as e:
        print('FAIL', lang, cid, e, flush=True)
