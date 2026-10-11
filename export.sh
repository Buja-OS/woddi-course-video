set -x
for L in yor ibo; do
  optimum-cli export onnx --model facebook/mms-tts-$L --task text-to-audio onnx_$L 2>&1 | tail -5 || true
  ls -la onnx_$L || true
done
python3 - <<'PY'
import os, glob, json
from onnxruntime.quantization import quantize_dynamic, QuantType
for L in ['yor','ibo']:
    d=f'onnx_{L}'
    src=[f for f in glob.glob(d+'/*.onnx')]
    print(L, src)
    if not src: continue
    os.makedirs(f'web_{L}/onnx', exist_ok=True)
    import shutil
    shutil.copy(src[0], f'web_{L}/onnx/model.onnx')
    quantize_dynamic(src[0], f'web_{L}/onnx/model_quantized.onnx', weight_type=QuantType.QUInt8)
    for f in glob.glob(d+'/*.json'): shutil.copy(f, f'web_{L}/')
    print(L, {f: os.path.getsize(f) for f in glob.glob(f'web_{L}/**', recursive=True) if os.path.isfile(f)})
PY
