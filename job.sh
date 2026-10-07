set -x
pip install -q torch --index-url https://download.pytorch.org/whl/cpu 2>&1 | tail -1
pip install -q transformers soundfile uroman librosa accelerate sentencepiece 2>&1 | tail -1
cd out && cp ../samples.json . && python3 ../tts_eval.py 2>&1 | grep -v Warning | tail -80
true
