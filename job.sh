set -x
sudo apt-get update -qq && sudo apt-get install -y -qq ffmpeg >/dev/null
pip install -q torch --index-url https://download.pytorch.org/whl/cpu 2>&1 | tail -1
pip install -q transformers soundfile librosa 2>&1 | tail -1
python3 asr2.py 2>&1 | grep "=>"
