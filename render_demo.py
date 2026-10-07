import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, demos
name, out = sys.argv[1], sys.argv[2]
frames = None
if len(sys.argv) > 3: frames = [int(x) for x in sys.argv[3].split(',')]
demos.DEMOS[name]()
v = int(os.environ.get('WODDI_VARIANT', '0'))
if v and name != 'scale_weigh': demos.vary_camera(v)
elif v == 2: demos.vary_camera(2)
t = time.time()
import kit
P, PN = int(os.environ.get('WODDI_PART', '0')), int(os.environ.get('WODDI_PARTS', '1'))
if PN > 1 and not frames:
    sc = bpy.context.scene; allf = list(range(sc.frame_start, sc.frame_end + 1))
    n = len(allf); a = n * P // PN; b = n * (P + 1) // PN; frames = allf[a:b]
kit.render(out, frames=frames)
print('RENDERED', name, len(frames or []), 'in', round(time.time() - t, 1), 's')
