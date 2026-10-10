import urllib.request, urllib.parse, json, re, os
UA={'User-Agent':'WODDI-Institute-research/1.0 (contact woddi.org@gmail.com)'}
def get(u, binary=False):
    r=urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=60); b=r.read(); return b if binary else b.decode('utf8','replace')
os.makedirs('media',exist_ok=True); meta=[]
for t,fn in [("File:Northern Ghana's village women learning Local liquid soap preparation.webm",'commons_ghana_women_liquid_soap.webm')]:
    u='https://commons.wikimedia.org/w/api.php?'+urllib.parse.urlencode({'action':'query','format':'json','titles':t,'prop':'imageinfo','iiprop':'url|extmetadata'})
    p=list(json.loads(get(u))['query']['pages'].values())[0]; ii=p['imageinfo'][0]; m=ii['extmetadata']
    open('media/'+fn,'wb').write(get(ii['url'],True))
    meta.append({'file':fn,'source':ii['descriptionurl'],'license':m.get('LicenseShortName',{}).get('value'),'artist':re.sub('<[^>]+>','',m.get('Artist',{}).get('value','')),'desc':re.sub('<[^>]+>','',m.get('ImageDescription',{}).get('value',''))[:400]})
    print(meta[-1])
u='https://commons.wikimedia.org/w/api.php?'+urllib.parse.urlencode({'action':'query','format':'json','titles':'File:Nigeria Liquid Soap Making.webm','prop':'imageinfo','iiprop':'extmetadata'})
p=list(json.loads(get(u))['query']['pages'].values())[0]; m=p['imageinfo'][0]['extmetadata']
print('NIGERIA', {k:re.sub('<[^>]+>','',str(v.get('value','')))[:300] for k,v in m.items() if k in ('Artist','LicenseShortName','ImageDescription','Credit','AttributionRequired')})
json.dump(meta,open('media/meta2.json','w'),indent=1)
