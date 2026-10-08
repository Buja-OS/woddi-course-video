set -x
cd out
for L in yo ig ha; do python3 ../mt.py ../candle_strings.json candle_$L.json $L; done
python3 -c "import json;d=json.load(open('candle_yo.json'));import itertools;[print(k[:80],'=>',v[:100]) for k,v in itertools.islice(d.items(),0,8)]"
