set -x
sudo apt-get update -qq && sudo apt-get install -y -qq ffmpeg >/dev/null
pip install -q torch torchaudio --index-url https://download.pytorch.org/whl/cpu 2>&1 | tail -1
pip install -q outetts uroman transformers soundfile inflect 2>&1 | tail -2
git clone -q https://github.com/saheedniyi02/yarngpt.git
pip install -q -e yarngpt 2>&1 | tail -1 || true
curl -sSL -o wavtokenizer_mediumdata_frame75_3s_nq1_code4096_dim512_kmeans200_attn.yaml https://huggingface.co/novateur/WavTokenizer-medium-speech-75token/resolve/main/wavtokenizer_mediumdata_frame75_3s_nq1_code4096_dim512_kmeans200_attn.yaml
curl -sSL -o wavtokenizer_large_speech_320_24k.ckpt https://huggingface.co/novateur/WavTokenizer-large-speech-75token/resolve/main/wavtokenizer_large_speech_320_24k.ckpt
ls -la *.ckpt *.yaml
python3 yarn_test.py 2>&1 | grep -E "OK|FAIL|speakers|Error|error" | head -30
cp -r out/* $GITHUB_WORKSPACE/out/ 2>/dev/null; true
# HF search for better TTS per language
for q in swahili-tts swahili arabic-tts yoruba-tts hausa-tts igbo-tts; do curl -s "https://huggingface.co/api/models?search=$q&filter=text-to-speech&sort=downloads&limit=15" | python3 -c "import json,sys;print('$q',[(m['id'],m.get('downloads')) for m in json.load(sys.stdin)])"; done
