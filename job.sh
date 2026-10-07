set -x
python3 --version
pip install -q bpy 2>&1 | tail -3
python3 -c "import bpy;print(bpy.app.version_string)"
git clone -q --depth 1 -b job-assets-out https://github.com/$GITHUB_REPOSITORY.git assets && cp gen/*.png assets/
WODDI_ASSETS=$PWD/assets WODDI_SAMPLES=12 timeout 600 python3 render_demo.py cut_bars out/frames "100,101" 2>&1 | tail -20
ls -la out/frames
which ffmpeg; nproc
