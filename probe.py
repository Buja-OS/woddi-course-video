import urllib.request, urllib.parse, os, time, json
os.makedirs('media', exist_ok=True)
UA = {'User-Agent': 'WODDI-Institute-research/1.0'}
P = {
 'p1_materials': 'documentary photo, clean bright small soap workshop in Kenya, white tiled table, neatly arranged labelled containers: sulphonic acid in a brown jerrycan, white caustic soda flakes in a clear jar, soda ash powder, nitrosol powder, SLES paste tub, salt, measuring jug, digital kitchen scale, white plastic bucket, pH strips, natural window light, shot on iPhone, realistic',
 'p2_nitrosol': 'close-up phone video still, African woman wearing safety goggles, blue nitrile gloves and a clean apron sprinkling white nitrosol powder slowly into a white plastic bucket of water while stirring with a long wooden stick, clean bright workshop, realistic UGC tutorial',
 'p3_ph': 'macro close-up, gloved hand holding a pH test strip next to a colour chart, strip shows green pH 7, white bucket of green liquid soap in background, clean workshop, realistic photo',
}
for k, p in P.items():
    for model in ('flux',):
        url = 'https://image.pollinations.ai/prompt/' + urllib.parse.quote(p) + '?width=1280&height=720&nologo=true&seed=42&model=' + model
        t = time.time()
        try:
            r = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=180); d = r.read()
            open('media/%s_%s.jpg' % (k, model), 'wb').write(d); print(k, model, r.status, len(d), round(time.time() - t, 1))
        except Exception as e: print(k, model, 'ERR', e)
for u in ['https://text.pollinations.ai/models', 'https://image.pollinations.ai/models', 'https://gen.pollinations.ai/', 'https://huggingface.co/api/spaces/Wan-AI/Wan2.1', 'https://api-inference.huggingface.co/']:
    try:
        r = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=30); print(u, r.status, r.read()[:600])
    except Exception as e: print(u, 'ERR', e)
