set -x
sudo apt-get install -y -qq espeak-ng > /dev/null 2>&1
pip install -q torch torchaudio --index-url https://download.pytorch.org/whl/cpu 2>&1 | tail -1
pip install -q "transformers<4.50" soundfile librosa sentencepiece coqui-tts piper-tts huggingface_hub accelerate 2>&1 | tail -2
python3 bake.py 2>&1 | grep -vE "Warning|warn" | tail -80
python3 asr.py 2>&1 | grep -E "SUMMARY|Error|error" | tail -60
