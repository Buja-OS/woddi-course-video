set -x
OUT=$PWD/out
UA="WODDI-Institute-video-bot/1.0 (noreply@woddiinstitute.com)"
# 1. Poly Haven CC0 models (glTF 1k) + HDRIs
mkdir -p $OUT/ph && cd $OUT/ph
for m in wooden_table_02 wooden_spoon wooden_bowl_01 wooden_bowl_02 plastic_bottle_gallon plastic_container plastic_jerrycan garden_gloves_01 jug_01 pot_enamel_01 wooden_cutting_board multi_cleaner_bottle bleach_bottle all_purpose_cleaner multi_cleaner_5_litre wooden_bucket_01 plastic_crate_01 brass_pan_01 ceramic_pot metal_jug cleaner_tin_01 medical_box clipboard; do
  curl -sS "https://api.polyhaven.com/files/$m" -o files.json
  python3 - "$m" <<'P'
import json,sys,os,urllib.request
m=sys.argv[1]; d=json.load(open('files.json'))
g=d.get('gltf',{}).get('1k',{}).get('gltf')
if not g: print('NO GLTF',m); sys.exit()
os.makedirs(m,exist_ok=True)
def get(u,p):
    os.makedirs(os.path.dirname(p) or '.',exist_ok=True); urllib.request.urlretrieve(u,p)
get(g['url'],m+'/'+m+'.gltf')
for rel,inc in g.get('include',{}).items(): get(inc['url'],m+'/'+rel)
P
done
rm -f files.json
mkdir -p hdri && for h in brown_photostudio_02 brown_photostudio_06 comfy_cafe small_empty_room_1 kitchen_2 ; do curl -sSfL "https://dl.polyhaven.org/file/ph-assets/HDRIs/hdr/2k/${h}_2k.hdr" -o hdri/$h.hdr || echo "nohdri $h"; done
for t in wood_table_001 laminate_floor_02 plastered_wall white_plaster_02 ; do mkdir -p tex/$t; for k in diff_2k.jpg nor_gl_2k.jpg rough_2k.jpg; do curl -sSfL "https://dl.polyhaven.org/file/ph-assets/Textures/jpg/2k/$t/${t}_$k" -o tex/$t/${t}_$k || true; done; done
# 2. HF search for Igbo / other TTS
cd $OUT && curl -sS "https://huggingface.co/api/models?search=igbo&filter=text-to-speech&limit=50" -o hf_igbo_tts.json
curl -sS "https://huggingface.co/api/models?search=tts-ibo&limit=50" -o hf_ibo.json
# 3. Wikimedia photos: CC0 / PD / CC BY only, width >= 1000
mkdir -p $OUT/wm && cd $OUT/wm
python3 - "$GITHUB_WORKSPACE/wm" <<'P'
import json,glob,os,sys,urllib.request,re,time
src=sys.argv[1]; seen=set(); meta=[]
ok=re.compile(r'^(CC0|Public domain|No restrictions|CC BY \d|CC BY-\d|CC BY \d\.\d)',re.I)
for f in sorted(glob.glob(src+'/wm_*.json')):
    q=os.path.basename(f)[3:-5]
    d=json.load(open(f)); pages=(d.get('query') or {}).get('pages',{})
    for p in pages.values():
        ii=(p.get('imageinfo') or [{}])[0]; em=ii.get('extmetadata',{})
        lic=em.get('LicenseShortName',{}).get('value','')
        if not ok.match(lic) or 'SA' in lic: continue
        if ii.get('width',0)<1000 or p['title'] in seen: continue
        if re.search(r'\.(pdf|svg|tif|tiff|djvu|webm|ogv)$',p['title'],re.I): continue
        seen.add(p['title'])
        n='%03d'%len(meta)
        try:
            req=urllib.request.Request(ii['thumburl'],headers={'User-Agent':'WODDI-Institute-video-bot/1.0 (noreply@woddiinstitute.com)'})
            open(n+'.jpg','wb').write(urllib.request.urlopen(req).read()); time.sleep(0.3)
        except Exception as e: print('fail',p['title'],e); continue
        meta.append({'n':n,'q':q,'title':p['title'],'license':lic,'artist':re.sub('<[^>]+>','',em.get('Artist',{}).get('value',''))[:120],'url':ii.get('descriptionurl')})
json.dump(meta,open('meta.json','w'),indent=1)
print(len(meta))
P
du -sh $OUT/*
