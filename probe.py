import urllib.request, urllib.parse, json, re
UA={'User-Agent':'WODDI-Institute-research/1.0 (contact woddi.org@gmail.com)'}
def get(u):
    try:
        r=urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=30); return r.status, r.read().decode('utf8','replace')
    except Exception as e: return getattr(e,'code',str(e)), ''
for q in ['soap making','handmade soap','soap','cold process soap','lye','making soap Africa','soap production']:
    u='https://commons.wikimedia.org/w/api.php?'+urllib.parse.urlencode({'action':'query','format':'json','generator':'search','gsrsearch':q+' filetype:video','gsrnamespace':6,'gsrlimit':20,'prop':'imageinfo','iiprop':'url|size|extmetadata|mediatype','iiextmetadatafilter':'LicenseShortName|Artist|ImageDescription'})
    s,b=get(u); print('== commons',q,s)
    try:
        for p in json.loads(b).get('query',{}).get('pages',{}).values():
            ii=p['imageinfo'][0]; m=ii.get('extmetadata',{})
            print('  ',p['title'],'|',m.get('LicenseShortName',{}).get('value'),'|',ii.get('width'),'x',ii.get('height'),'|',round(ii.get('duration',0) or 0),'s |',ii['url'])
    except Exception as e: print('  parse',e)
for name,u in [('pexels','https://www.pexels.com/search/videos/soap%20making/'),('pixabay','https://pixabay.com/videos/search/soap%20making/'),('mixkit','https://mixkit.co/free-stock-video/soap/'),('coverr','https://coverr.co/s?q=soap'),('videvo','https://www.videvo.net/search/soap/')]:
    s,b=get(u); mp4=sorted(set(re.findall(r'https?://[^"\' ]+?\.mp4',b)))
    print('==',name,s,len(b),'mp4 links',len(mp4)); [print('  ',x) for x in mp4[:12]]
