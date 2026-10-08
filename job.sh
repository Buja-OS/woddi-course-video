set -x
cd out
for L in fr pt ar yo ha ig sw; do python3 ../mt.py ../catalog_in.json _catalog_$L.json $L & done; wait
ls -la
