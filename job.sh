set -x
which ffmpeg; ffmpeg -version | head -1
which ffmpeg || (sudo apt-get update -qq && sudo apt-get install -y -qq ffmpeg)
ffmpeg -version | head -1
mkdir -p node && cd node && npm init -y >/dev/null && npm i -s @fontsource/noto-sans @fontsource/noto-sans-arabic playwright >/dev/null 2>&1 && npx playwright install --with-deps chromium >/dev/null 2>&1; cd ..
WODDI_NM=$PWD/node/node_modules/@fontsource WODDI_PW=$PWD/node/node_modules/playwright python3 comp/compose.py detergent-cleaning-products-production m1 yo /tmp/tout 2>&1 | tail -30
ls /tmp/tout
