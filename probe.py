import urllib.request, urllib.parse, json, re, os, subprocess
UA={'User-Agent':'WODDI-Institute-research/1.0 (contact woddi.org@gmail.com)'}
def get(u, binary=False):
    r=urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=60); b=r.read(); return b if binary else b.decode('utf8','replace')
os.makedirs('media',exist_ok=True); meta=[]
# Wikimedia Commons: real liquid soap making in Nigeria + extra searches
for q in ['liquid soap','detergent making','Nigeria Liquid Soap Making','soap making Nigeria','hand washing liquid soap']:
    u='https://commons.wikimedia.org/w/api.php?'+urllib.parse.urlencode({'action':'query','format':'json','generator':'search','gsrsearch':q+' filetype:video','gsrnamespace':6,'gsrlimit':10,'prop':'imageinfo','iiprop':'url|size|extmetadata','iiextmetadatafilter':'LicenseShortName|Artist|ImageDescription'})
    for p in json.loads(get(u)).get('query',{}).get('pages',{}).values():
        ii=p['imageinfo'][0]; m=ii.get('extmetadata',{})
        print('commons',q,'|',p['title'],'|',m.get('LicenseShortName',{}).get('value'),'|',round(ii.get('duration',0) or 0),'s')
t='File:Nigeria Liquid Soap Making.webm'
u='https://commons.wikimedia.org/w/api.php?'+urllib.parse.urlencode({'action':'query','format':'json','titles':t,'prop':'imageinfo','iiprop':'url|extmetadata'})
p=list(json.loads(get(u))['query']['pages'].values())[0]; ii=p['imageinfo'][0]; m=ii['extmetadata']
open('media/commons_nigeria_liquid_soap.webm','wb').write(get(ii['url'],True))
meta.append({'file':'commons_nigeria_liquid_soap.webm','source':ii['descriptionurl'],'license':m.get('LicenseShortName',{}).get('value'),'artist':re.sub('<[^>]+>','',m.get('Artist',{}).get('value','')),'desc':re.sub('<[^>]+>','',m.get('ImageDescription',{}).get('value',''))[:400]})
# Mixkit: soap and related craft searches; keep only clips under the Mixkit Free License
seen=set()
for term in ['soap','liquid-soap','hand-washing','pouring','bottles','bucket','chemistry','gloves','cleaning','mixing']:
    try: html=get('https://mixkit.co/free-stock-video/%s/'%term)
    except Exception as e: print('mixkit',term,e); continue
    for vid,slug in re.findall(r'href="/free-stock-video/([a-z0-9-]+)-(\d+)/"',html) and [(b,a) for a,b in re.findall(r'href="/free-stock-video/([a-z0-9-]+)-(\d+)/"',html)]:
        if vid in seen or len(seen)>=40: continue
        seen.add(vid)
        try:
            page=get('https://mixkit.co/free-stock-video/%s-%s/'%(slug,vid))
            lic='Restricted' if 'Restricted License' in page else ('Free' if 'Free License' in page or 'free license' in page.lower() else 'unknown')
            title=(re.search(r'<title>([^<]+)',page) or [None,''])[1].strip()
            print('mixkit',term,vid,lic,'|',title)
            if lic!='Free': continue
            for res in ['1080','720']:
                try: b=get('https://assets.mixkit.co/videos/%s/%s-%s.mp4'%(vid,vid,res),True); break
                except Exception: b=None
            if b:
                fn='mixkit_%s_%s.mp4'%(vid,slug[:40]); open('media/'+fn,'wb').write(b)
                meta.append({'file':fn,'source':'https://mixkit.co/free-stock-video/%s-%s/'%(slug,vid),'license':'Mixkit Stock Video Free License','title':title,'term':term})
        except Exception as e: print('mixkit item',vid,e)
json.dump(meta,open('media/meta.json','w'),indent=1)
print('downloaded',len(meta))
