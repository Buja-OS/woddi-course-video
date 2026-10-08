"""Demo shots for the WODDI v2 videos. Each demo builds a scene and returns nothing; frame range set on scene.
Run: python render_demo.py <demo> <out_dir> [frame_step]"""
import bpy, math, random
from mathutils import Vector as V
from kit import *

DEMOS = {}
import os
VARIANT = lambda: int(os.environ.get('WODDI_VARIANT', '0'))
def demo(name):
    def reg(fn): DEMOS[name] = fn; return fn
    return reg


def base(hdri='brown_photostudio_02', strength=0.7, rot=0.0, wall=(0.93, 0.86, 0.78)):
    reset(); world(hdri, strength, rot); materials(); room(wall_color=wall)


def falling(objs, start_pts, end_pts, f0, f1, sink_to=None, f_sink=None, shrink_at=None, seed=3):
    random.seed(seed)
    for o, a, b in zip(objs, start_pts, end_pts):
        d = random.randint(0, max(1, (f1 - f0) // 2))
        visible(o, 1, False); visible(o, f0 + d - 1, False); visible(o, f0 + d, True)
        key(o, f0 + d, loc=a, rot=(random.random() * 3, random.random() * 3, 0))
        t = f0 + d + random.randint(7, 11)
        key(o, t, loc=b, rot=(random.random() * 6, random.random() * 6, random.random() * 2))
        if sink_to is not None:
            s = sink_to(b); key(o, t + random.randint(12, 30), loc=s)
        if shrink_at:
            key(o, shrink_at[0] + random.randint(0, 20), scale=o.scale[:])
            key(o, shrink_at[1] + random.randint(0, 25), scale=(0.001, 0.001, 0.001))
        for c in fcurves(o):
            if c.data_path == 'location':
                for k in c.keyframe_points: k.interpolation = 'QUAD'; k.easing = 'EASE_IN'


# ───────────────────────── caustic soda ─────────────────────────
@demo('lye_mix')
def lye_mix():
    base()
    J = (-0.07, 0.03)
    jug, water = measuring_jug((J[0], J[1], 0), h=0.2, r=0.075, fill=0.55, liq_mat=M['lye_sol'])
    T = (0.2, 0.1)
    t, lid = tub((T[0], T[1], 0), r=0.07, h=0.09, lid=False)
    flakes_pile(T, 0.052, 0.07, n=240, seed=4, zbase=0.004)
    goggles((-0.34, -0.14, 0), rot_z=math.radians(25))
    import_ph('garden_gloves_01', loc=(0.33, -0.18, 0), rot_z=math.radians(-30), scale=1.0, recolor=M['glove'])
    # scoop: dips in the tub, carries flakes over the jug, tips them in, goes back
    sc_ = scoop((T[0], T[1], 0.06))
    inside = flakes_pile((0, 0), 0.02, 0.014, n=45, seed=7, zbase=0.003)
    for o in inside: o.parent = sc_
    top = 0.255
    key(sc_, 1, loc=(T[0], T[1], 0.05), rot=(0, 0, math.radians(15)))
    key(sc_, 28, loc=(T[0], T[1], 0.05), rot=(0, 0, math.radians(15)))
    key(sc_, 50, loc=(T[0], T[1], 0.16), rot=(0, 0, math.radians(10)))
    key(sc_, 88, loc=(J[0] + 0.005, J[1], top), rot=(0, 0, 0))
    key(sc_, 96, loc=(J[0] + 0.005, J[1], top), rot=(0, 0, 0))
    key(sc_, 122, loc=(J[0] + 0.005, J[1] + 0.01, top), rot=(math.radians(-115), 0, 0))
    key(sc_, 150, loc=(J[0] + 0.005, J[1] + 0.01, top), rot=(math.radians(-115), 0, 0))
    key(sc_, 175, loc=(T[0], T[1], 0.18), rot=(0, 0, math.radians(15)))
    ease_all(sc_)
    for o in inside: visible(o, 1, True); visible(o, 112, True); visible(o, 113, False)
    falls = flakes_pile((0, 0), 0.01, 0.01, n=60, seed=9, zbase=0)
    random.seed(11)
    st = [(J[0] + random.uniform(-0.012, 0.012), J[1] - 0.015 + random.uniform(-0.01, 0.01), top - 0.03) for _ in falls]
    en = [(x + random.uniform(-0.02, 0.02), y + random.uniform(-0.015, 0.02), 0.115) for x, y, z in st]
    falling(falls, st, en, 106, 134, sink_to=lambda b: (b[0], b[1], 0.012), shrink_at=(150, 200))
    steam((J[0], J[1], 0.13), size=(0.15, 0.15, 0.3), f_on=112, f_peak=165, peak=60.0)
    sp = spoon(recolor=M['steel'])
    key(sp, 1, loc=(J[0] + 0.3, J[1] + 0.25, 0.4), rot=(0, 0, 0))
    key(sp, 150, loc=(J[0] + 0.12, J[1] + 0.1, 0.32), rot=(0, math.radians(-15), 0))
    for i, f in enumerate(range(168, 241, 3)):
        a = i * 0.9
        key(sp, f, loc=(J[0] + 0.03 * math.cos(a), J[1] + 0.03 * math.sin(a), 0.015), rot=(math.radians(12 * math.sin(a)), math.radians(-12 * math.cos(a)), 0))
    camera([(1, (0.16, -0.78, 0.36)), (110, (0.05, -0.68, 0.33)), (240, (0.0, -0.62, 0.3))],
           [(1, (0.08, 0.06, 0.11)), (95, (-0.02, 0.04, 0.16)), (140, (-0.06, 0.03, 0.13)), (240, (-0.07, 0.03, 0.11))], lens=40, fstop=4.0, frames=240)


def cam_dolly(a, b, look_a, look_b, frames=192, lens=40, fstop=3.5):
    return camera([(1, a), (frames, b)], [(1, look_a), (frames, look_b)], lens=lens, fstop=fstop, frames=frames)


def hazard_on_tub(T, r, h, name='hz'):
    return wrap_label((T[0], T[1], 0), r + 0.0015, h * 0.25, h * 0.75, ASSETS + '/hazard.png', name=name, arc_deg=70, alpha=True)


@demo('caustic_flakes')
def caustic_flakes():
    base()
    T = (0.0, 0.05)
    t, lid = tub((T[0], T[1], 0), r=0.09, h=0.1, lid=False)
    flakes_pile(T, 0.07, 0.085, n=650, seed=21, zbase=0.004)
    # a few flakes spilled on a dark tray so their shape is easy to see
    tray = box('tray', (0.26, 0.16, 0.008), (0.24, -0.06, 0.004), M['black_plastic'], bevel=0.003)
    random.seed(5)
    loose = flakes_pile((0.24, -0.06), 0.07, 0.004, n=45, seed=22, zbase=0.008)
    lid_o = lathe('lid', [(0.0, 0.012), (0.095, 0.012), (0.097, 0.0)], M['red'], loc=(-0.2, -0.05, 0.0))
    sc_ = scoop((0.15, 0.12, 0.0)); sc_.rotation_euler = (0, 0, math.radians(30))
    cam_dolly((0.25, -0.5, 0.42), (0.12, -0.36, 0.3), (0.05, 0.03, 0.06), (0.1, 0.0, 0.04), lens=50, fstop=2.8)


@demo('caustic_pellets')
def caustic_pellets():
    base()
    d = lathe('dish', [(0.0, 0.0), (0.07, 0.0), (0.1, 0.015), (0.105, 0.02)], M['clear'], thick=0.003, loc=(0, 0.02, 0))
    flakes_pile((0, 0.02), 0.075, 0.025, n=420, seed=31, kind='pearl', zbase=0.004)
    t, lid = tub((0.24, 0.12, 0), r=0.07, h=0.11, lid=True)
    cam_dolly((-0.12, -0.42, 0.32), (0.02, -0.3, 0.24), (0.0, 0.02, 0.01), (0.02, 0.03, 0.02), lens=55, fstop=2.4)


@demo('caustic_storage')
def caustic_storage():
    base()
    shelf((0.0, 0.95, 0.75), width=1.1, levels=(0.0,), depth=0.28)
    T = (0.0, 0.05)
    t, lid = tub((T[0], T[1], 0), r=0.08, h=0.11, lid=True, lid_mat=M['red'])
    flakes_pile(T, 0.062, 0.08, n=280, seed=41, zbase=0.004)
    hazard_on_tub(T, 0.08, 0.11)
    # lid comes down and closes, then the tub is lifted onto the high shelf
    key(lid, 1, loc=(T[0] + 0.18, T[1] - 0.05, 0.02), rot=(0, math.radians(0), 0))
    key(lid, 30, loc=(T[0] + 0.18, T[1] - 0.05, 0.02))
    key(lid, 60, loc=(T[0], T[1], 0.2))
    key(lid, 80, loc=(T[0], T[1], 0.116))
    ease_all(lid)
    grp = bpy.data.objects.new('carry', None); bpy.context.collection.objects.link(grp)
    for o in list(bpy.data.objects):
        if o.name.startswith(('tub', 'flakes', 'hz')) and o.parent is None: o.parent = grp
    key(grp, 1, loc=(0, 0, 0)); key(grp, 100, loc=(0, 0, 0)); key(grp, 150, loc=(0.0, 0.5, 0.95)); key(grp, 175, loc=(-0.05, 0.85, 0.77))
    lid.parent = None
    key(lid, 100, loc=(T[0], T[1], 0.116)); key(lid, 150, loc=(T[0], T[1] + 0.5, 0.95 + 0.116)); key(lid, 175, loc=(T[0] - 0.05, T[1] + 0.85, 0.77 + 0.116))
    ease_all(grp); ease_all(lid)
    for o in ('bottle_food',):
        b, cap, lq, lab = bottle((0.3, 0.1, 0), h=0.22, r=0.035, mat_=M['clear'], cap_mat=M['bucket_blue'], liq=M['water'], fill=0.9, name='drinkbottle', label=False)
    camera([(1, (0.2, -0.75, 0.35)), (100, (0.15, -0.7, 0.4)), (192, (0.05, -0.55, 0.75))],
           [(1, (0.03, 0.05, 0.08)), (100, (0.03, 0.05, 0.1)), (192, (-0.03, 0.85, 0.82))], lens=35, fstop=4, frames=192)


@demo('oils_lineup')
def oils_lineup():
    base()
    xs = [-0.33, -0.11, 0.11, 0.33]
    # palm oil (red-orange, partly solid), palm kernel oil (pale liquid), coconut oil (white solid), shea butter (block)
    j1, l1 = measuring_jug((xs[0], 0.05, 0), h=0.17, r=0.06, fill=0.7, liq_mat=M['palm'], name='palm')
    b2, c2, l2, lab2 = bottle((xs[1], 0.05, 0), h=0.24, r=0.045, mat_=M['clear'], cap_mat=M['lemon'], liq=M['pko'], fill=0.9, name='pko', label=False)
    jar = lathe('cocojar', [(0.0, 0.0), (0.055, 0.0), (0.06, 0.01), (0.06, 0.11)], M['clear'], thick=0.003, loc=(xs[2], 0.05, 0))
    lc = liquid('coco', 0.054, 0.056, 0.085, M['coco'], loc=(xs[2], 0.05, 0))
    b = bowl((xs[3], 0.05, 0), r=0.09, h=0.05, mat_=M['wood_light'])
    sh = box('shea_block', (0.09, 0.07, 0.045), (xs[3], 0.05, 0.035), M['shea'], bevel=0.012)
    d = sh.modifiers.new('d', 'DISPLACE'); tx = bpy.data.textures.new('sh', 'CLOUDS'); tx.noise_scale = 0.05; d.texture = tx; d.strength = 0.004
    sp = spoon(); sp.location = (xs[3] + 0.08, -0.08, 0.012); sp.rotation_euler = (math.radians(88), 0, math.radians(60))
    cam_dolly((-0.35, -0.75, 0.32), (0.25, -0.72, 0.3), (-0.2, 0.05, 0.07), (0.2, 0.05, 0.07), lens=38, fstop=4.5)


@demo('water_jug')
def water_jug():
    base()
    J = (0.0, 0.03)
    jug, w = measuring_jug((J[0], J[1], 0), h=0.2, r=0.075, fill=0.6, liq_mat=M['water'])
    key(w, 1, scale=(1, 1, 0.15)); key(w, 150, scale=(1, 1, 1.0))
    b, cap, lq, lab = bottle((0.2, 0.08, 0), h=0.3, r=0.05, mat_=M['clear'], cap_mat=M['bucket_blue'], liq=M['water'], fill=0.9, name='waterbottle', label=False)
    s = stream('pour', [(J[0] + 0.02, J[1] + 0.02, 0.36), (J[0] + 0.015, J[1] + 0.015, 0.25), (J[0] + 0.01, J[1] + 0.01, 0.04)], 0.004, M['water'])
    stream_flow(s, 10, 22, 150, 162)
    cam_dolly((0.15, -0.55, 0.3), (0.05, -0.48, 0.26), (0.02, 0.03, 0.12), (0.0, 0.03, 0.1), lens=45, fstop=3.5)


@demo('ppe_set')
def ppe_set():
    base()
    goggles((-0.14, 0.0, 0), rot_z=math.radians(-12))
    import_ph('garden_gloves_01', loc=(0.17, -0.02, 0), rot_z=math.radians(-25), scale=1.0, recolor=M['glove'])
    ap = box('apron', (0.34, 0.22, 0.03), (-0.02, 0.24, 0.015), M['apron'], bevel=0.012)   # folded long-sleeve apron
    dd = ap.modifiers.new('d', 'DISPLACE'); tx = bpy.data.textures.new('ap', 'CLOUDS'); tx.noise_scale = 0.08; dd.texture = tx; dd.strength = 0.004
    sub = ap.modifiers.new('s', 'SUBSURF'); sub.levels = 2; sub.render_levels = 2; ap.modifiers.move(1, 0)
    m_ = mat('mask', (0.92, 0.94, 0.96), 0.8)
    mk = box('mask', (0.12, 0.07, 0.02), (-0.35, -0.05, 0.012), m_, bevel=0.012)
    cam_dolly((-0.22, -0.5, 0.3), (0.16, -0.48, 0.28), (-0.08, 0.04, 0.03), (0.1, 0.04, 0.03), lens=40, fstop=4.0)


@demo('lye_cool')
def lye_cool():
    base()
    J = (0.0, 0.03)
    jug, w = measuring_jug((J[0], J[1], 0), h=0.2, r=0.075, fill=0.55, liq_mat=M['lye_sol'])
    t2, l2 = tub((0.22, 0.12, 0), r=0.07, h=0.1, lid=True)
    hazard_on_tub((0.22, 0.12), 0.07, 0.1)
    thermometer((J[0] + 0.03, J[1] + 0.01, 0.13), rot=(math.radians(-8), math.radians(12), 0))
    steam((J[0], J[1], 0.12), size=(0.15, 0.15, 0.3), f_on=1, f_peak=40, f_off=190, peak=50)
    cam_dolly((0.25, -0.6, 0.3), (0.12, -0.5, 0.26), (0.0, 0.03, 0.13), (0.0, 0.03, 0.12), lens=45, fstop=3.0)


@demo('first_aid_rinse')
def first_aid_rinse():
    base()
    basin, tap = sink_tap((0.0, 0.05, 0.0))
    s = stream('tapwater', [(0.0, 0.08, 0.32), (0.0, 0.075, 0.2), (0.0, 0.07, 0.03)], 0.006, M['water'])
    stream_flow(s, 1, 12, 400, 410)

    eb, ec, el, elab = bottle((0.3, 0.0, 0), h=0.16, r=0.035, mat_=M['clear'], cap_mat=M['bucket_blue'], liq=M['water'], fill=0.9, name='eyewash', label=True)
    cam_dolly((0.3, -0.7, 0.45), (0.15, -0.6, 0.4), (0.05, 0.05, 0.12), (0.03, 0.05, 0.12), lens=38, fstop=3.5)


@demo('scale_weigh')
def scale_weigh():
    if VARIANT() == 1:
        return scale_weigh_liquid()
    base()
    S = (0.0, 0.02)
    sbase, plat, txt = scale_device((S[0], S[1], 0), display='0')
    b = bowl((S[0], S[1] + 0.012, 0.035), r=0.08, h=0.05, mat_=M['steel'])
    T = (0.24, 0.1)
    t, lid = tub((T[0], T[1], 0), r=0.07, h=0.09, lid=False)
    flakes_pile(T, 0.052, 0.07, n=200, seed=51, zbase=0.004)
    inbowl = flakes_pile((S[0], S[1] + 0.012), 0.05, 0.02, n=90, seed=52, zbase=0.038)
    for i, o in enumerate(inbowl):
        f = 40 + (i * 110) // len(inbowl)
        visible(o, 1, False); visible(o, f - 1, False); visible(o, f, True)
    sc_ = scoop((T[0], T[1], 0.06))
    for i in range(3):
        f0 = 20 + i * 45
        key(sc_, f0, loc=(T[0], T[1], 0.05), rot=(0, 0, 0))
        key(sc_, f0 + 18, loc=(S[0] + 0.01, S[1] - 0.01, 0.17), rot=(0, 0, 0))
        key(sc_, f0 + 28, loc=(S[0] + 0.01, S[1] - 0.01, 0.17), rot=(math.radians(-100), 0, 0))
        key(sc_, f0 + 40, loc=(T[0], T[1], 0.06), rot=(0, 0, 0))
    ease_all(sc_)
    # display counts up (numbers only)
    vals = [0, 41, 88, 126, 166]
    for i, v in enumerate(vals):
        f = 1 + i * 38
        def setter(scene, v=v, f=f):
            pass
    txt.data.body = '0'
    # text bodies cannot be keyframed: use separate text objects shown in turn
    txt.hide_render = True
    for i, v in enumerate(vals):
        o = text_obj(str(v), txt.location[:], size=0.012, mat_=M['lcd_text'], rot=txt.rotation_euler[:], align='RIGHT')
        f_on = 1 if i == 0 else 30 + i * 45
        f_off = 30 + (i + 1) * 45 if i < len(vals) - 1 else 999
        visible(o, 1, i == 0); visible(o, f_on, True); visible(o, f_off, False)
    camera([(1, (0.12, -0.5, 0.36)), (192, (0.05, -0.42, 0.3))], [(1, (0.05, 0.0, 0.05)), (192, (0.02, -0.03, 0.04))], lens=45, fstop=3.2, frames=192)


@demo('laundry_bars')
def laundry_bars():
    base()
    random.seed(61)
    for i in range(3):
        for j in range(2):
            for k in range(3 - j):
                soap_bar((-0.1 + i * 0.1 + j * 0.05 + k * 0.0, 0.02 + k * 0.07 - j * 0.0, j * 0.032), size=(0.095, 0.065, 0.032), mat_=M['soap_blue'] if (i + k) % 2 else M['soap_bar'], rot_z=random.uniform(-0.04, 0.04), name='lb')
    cam_dolly((0.3, -0.55, 0.32), (0.08, -0.45, 0.24), (0.0, 0.08, 0.03), (0.0, 0.08, 0.04), lens=45, fstop=2.8)


@demo('costing_desk')
def costing_desk():
    base(wall=(0.9, 0.88, 0.84))
    notebook((-0.08, 0.02, 0), rot_z=math.radians(-6))
    calculator((0.16, 0.0, 0), rot_z=math.radians(8))
    pen((0.02, -0.12, 0), rot_z=math.radians(20))
    for i in range(4):
        soap_bar((0.2 + (i % 2) * 0.1, 0.22 + (i // 2) * 0.07, 0), mat_=M['soap_bar'] if i % 2 else M['soap_blue'], name='cb')
    cam_dolly((-0.15, -0.5, 0.55), (0.1, -0.42, 0.5), (0.0, 0.05, 0.0), (0.08, 0.06, 0.0), lens=38, fstop=4)


@demo('ventilated_room')
def ventilated_room():
    base()
    window((-0.1, 1.09, 0.62), w=0.9, h=0.75)
    curtain((0.48, 1.05, 0.62), w=0.3, h=0.8)
    jug, w = measuring_jug((0.05, 0.25, 0), h=0.2, r=0.075, fill=0.5, liq_mat=M['water'])
    t, lid = tub((0.3, 0.3, 0), r=0.07, h=0.1, lid=True)
    goggles((-0.15, 0.05, 0), rot_z=math.radians(10))
    import_ph('garden_gloves_01', loc=(0.25, 0.0, 0), rot_z=math.radians(-20), recolor=M['glove'])
    camera([(1, (0.35, -0.95, 0.42)), (192, (0.2, -0.85, 0.4))], [(1, (0.0, 0.6, 0.3)), (192, (0.0, 0.55, 0.28))], lens=30, fstop=5, frames=192)


@demo('oil_melt')
def oil_melt():
    base()
    burner((0.0, 0.05, 0))
    P = (0.0, 0.05, 0.058)
    p = pot(P, r=0.13, h=0.13, mat_=M['steel'])
    lq = liquid('oil', 0.122, 0.124, 0.06, M['pko'], loc=P)
    key(lq, 1, scale=(1, 1, 0.3)); key(lq, 192, scale=(1, 1, 1.0))
    random.seed(71)
    for i in range(9):
        a = random.random() * math.tau; rr = random.random() * 0.07
        c = box('chunk', (0.05, 0.04, 0.03), (P[0] + rr * math.cos(a), P[1] + rr * math.sin(a), P[2] + 0.02 + random.random() * 0.02), M['coco'] if i % 2 else M['palm'], bevel=0.008, rot=(random.random(), random.random(), random.random()))
        key(c, 1, scale=(1, 1, 1)); key(c, 120 + i * 6, scale=(0.15, 0.15, 0.15)); visible(c, 150 + i * 4, False)
    sp = spoon()
    for i, f in enumerate(range(60, 193, 4)):
        a = i * 0.7
        key(sp, f, loc=(P[0] + 0.05 * math.cos(a), P[1] + 0.05 * math.sin(a), P[2] + 0.01), rot=(math.radians(15 * math.sin(a)), math.radians(-15 * math.cos(a)), 0))
    key(sp, 1, loc=(0.35, 0.3, 0.4))
    cam_dolly((0.3, -0.75, 0.42), (0.16, -0.65, 0.4), (0.0, 0.05, 0.1), (0.0, 0.05, 0.1), lens=40, fstop=3.5)


@demo('combine_pour')
def combine_pour():
    base()
    P = (0.05, 0.08, 0.0)
    p = pot(P, r=0.13, h=0.13, mat_=M['steel'])
    oil = liquid('oil', 0.122, 0.124, 0.06, M['pko'], loc=P)
    key(oil, 1, scale=(1, 1, 1)); key(oil, 170, scale=(1, 1, 1.45))
    jug, lye = measuring_jug((-0.25, 0.0, 0), h=0.2, r=0.07, fill=0.5, liq_mat=M['lye_sol'], name='lyejug')
    grp = bpy.data.objects.new('jugcarry', None); bpy.context.collection.objects.link(grp); grp.location = (-0.25, 0.0, 0)
    jug.parent = grp; lye.parent = grp; jug.location = (0, 0, 0); lye.location = (0, 0, 0.004)
    key(grp, 1, loc=(-0.25, 0.0, 0), rot=(0, 0, 0))
    key(grp, 40, loc=(-0.14, 0.06, 0.24), rot=(0, 0, 0))
    key(grp, 70, loc=(-0.13, 0.06, 0.24), rot=(0, math.radians(62), 0))
    key(grp, 160, loc=(-0.13, 0.06, 0.24), rot=(0, math.radians(75), 0))
    key(grp, 185, loc=(-0.2, 0.0, 0.1), rot=(0, 0, 0))
    ease_all(grp)
    key(lye, 60, scale=(1, 1, 1)); key(lye, 165, scale=(1, 1, 0.08))
    s = stream('lyestream', [(-0.04, 0.06, 0.3), (-0.02, 0.07, 0.2), (0.0, 0.08, 0.09)], 0.004, M['lye_sol'])
    stream_flow(s, 70, 80, 155, 165)
    cam_dolly((0.2, -0.85, 0.42), (0.08, -0.75, 0.4), (-0.04, 0.06, 0.16), (0.0, 0.07, 0.14), lens=38, fstop=3.5)


@demo('stir_trace')
def stir_trace():
    base()
    P = (0.0, 0.06, 0.0)
    p = pot(P, r=0.13, h=0.13, mat_=M['steel'])
    # the batter thickens: thin translucent oil fades into opaque cream
    thin = liquid('thin', 0.122, 0.124, 0.085, M['batter_thin'], loc=P)
    thick = liquid('thick', 0.1215, 0.1235, 0.086, M['batter'], loc=P)
    mt = M['batter']; b = mt.node_tree.nodes['Principled BSDF']
    mt.blend_method = 'BLEND' if hasattr(mt, 'blend_method') else None
    # cross-fade with alpha on the cream layer
    b.inputs['Alpha'].default_value = 0.0; b.inputs['Alpha'].keyframe_insert('default_value', frame=1)
    b.inputs['Alpha'].default_value = 0.0; b.inputs['Alpha'].keyframe_insert('default_value', frame=30)
    b.inputs['Alpha'].default_value = 1.0; b.inputs['Alpha'].keyframe_insert('default_value', frame=130)
    # trace: a trail of batter drizzled on the surface that stays visible
    tr = stream('trace', [(P[0] - 0.06, P[1] - 0.02, 0.092), (P[0] - 0.02, P[1] + 0.03, 0.093), (P[0] + 0.03, P[1] - 0.02, 0.093), (P[0] + 0.07, P[1] + 0.02, 0.092)], 0.0035, M['batter'])
    tr.data.bevel_factor_end = 0; tr.data.keyframe_insert('bevel_factor_end', frame=150); tr.data.bevel_factor_end = 1; tr.data.keyframe_insert('bevel_factor_end', frame=175)
    tr.scale = (1, 1, 1)
    sp = spoon()
    for i, f in enumerate(range(1, 141, 3)):
        a = i * 0.8
        key(sp, f, loc=(P[0] + 0.055 * math.cos(a), P[1] + 0.055 * math.sin(a), 0.012), rot=(math.radians(15 * math.sin(a)), math.radians(-15 * math.cos(a)), 0))
    key(sp, 150, loc=(P[0] - 0.07, P[1] - 0.02, 0.14), rot=(0, math.radians(-30), 0))
    key(sp, 175, loc=(P[0] + 0.08, P[1] + 0.02, 0.14), rot=(0, math.radians(-30), 0))
    key(sp, 192, loc=(P[0] + 0.2, P[1] + 0.1, 0.2), rot=(0, math.radians(-30), 0))
    cam_dolly((0.12, -0.5, 0.48), (0.05, -0.42, 0.45), (0.0, 0.06, 0.08), (0.0, 0.06, 0.08), lens=40, fstop=3.5)


@demo('hot_process_pot')
def hot_process_pot():
    base()
    burner((0.0, 0.06, 0))
    P = (0.0, 0.06, 0.058)
    p = pot(P, r=0.15, h=0.16, mat_=M['steel'])
    paste = liquid('paste', 0.142, 0.144, 0.1, M['batter'], loc=P)
    d = paste.modifiers.new('bubble', 'DISPLACE'); tx = bpy.data.textures.new('bub', 'VORONOI'); tx.noise_scale = 0.025; d.texture = tx; d.strength = 0.012
    d.texture_coords = 'GLOBAL'
    sub = paste.modifiers.new('sub', 'SUBSURF'); sub.levels = 2; sub.render_levels = 3
    paste.modifiers.move(1, 0)
    key(paste, 1, loc=(P[0], P[1], P[2] + 0.004)); key(paste, 192, loc=(P[0], P[1], P[2] + 0.004))
    # move the texture space slowly so the surface "glops"
    em = bpy.data.objects.new('texspace', None); bpy.context.collection.objects.link(em); d.texture_coords = 'OBJECT'; d.texture_coords_object = em
    key(em, 1, loc=(0, 0, 0)); key(em, 192, loc=(0.01, 0.005, 0.06))
    steam((P[0], P[1], P[2] + 0.12), size=(0.25, 0.25, 0.3), f_on=1, f_peak=40, peak=35)
    sp = spoon()
    for i, f in enumerate(range(80, 193, 5)):
        a = i * 0.6
        key(sp, f, loc=(P[0] + 0.07 * math.cos(a), P[1] + 0.07 * math.sin(a), P[2] + 0.03), rot=(math.radians(15 * math.sin(a)), math.radians(-15 * math.cos(a)), 0))
    key(sp, 1, loc=(0.4, 0.3, 0.5))
    cam_dolly((0.35, -0.8, 0.5), (0.2, -0.7, 0.48), (0.0, 0.06, 0.14), (0.0, 0.06, 0.14), lens=38, fstop=3.5)


@demo('mould_pour')
def mould_pour():
    base()
    mould_box((0.05, 0.08, 0.0), size=(0.32, 0.1, 0.08))
    fill = box('loaf', (0.318, 0.098, 0.06), (0.05, 0.08, 0.013 + 0.03), M['batter'], bevel=0.002)
    fill.location.z = 0.013; # origin at centre: emulate level by scale from bottom
    me = fill.data
    for v in me.vertices: v.co.z += 0.03
    fill.location = (0.05, 0.08, 0.013)
    key(fill, 1, scale=(1, 1, 0.02)); key(fill, 40, scale=(1, 1, 0.05)); key(fill, 175, scale=(1, 1, 1.0))
    P = pot((-0.25, 0.05, 0), r=0.11, h=0.12, mat_=M['steel'], handles=True)
    bat = liquid('potbatter', 0.102, 0.104, 0.06, M['batter'], loc=(0, 0, 0)); bat.parent = P; bat.location = (0, 0, 0.004)
    grp = bpy.data.objects.new('potcarry', None); bpy.context.collection.objects.link(grp)
    P.parent = grp; P.location = (0, 0, 0); grp.location = (-0.25, 0.05, 0)
    key(grp, 1, loc=(-0.25, 0.05, 0), rot=(0, 0, 0)); key(grp, 30, loc=(-0.14, 0.08, 0.2), rot=(0, 0, 0))
    key(grp, 50, loc=(-0.12, 0.08, 0.2), rot=(0, math.radians(55), 0))
    for i, f in enumerate(range(60, 181, 30)):
        key(grp, f, loc=(-0.12 + i * 0.05, 0.08, 0.2), rot=(0, math.radians(60 + i * 3), 0))
    key(grp, 192, loc=(0.1, 0.08, 0.25), rot=(0, math.radians(20), 0))
    ease_all(grp)
    s = stream('batterstream', [(-0.03, 0.08, 0.26), (-0.01, 0.08, 0.15), (0.0, 0.08, 0.05)], 0.007, M['batter'])
    s.parent = None
    # stream follows the pot along x
    key(s, 50, loc=(0, 0, 0)); key(s, 180, loc=(0.2, 0, 0)); stream_flow(s, 50, 60, 172, 182)
    cam_dolly((0.35, -0.6, 0.45), (0.2, -0.5, 0.4), (0.0, 0.08, 0.08), (0.08, 0.08, 0.07), lens=38, fstop=4)


@demo('mould_cover')
def mould_cover():
    base()
    mould_box((0.0, 0.08, 0.0), size=(0.32, 0.1, 0.08))
    lf = box('loaf', (0.318, 0.098, 0.07), (0.0, 0.08, 0.048), M['batter'], bevel=0.003)
    lid = box('lid', (0.36, 0.14, 0.012), (0.0, 0.08, 0.1), M['wood_light'], bevel=0.003)
    key(lid, 1, loc=(0.0, 0.3, 0.3)); key(lid, 60, loc=(0.0, 0.08, 0.1)); ease_all(lid)
    t = towel((0.0, 0.08, 0.11), size=(0.5, 0.35), col=(0.75, 0.55, 0.35))
    key(t, 1, loc=(0.0, 0.5, 0.5)); key(t, 70, loc=(0.0, 0.5, 0.5)); key(t, 130, loc=(0.0, 0.08, 0.112)); ease_all(t)
    cam_dolly((0.3, -0.6, 0.42), (0.15, -0.5, 0.38), (0.0, 0.08, 0.08), (0.0, 0.08, 0.09), lens=40, fstop=4)


@demo('cut_bars')
def cut_bars():
    base()
    board = import_ph('wooden_cutting_board', loc=(0.0, 0.05, 0.0))
    z0 = 0.041
    bars = []
    for i in range(6):
        b = box('bar', (0.05, 0.1, 0.07), (-0.125 + i * 0.05, 0.05, z0 + 0.035), M['soap_bar'], bevel=0.0015)
        bars.append(b)
    kn = knife((0.0, 0.05, 0.25), rot=(0, 0, math.radians(90)))
    for i in range(5):
        x = -0.1 + i * 0.05; f = 15 + i * 32
        key(kn, f, loc=(x, 0.05, z0 + 0.11)); key(kn, f + 12, loc=(x, 0.05, z0 + 0.0)); key(kn, f + 20, loc=(x, 0.05, z0 + 0.11))
        for j, b in enumerate(bars[i + 1:]):
            key(b, f + 12, loc=b.location[:]); key(b, f + 20, loc=(b.location[0] + 0.006, b.location[1], b.location[2]))
    ease_all(kn)
    cam_dolly((0.3, -0.42, 0.35), (0.12, -0.38, 0.32), (0.0, 0.05, 0.07), (0.02, 0.05, 0.07), lens=40, fstop=3.5)


@demo('cure_rack')
def cure_rack():
    base()
    wire_rack((0.0, 0.1, 0.0), w=0.7, d=0.35)
    for i in range(6):
        for j in range(3):
            soap_bar((-0.28 + i * 0.112, -0.02 + j * 0.12, 0.031), size=(0.085, 0.06, 0.03), mat_=M['soap_bar'] if (i + j) % 3 else M['soap_green'], name='cure')
    window((-0.55, 1.09, 0.85), w=0.8, h=0.7)
    camera([(1, (-0.55, -0.4, 0.3)), (192, (0.45, -0.45, 0.32))], [(1, (-0.1, 0.1, 0.04)), (192, (0.1, 0.1, 0.04))], lens=35, fstop=3.5, frames=192)


@demo('grate_powder')
def grate_powder():
    base()
    b = bowl((0.0, 0.05, 0.0), r=0.14, h=0.07, mat_=M['steel'])
    plate = box('grater', (0.12, 0.004, 0.24), (0.0, 0.05, 0.13), M['steel'], bevel=0.001, rot=(math.radians(-20), 0, 0))
    for i in range(8):
        for j in range(4):
            sl = box('slot', (0.014, 0.006, 0.006), (0, 0, 0), M['black_plastic'], bevel=0.001); sl.parent = plate
            sl.location = (-0.04 + j * 0.027, -0.0005, -0.09 + i * 0.026)
    bar = soap_bar((0.0, 0.0, 0.2), size=(0.09, 0.03, 0.06), mat_=M['soap_blue'], name='gbar')
    for f in range(1, 193, 24):
        key(bar, f, loc=(0.0, 0.015, 0.21)); key(bar, f + 12, loc=(0.0, 0.03, 0.12))
    pile = flakes_pile((0.0, 0.0), 0.1, 0.03, n=260, seed=81, zbase=0.004, mat_=M['soap_blue'])
    for i, o in enumerate(pile):
        o.scale = (0.6, 0.35, 0.6); f = 10 + (i * 170) // len(pile); visible(o, 1, False); visible(o, f, True)
    cam_dolly((0.3, -0.5, 0.42), (0.18, -0.45, 0.38), (0.0, 0.04, 0.1), (0.0, 0.04, 0.09), lens=40, fstop=4)


@demo('soap_base_cubes')
def soap_base_cubes():
    base()
    random.seed(91)
    clear = mat('mp_clear', (0.95, 0.92, 0.85), 0.08, 0.7, 1.45, sss=0.3)
    white = mat('mp_white', (0.97, 0.96, 0.94), 0.35, 0, 1.45, sss=0.6)
    b = import_ph('wooden_cutting_board', loc=(0.0, 0.05, 0.0))
    for i in range(18):
        box('cube', (0.03, 0.03, 0.03), (-0.12 + (i % 6) * 0.045 + random.uniform(-0.005, 0.005), -0.02 + (i // 6) * 0.05, 0.057), clear if i % 3 else white, bevel=0.002, rot=(0, 0, random.uniform(-0.3, 0.3)))
    cam_dolly((-0.2, -0.45, 0.35), (0.05, -0.38, 0.3), (0.0, 0.03, 0.05), (0.0, 0.03, 0.05), lens=45, fstop=2.8)


@demo('melt_pour')
def melt_pour():
    base()
    sil = mat('silicone_tray', (0.75, 0.15, 0.3), 0.4, sss=0.3)
    tray = box('tray', (0.32, 0.12, 0.035), (0.08, 0.08, 0.0175), sil, bevel=0.006)
    cells = []
    for i in range(4):
        c = box('cell_fill', (0.06, 0.08, 0.02), (-0.03 + i * 0.075, 0.08, 0.026), mat('mp_melt%d' % i, (0.92, 0.88, 0.80), 0.05, 0.6, 1.45, sss=0.3), bevel=0.002)
        key(c, 1, scale=(1, 1, 0.01)); key(c, 40 + i * 35, scale=(1, 1, 0.01)); key(c, 70 + i * 35, scale=(1, 1, 1.0)); cells.append(c)
    jug, base_ = measuring_jug((-0.25, 0.0, 0.0), h=0.16, r=0.06, fill=0.55, liq_mat=mat('mp_liq', (0.95, 0.9, 0.8), 0.04, 0.8, 1.45))
    grp = bpy.data.objects.new('jugcarry', None); bpy.context.collection.objects.link(grp); grp.location = (-0.25, 0, 0)
    jug.parent = grp; base_.parent = grp; jug.location = (0, 0, 0); base_.location = (0, 0, 0.004)
    key(grp, 1, loc=(-0.25, 0.0, 0.0), rot=(0, 0, 0)); key(grp, 35, loc=(-0.13, 0.08, 0.17), rot=(0, 0, 0))
    for i in range(4):
        key(grp, 45 + i * 35, loc=(-0.13 + i * 0.075, 0.08, 0.17), rot=(0, math.radians(58), 0))
        key(grp, 70 + i * 35, loc=(-0.13 + i * 0.075, 0.08, 0.17), rot=(0, math.radians(58), 0))
    key(grp, 192, loc=(0.25, 0.1, 0.2), rot=(0, 0, 0)); ease_all(grp)
    for i in range(4):
        s = stream('mpstream%d' % i, [(-0.05 + i * 0.075, 0.08, 0.22), (-0.04 + i * 0.075, 0.08, 0.12), (-0.03 + i * 0.075, 0.08, 0.03)], 0.004, M['water'])
        stream_flow(s, 45 + i * 35, 52 + i * 35, 66 + i * 35, 72 + i * 35)
    cam_dolly((0.3, -0.62, 0.42), (0.18, -0.52, 0.38), (0.0, 0.07, 0.1), (0.06, 0.08, 0.09), lens=38, fstop=4)


@demo('additives_tray')
def additives_tray():
    base()
    tray = box('tray', (0.4, 0.22, 0.01), (0.0, 0.08, 0.005), M['wood_light'], bevel=0.003)
    for i, c in enumerate([(0.55, 0.25, 0.05), (0.5, 0.35, 0.1), (0.3, 0.1, 0.4), (0.6, 0.45, 0.2)]):
        b, cap, lq, lab = bottle((-0.13 + i * 0.085, 0.13, 0.01), h=0.09, r=0.022, mat_=M['amber_glass'], cap_mat=M['black_plastic'], liq=None, name='ess%d' % i, label=False)
    bw = bowl((0.05, -0.01, 0.01), r=0.07, h=0.04, mat_=M['enamel'])
    lq = liquid('base', 0.04, 0.06, 0.02, M['batter'], loc=(0.05, -0.01, 0.01))
    dr = cyl('dropper', 0.004, 0.08, (0.05, -0.01, 0.15), M['clear'], verts=12)
    bulb = cyl('bulb', 0.008, 0.025, (0.05, -0.01, 0.2), M['black_plastic'], verts=16); bulb.parent = dr; bulb.location = (0, 0, 0.05)
    for k in range(4):
        d = bpy.ops.mesh.primitive_uv_sphere_add(radius=0.003, location=(0.05, -0.01, 0.1)); dop = bpy.context.object; dop.data.materials.append(M['amber_glass'])
        f = 40 + k * 35; visible(dop, 1, False); visible(dop, f, True); key(dop, f, loc=(0.05, -0.01, 0.105)); key(dop, f + 8, loc=(0.05, -0.01, 0.035)); visible(dop, f + 9, False)
    cam_dolly((0.25, -0.45, 0.35), (0.12, -0.4, 0.3), (0.02, 0.03, 0.06), (0.04, 0.0, 0.05), lens=42, fstop=3.2)


@demo('quality_test')
def quality_test():
    base()
    b = soap_bar((0.0, 0.05, 0.0), size=(0.1, 0.07, 0.035), mat_=M['soap_bar'])
    half = box('half', (0.05, 0.07, 0.035), (0.13, 0.05, 0.0175), M['soap_bar'], bevel=0.002)
    strip = box('strip', (0.008, 0.06, 0.0005), (0.0, 0.3, 0.2), M['strip'], bevel=0)
    key(strip, 1, loc=(0.0, 0.3, 0.2)); key(strip, 60, loc=(0.0, 0.04, 0.0365)); key(strip, 192, loc=(0.0, 0.04, 0.0365))
    sm = M['strip'].node_tree.nodes['Principled BSDF']
    sm.inputs['Base Color'].default_value = (0.95, 0.85, 0.2, 1); sm.inputs['Base Color'].keyframe_insert('default_value', frame=70)
    sm.inputs['Base Color'].default_value = (0.25, 0.35, 0.65, 1); sm.inputs['Base Color'].keyframe_insert('default_value', frame=120)
    chart = box('chart', (0.12, 0.03, 0.001), (-0.13, 0.0, 0.001), M['paper'], bevel=0)
    cols = [(0.9, 0.2, 0.1), (0.95, 0.6, 0.1), (0.95, 0.85, 0.2), (0.5, 0.75, 0.2), (0.2, 0.55, 0.45), (0.25, 0.35, 0.65), (0.25, 0.15, 0.45)]
    for i, c in enumerate(cols):
        box('chip', (0.014, 0.02, 0.0012), (-0.18 + i * 0.017, 0.0, 0.0015), mat('chip%d' % i, c, 0.6), bevel=0)
    cam_dolly((0.2, -0.38, 0.35), (0.06, -0.32, 0.3), (0.0, 0.03, 0.02), (-0.03, 0.02, 0.02), lens=45, fstop=3.0)


@demo('wrap_label')
def wrap_label_demo():
    base()
    for i in range(5):
        b = soap_bar((-0.2 + i * 0.1, 0.12, 0.0), size=(0.085, 0.06, 0.03), mat_=M['paper_brown'], name='wrapped')
        lab = box('wlabel', (0.06, 0.035, 0.0008), (-0.2 + i * 0.1, 0.12, 0.0306), img_mat('lbl%d' % i, ASSETS + '/label_magenta.png' if i % 2 else ASSETS + '/label_green.png', 0.6), bevel=0)
    bar = soap_bar((0.0, -0.05, 0.0), size=(0.085, 0.06, 0.03), mat_=M['soap_bar'])
    paper = box('paper', (0.22, 0.16, 0.0006), (0.0, -0.05, 0.0003), M['paper_brown'], bevel=0)
    key(paper, 1, scale=(1, 1, 1)); key(paper, 100, scale=(0.45, 0.42, 1)); key(paper, 101, scale=(0.45, 0.42, 60))
    key(paper, 1, loc=(0.0, -0.05, 0.0003)); key(paper, 100, loc=(0.0, -0.05, 0.0003)); key(paper, 101, loc=(0.0, -0.05, 0.015))
    visible(bar, 1, True); visible(bar, 101, False)
    st = box('sticker', (0.06, 0.035, 0.0008), (0.0, -0.05, 0.4), img_mat('lblx', ASSETS + '/label_magenta.png', 0.6), bevel=0)
    key(st, 1, loc=(0.0, -0.05, 0.4)); key(st, 120, loc=(0.0, -0.05, 0.4)); key(st, 150, loc=(0.0, -0.05, 0.0316)); ease_all(st)
    cam_dolly((0.25, -0.5, 0.4), (0.1, -0.42, 0.34), (0.0, 0.03, 0.02), (0.0, 0.0, 0.02), lens=42, fstop=3.5)


@demo('market_stall')
def market_stall():
    base(wall=(0.95, 0.9, 0.75))
    crate = import_ph('plastic_crate_01', loc=(0.35, 0.25, 0.0), rot_z=math.radians(80))
    for i in range(4):
        for j in range(2):
            soap_bar((-0.3 + i * 0.1, 0.0 + j * 0.08, 0.0), size=(0.085, 0.06, 0.03), mat_=M['paper_brown'] if (i + j) % 2 else M['soap_blue'], name='sb')
    for i in range(4):
        bottle((-0.2 + i * 0.09, 0.22, 0.0), h=0.2, r=0.035, mat_=M['clear'], cap_mat=M['magenta'] if i % 2 else M['lemon'], liq=M['liquid_soap'] if i % 2 else M['dish_green'], fill=0.9, name='sbot%d' % i)
    cam_dolly((-0.4, -0.7, 0.45), (0.1, -0.65, 0.42), (-0.1, 0.1, 0.08), (0.05, 0.1, 0.08), lens=35, fstop=4)


@demo('chemical_store')
def chemical_store():
    base(wall=(0.9, 0.9, 0.88))
    shelf((0.0, 0.95, 0.35), width=1.3, levels=(0.0, 0.4), depth=0.28)
    # alkalis on the left, acids on the right, a gap between them
    for i in range(3):
        t, lid = tub((-0.5 + i * 0.16, 0.95, 0.3625), r=0.06, h=0.11, lid=True, lid_mat=M['red'])
    for i in range(3):
        b, c, l, lab = bottle((0.2 + i * 0.13, 0.95, 0.3625), h=0.22, r=0.045, mat_=M['hdpe'], cap_mat=M['bucket_blue'], name='acid%d' % i, label=True)
    import_ph('multi_cleaner_5_litre', loc=(-0.3, 0.95, 0.7625), recolor=M['hdpe'])
    import_ph('plastic_jerrycan', loc=(0.35, 0.95, 0.7625), rot_z=math.radians(90), scale=0.8, recolor=M['bucket_blue'])
    decal('hz1', ASSETS + '/hazard.png', (0.05, 0.05), (-0.34, 0.885, 0.43), (math.radians(90), 0, 0))
    camera([(1, (0.0, -0.9, 0.7)), (192, (0.0, -0.7, 0.62))], [(1, (0.0, 0.9, 0.55)), (192, (0.0, 0.9, 0.52))], lens=30, fstop=5, frames=192)


def title_scene(kind):
    base()
    if kind == 'soap':
        for i in range(5):
            soap_bar((-0.2 + i * 0.1, 0.1 + (i % 2) * 0.03, 0.0), size=(0.085, 0.06, 0.03), mat_=[M['soap_bar'], M['soap_blue'], M['soap_green'], M['paper_brown'], M['soap_bar']][i], name='tb')
        t, lid = tub((-0.32, 0.25, 0), r=0.06, h=0.09, lid=False)
        flakes_pile((-0.32, 0.25), 0.055, 0.06, n=160, seed=3, zbase=0.004)
    elif kind == 'liquid':
        for i in range(5):
            bottle((-0.24 + i * 0.12, 0.12, 0.0), h=0.24, r=0.04, mat_=M['clear'], cap_mat=[M['magenta'], M['lemon'], M['bucket_blue'], M['magenta'], M['lemon']][i], liq=[M['liquid_soap'], M['dish_green'], M['softener'], M['cream'], M['liquid_soap']][i], fill=0.9, name='tl%d' % i)
    else:
        bucket((-0.25, 0.25, 0), r=0.15, h=0.28)
        for i in range(3):
            bottle((0.05 + i * 0.12, 0.15, 0.0), h=0.24, r=0.04, mat_=M['hdpe'], cap_mat=[M['magenta'], M['lemon'], M['bucket_blue']][i], name='tw%d' % i)
        goggles((-0.05, -0.05, 0), rot_z=math.radians(10))
    camera([(1, (0.05, -0.72, 0.3)), (192, (0.0, -0.58, 0.26))], [(1, (0.0, 0.12, 0.07)), (192, (0.0, 0.12, 0.07))], lens=40, fstop=2.8, frames=192)


for _k, _v in (('title_soap', 'soap'), ('title_liquid', 'liquid'), ('title_workshop', 'workshop')):
    DEMOS[_k] = (lambda v: (lambda: title_scene(v)))(_v)
for _k, _v in (('outro_bars', 'soap'), ('outro_bottles', 'liquid'), ('outro_workshop', 'workshop')):
    DEMOS[_k] = (lambda v: (lambda: title_scene(v)))(_v)


# ───────────────────────── liquid products ─────────────────────────
@demo('bucket_mix')
def bucket_mix():
    base()
    B = (0.0, 0.1, 0.0)
    bucket(B, r=0.16, h=0.3, mat_=M['bucket_white'])
    lq = liquid('bucketliq', 0.132, 0.15, 0.2, M['liquid_soap'], loc=B)
    key(lq, 1, scale=(1, 1, 0.35)); key(lq, 120, scale=(1, 1, 1.0))
    jug, w = measuring_jug((-0.3, -0.05, 0), h=0.2, r=0.07, fill=0.6, liq_mat=M['water'], name='wjug')
    grp = bpy.data.objects.new('jc', None); bpy.context.collection.objects.link(grp); grp.location = (-0.3, -0.05, 0)
    jug.parent = grp; w.parent = grp; jug.location = (0, 0, 0); w.location = (0, 0, 0.004)
    key(grp, 1, loc=(-0.3, -0.05, 0), rot=(0, 0, 0)); key(grp, 25, loc=(-0.24, 0.08, 0.42), rot=(0, 0, 0))
    key(grp, 40, loc=(-0.22, 0.08, 0.42), rot=(0, math.radians(70), 0)); key(grp, 110, loc=(-0.22, 0.08, 0.42), rot=(0, math.radians(85), 0))
    key(grp, 135, loc=(-0.32, -0.05, 0.05), rot=(0, 0, 0)); ease_all(grp)
    key(w, 40, scale=(1, 1, 1)); key(w, 110, scale=(1, 1, 0.08))
    s = stream('wstream', [(-0.12, 0.08, 0.48), (-0.09, 0.09, 0.32), (-0.05, 0.1, 0.12)], 0.005, M['water']); stream_flow(s, 40, 48, 104, 112)
    pd = paddle(length=0.45)
    key(pd, 1, loc=(0.3, 0.3, 0.3), rot=(0, math.radians(-25), 0))
    for i, f in enumerate(range(120, 193, 4)):
        a = i * 0.55
        key(pd, f, loc=(B[0] + 0.06 * math.cos(a), B[1] + 0.06 * math.sin(a), 0.03), rot=(math.radians(10 * math.sin(a)), math.radians(-10 * math.cos(a)), a))
    cam_dolly((0.25, -0.85, 0.65), (0.15, -0.75, 0.62), (0.0, 0.08, 0.22), (0.0, 0.08, 0.2), lens=35, fstop=4)


@demo('ph_test')
def ph_test():
    base()
    c, lq = cup((0.0, 0.05, 0.0), r=0.035, h=0.08, liq=M['liquid_soap'], fill=0.7)
    strip = box('strip', (0.007, 0.0006, 0.08), (0.0, 0.05, 0.25), M['paper'], bevel=0)
    pad = box('pad', (0.007, 0.0012, 0.01), (0, 0, -0.034), M['strip'], bevel=0); pad.parent = strip
    key(strip, 1, loc=(0.0, 0.05, 0.25)); key(strip, 40, loc=(0.0, 0.05, 0.075)); key(strip, 70, loc=(0.0, 0.05, 0.075))
    key(strip, 100, loc=(-0.12, -0.02, 0.06), rot=(0, 0, 0)); key(strip, 130, loc=(-0.12, -0.04, 0.02), rot=(math.radians(-80), 0, 0)); ease_all(strip)
    sm = M['strip'].node_tree.nodes['Principled BSDF']
    sm.inputs['Base Color'].default_value = (0.95, 0.85, 0.2, 1); sm.inputs['Base Color'].keyframe_insert('default_value', frame=45)
    sm.inputs['Base Color'].default_value = (0.55, 0.72, 0.2, 1); sm.inputs['Base Color'].keyframe_insert('default_value', frame=85)
    chart = box('chart', (0.17, 0.05, 0.001), (-0.12, -0.08, 0.0006), M['paper'], bevel=0)
    cols = [(0.9, 0.2, 0.1), (0.95, 0.5, 0.1), (0.95, 0.75, 0.15), (0.95, 0.85, 0.2), (0.55, 0.72, 0.2), (0.25, 0.6, 0.4), (0.2, 0.4, 0.65), (0.3, 0.2, 0.5)]
    for i, col in enumerate(cols):
        box('chip', (0.016, 0.025, 0.0012), (-0.19 + i * 0.02, -0.08, 0.0015), mat('chp%d' % i, col, 0.6), bevel=0)
    cam_dolly((0.12, -0.42, 0.3), (0.0, -0.35, 0.25), (0.0, 0.03, 0.06), (-0.1, -0.05, 0.02), lens=45, fstop=3.2)


@demo('thicken')
def thicken():
    base()
    B = (0.0, 0.1, 0.0)
    bucket(B, r=0.16, h=0.3, mat_=M['bucket_white'])
    lq = liquid('bucketliq', 0.132, 0.15, 0.2, M['dish_green'], loc=B)
    c, sl = cup((-0.28, -0.05, 0.0), r=0.04, h=0.09, liq=M['water'], fill=0.6, name='saltcup')
    grp = bpy.data.objects.new('cc', None); bpy.context.collection.objects.link(grp); grp.location = (-0.28, -0.05, 0)
    c.parent = grp; sl.parent = grp; c.location = (0, 0, 0); sl.location = (0, 0, 0.004)
    key(grp, 1, loc=(-0.28, -0.05, 0)); key(grp, 25, loc=(-0.12, 0.08, 0.35)); key(grp, 40, loc=(-0.12, 0.08, 0.35), rot=(0, math.radians(75), 0))
    key(grp, 75, loc=(-0.12, 0.08, 0.35), rot=(0, math.radians(85), 0)); key(grp, 95, loc=(-0.3, -0.05, 0.0), rot=(0, 0, 0)); ease_all(grp)
    key(sl, 40, scale=(1, 1, 1)); key(sl, 75, scale=(1, 1, 0.05))
    s = stream('saltstream', [(-0.07, 0.08, 0.39), (-0.06, 0.09, 0.3), (-0.04, 0.1, 0.2)], 0.003, M['water']); stream_flow(s, 40, 46, 70, 76)
    pd = paddle(length=0.45)
    for i, f in enumerate(range(80, 160, 4)):
        a = i * 0.5
        key(pd, f, loc=(B[0] + 0.06 * math.cos(a), B[1] + 0.06 * math.sin(a), 0.03), rot=(0, 0, a))
    key(pd, 1, loc=(0.35, 0.3, 0.3), rot=(0, math.radians(-25), 0))
    # lift the paddle: thick liquid runs off slowly in a ribbon
    key(pd, 170, loc=(B[0], B[1] - 0.02, 0.3), rot=(0, math.radians(-10), 0)); key(pd, 192, loc=(B[0], B[1] - 0.02, 0.32), rot=(0, math.radians(-10), 0))
    rib = stream('ribbon', [(B[0], B[1] - 0.02, 0.29), (B[0], B[1] - 0.02, 0.25), (B[0], B[1] - 0.02, 0.2)], 0.004, M['dish_green']); stream_flow(rib, 170, 182, 400, 410)
    cam_dolly((0.2, -0.75, 0.62), (0.12, -0.66, 0.58), (0.0, 0.08, 0.24), (0.0, 0.08, 0.24), lens=38, fstop=4)


@demo('bottle_fill')
def bottle_fill():
    base()
    xs = [-0.2, -0.08, 0.04, 0.16, 0.28]
    lqs = []
    for i, x in enumerate(xs):
        b, cap, lq, lab = bottle((x, 0.08, 0.0), h=0.22, r=0.035, mat_=M['clear'], cap_mat=M['magenta'], liq=M['liquid_soap'], fill=0.92, name='fb%d' % i)
        bpy.data.objects.remove(cap)
        f0 = 20 + i * 34
        key(lq, 1, scale=(1, 1, 1.0 if i == 0 else 0.01))
        if i > 0: key(lq, f0, scale=(1, 1, 0.01)); key(lq, f0 + 30, scale=(1, 1, 1.0))
        lqs.append(lq)
    fn = funnel((xs[1], 0.08, 0.27))
    jug, w = measuring_jug((0, 0, 0), h=0.2, r=0.075, fill=0.7, liq_mat=M['liquid_soap'], name='fjug')
    grp = bpy.data.objects.new('jc', None); bpy.context.collection.objects.link(grp)
    jug.parent = grp; w.parent = grp; jug.location = (0, 0, 0); w.location = (0, 0, 0.004)
    for i, x in enumerate(xs[1:]):
        f0 = 20 + (i + 1) * 34
        key(fn, f0 - 8, loc=(x, 0.08, 0.27))
        key(grp, f0 - 4, loc=(x - 0.14, 0.08, 0.36), rot=(0, math.radians(40), 0))
        key(grp, f0 + 26, loc=(x - 0.14, 0.08, 0.36), rot=(0, math.radians(55), 0))
        st = stream('fs%d' % i, [(x - 0.06, 0.08, 0.42), (x - 0.03, 0.08, 0.36), (x, 0.08, 0.31)], 0.004, M['liquid_soap']); stream_flow(st, f0, f0 + 4, f0 + 24, f0 + 28)
    ease_all(grp)
    cam_dolly((0.3, -0.95, 0.5), (0.1, -0.88, 0.48), (0.02, 0.08, 0.2), (0.08, 0.08, 0.2), lens=33, fstop=4.5)


@demo('shampoo_bottles')
def shampoo_bottles():
    base(wall=(0.95, 0.9, 0.88))
    cols = [M['cream'], M['liquid_soap'], M['cream'], M['softener']]
    for i in range(4):
        b, cap, lq, lab = bottle((-0.18 + i * 0.12, 0.08, 0.0), h=0.24, r=0.042, mat_=M['hdpe'] if i % 2 == 0 else M['clear'], cap_mat=M['magenta'] if i % 2 == 0 else M['lemon'], liq=cols[i], fill=0.9, name='sh%d' % i)
        if lab: wrap_label((-0.18 + i * 0.12, 0.08, 0.0), 0.0435, 0.05, 0.13, ASSETS + ('/label_magenta.png' if i % 2 == 0 else '/label_green.png'), name='shl%d' % i)
    cam_dolly((-0.25, -0.6, 0.3), (0.2, -0.58, 0.28), (-0.05, 0.08, 0.12), (0.08, 0.08, 0.12), lens=40, fstop=3)


@demo('conditioner_cream')
def conditioner_cream():
    base()
    # double boiler: small pot sitting in a wider pot of hot water on the burner
    burner((0.0, 0.06, 0))
    big = pot((0.0, 0.06, 0.058), r=0.15, h=0.1, mat_=M['steel'])
    hw = liquid('hotwater', 0.142, 0.144, 0.06, M['water'], loc=(0.0, 0.06, 0.058))
    small = pot((0.0, 0.06, 0.08), r=0.11, h=0.12, mat_=M['enamel'], handles=False)
    cr = liquid('cream', 0.102, 0.104, 0.07, M['cream'], loc=(0.0, 0.06, 0.08))
    steam((0.0, 0.06, 0.2), size=(0.25, 0.25, 0.25), f_on=1, f_peak=30, peak=25)
    sp = spoon()
    for i, f in enumerate(range(1, 193, 4)):
        a = i * 0.6
        key(sp, f, loc=(0.0 + 0.05 * math.cos(a), 0.06 + 0.05 * math.sin(a), 0.1), rot=(math.radians(15 * math.sin(a)), math.radians(-15 * math.cos(a)), 0))
    thermometer((0.06, 0.1, 0.17), rot=(math.radians(-10), math.radians(15), 0))
    cam_dolly((0.3, -0.75, 0.5), (0.18, -0.66, 0.48), (0.0, 0.06, 0.15), (0.0, 0.06, 0.15), lens=38, fstop=3.5)


@demo('softener_mix')
def softener_mix():
    base()
    B = (0.0, 0.1, 0.0)
    bucket(B, r=0.16, h=0.3, mat_=M['bucket_blue'])
    lq = liquid('soft', 0.132, 0.15, 0.2, M['softener'], loc=B)
    pd = paddle(length=0.45)
    for i, f in enumerate(range(1, 193, 4)):
        a = i * 0.45
        key(pd, f, loc=(B[0] + 0.06 * math.cos(a), B[1] + 0.06 * math.sin(a), 0.03), rot=(math.radians(8 * math.sin(a)), math.radians(-8 * math.cos(a)), a))
    import_ph('multi_cleaner_5_litre', loc=(0.32, 0.15, 0.0), rot_z=math.radians(-30), recolor=M['hdpe'])
    cam_dolly((0.25, -0.8, 0.65), (0.12, -0.72, 0.62), (0.0, 0.08, 0.22), (0.0, 0.08, 0.2), lens=35, fstop=4)


@demo('spray_wipe')
def spray_wipe():
    base(wall=(0.9, 0.9, 0.88))
    # a smudged worktop panel that is sprayed and then wiped clean
    tile = box('tile', (0.5, 0.3, 0.01), (0.0, 0.1, 0.005), M['enamel'], bevel=0.002)
    dirt = mat('smudge', (0.45, 0.38, 0.3), 0.8, alpha=0.6)
    smudges = []
    random.seed(101)
    for i in range(14):
        sdg = cyl('smudge', random.uniform(0.012, 0.03), 0.0006, (random.uniform(-0.2, 0.2), random.uniform(0.0, 0.2), 0.0105), dirt, verts=24)
        f = 100 + int((sdg.location.x + 0.2) / 0.4 * 70)
        visible(sdg, 1, True); visible(sdg, f, False); smudges.append(sdg)
    b, head, lq = spray_bottle((0.0, 0.0, 0.0), liq=M['dish_green'])
    grp = bpy.data.objects.new('sb', None); bpy.context.collection.objects.link(grp)
    for o in list(bpy.data.objects):
        if o.name.startswith('spray') and o.parent is None: o.parent = grp
    key(grp, 1, loc=(0.32, -0.12, 0.0), rot=(0, 0, math.radians(120))); key(grp, 25, loc=(0.25, -0.15, 0.12), rot=(math.radians(-15), 0, math.radians(110)))
    key(grp, 70, loc=(0.25, -0.15, 0.12), rot=(math.radians(-15), 0, math.radians(110))); key(grp, 90, loc=(0.4, -0.1, 0.0), rot=(0, 0, math.radians(120))); ease_all(grp)
    # mist: a cloud of tiny droplets
    mist = []
    random.seed(7)
    for i in range(160):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=6, ring_count=4, radius=0.0012, location=(0.2, -0.12, 0.33)); o = bpy.context.object
        o.data.materials.append(M['water']); f = 30 + (i % 40)
        visible(o, 1, False); visible(o, f, True); key(o, f, loc=(0.18, -0.08, 0.33))
        key(o, f + 10, loc=(random.uniform(-0.2, 0.15), random.uniform(0.0, 0.22), 0.0115)); visible(o, 100 + int(random.random() * 60), False)
    cloth = towel((0.0, 0.0, 0.03), size=(0.14, 0.1), col=(0.95, 0.75, 0.1))
    key(cloth, 1, loc=(-0.35, -0.15, 0.03)); key(cloth, 95, loc=(-0.25, 0.1, 0.02))
    for i, f in enumerate(range(100, 175, 15)):
        key(cloth, f, loc=(-0.22 + i * 0.09, 0.05 + (0.08 if i % 2 else 0.0), 0.016))
    key(cloth, 192, loc=(0.3, 0.1, 0.02)); ease_all(cloth)
    cam_dolly((0.05, -0.62, 0.5), (0.0, -0.55, 0.46), (0.0, 0.08, 0.05), (0.0, 0.08, 0.05), lens=38, fstop=5)


@demo('dilution_ladder')
def dilution_ladder():
    base()
    for i in range(5):
        a = 1.0 - i * 0.2
        m_ = mat('dil%d' % i, (0.25 + 0.7 * (1 - a), 0.8, 0.3 + 0.65 * (1 - a)), 0.05, 0.55 + 0.4 * (1 - a), 1.36, sss=0.3 * a)
        cup((-0.24 + i * 0.12, 0.06, 0.0), r=0.04, h=0.1, liq=m_, fill=0.75, name='dl%d' % i)
    camera([(1, (-0.35, -0.55, 0.3)), (192, (0.3, -0.55, 0.3))], [(1, (-0.12, 0.06, 0.05)), (192, (0.12, 0.06, 0.05))], lens=40, fstop=3.5, frames=192)


@demo('disinfect_timer')
def disinfect_timer():
    base(wall=(0.9, 0.92, 0.92))
    tile = box('tile', (0.45, 0.3, 0.01), (-0.05, 0.1, 0.005), M['enamel'], bevel=0.002)
    wet = box('wetfilm', (0.36, 0.22, 0.0006), (-0.05, 0.1, 0.0105), mat('wet', (0.9, 0.95, 1.0), 0.02, 0.0, 1.33, alpha=0.25, coat=1.0), bevel=0)
    visible(wet, 1, False); visible(wet, 40, True)
    b, head, lq = spray_bottle((0.3, -0.05, 0.0), liq=mat('bkc', (0.6, 0.85, 1.0), 0.05, 0.6, 1.36, sss=0.2), cap_mat=M['bucket_blue'])
    # kitchen timer: a dial whose hand turns (numbers on its face only)
    face = cyl('timer', 0.05, 0.03, (0.28, 0.2, 0.05), M['hdpe'], rot=(math.radians(70), 0, 0), bevel=0.006)
    dial = cyl('dial', 0.042, 0.002, (0, 0, 0.016), M['paper'], verts=48); dial.parent = face
    hand = box('hand', (0.003, 0.035, 0.002), (0, 0.016, 0.018), M['red'], bevel=0); hand.parent = face
    piv = bpy.data.objects.new('handpiv', None); bpy.context.collection.objects.link(piv); piv.parent = face; piv.location = (0, 0, 0.018)
    hand.parent = piv; hand.location = (0, 0.016, 0)
    for i in range(12):
        tk = box('tick', (0.002, 0.008, 0.001), (0, 0, 0), M['black_plastic'], bevel=0); tk.parent = face
        a = i / 12 * math.tau; tk.location = (0.036 * math.sin(a), 0.036 * math.cos(a), 0.0175); tk.rotation_euler = (0, 0, -a)
    key(piv, 1, rot=(0, 0, 0)); key(piv, 192, rot=(0, 0, -math.radians(300)))
    for fc in fcurves(piv):
        for k in fc.keyframe_points: k.interpolation = 'LINEAR'
    cam_dolly((0.15, -0.6, 0.45), (0.05, -0.52, 0.4), (0.05, 0.1, 0.04), (0.05, 0.1, 0.04), lens=38, fstop=5)


@demo('hand_rub_mix')
def hand_rub_mix():
    base()
    c1, l1 = grad_cylinder((-0.22, 0.12, 0.0), h=0.25, r=0.025, liq=M['water'], fill=0.8, name='alc')
    c2, l2 = grad_cylinder((-0.12, 0.16, 0.0), h=0.18, r=0.015, liq=mat('glyc', (0.98, 0.97, 0.9), 0.02, 0.9, 1.47), fill=0.3, name='gly')
    c3, l3 = grad_cylinder((-0.04, 0.18, 0.0), h=0.18, r=0.015, liq=M['water'], fill=0.4, name='per')
    b, cap, lq, lab = bottle((0.15, 0.05, 0.0), h=0.26, r=0.05, mat_=M['clear'], cap_mat=M['bucket_blue'], liq=M['water'], fill=0.9, name='rub')
    bpy.data.objects.remove(cap)
    key(lq, 1, scale=(1, 1, 0.02)); key(lq, 60, scale=(1, 1, 0.02)); key(lq, 170, scale=(1, 1, 1.0))
    fn = funnel((0.15, 0.05, 0.31))
    grp = bpy.data.objects.new('cc', None); bpy.context.collection.objects.link(grp); grp.location = (-0.22, 0.12, 0)
    c1.parent = grp; l1.parent = grp; c1.location = (0, 0, 0); l1.location = (0, 0, 0.01)
    key(grp, 1, loc=(-0.22, 0.12, 0), rot=(0, 0, 0)); key(grp, 40, loc=(0.04, 0.05, 0.36), rot=(0, 0, 0))
    key(grp, 60, loc=(0.06, 0.05, 0.36), rot=(0, math.radians(100), 0)); key(grp, 150, loc=(0.06, 0.05, 0.36), rot=(0, math.radians(110), 0))
    key(grp, 180, loc=(-0.22, 0.12, 0.0), rot=(0, 0, 0)); ease_all(grp)
    key(l1, 60, scale=(1, 1, 1)); key(l1, 150, scale=(1, 1, 0.04))
    s = stream('alcstream', [(0.12, 0.05, 0.36), (0.14, 0.05, 0.33), (0.15, 0.05, 0.3)], 0.003, M['water']); stream_flow(s, 60, 66, 145, 152)
    cam_dolly((0.15, -0.65, 0.42), (0.05, -0.58, 0.38), (-0.02, 0.08, 0.16), (0.02, 0.08, 0.15), lens=38, fstop=4)


@demo('mixing_rule')
def mixing_rule():
    base(wall=(0.92, 0.88, 0.85))
    import_ph('bleach_bottle', loc=(-0.12, 0.05, 0.0), recolor=M['hdpe'])
    import_ph('all_purpose_cleaner', loc=(0.12, 0.05, 0.0), recolor=M['bucket_blue'])
    a = [o for o in bpy.data.objects if o.name == 'bleach_bottle_root'][0]
    b = [o for o in bpy.data.objects if o.name == 'all_purpose_cleaner_root'][0]
    key(a, 1, loc=(-0.1, 0.05, 0.0)); key(b, 1, loc=(0.1, 0.05, 0.0))
    key(a, 60, loc=(-0.1, 0.05, 0.0)); key(b, 60, loc=(0.1, 0.05, 0.0))
    key(a, 140, loc=(-0.32, 0.12, 0.0)); key(b, 140, loc=(0.32, 0.12, 0.0)); ease_all(a); ease_all(b)
    decal('hzb', ASSETS + '/hazard.png', (0.05, 0.05), (0, 0, 0), (math.radians(90), 0, 0)).parent = a
    cam_dolly((0.0, -0.75, 0.32), (0.0, -0.68, 0.3), (0.0, 0.08, 0.12), (0.0, 0.08, 0.12), lens=35, fstop=4)


def scale_weigh_liquid():
    base()
    S = (0.0, 0.02)
    sbase, plat, txt = scale_device((S[0], S[1], 0), display='0')
    jb, wl = measuring_jug((S[0], S[1] + 0.012, 0.035), h=0.14, r=0.055, fill=0.6, liq_mat=M['liquid_soap'], name='sjug')
    key(wl, 1, scale=(1, 1, 0.05)); key(wl, 40, scale=(1, 1, 0.05)); key(wl, 160, scale=(1, 1, 1.0))
    b, cap, lq, lab = bottle((0.0, 0.0, 0.0), h=0.22, r=0.04, mat_=M['hdpe'], cap_mat=M['bucket_blue'], liq=None, name='src', label=True)
    bpy.data.objects.remove(cap)
    grp = bpy.data.objects.new('bc', None); bpy.context.collection.objects.link(grp)
    for o in list(bpy.data.objects):
        if o.name.startswith('src') and o.parent is None: o.parent = grp
    key(grp, 1, loc=(0.32, 0.12, 0.0), rot=(0, 0, 0)); key(grp, 30, loc=(0.2, 0.03, 0.26), rot=(0, 0, 0))
    key(grp, 45, loc=(0.19, 0.03, 0.26), rot=(0, math.radians(-100), 0)); key(grp, 160, loc=(0.19, 0.03, 0.26), rot=(0, math.radians(-110), 0))
    key(grp, 185, loc=(0.3, 0.1, 0.0), rot=(0, 0, 0)); ease_all(grp)
    s = stream('ls', [(0.06, 0.03, 0.25), (0.03, 0.03, 0.16), (0.0, 0.03, 0.08)], 0.003, M['liquid_soap']); stream_flow(s, 45, 52, 155, 162)
    txt.hide_render = True
    vals = [0, 210, 450, 690, 900]
    for i, v in enumerate(vals):
        o = text_obj(str(v), txt.location[:], size=0.012, mat_=M['lcd_text'], rot=txt.rotation_euler[:], align='RIGHT')
        f_on = 1 if i == 0 else 40 + i * 28
        f_off = 40 + (i + 1) * 28 if i < len(vals) - 1 else 999
        visible(o, 1, i == 0); visible(o, f_on, True); visible(o, f_off, False)
    camera([(1, (-0.1, -0.5, 0.36)), (192, (-0.04, -0.42, 0.3))], [(1, (0.02, 0.0, 0.08)), (192, (0.02, -0.02, 0.06))], lens=45, fstop=3.2, frames=192)


def vary_camera(v):
    """Alternative angle for variant v: orbit the camera around its aim point and change the lens."""
    if v <= 0: return
    sc = bpy.context.scene; cam = sc.camera
    tgt = cam.constraints[0].target
    ang = [0, math.radians(34), math.radians(-30), math.radians(16)][v % 4]
    dist = [1, 0.78, 1.1, 0.88][v % 4]
    from kit import fcurves
    sc.frame_set(1); t0 = tgt.matrix_world.translation.copy()
    for fc in fcurves(cam):
        pass
    # rebuild location keys
    frames = sorted({int(k.co[0]) for fc in fcurves(cam) if fc.data_path == 'location' for k in fc.keyframe_points})
    pts = []
    for f in frames:
        sc.frame_set(f); p = cam.location.copy(); pts.append((f, p))
    for f, p in pts:
        rel = p - t0; rel.z *= (1.12 if v == 1 else 0.85 if v == 3 else 1.2)
        x = rel.x * math.cos(ang) - rel.y * math.sin(ang); y = rel.x * math.sin(ang) + rel.y * math.cos(ang)
        cam.location = (t0.x + x * dist, t0.y + y * dist, t0.z + rel.z * dist); cam.keyframe_insert('location', frame=f)
    cam.data.lens = cam.data.lens * (1.15 if v == 1 else 1.05 if v == 3 else 0.9)
