#!/bin/bash
# Compose every module of one course in all 8 languages, then upload to the release v2-<course>.
C=$1; REPO=$2; LANGS="${3:-en fr pt ar yo ha ig sw}"
set -u
mkdir -p clips voice out vt
python3 - "$C" > demos.txt <<'P'
import json,glob,sys
c=sys.argv[1]; d=set()
for f in glob.glob('scripts/%s/m*.json'%c):
    for sh in json.load(open(f))['shots']: d.add(sh['demo'])
d|={'title_soap','title_liquid','title_workshop','meeting_table','receipts_records','calendar_clock','flipchart','costing_desk','market_stall'}
print('\n'.join(sorted(d)))
P
for d in $(cat demos.txt); do gh release download clips-r4 -R $REPO -p "$d-v*.mp4" -D clips --clobber 2>/dev/null || true; done
echo "clips: $(ls clips | wc -l)"
for L in $LANGS; do
  mkdir -p voice/$L
  ( { [ $L = yo ] || [ $L = ig ]; } && gh release download voice2b-$L -R $REPO -p "$C.tar" -D vt/$L --clobber 2>/dev/null ) || gh release download voice2-$L -R $REPO -p "$C.tar" -D vt/$L --clobber 2>/dev/null
  [ -f vt/$L/$C.tar ] && tar -xf vt/$L/$C.tar -C voice/$L/ || echo "NO VOICE $L $C"
done
for sp in $(ls scripts/$C/ | grep -E '^m[0-9]+\.json$' | sort -V); do
  M=${sp%.json}
  for L in $LANGS; do
    [ -d voice/$L/$C/$M ] || { echo "skip $L $M (no voice)"; continue; }
    python3 comp/compose.py $C $M $L out/$L 2>&1 | tail -3 || echo "FAILED $L $M"
    rm -rf out/$L/_w_*
  done
done
gh release create "v2-$C" -R $REPO --title "Videos: $C" --notes "WODDI module videos for $C in 8 languages." >/dev/null 2>&1 || true
mkdir -p up
for L in $LANGS; do
  for f in out/$L/*; do [ -f "$f" ] && cp "$f" "up/${L}__$(basename $f)"; done
done
ls up | wc -l
for i in 1 2 3 4 5; do gh release upload "v2-$C" up/* --clobber -R $REPO && break; sleep $((i*11)); done
