"""Phase 2 demo scenes: food, candles, textiles, crafts, hair & skin, farming, health, business and digital work.
Same conventions as demos.py (table top z=0, camera looks towards +y, 192 frames unless stated)."""
import bpy, math, random, os
from kit import *
from mathutils import Vector as V
from demos import DEMOS, demo, base, cam_dolly, falling, VARIANT
import kit as _kit
from mathutils import Matrix


def box(name, size, loc, mat_=None, bevel=0.002, rot=(0, 0, 0)):
    """kit.box bakes the location into the mesh; keep the origin at loc so boxes can be animated and scaled in place."""
    o = _kit.box(name, size, loc, mat_, bevel, rot)
    if o.location.length < 1e-9 and V(loc).length > 0:
        o.data.transform(Matrix.Translation(-V(loc))); o.location = loc
    return o
SCREENS = os.environ.get('WODDI_SCREENS', '/home/claude/vid3/screens')


FIT = {'yellow_onion': 0.08, 'lemon': 0.065, 'food_ginger_01': 0.09, 'food_avocado_01': 0.1, 'bananas': 0.2, 'potted_plant_01': 0.35, 'potted_plant_02': 0.35,
       'watering_can_metal_01': 0.32, 'medical_box': 0.26, 'vintage_flashlight': 0.16, 'alarm_clock_01': 0.11, 'magnifying_glass_01': 0.18,
       'wicker_basket_01': 0.3, 'ceramic_vase_01': 0.22, 'ceramic_vase_03': 0.25, 'brass_candleholders': 0.2, 'modified_thermos': 0.22,
       'plastic_container': 0.25, 'cardboard_box_01': 0.3}


def ph(name, loc=(0, 0, 0), rot_z=0.0, scale=1.0, recolor=None, size=None):
    """Import a Poly Haven model; size (metres) fits its largest side so props never come in at the wrong scale."""
    try:
        r = import_ph(name, loc=loc, rot_z=rot_z, scale=1.0, recolor=recolor)
    except Exception as e:
        print('missing model', name, e); return None
    size = size or FIT.get(name)
    meshes = [o for o in r.children_recursive if o.type == 'MESH']
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ V(c) for o in meshes for c in o.bound_box]
    if not pts: return r
    dims = [max(p[i] for p in pts) - min(p[i] for p in pts) for i in range(3)]
    k = (size / max(dims)) if size else scale
    zmin = min(p.z for p in pts) - r.location.z
    r.scale = (k, k, k); r.location = (loc[0], loc[1], loc[2] - zmin * k)
    return r


def screen_mat(key):
    m = bpy.data.materials.new('screen_' + key); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(SCREENS + '/' + key + '.png')
    nt.links.new(t.outputs['Color'], b.inputs['Base Color']); nt.links.new(t.outputs['Color'], b.inputs['Emission Color'])
    b.inputs['Emission Strength'].default_value = 0.9; b.inputs['Roughness'].default_value = 0.15; b.inputs['Coat Weight'].default_value = 0.6
    return m


def uv_plane(name, size, loc, rot, mat_):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object; o.name = name; o.scale = (size[0], size[1], 1); o.data.materials.append(mat_)
    return o


def laptop(loc, screen='sheet', rot_z=0.0, open_deg=108, name='laptop'):
    root = bpy.data.objects.new(name, None); bpy.context.collection.objects.link(root)
    alu = mat('alu', (0.55, 0.56, 0.6), 0.32, metal=0.8)
    b = box(name + '_base', (0.32, 0.22, 0.014), (0, 0, 0.007), alu, bevel=0.004); b.parent = root
    kb = box(name + '_kb', (0.27, 0.1, 0.0012), (0, 0.025, 0.0145), M['black_plastic'], bevel=0.001); kb.parent = root
    tp = box(name + '_tp', (0.1, 0.06, 0.0008), (0, -0.065, 0.0142), mat('tp', (0.45, 0.46, 0.5), 0.3), bevel=0.001); tp.parent = root
    hinge = bpy.data.objects.new(name + '_hinge', None); bpy.context.collection.objects.link(hinge); hinge.parent = root; hinge.location = (0, 0.108, 0.014)
    hinge.rotation_euler = (math.radians(open_deg - 90) * -1 + 0, 0, 0)
    lid = box(name + '_lid', (0.32, 0.008, 0.21), (0, 0.004, 0.105), alu, bevel=0.004); lid.parent = hinge
    sc = uv_plane(name + '_screen', (0.296, 0.185), (0, -0.0005, 0.108), (math.radians(90), 0, 0), screen_mat(screen)); sc.parent = hinge
    sc.rotation_euler = (math.radians(90), 0, math.radians(180)); sc.location = (0, -0.0006, 0.108)
    hinge.rotation_euler = (math.radians(-(open_deg - 90)), 0, 0)
    root.location = loc; root.rotation_euler = (0, 0, rot_z)
    return root


def phone(loc, screen='chat_phone', rot=(math.radians(75), 0, 0), name='phone'):
    root = bpy.data.objects.new(name, None); bpy.context.collection.objects.link(root)
    body = box(name + '_body', (0.075, 0.009, 0.155), (0, 0, 0), M['black_plastic'], bevel=0.008); body.parent = root
    sc = uv_plane(name + '_screen', (0.068, 0.146), (0, -0.0047, 0), (math.radians(90), 0, 0), screen_mat(screen)); sc.parent = root
    sc.rotation_euler = (math.radians(90), 0, math.radians(180))
    root.location = loc; root.rotation_euler = rot
    return root


def phone_stand(loc, screen='chat_phone', name='phone'):
    st = box(name + '_stand', (0.06, 0.05, 0.006), (loc[0], loc[1] + 0.02, 0.003), M['black_plastic'], bevel=0.002)
    return phone((loc[0], loc[1], 0.083), screen, rot=(math.radians(-12), 0, 0), name=name)


def mug(loc, col=(0.9, 0.9, 0.88)):
    m = mat('mug', col, 0.2, coat=0.5)
    c = lathe('mug', [(0.0, 0.0), (0.04, 0.0), (0.042, 0.09)], m, thick=0.004, loc=loc)
    lq = liquid('coffee', 0.036, 0.038, 0.07, mat('coffee', (0.15, 0.07, 0.03), 0.05, 0.3), loc=loc)
    return c


def plant(loc, scale=1.0):
    return ph('potted_plant_02', loc=loc, scale=scale) or ph('potted_plant_01', loc=loc, scale=scale)


def cash_notes(loc, n=6, rot_z=0.0, name='note'):
    cols = [(0.55, 0.35, 0.55), (0.25, 0.45, 0.6), (0.65, 0.4, 0.25), (0.3, 0.55, 0.35)]
    out = []
    for i in range(n):
        o = box(name, (0.15, 0.072, 0.0008), (loc[0] + random.uniform(-0.01, 0.01), loc[1] + random.uniform(-0.01, 0.01), loc[2] + 0.0009 * i), mat('cash%d' % (i % 4), cols[i % 4], 0.8), bevel=0, rot=(0, 0, rot_z + random.uniform(-0.08, 0.08)))
        out.append(o)
    return out


def coins(loc, n=8):
    gold = mat('coin', (0.85, 0.65, 0.3), 0.3, metal=1.0)
    return [cyl('coin', 0.011, 0.002, (loc[0] + random.uniform(-0.03, 0.03), loc[1] + random.uniform(-0.03, 0.03), loc[2] + 0.001 + 0.0021 * (i % 3)), gold, verts=24) for i in range(n)]


def desk_scene(screen='sheet', device='laptop', extras=True):
    base(wall=(0.9, 0.88, 0.85))
    random.seed(VARIANT() + 3)
    if device == 'laptop':
        laptop((0.0, 0.08, 0.0), screen)
        if extras:
            notebook((-0.33, -0.02, 0), rot_z=math.radians(12)); pen((-0.25, -0.1, 0), rot_z=math.radians(-20)); mug((0.3, 0.05, 0))
            phone((0.25, -0.12, 0.004), screen + '_phone' if os.path.exists(SCREENS + '/' + screen + '_phone.png') else 'chat_phone', rot=(0, 0, math.radians(-15)))
        camera([(1, (0.12, -0.62, 0.38)), (192, (0.02, -0.5, 0.3))], [(1, (0.0, 0.1, 0.12)), (192, (0.0, 0.12, 0.12))], lens=38, fstop=2.8, frames=192)
    else:
        phone_stand((0.0, 0.05, 0.0), screen + '_phone')
        if extras:
            notebook((-0.25, 0.05, 0), rot_z=math.radians(-8)); mug((0.22, 0.12, 0)); plant((0.36, 0.3, 0), 0.6)
        camera([(1, (0.05, -0.42, 0.22)), (192, (0.0, -0.3, 0.17))], [(1, (0.0, 0.05, 0.1)), (192, (0.0, 0.05, 0.1))], lens=45, fstop=2.4, frames=192)


for _s in ['sheet', 'dashboard', 'chat', 'email', 'social', 'ads', 'search', 'code', 'design', 'website', 'ai_chat', 'payment', 'bank', 'calendar', 'kanban', 'form', 'security', 'map', 'pos']:
    DEMOS['laptop_' + _s] = (lambda s: (lambda: desk_scene(s, 'laptop')))(_s)
    DEMOS['phone_' + _s] = (lambda s: (lambda: desk_scene(s, 'phone')))(_s)


# ───────────────────────── food ─────────────────────────
def powder_mat(col=(0.97, 0.95, 0.9), name='flourpowder'):
    return mat(name, col, 0.95, spec=0.2)


def mound(loc, r, h, mat_, name='mound'):
    """A soft heap of powder (flour, sugar, chalk): displaced, flattened sphere."""
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=loc, segments=48, ring_count=24); o = bpy.context.object; o.name = name
    o.scale = (r, r, h); o.data.materials.append(mat_)
    d = o.modifiers.new('d', 'DISPLACE'); tx = bpy.data.textures.new(name + 'n', 'CLOUDS'); tx.noise_scale = 0.25; d.texture = tx; d.strength = 0.08
    for p in o.data.polygons: p.use_smooth = True
    return o


@demo('flour_weigh')
def flour_weigh():
    base()
    sbase, plat, txt = scale_device((0.0, 0.02, 0), display='0')
    b = bowl((0.0, 0.032, 0.035), r=0.09, h=0.06, mat_=M['steel'])
    fl = mound((0.0, 0.032, 0.045), 0.06, 0.03, powder_mat())
    key(fl, 1, scale=(0.001, 0.001, 0.001)); key(fl, 30, scale=(0.02, 0.02, 0.008)); key(fl, 160, scale=(0.065, 0.065, 0.032))
    sack = box('flour_bag', (0.16, 0.1, 0.24), (0.3, 0.12, 0.12), mat('flourbag', (0.93, 0.9, 0.82), 0.9), bevel=0.03)
    d = sack.modifiers.new('d', 'DISPLACE'); tx = bpy.data.textures.new('sk', 'CLOUDS'); tx.noise_scale = 0.1; d.texture = tx; d.strength = 0.01
    sc_ = scoop((0.3, 0.0, 0.15), mat_=M['steel'])
    for i in range(3):
        f0 = 20 + i * 50
        key(sc_, f0, loc=(0.25, 0.0, 0.2), rot=(0, 0, 0)); key(sc_, f0 + 15, loc=(0.02, 0.0, 0.2), rot=(0, 0, 0))
        key(sc_, f0 + 25, loc=(0.02, 0.0, 0.2), rot=(math.radians(-100), 0, 0)); key(sc_, f0 + 40, loc=(0.25, 0.0, 0.2), rot=(0, 0, 0))
    ease_all(sc_)
    txt.hide_render = True
    for i, v in enumerate([0, 250, 500, 750]):
        o = text_obj(str(v), txt.location[:], size=0.012, mat_=M['lcd_text'], rot=txt.rotation_euler[:], align='RIGHT')
        f_on = 1 if i == 0 else 45 + (i - 1) * 50; f_off = 45 + i * 50 if i < 3 else 999
        visible(o, 1, i == 0); visible(o, f_on, True); visible(o, f_off, False)
    cam_dolly((0.15, -0.5, 0.38), (0.06, -0.42, 0.32), (0.05, 0.02, 0.06), (0.03, 0.0, 0.05), lens=45, fstop=3.2)


def dough(loc, r=0.06, name='dough'):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=48, ring_count=24); o = bpy.context.object; o.name = name
    o.scale = (1, 1, 0.6); o.data.materials.append(mat('dough', (0.95, 0.86, 0.68), 0.6, sss=0.4))
    d = o.modifiers.new('d', 'DISPLACE'); tx = bpy.data.textures.new('dg', 'CLOUDS'); tx.noise_scale = 0.03; d.texture = tx; d.strength = 0.004
    for p in o.data.polygons: p.use_smooth = True
    return o


@demo('dough_mix')
def dough_mix():
    base()
    b = bowl((0.0, 0.06, 0.0), r=0.15, h=0.09, mat_=M['enamel'])
    dg = dough((0.0, 0.06, 0.04), r=0.07)
    key(dg, 1, scale=(0.6, 0.6, 0.25)); key(dg, 180, scale=(1.0, 1.0, 0.6))
    flour = mound((0.05, 0.08, 0.035), 0.06, 0.03, powder_mat())
    key(flour, 1, scale=(0.06, 0.06, 0.03)); key(flour, 160, scale=(0.001, 0.001, 0.001))
    sp = spoon()
    for i, f in enumerate(range(1, 193, 4)):
        a = i * 0.7
        key(sp, f, loc=(0.0 + 0.06 * math.cos(a), 0.06 + 0.06 * math.sin(a), 0.03), rot=(math.radians(18 * math.sin(a)), math.radians(-18 * math.cos(a)), 0))
    jug, w = measuring_jug((0.3, 0.15, 0), h=0.16, r=0.06, fill=0.5, liq_mat=M['water'], name='wj')
    eggs = []
    for i in range(3):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.022, location=(-0.3 + i * 0.05, 0.0, 0.02)); eggs.append(bpy.context.object)
    for e in eggs: e.scale = (1, 1, 1.25); e.data.materials.append(mat('egg', (0.92, 0.82, 0.68), 0.5, sss=0.2))
    cam_dolly((0.2, -0.55, 0.45), (0.08, -0.45, 0.42), (0.0, 0.06, 0.05), (0.0, 0.06, 0.05), lens=40, fstop=3.5)


@demo('dough_knead')
def dough_knead():
    base()
    ph('wooden_cutting_board', loc=(0.0, 0.05, 0.0))
    dg = dough((0.0, 0.05, 0.075), r=0.08)
    for i, f in enumerate(range(1, 193, 24)):
        key(dg, f, scale=(1.0, 1.0, 0.6)); key(dg, f + 10, scale=(1.35, 1.1, 0.38)); key(dg, f + 20, scale=(1.0, 1.0, 0.6))
        key(dg, f, rot=(0, 0, math.radians(i * 40)))
    dust = decal('flourdust', ASSETS + '/flour_dust.png', (0.34, 0.22), (0.0, 0.05, 0.0415), (0, 0, 0)) if os.path.exists(ASSETS + '/flour_dust.png') else None
    pin = cyl('rolling_pin', 0.022, 0.3, (0.0, -0.12, 0.063), M['wood_light'], rot=(0, math.radians(90), 0))
    cam_dolly((0.25, -0.5, 0.4), (0.1, -0.42, 0.35), (0.0, 0.05, 0.07), (0.0, 0.05, 0.07), lens=40, fstop=3.2)


@demo('dough_cut')
def dough_cut():
    base()
    ph('wooden_cutting_board', loc=(0.0, 0.05, 0.0))
    sheet = box('dough_sheet', (0.32, 0.17, 0.008), (0.0, 0.05, 0.045), mat('dough', (0.95, 0.86, 0.68), 0.6, sss=0.4), bevel=0.003)
    kn = knife((0.0, 0.05, 0.12), rot=(0, 0, 0))
    pieces = []
    for i in range(8):
        for j in range(4):
            p_ = box('piece', (0.035, 0.035, 0.008), (-0.14 + i * 0.04, -0.01 + j * 0.04, 0.045), mat('dough', (0.95, 0.86, 0.68), 0.6, sss=0.4), bevel=0.002)
            visible(p_, 1, False); visible(p_, 140, True); pieces.append(p_)
    visible(sheet, 1, True); visible(sheet, 140, False)
    for i in range(6):
        f = 10 + i * 20; x = -0.12 + i * 0.048
        key(kn, f, loc=(x, 0.05, 0.1), rot=(0, 0, math.radians(90))); key(kn, f + 8, loc=(x, 0.05, 0.05), rot=(0, 0, math.radians(90))); key(kn, f + 16, loc=(x, 0.05, 0.1), rot=(0, 0, math.radians(90)))
    key(kn, 150, loc=(0.35, 0.1, 0.15)); ease_all(kn)
    cam_dolly((0.2, -0.42, 0.42), (0.08, -0.36, 0.38), (0.0, 0.05, 0.04), (0.0, 0.05, 0.04), lens=40, fstop=3.5)


@demo('oven_tray')
def oven_tray():
    base()
    tray = box('tray', (0.42, 0.3, 0.012), (0.0, 0.06, 0.006), mat('tray', (0.25, 0.25, 0.27), 0.35, metal=0.8), bevel=0.004)
    buns = []
    for i in range(4):
        for j in range(3):
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.04, location=(-0.15 + i * 0.1, -0.03 + j * 0.09, 0.012), segments=32, ring_count=16)
            o = bpy.context.object; o.scale = (1, 1, 0.55); o.data.materials.append(mat('bun', (0.8, 0.5, 0.2), 0.45, sss=0.3, coat=0.3))
            for p in o.data.polygons: p.use_smooth = True
            key(o, 1, scale=(0.75, 0.75, 0.35)); key(o, 150, scale=(1.0, 1.0, 0.6)); buns.append(o)
    mt = buns[0].data.materials[0].node_tree.nodes['Principled BSDF']
    mt.inputs['Base Color'].default_value = (0.95, 0.85, 0.62, 1); mt.inputs['Base Color'].keyframe_insert('default_value', frame=1)
    mt.inputs['Base Color'].default_value = (0.72, 0.4, 0.14, 1); mt.inputs['Base Color'].keyframe_insert('default_value', frame=170)
    for o in buns[1:]: o.data.materials[0] = buns[0].data.materials[0]
    steam((0.0, 0.06, 0.04), size=(0.35, 0.25, 0.2), f_on=60, f_peak=150, peak=12)
    cam_dolly((0.25, -0.5, 0.4), (0.1, -0.42, 0.34), (0.0, 0.06, 0.03), (0.0, 0.06, 0.03), lens=40, fstop=3.2)


@demo('deep_fry')
def deep_fry():
    base()
    burner((0.0, 0.06, 0))
    P = (0.0, 0.06, 0.058)
    pt = pot(P, r=0.15, h=0.12, mat_=mat('blackpot', (0.08, 0.08, 0.08), 0.35, metal=0.6))
    oil = liquid('oil', 0.142, 0.144, 0.07, mat('fryoil', (0.11, 0.045, 0.004), 0.2, spec=0.3), loc=P)
    d = oil.modifiers.new('bubbles', 'DISPLACE'); tx = bpy.data.textures.new('bb', 'VORONOI'); tx.noise_scale = 0.012; d.texture = tx; d.strength = 0.004
    em = bpy.data.objects.new('bt', None); bpy.context.collection.objects.link(em); d.texture_coords = 'OBJECT'; d.texture_coords_object = em
    key(em, 1, loc=(0, 0, 0)); key(em, 192, loc=(0.02, 0.01, 0.08))
    random.seed(9)
    for i in range(9):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.022, location=(P[0] + random.uniform(-0.08, 0.08), P[1] + random.uniform(-0.08, 0.08), P[2] + 0.072))
        o = bpy.context.object; o.data.materials.append(mat('puff', (0.42, 0.17, 0.03), 0.5, sss=0.15)); o.scale = (1, 1, 0.9)
        for f in range(1, 193, 16): key(o, f, loc=(o.location.x + random.uniform(-0.004, 0.004), o.location.y + random.uniform(-0.004, 0.004), P[2] + 0.07 + random.uniform(0, 0.006)))
    cam_dolly((0.3, -0.6, 0.55), (0.15, -0.5, 0.5), (0.0, 0.06, 0.12), (0.0, 0.06, 0.12), lens=38, fstop=3.5)


@demo('snacks_pack')
def snacks_pack():
    base()
    pile = flakes_pile((-0.15, 0.08), 0.1, 0.05, n=180, seed=12, kind='pearl', zbase=0.004, mat_=mat('chinchin', (0.8, 0.55, 0.22), 0.5))
    for o in pile: o.scale = (1.4, 1.0, 0.7)
    for i in range(5):
        pouch = box('pouch', (0.09, 0.03, 0.14), (0.08 + i * 0.07, 0.12 - (i % 2) * 0.05, 0.07), M['clear'], bevel=0.008)
        fill = box('fill', (0.08, 0.02, 0.09), (0.08 + i * 0.07, 0.12 - (i % 2) * 0.05, 0.05), mat('chinchin', (0.8, 0.55, 0.22), 0.5), bevel=0.006)
        lab = box('plab', (0.06, 0.0008, 0.04), (0.08 + i * 0.07, 0.12 - (i % 2) * 0.05 - 0.0158, 0.1), img_mat('pl%d' % i, ASSETS + '/label_magenta.png', 0.6), bevel=0)
    cam_dolly((-0.2, -0.55, 0.35), (0.1, -0.5, 0.32), (-0.05, 0.08, 0.06), (0.1, 0.08, 0.07), lens=40, fstop=3.2)


@demo('cake_decor')
def cake_decor():
    base()
    stand = lathe('stand', [(0.0, 0.0), (0.05, 0.0), (0.03, 0.06), (0.16, 0.065), (0.17, 0.075)], M['enamel'], loc=(0.0, 0.08, 0.0))
    cake = cyl('cake', 0.13, 0.09, (0.0, 0.08, 0.12), mat('sponge', (0.9, 0.75, 0.45), 0.7, sss=0.3), verts=64, bevel=0.01)
    icing = cyl('icing', 0.133, 0.093, (0.0, 0.08, 0.12), mat('icing', (0.98, 0.9, 0.95), 0.4, sss=0.5), verts=64, bevel=0.012)
    key(icing, 1, scale=(1, 1, 0.02), loc=(0.0, 0.08, 0.166)); key(icing, 150, scale=(1, 1, 1), loc=(0.0, 0.08, 0.12))
    for i in range(12):
        a = i / 12 * math.tau
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.012, location=(0.11 * math.cos(a), 0.08 + 0.11 * math.sin(a), 0.172))
        o = bpy.context.object; o.data.materials.append(mat('rosette', (0.83, 0.1, 0.45), 0.4, sss=0.3)); visible(o, 1, False); visible(o, 150 + i * 3, True)
    cam_dolly((0.2, -0.55, 0.38), (0.08, -0.45, 0.33), (0.0, 0.08, 0.13), (0.0, 0.08, 0.14), lens=40, fstop=3.2)


@demo('cooking_pot')
def cooking_pot():
    base()
    burner((0.0, 0.06, 0))
    P = (0.0, 0.06, 0.058)
    pot(P, r=0.15, h=0.15, mat_=M['steel'])
    stew = liquid('stew', 0.142, 0.144, 0.1, mat('stew', (0.17, 0.02, 0.003), 0.35, spec=0.25), loc=P)
    d = stew.modifiers.new('d', 'DISPLACE'); tx = bpy.data.textures.new('st', 'VORONOI'); tx.noise_scale = 0.03; d.texture = tx; d.strength = 0.005
    steam((P[0], P[1], P[2] + 0.34), size=(0.2, 0.2, 0.22), f_on=1, f_peak=30, peak=1.2)
    sp = spoon()
    for i, f in enumerate(range(1, 193, 5)):
        a = i * 0.6
        key(sp, f, loc=(P[0] + 0.07 * math.cos(a), P[1] + 0.07 * math.sin(a), P[2] + 0.04), rot=(math.radians(12 * math.sin(a)), math.radians(-12 * math.cos(a)), 0))
    for i, n in enumerate(['yellow_onion', 'food_ginger_01', 'lemon']):
        ph(n, loc=(-0.32 + i * 0.08, -0.08, 0.0))
    cam_dolly((0.3, -0.7, 0.5), (0.15, -0.6, 0.47), (0.0, 0.06, 0.13), (0.0, 0.06, 0.13), lens=38, fstop=3.5)


@demo('veg_chop')
def veg_chop():
    base()
    ph('wooden_cutting_board', loc=(0.0, 0.05, 0.0))
    ph('yellow_onion', loc=(0.08, 0.05, 0.041))
    tom = mat('tomato', (0.62, 0.025, 0.01), 0.3, sss=0.15, coat=0.5)
    for i in range(3):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.03, location=(-0.3 + i * 0.07, 0.15, 0.028)); o = bpy.context.object; o.scale = (1, 1, 0.85); o.data.materials.append(tom)
    slices = []
    for i in range(8):
        s = cyl('slice', 0.026, 0.006, (-0.1 + i * 0.012, 0.05, 0.044 + 0.01), tom, rot=(0, math.radians(80), 0), verts=32)
        visible(s, 1, False); visible(s, 20 + i * 18, True); slices.append(s)
    kn = knife((0.0, 0.05, 0.12))
    for i in range(8):
        f = 10 + i * 18; x = -0.1 + i * 0.012
        key(kn, f, loc=(x + 0.012, 0.0, 0.1), rot=(0, 0, math.radians(90))); key(kn, f + 8, loc=(x + 0.012, 0.0, 0.045), rot=(0, 0, math.radians(90)))
    ease_all(kn)
    cam_dolly((0.25, -0.45, 0.38), (0.1, -0.38, 0.33), (0.0, 0.05, 0.05), (-0.03, 0.05, 0.05), lens=42, fstop=3.0)


@demo('food_jars')
def food_jars():
    base()
    shelf((0.0, 0.95, 0.4), width=1.2, levels=(0.0,), depth=0.26)
    cols = [(0.75, 0.15, 0.08), (0.9, 0.55, 0.08), (0.45, 0.6, 0.15), (0.6, 0.1, 0.3), (0.95, 0.75, 0.2)]
    for i in range(6):
        x = -0.3 + i * 0.12
        jar = lathe('jar', [(0.0, 0.0), (0.045, 0.0), (0.05, 0.01), (0.05, 0.11), (0.035, 0.125)], M['clear'], thick=0.002, loc=(x, 0.05, 0))
        liquid('pres', 0.044, 0.047, 0.1, mat('pres%d' % i, cols[i % 5], 0.2, sss=0.5), loc=(x, 0.05, 0))
        cyl('jlid', 0.038, 0.016, (x, 0.05, 0.132), mat('jlid', (0.75, 0.6, 0.2), 0.3, metal=0.9), verts=40, bevel=0.002)
        wrap_label((x, 0.05, 0), 0.0505, 0.035, 0.075, ASSETS + '/label_green.png', name='jl%d' % i, arc_deg=120)
    camera([(1, (-0.35, -0.5, 0.25)), (192, (0.35, -0.5, 0.25))], [(1, (-0.1, 0.05, 0.07)), (192, (0.1, 0.05, 0.07))], lens=40, fstop=3, frames=192)


@demo('sun_drying')
def sun_drying():
    base(hdri='brown_photostudio_02', strength=1.1)
    rack = box('mesh_tray', (0.6, 0.4, 0.01), (0.0, 0.12, 0.05), mat('mesh', (0.6, 0.6, 0.6), 0.5, metal=0.6, alpha=0.6), bevel=0.002)
    for sx in (-1, 1):
        for sy in (-1, 1): box('leg', (0.015, 0.015, 0.05), (sx * 0.28, 0.12 + sy * 0.18, 0.025), M['wood_light'], bevel=0.002)
    random.seed(14)
    m1 = mat('dried', (0.85, 0.55, 0.15), 0.6, sss=0.3)
    pcs = []
    for i in range(70):
        s = cyl('drypiece', 0.02, 0.004, (random.uniform(-0.27, 0.27), 0.12 + random.uniform(-0.17, 0.17), 0.058), m1, verts=20)
        pcs.append(s)
    mt = m1.node_tree.nodes['Principled BSDF']
    mt.inputs['Base Color'].default_value = (0.95, 0.75, 0.3, 1); mt.inputs['Base Color'].keyframe_insert('default_value', frame=1)
    mt.inputs['Base Color'].default_value = (0.65, 0.35, 0.1, 1); mt.inputs['Base Color'].keyframe_insert('default_value', frame=190)
    area((0.6, -0.4, 1.4), (0, 0.1, 0), 600, 0.4, (1.0, 0.92, 0.78))
    cam_dolly((0.35, -0.65, 0.5), (0.15, -0.55, 0.45), (0.0, 0.12, 0.05), (0.0, 0.12, 0.05), lens=35, fstop=4)


@demo('food_storage')
def food_storage():
    base(wall=(0.9, 0.9, 0.86))
    pal = box('pallet', (0.7, 0.4, 0.06), (0.0, 0.3, 0.03), M['wood_light'], bevel=0.003)
    for i in range(3):
        s = box('sack', (0.2, 0.32, 0.12), (-0.22 + i * 0.22, 0.3, 0.12), sack_mat(), bevel=0.04)
        d = s.modifiers.new('d', 'DISPLACE'); tx = bpy.data.textures.new('sk%d' % i, 'CLOUDS'); tx.noise_scale = 0.08; d.texture = tx; d.strength = 0.015
    ph('plastic_crate_01', loc=(-0.3, -0.05, 0.0), rot_z=math.radians(90), scale=0.8)
    ph('plastic_container', loc=(0.3, -0.02, 0.0), scale=0.35)
    camera([(1, (0.3, -1.0, 0.6)), (192, (0.15, -0.85, 0.55))], [(1, (0.0, 0.2, 0.15)), (192, (0.0, 0.2, 0.15))], lens=32, fstop=5, frames=192)


@demo('hand_wash')
def hand_wash():
    base(wall=(0.88, 0.92, 0.9))
    stand = box('stand', (0.3, 0.3, 0.02), (0.0, 0.25, 0.25), M['wood_light'], bevel=0.003)
    for sx in (-1, 1):
        for sy in (-1, 1): box('leg', (0.02, 0.02, 0.25), (sx * 0.13, 0.25 + sy * 0.13, 0.125), M['wood_light'], bevel=0.002)
    bk = bucket((0.0, 0.25, 0.26), r=0.12, h=0.22, mat_=M['bucket_blue'])
    tap = cyl('tap', 0.012, 0.05, (0.0, 0.12, 0.33), M['steel'], rot=(math.radians(90), 0, 0))
    basin = lathe('basin', [(0.0, 0.0), (0.12, 0.0), (0.17, 0.06)], M['enamel'], thick=0.004, loc=(0.0, 0.08, 0.0))
    s = stream('tapw', [(0.0, 0.095, 0.33), (0.0, 0.09, 0.2), (0.0, 0.085, 0.02)], 0.004, M['water']); stream_flow(s, 1, 10, 400, 410)
    soap_bar((0.22, 0.0, 0.0), mat_=M['soap_bar'])
    cam_dolly((0.3, -0.7, 0.42), (0.15, -0.6, 0.38), (0.0, 0.15, 0.2), (0.0, 0.15, 0.2), lens=35, fstop=4)


@demo('plate_meal')
def plate_meal():
    base()
    plate = lathe('plate', [(0.0, 0.0), (0.09, 0.0), (0.13, 0.015), (0.14, 0.02)], M['enamel'], thick=0.004, loc=(0.0, 0.05, 0.0))
    rice = flakes_pile((-0.04, 0.03), 0.05, 0.03, n=260, seed=15, kind='pearl', zbase=0.006, mat_=mat('rice', (0.97, 0.96, 0.92), 0.5, sss=0.3))
    for o in rice: o.scale = (0.5, 0.25, 0.25)
    beans = flakes_pile((0.05, 0.03), 0.04, 0.02, n=120, seed=16, kind='pearl', zbase=0.006, mat_=mat('beans', (0.45, 0.2, 0.1), 0.4))
    for o in beans: o.scale = (0.9, 0.6, 0.6)
    greens = flakes_pile((0.0, 0.1), 0.045, 0.02, n=60, seed=17, zbase=0.008, mat_=mat('greens', (0.15, 0.5, 0.1), 0.5, sss=0.3))
    ph('bananas', loc=(0.25, 0.12, 0.0)); ph('food_avocado_01', loc=(-0.24, 0.12, 0.0))
    cup((0.22, -0.05, 0.0), r=0.035, h=0.09, liq=M['water'], fill=0.8, name='watercup')
    cam_dolly((0.15, -0.42, 0.42), (0.05, -0.35, 0.38), (0.0, 0.05, 0.02), (0.0, 0.05, 0.02), lens=40, fstop=3.2)


@demo('catering_table')
def catering_table():
    base(wall=(0.95, 0.9, 0.85))
    cloth = box('tablecloth', (1.3, 0.7, 0.003), (0.0, 0.25, 0.0015), mat('cloth', (0.95, 0.95, 0.93), 0.85), bevel=0)
    for i in range(3):
        x = -0.35 + i * 0.35
        tr = box('chafing', (0.3, 0.2, 0.06), (x, 0.3, 0.03), M['steel'], bevel=0.01)
        food = box('food', (0.26, 0.16, 0.01), (x, 0.3, 0.06), mat('food%d' % i, [(0.85, 0.4, 0.1), (0.95, 0.92, 0.85), (0.4, 0.55, 0.15)][i], 0.5, sss=0.3), bevel=0.004)
    for i in range(6):
        lathe('plate', [(0.0, 0.0), (0.07, 0.0), (0.1, 0.012)], M['enamel'], thick=0.003, loc=(-0.5 + i * 0.2, -0.05, 0.0035 + 0.0))
    camera([(1, (-0.5, -0.8, 0.5)), (192, (0.4, -0.8, 0.5))], [(1, (-0.2, 0.2, 0.05)), (192, (0.2, 0.2, 0.05))], lens=32, fstop=4, frames=192)


# ───────────────────────── candles ─────────────────────────
def flame(loc, name='flame'):
    m = mat('flamem', (1.0, 0.6, 0.2), 0.5, emit=((1.0, 0.55, 0.15), 30))
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.006, location=loc); f = bpy.context.object; f.scale = (0.8, 0.8, 2.2); f.data.materials.append(m)
    for fr in range(1, 193, 4): key(f, fr, scale=(0.8, 0.8, 2.0 + 0.4 * random.random()))
    bpy.ops.object.light_add(type='POINT', location=(loc[0], loc[1], loc[2] + 0.01)); L = bpy.context.object; L.data.energy = 1.5; L.data.color = (1, 0.7, 0.35); L.data.shadow_soft_size = 0.01
    return f


def jar_candle(loc, wax_col=(0.95, 0.92, 0.85), lit=False, wick=True, fill=0.75, name='jc'):
    j = lathe(name, [(0.0, 0.0), (0.04, 0.0), (0.042, 0.01), (0.042, 0.1)], M['clear'], thick=0.002, loc=loc)
    w = liquid(name + '_wax', 0.04, 0.041, 0.1 * fill, mat(name + 'wax', wax_col, 0.4, sss=0.7), loc=loc)
    if wick:
        cyl(name + '_wick', 0.0012, 0.03, (loc[0], loc[1], loc[2] + 0.1 * fill + 0.012), M['black_plastic'], verts=8)
    if lit: flame((loc[0], loc[1], loc[2] + 0.1 * fill + 0.03))
    return j, w


@demo('wax_melt')
def wax_melt():
    base()
    burner((0.0, 0.06, 0))
    big = pot((0.0, 0.06, 0.058), r=0.15, h=0.1, mat_=M['steel'])
    liquid('hotwater', 0.142, 0.144, 0.06, M['water'], loc=(0.0, 0.06, 0.058))
    jug, wax = measuring_jug((0.0, 0.06, 0.08), h=0.15, r=0.08, fill=0.5, liq_mat=mat('meltwax', (0.97, 0.94, 0.85), 0.1, 0.3, sss=0.5), name='waxjug')
    key(wax, 1, scale=(1, 1, 0.2)); key(wax, 190, scale=(1, 1, 1.0))
    fl = flakes_pile((0.0, 0.06), 0.06, 0.06, n=200, seed=18, zbase=0.09, mat_=mat('waxflake', (0.97, 0.96, 0.92), 0.4, sss=0.6))
    for i, o in enumerate(fl): key(o, 1, scale=o.scale[:]); key(o, 40 + (i * 140) // len(fl), scale=(0.01, 0.01, 0.01))
    thermometer((0.03, 0.08, 0.2), rot=(math.radians(-8), math.radians(12), 0))
    steam((0.0, 0.06, 0.2), size=(0.25, 0.25, 0.2), f_on=1, f_peak=30, peak=12)
    cam_dolly((0.3, -0.7, 0.5), (0.15, -0.6, 0.47), (0.0, 0.06, 0.15), (0.0, 0.06, 0.15), lens=38, fstop=3.5)


@demo('candle_pour')
def candle_pour():
    base()
    lqs = []
    for i in range(4):
        x = -0.12 + i * 0.1
        j, w = jar_candle((x, 0.08, 0.0), fill=0.75, name='cj%d' % i)
        key(w, 1, scale=(1, 1, 0.01 if i else 1.0))
        if i: key(w, 20 + i * 40, scale=(1, 1, 0.01)); key(w, 50 + i * 40, scale=(1, 1, 1.0))
        stick = box('wickbar', (0.1, 0.006, 0.004), (x, 0.08, 0.105), M['wood_light'], bevel=0)
    jug, wx = measuring_jug((0, 0, 0), h=0.15, r=0.06, fill=0.6, liq_mat=mat('meltwax2', (0.97, 0.9, 0.8), 0.1, 0.3, sss=0.5), name='pj')
    grp = bpy.data.objects.new('pjc', None); bpy.context.collection.objects.link(grp); jug.parent = grp; wx.parent = grp; wx.location = (0, 0, 0.004)
    for i in range(1, 4):
        x = -0.12 + i * 0.1; f0 = 20 + i * 40
        key(grp, f0 - 6, loc=(x - 0.12, 0.08, 0.18), rot=(0, math.radians(35), 0)); key(grp, f0 + 28, loc=(x - 0.12, 0.08, 0.18), rot=(0, math.radians(55), 0))
        s = stream('cps%d' % i, [(x - 0.05, 0.08, 0.24), (x - 0.02, 0.08, 0.17), (x, 0.08, 0.08)], 0.004, mat('meltwax3', (0.97, 0.9, 0.8), 0.1, 0.3, sss=0.5)); stream_flow(s, f0, f0 + 4, f0 + 26, f0 + 30)
    key(grp, 1, loc=(-0.35, 0.0, 0.0), rot=(0, 0, 0)); ease_all(grp)
    cam_dolly((0.3, -0.6, 0.38), (0.15, -0.52, 0.35), (0.02, 0.08, 0.1), (0.06, 0.08, 0.1), lens=38, fstop=3.5)


@demo('candles_lit')
def candles_lit():
    base(strength=0.35)
    random.seed(19)
    for i in range(4):
        jar_candle((-0.2 + i * 0.12, 0.1 + (i % 2) * 0.05, 0.0), wax_col=[(0.95, 0.92, 0.85), (0.9, 0.7, 0.75), (0.85, 0.9, 0.75), (0.95, 0.85, 0.6)][i], lit=True, name='lc%d' % i)
    for i in range(2):
        cyl('pillar', 0.035, 0.14 - i * 0.03, (0.3 + i * 0.09, 0.0, (0.14 - i * 0.03) / 2), mat('pillarw', (0.97, 0.95, 0.9), 0.4, sss=0.7), verts=48, bevel=0.004)
        flame((0.3 + i * 0.09, 0.0, 0.14 - i * 0.03 + 0.015))
    for L in [o for o in bpy.data.objects if o.type == 'LIGHT' and o.data.type in ('AREA', 'SPOT')]: L.data.energy *= 0.35
    cam_dolly((0.0, -0.6, 0.25), (0.05, -0.5, 0.22), (0.05, 0.08, 0.08), (0.05, 0.08, 0.08), lens=42, fstop=2.2)


@demo('wick_setup')
def wick_setup():
    base()
    for i in range(5):
        x = -0.24 + i * 0.12
        jar_candle((x, 0.08, 0.0), fill=0.0001, name='wj%d' % i)
        w = cyl('wick', 0.0012, 0.11, (x, 0.08, 0.055), M['black_plastic'], verts=8)
        tab = cyl('tab', 0.008, 0.002, (x, 0.08, 0.002), M['steel'], verts=16)
        key(w, 1, loc=(x, 0.08, 0.3)); key(w, 30 + i * 25, loc=(x, 0.08, 0.3)); key(w, 50 + i * 25, loc=(x, 0.08, 0.057)); ease_all(w)
        key(tab, 1, loc=(x, 0.08, 0.25)); key(tab, 30 + i * 25, loc=(x, 0.08, 0.25)); key(tab, 50 + i * 25, loc=(x, 0.08, 0.002)); ease_all(tab)
    cam_dolly((0.2, -0.5, 0.35), (0.08, -0.42, 0.3), (0.0, 0.08, 0.06), (0.0, 0.08, 0.06), lens=40, fstop=3.5)


# ───────────────────────── textiles ─────────────────────────
def fabric_mat(name='fabric', col=None, scale=5.0):
    """Bright wax-print cotton (an original pattern drawn for WODDI, assets/ankara.png), tiled."""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(ASSETS + '/ankara.png')
    tc = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (scale, scale, scale)
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector']); nt.links.new(mp.outputs[0], t.inputs['Vector'])
    nt.links.new(t.outputs['Color'], b.inputs['Base Color']); b.inputs['Roughness'].default_value = 0.85
    b.inputs['Sheen Weight'].default_value = 0.4
    return m


def cloth_sheet(size, loc, mat_, name='cloth'):
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=60, y_subdivisions=40, size=1, location=loc)
    o = bpy.context.object; o.name = name; o.scale = (size[0], size[1], 1)
    d = o.modifiers.new('d', 'DISPLACE'); tx = bpy.data.textures.new(name + 'tx', 'CLOUDS'); tx.noise_scale = 0.25; d.texture = tx; d.strength = 0.006
    s = o.modifiers.new('t', 'SOLIDIFY'); s.thickness = 0.002
    o.data.materials.append(mat_)
    for p in o.data.polygons: p.use_smooth = True
    return o


def tape_measure(loc, length=0.5, f0=1, f1=80):
    m = mat('tape', (0.95, 0.85, 0.2), 0.5)
    t = box('tape', (length, 0.016, 0.0006), (loc[0] + length / 2, loc[1], loc[2]), m, bevel=0)
    for i in range(int(length / 0.02)):
        mk = box('tk', (0.0008, 0.008 if i % 5 else 0.014, 0.0007), (loc[0] + i * 0.02, loc[1] + 0.004, loc[2] + 0.0002), M['black_plastic'], bevel=0)
    reel = cyl('reel', 0.03, 0.02, (loc[0] - 0.02, loc[1], loc[2] + 0.01), M['red'], verts=32)
    return t


def scissors(loc, rot_z=0.0, name='scissors'):
    piv = bpy.data.objects.new(name, None); bpy.context.collection.objects.link(piv)
    for s in (-1, 1):
        b = box(name + '_blade', (0.12, 0.012, 0.002), (0.06, s * 0.004, 0.002), M['steel'], bevel=0.001, rot=(0, 0, s * 0.08)); b.parent = piv
        bpy.ops.mesh.primitive_torus_add(major_radius=0.016, minor_radius=0.004, location=(-0.03, s * 0.018, 0.003)); h = bpy.context.object; h.data.materials.append(M['magenta']); h.parent = piv
    piv.location = loc; piv.rotation_euler = (0, 0, rot_z)
    return piv


@demo('fabric_measure')
def fabric_measure():
    base()
    cloth_sheet((0.8, 0.5), (0.0, 0.15, 0.003), fabric_mat())
    t = tape_measure((-0.3, 0.0, 0.009), length=0.6)
    key(t, 1, scale=(0.05, 1, 1), loc=(-0.3 + 0.015, 0.0, 0.009)); key(t, 120, scale=(1, 1, 1), loc=(0.0, 0.0, 0.009)); ease_all(t)
    chalk = box('chalk', (0.04, 0.03, 0.006), (0.3, -0.1, 0.006), mat('chalk', (0.95, 0.95, 0.98), 0.9), bevel=0.003)
    line = box('chalkline', (0.5, 0.002, 0.0004), (0.0, 0.08, 0.0055), mat('chalkl', (0.98, 0.98, 1.0), 0.9), bevel=0)
    key(line, 1, scale=(0.01, 1, 1)); key(line, 120, scale=(0.01, 1, 1)); key(line, 190, scale=(1, 1, 1))
    cam_dolly((0.2, -0.6, 0.45), (0.05, -0.5, 0.4), (0.0, 0.05, 0.0), (0.0, 0.05, 0.0), lens=38, fstop=4)


@demo('fabric_cut')
def fabric_cut():
    base()
    left = cloth_sheet((0.35, 0.45), (-0.175, 0.15, 0.003), fabric_mat('fab_l'))
    right = cloth_sheet((0.35, 0.45), (0.175, 0.15, 0.003), fabric_mat('fab_r'))
    key(right, 1, loc=(0.175, 0.15, 0.003)); key(right, 150, loc=(0.175, 0.15, 0.003)); key(right, 190, loc=(0.2, 0.17, 0.003))
    sc = scissors((0.0, -0.12, 0.01), rot_z=math.radians(90))
    key(sc, 1, loc=(0.0, -0.12, 0.01)); key(sc, 150, loc=(0.0, 0.38, 0.01))
    for c in fcurves(sc):
        for k in c.keyframe_points: k.interpolation = 'LINEAR'
    cam_dolly((0.25, -0.55, 0.45), (0.1, -0.45, 0.4), (0.0, 0.1, 0.0), (0.0, 0.2, 0.0), lens=38, fstop=4)


@demo('sewing_machine')
def sewing_machine():
    base()
    body = mat('machine', (0.92, 0.92, 0.9), 0.3, coat=0.5)
    box('sm_base', (0.42, 0.18, 0.05), (0.0, 0.1, 0.025), body, bevel=0.012)
    box('sm_pillar', (0.07, 0.14, 0.2), (0.17, 0.1, 0.15), body, bevel=0.015)
    box('sm_arm', (0.36, 0.11, 0.07), (0.02, 0.1, 0.27), body, bevel=0.02)
    box('sm_head', (0.06, 0.1, 0.12), (-0.15, 0.1, 0.22), body, bevel=0.012)
    wheel = cyl('sm_wheel', 0.06, 0.02, (0.22, 0.1, 0.25), M['steel'], rot=(0, math.radians(90), 0), verts=40)
    needle = cyl('needle', 0.0015, 0.06, (-0.15, 0.08, 0.13), M['steel'], verts=8)
    for f in range(1, 193, 4): key(needle, f, loc=(-0.15, 0.08, 0.13)); key(needle, f + 2, loc=(-0.15, 0.08, 0.1))
    key(wheel, 1, rot=(0, math.radians(90), 0)); key(wheel, 192, rot=(math.radians(720), math.radians(90), 0))
    cl = cloth_sheet((0.3, 0.2), (-0.15, 0.08, 0.052), fabric_mat())
    key(cl, 1, loc=(-0.15, 0.2, 0.052)); key(cl, 192, loc=(-0.15, -0.02, 0.052))
    for c in fcurves(cl):
        for k in c.keyframe_points: k.interpolation = 'LINEAR'
    sp = cyl('spool', 0.012, 0.03, (0.05, 0.1, 0.32), M['magenta'], verts=24)
    cam_dolly((0.3, -0.65, 0.4), (0.12, -0.55, 0.35), (-0.05, 0.1, 0.15), (-0.08, 0.1, 0.13), lens=38, fstop=3.5)


@demo('thread_spools')
def thread_spools():
    base()
    cols = [(0.83, 0.0, 0.42), (0.49, 0.71, 0.09), (0.2, 0.4, 0.8), (0.95, 0.75, 0.1), (0.1, 0.1, 0.1), (0.95, 0.95, 0.95)]
    for i, c in enumerate(cols):
        x = -0.2 + i * 0.08
        cyl('spool_end', 0.018, 0.006, (x, 0.08, 0.003), M['wood_light'], verts=24); cyl('thread', 0.015, 0.04, (x, 0.08, 0.026), mat('th%d' % i, c, 0.6), verts=32)
        cyl('spool_top', 0.018, 0.006, (x, 0.08, 0.049), M['wood_light'], verts=24)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.05, location=(0.25, -0.05, 0.02)); pin = bpy.context.object; pin.scale = (1, 1, 0.5); pin.data.materials.append(M['red'])
    for i in range(8):
        a = i / 8 * math.tau
        cyl('pin', 0.0008, 0.05, (0.25 + 0.03 * math.cos(a), -0.05 + 0.03 * math.sin(a), 0.05), M['steel'], verts=6, rot=(0.3 * math.sin(a), 0.3 * math.cos(a), 0))
    sc = scissors((-0.15, -0.08, 0.004), rot_z=math.radians(20))
    tape_measure((-0.3, -0.18, 0.001), length=0.3)
    cam_dolly((-0.25, -0.5, 0.35), (0.15, -0.45, 0.3), (0.0, 0.03, 0.03), (0.05, 0.0, 0.03), lens=40, fstop=3.0)


def dress(loc, col_mat, name='dress'):
    prof = [(0.03, 0.0), (0.06, -0.05), (0.07, -0.18), (0.11, -0.45), (0.14, -0.6)]
    d = lathe(name, prof, col_mat, thick=0.003, loc=loc, seg=48); d.scale = (1, 0.55, 1)
    bpy.ops.curve.primitive_bezier_curve_add(location=(0, 0, 0)); h = bpy.context.object
    p0, p1 = h.data.splines[0].bezier_points
    p0.co = (loc[0] - 0.13, loc[1], loc[2] + 0.02); p0.handle_right = (loc[0] - 0.05, loc[1], loc[2] + 0.06); p0.handle_left = (loc[0] - 0.15, loc[1], loc[2])
    p1.co = (loc[0] + 0.13, loc[1], loc[2] + 0.02); p1.handle_left = (loc[0] + 0.05, loc[1], loc[2] + 0.06); p1.handle_right = (loc[0] + 0.15, loc[1], loc[2])
    h.data.bevel_depth = 0.004; h.data.materials.append(M['wood_light'])
    hk = cyl('hook', 0.002, 0.04, (loc[0], loc[1], loc[2] + 0.07), M['steel'], verts=8)
    return d


@demo('garment_hanger')
def garment_hanger():
    base(wall=(0.93, 0.9, 0.88))
    rail = cyl('rail', 0.008, 1.0, (0.0, 0.5, 0.95), M['steel'], rot=(0, math.radians(90), 0), verts=16)
    for s in (-1, 1): cyl('post', 0.01, 0.95, (s * 0.5, 0.5, 0.475), M['steel'], verts=16)
    for i in range(4):
        dress((-0.3 + i * 0.2, 0.5, 0.88), fabric_mat('dr%d' % i, scale=4.0 + i * 1.5) if i != 2 else mat('drp%d' % i, (0.1, 0.25, 0.55), 0.8), name='dress%d' % i)
    camera([(1, (-0.4, -0.6, 0.7)), (192, (0.35, -0.6, 0.7))], [(1, (-0.1, 0.5, 0.6)), (192, (0.1, 0.5, 0.6))], lens=32, fstop=3.5, frames=192)


@demo('iron_press')
def iron_press():
    base()
    board = box('ironboard', (0.7, 0.3, 0.02), (0.0, 0.1, 0.01), mat('board', (0.85, 0.85, 0.88), 0.8), bevel=0.01)
    cloth_sheet((0.5, 0.25), (0.0, 0.1, 0.023), fabric_mat())
    iron = box('iron', (0.2, 0.09, 0.05), (0.0, 0.1, 0.05), mat('ironb', (0.25, 0.45, 0.8), 0.3, coat=0.5), bevel=0.02)
    plate = box('soleplate', (0.2, 0.09, 0.008), (0.0, 0.1, 0.028), M['steel'], bevel=0.01)
    plate.parent = iron; plate.location = (0, 0, -0.022)
    for i, f in enumerate(range(1, 193, 32)):
        key(iron, f, loc=(-0.15, 0.1, 0.05)); key(iron, f + 16, loc=(0.15, 0.1, 0.05))
    steam((0.0, 0.1, 0.06), size=(0.35, 0.15, 0.15), f_on=1, f_peak=30, peak=10)
    cam_dolly((0.25, -0.55, 0.42), (0.1, -0.45, 0.37), (0.0, 0.1, 0.03), (0.0, 0.1, 0.03), lens=38, fstop=3.5)


@demo('yarn_crochet')
def yarn_crochet():
    base()
    ph('wicker_basket_01', loc=(0.25, 0.15, 0.0), scale=0.6)
    for i, c in enumerate([(0.83, 0.0, 0.42), (0.49, 0.71, 0.09), (0.95, 0.75, 0.1), (0.2, 0.4, 0.8)]):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.04, location=(-0.25 + i * 0.09, 0.15, 0.04)); b = bpy.context.object
        b.data.materials.append(mat('yarn%d' % i, c, 0.9, sss=0.2))
        d = b.modifiers.new('d', 'DISPLACE'); tx = bpy.data.textures.new('yr%d' % i, 'WOOD'); tx.wood_type = 'RINGNOISE'; tx.noise_scale = 0.01; d.texture = tx; d.strength = 0.004
    sw = cloth_sheet((0.18, 0.1), (0.0, -0.02, 0.004), mat('swatch', (0.83, 0.0, 0.42), 0.9))
    key(sw, 1, scale=(0.18, 0.02, 1)); key(sw, 190, scale=(0.18, 0.1, 1))
    hook = cyl('hook', 0.0025, 0.15, (0.05, -0.08, 0.01), M['steel'], rot=(0, math.radians(80), math.radians(20)), verts=12)
    for f in range(1, 193, 12): key(hook, f, loc=(0.05, -0.08, 0.01)); key(hook, f + 6, loc=(0.06, -0.075, 0.025))
    cam_dolly((-0.2, -0.5, 0.35), (0.05, -0.42, 0.3), (0.0, 0.05, 0.03), (0.0, 0.03, 0.02), lens=40, fstop=3.0)


@demo('pattern_paper')
def pattern_paper():
    base()
    paper = box('pattern', (0.6, 0.4, 0.0008), (0.0, 0.1, 0.0004), mat('ppaper', (0.92, 0.88, 0.75), 0.9), bevel=0)
    pts = [(-0.2, -0.05), (-0.05, 0.25), (0.15, 0.25), (0.22, -0.05)]
    for (a, b) in zip(pts, pts[1:] + pts[:1]):
        L = math.dist(a, b); ang = math.atan2(b[1] - a[1], b[0] - a[0])
        seg = box('pline', (L, 0.002, 0.0004), ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, 0.001), M['black_plastic'], bevel=0, rot=(0, 0, ang))
    ruler = box('ruler', (0.5, 0.04, 0.003), (0.0, -0.08, 0.002), mat('ruler', (0.95, 0.92, 0.6), 0.5, trans=0.3), bevel=0.001)
    pencil = cyl('pencil', 0.004, 0.16, (0.0, 0.0, 0.006), mat('pencilm', (0.95, 0.75, 0.1), 0.5), rot=(0, math.radians(90), 0.4), verts=6)
    for i, (x, y) in enumerate(pts + pts[:1]):
        key(pencil, 1 + i * 40, loc=(x + 0.08, y, 0.01))
    cam_dolly((0.15, -0.55, 0.55), (0.05, -0.45, 0.5), (0.0, 0.1, 0.0), (0.0, 0.1, 0.0), lens=36, fstop=4)


# ───────────────────────── crafts, beads, decor ─────────────────────────
BEAD_COLS = [(0.83, 0.0, 0.42), (0.49, 0.71, 0.09), (0.95, 0.75, 0.1), (0.2, 0.4, 0.8), (0.95, 0.95, 0.95), (0.1, 0.1, 0.1), (0.9, 0.3, 0.1)]


@demo('beads_bowls')
def beads_bowls():
    base()
    for i, c in enumerate(BEAD_COLS[:5]):
        x = -0.24 + i * 0.12; y = 0.08 + (i % 2) * 0.05
        lathe('bb%d' % i, [(0.0, 0.0), (0.03, 0.0), (0.05, 0.03)], M['wood_light'], thick=0.003, loc=(x, y, 0.0))
        pile = flakes_pile((x, y), 0.035, 0.02, n=120, seed=20 + i, kind='pearl', zbase=0.004, mat_=mat('bead%d' % i, c, 0.15, coat=0.8))
    cam_dolly((-0.2, -0.45, 0.32), (0.1, -0.4, 0.28), (-0.05, 0.08, 0.02), (0.08, 0.08, 0.02), lens=42, fstop=2.8)


@demo('bead_string')
def bead_string():
    base()
    pts = [(-0.25, 0.0, 0.004), (-0.1, 0.05, 0.004), (0.05, 0.08, 0.004), (0.2, 0.06, 0.004)]
    s = stream('wire', pts, 0.0008, M['steel']); stream_flow(s, 1, 2, 999, 1000)
    random.seed(21)
    for i in range(30):
        t = i / 30
        x = -0.25 + t * 0.45; y = 0.0 + 0.08 * math.sin(t * 2.5)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.006, location=(x, y, 0.008)); b = bpy.context.object
        b.data.materials.append(mat('sb%d' % (i % 7), BEAD_COLS[i % 7], 0.15, coat=0.8))
        f = 5 + i * 6; key(b, 1, loc=(0.25, 0.08, 0.06)); key(b, f, loc=(0.25, 0.08, 0.06)); key(b, f + 10, loc=(x, y, 0.008)); visible(b, 1, False); visible(b, f, True)
    for i, c in enumerate(BEAD_COLS[:3]):
        flakes_pile((0.3, -0.05 + i * 0.07), 0.025, 0.01, n=40, seed=30 + i, kind='pearl', zbase=0.002, mat_=mat('bpile%d' % i, c, 0.15, coat=0.8))
    cam_dolly((0.0, -0.4, 0.3), (0.05, -0.32, 0.25), (0.0, 0.03, 0.0), (0.0, 0.03, 0.0), lens=45, fstop=2.8)


@demo('jewelry_finished')
def jewelry_finished():
    base(wall=(0.88, 0.85, 0.82))
    velvet = box('velvet', (0.5, 0.3, 0.02), (0.0, 0.1, 0.01), mat('velvet', (0.15, 0.05, 0.12), 0.9), bevel=0.006)
    for n in range(3):
        for i in range(36):
            a = i / 36 * math.tau
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.006, location=(-0.15 + n * 0.15 + 0.055 * math.cos(a), 0.1 + 0.07 * math.sin(a), 0.026))
            bpy.context.object.data.materials.append(mat('jb%d' % ((i + n) % 7), BEAD_COLS[(i + n) % 7], 0.12, coat=0.9))
    cam_dolly((-0.15, -0.45, 0.4), (0.12, -0.4, 0.35), (0.0, 0.1, 0.02), (0.0, 0.1, 0.02), lens=40, fstop=2.8)


@demo('paint_decor')
def paint_decor():
    base()
    panel = box('panel', (0.4, 0.02, 0.3), (0.0, 0.25, 0.15), mat('panelw', (0.95, 0.93, 0.9), 0.8), bevel=0.003)
    stripe = box('stripe', (0.4, 0.002, 0.1), (0.0, 0.239, 0.15), M['magenta'], bevel=0)
    key(stripe, 1, scale=(0.01, 1, 1)); key(stripe, 170, scale=(1, 1, 1))
    for i, c in enumerate([M['magenta'], M['lemon'], M['bucket_blue']]):
        cyl('tin', 0.045, 0.08, (-0.3 + i * 0.11, -0.05, 0.04), M['steel'], verts=40); cyl('paint', 0.042, 0.004, (-0.3 + i * 0.11, -0.05, 0.081), c, verts=40)
    brush = box('brush', (0.025, 0.01, 0.16), (0.0, 0.2, 0.15), M['wood_light'], bevel=0.003)
    for f in range(1, 171, 20): key(brush, f, loc=(-0.2 + 0.4 * f / 170, 0.225, 0.17 + (0.02 if (f // 20) % 2 else -0.02)))
    ph('ceramic_vase_01', loc=(0.3, 0.05, 0.0), scale=0.6)
    cam_dolly((0.2, -0.55, 0.35), (0.08, -0.45, 0.3), (0.0, 0.15, 0.13), (0.0, 0.15, 0.13), lens=36, fstop=4)


@demo('upcycle_bottles')
def upcycle_bottles():
    base()
    for i in range(4):
        b, cap, lq, lab = bottle((-0.18 + i * 0.12, 0.08, 0.0), h=0.22, r=0.04, mat_=[M['magenta'], M['lemon'], M['bucket_blue'], mat('gold', (0.85, 0.65, 0.3), 0.3, metal=1)][i], cap_mat=M['black_plastic'], name='ub%d' % i, label=False)
        bpy.data.objects.remove(cap)
        stem = cyl('stem', 0.003, 0.2, (-0.18 + i * 0.12, 0.08, 0.3), mat('stemm', (0.2, 0.5, 0.15), 0.6), verts=8)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.025, location=(-0.18 + i * 0.12, 0.08, 0.4)); bpy.context.object.data.materials.append(mat('flower%d' % i, [(0.95, 0.4, 0.5), (0.95, 0.85, 0.2), (0.9, 0.9, 0.95), (0.95, 0.5, 0.2)][i], 0.6, sss=0.3))
    cam_dolly((-0.2, -0.65, 0.3), (0.15, -0.6, 0.3), (0.0, 0.08, 0.15), (0.0, 0.08, 0.15), lens=38, fstop=3)


@demo('event_decor')
def event_decor():
    base(wall=(0.97, 0.92, 0.9))
    cloth = box('tablecloth', (1.2, 0.6, 0.004), (0.0, 0.25, 0.002), mat('ecloth', (0.98, 0.97, 0.95), 0.85), bevel=0)
    runner = box('runner', (1.2, 0.18, 0.005), (0.0, 0.25, 0.004), M['magenta'], bevel=0)
    random.seed(22)
    for i in range(9):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.07, location=(-0.6 + i * 0.15, 0.9, 0.7 + random.uniform(-0.1, 0.15))); o = bpy.context.object
        o.scale = (1, 1, 1.15); o.data.materials.append([M['magenta'], M['lemon'], mat('gold', (0.85, 0.65, 0.3), 0.25, metal=1)][i % 3])
    ph('ceramic_vase_03', loc=(0.0, 0.25, 0.006), scale=0.7)
    for i in range(4): ph('brass_candleholders', loc=(-0.4 + i * 0.27, 0.3, 0.006), scale=0.5) if i in (0, 3) else None
    camera([(1, (-0.4, -0.9, 0.55)), (192, (0.3, -0.85, 0.5))], [(1, (0.0, 0.4, 0.3)), (192, (0.0, 0.4, 0.3))], lens=30, fstop=4, frames=192)


@demo('handbag')
def handbag():
    base()
    bag = box('bag', (0.26, 0.09, 0.18), (0.0, 0.1, 0.09), tex_mat('leather', 'leather_red_02', 2.0) if os.path.exists(PH + '/tex/leather_red_02/leather_red_02_diff_2k.jpg') else mat('leatherm', (0.5, 0.12, 0.08), 0.4), bevel=0.02)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.08, minor_radius=0.006, location=(0.0, 0.1, 0.18), rotation=(math.radians(90), 0, 0)); h = bpy.context.object; h.scale = (1, 1, 0.8); h.data.materials.append(M['black_plastic'])
    clasp = box('clasp', (0.04, 0.01, 0.02), (0.0, 0.054, 0.15), mat('gold', (0.85, 0.65, 0.3), 0.25, metal=1), bevel=0.003)
    for i in range(2): box('clutch', (0.18, 0.04, 0.1), (-0.3 + i * 0.6, 0.0, 0.05), [M['magenta'], M['lemon']][i], bevel=0.015)
    cam_dolly((0.25, -0.55, 0.3), (0.1, -0.45, 0.25), (0.0, 0.08, 0.1), (0.0, 0.08, 0.1), lens=40, fstop=2.8)


# ───────────────────────── hair and skin ─────────────────────────
@demo('hair_tools')
def hair_tools():
    base(wall=(0.95, 0.9, 0.9))
    comb = box('comb', (0.2, 0.012, 0.004), (0.0, 0.0, 0.002), M['black_plastic'], bevel=0.001)
    for i in range(30): box('tooth', (0.002, 0.03, 0.004), (-0.095 + i * 0.0066, -0.02, 0.002), M['black_plastic'], bevel=0)
    pick = box('pick', (0.05, 0.12, 0.004), (-0.25, 0.05, 0.002), M['magenta'], bevel=0.003)
    for i in range(3):
        b, cap, lq, lab = bottle((0.1 + i * 0.1, 0.18, 0.0), h=0.18, r=0.035, mat_=M['hdpe'], cap_mat=[M['magenta'], M['lemon'], M['bucket_blue']][i], name='hp%d' % i)
    jar = cyl('pomade', 0.05, 0.05, (-0.12, 0.17, 0.025), M['amber_glass'], verts=48); cyl('pomlid', 0.052, 0.015, (-0.12, 0.17, 0.057), M['black_plastic'], verts=48, bevel=0.003)
    for i in range(4): cyl('braid', 0.008, 0.35, (-0.3 + i * 0.02, -0.12, 0.008), mat('ext', (0.05, 0.03, 0.02), 0.6), rot=(0, math.radians(90), 0.1 * i), verts=12)
    cam_dolly((-0.15, -0.5, 0.35), (0.1, -0.45, 0.32), (0.0, 0.05, 0.04), (0.05, 0.08, 0.05), lens=40, fstop=3)


@demo('cream_jars')
def cream_jars():
    base(wall=(0.95, 0.92, 0.9))
    for i in range(4):
        x = -0.2 + i * 0.13
        cyl('cjar', 0.045, 0.06, (x, 0.08, 0.03), M['clear'], verts=48); c = cyl('cream', 0.042, 0.05, (x, 0.08, 0.026), M['cream'], verts=48)
        key(c, 1, scale=(1, 1, 0.1 if i == 3 else 1.0)); key(c, 60, scale=(1, 1, 0.1 if i == 3 else 1.0)); key(c, 160, scale=(1, 1, 1.0))
        if i < 3: cyl('clid', 0.047, 0.015, (x - 0.0, 0.2, 0.0075), mat('lid%d' % i, [(0.83, 0.0, 0.42), (0.49, 0.71, 0.09), (0.95, 0.95, 0.95)][i], 0.3), verts=48, bevel=0.003)
    spat = box('spatula', (0.02, 0.12, 0.003), (0.19, 0.0, 0.12), M['hdpe'], bevel=0.002, rot=(math.radians(60), 0, 0))
    key(spat, 1, loc=(0.25, -0.05, 0.15)); key(spat, 60, loc=(0.19, 0.06, 0.09)); key(spat, 160, loc=(0.19, 0.06, 0.07)); key(spat, 190, loc=(0.25, -0.05, 0.15))
    cam_dolly((0.2, -0.5, 0.3), (0.08, -0.42, 0.25), (0.0, 0.08, 0.04), (0.0, 0.08, 0.04), lens=42, fstop=2.8)


# ───────────────────────── farming, climate, health ─────────────────────────
def soil_mat():
    for t in ('brown_mud_leaves_01', 'forest_ground_04', 'aerial_rocks_02'):
        if os.path.exists(PH + '/tex/' + t + '/' + t + '_diff_2k.jpg'): return tex_mat('soil', t, 2.0)
    m = mat('soilm', (0.08, 0.045, 0.022), 0.95)
    nt = m.node_tree; b = nt.nodes['Principled BSDF']; n = nt.nodes.new('ShaderNodeTexNoise'); n.inputs['Scale'].default_value = 60
    bm = nt.nodes.new('ShaderNodeBump'); bm.inputs['Strength'].default_value = 0.6; nt.links.new(n.outputs['Fac'], bm.inputs['Height']); nt.links.new(bm.outputs['Normal'], b.inputs['Normal'])
    return m


def sack_mat(name='sackm'):
    m = mat(name, (0.24, 0.17, 0.08), 0.95)
    nt = m.node_tree; b = nt.nodes['Principled BSDF']; w = nt.nodes.new('ShaderNodeTexWave'); w.inputs['Scale'].default_value = 140
    w2 = nt.nodes.new('ShaderNodeTexWave'); w2.wave_type = 'BANDS'; w2.bands_direction = 'Y'; w2.inputs['Scale'].default_value = 140
    mx = nt.nodes.new('ShaderNodeMath'); mx.operation = 'MAXIMUM'; nt.links.new(w.outputs['Fac'], mx.inputs[0]); nt.links.new(w2.outputs['Fac'], mx.inputs[1])
    bm = nt.nodes.new('ShaderNodeBump'); bm.inputs['Strength'].default_value = 0.35; nt.links.new(mx.outputs[0], bm.inputs['Height']); nt.links.new(bm.outputs['Normal'], b.inputs['Normal'])
    return m


def outdoor(hdri='rural_asphalt_road'):
    reset(); world(hdri, 1.0); materials()
    bpy.ops.mesh.primitive_plane_add(size=6, location=(0, 1.0, 0)); g = bpy.context.object; g.data.materials.append(soil_mat())
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 3.5, 1.5), rotation=(math.radians(90), 0, 0)); sky = bpy.context.object; sky.scale = (12, 4, 1)
    sky.data.materials.append(mat('skyw', (0.6, 0.78, 0.95), 0.5, emit=((0.6, 0.78, 0.95), 1.4)))
    area((1.5, -1.0, 2.5), (0, 0.5, 0), 900, 0.6, (1.0, 0.95, 0.85))


def seedling(loc, h=0.06, name='seed'):
    stem = cyl(name + '_stem', 0.0018, h, (loc[0], loc[1], loc[2] + h / 2), mat('stemg', (0.25, 0.55, 0.12), 0.6, sss=0.3), verts=8)
    for s in (-1, 1):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.012, location=(loc[0] + s * 0.012, loc[1], loc[2] + h)); lf = bpy.context.object
        lf.scale = (1.3, 0.6, 0.15); lf.rotation_euler = (0, s * 0.4, 0); lf.data.materials.append(mat('leaf', (0.2, 0.6, 0.12), 0.5, sss=0.4)); lf.parent = stem; lf.location = (s * 0.012, 0, h / 2)
    return stem


@demo('soil_bed')
def soil_bed():
    outdoor()
    random.seed(23)
    for r in range(4):
        bed = box('bed', (1.4, 0.18, 0.06), (0.0, 0.1 + r * 0.32, 0.03), soil_mat(), bevel=0.03)
        for i in range(10):
            s = seedling((-0.6 + i * 0.13 + random.uniform(-0.01, 0.01), 0.1 + r * 0.32, 0.06), h=0.05 + random.uniform(0, 0.03))
            key(s, 1, scale=(0.3, 0.3, 0.3)); key(s, 190, scale=(1.0, 1.0, 1.0))
    ph('watering_can_metal_01', loc=(0.5, -0.25, 0.0), rot_z=math.radians(200))
    camera([(1, (0.6, -0.8, 0.45)), (192, (0.3, -0.7, 0.4))], [(1, (0.0, 0.4, 0.05)), (192, (0.0, 0.4, 0.05))], lens=30, fstop=5, frames=192)


@demo('seedling_tray')
def seedling_tray():
    outdoor()
    for t in range(2):
        tray = box('stray', (0.4, 0.26, 0.05), (-0.22 + t * 0.44, 0.15, 0.025), M['black_plastic'], bevel=0.004)
        for i in range(6):
            for j in range(4):
                s = seedling((-0.4 + t * 0.44 + i * 0.065, 0.06 + j * 0.06, 0.05), h=0.05)
                key(s, 1, scale=(0.5, 0.5, 0.5)); key(s, 190, scale=(1.0, 1.0, 1.0))
    can = ph('watering_can_metal_01', loc=(0.0, -0.1, 0.25), rot_z=math.radians(180))
    if can:
        key(can, 1, loc=(0.3, -0.1, 0.3), rot=(0, 0, math.radians(180))); key(can, 60, loc=(0.0, 0.0, 0.3), rot=(math.radians(25), 0, math.radians(180))); key(can, 170, loc=(-0.25, 0.0, 0.3), rot=(math.radians(25), 0, math.radians(180)))
    for i in range(6):
        s = stream('rain%d' % i, [(-0.05 + i * 0.01, 0.1, 0.27), (-0.05 + i * 0.012, 0.12, 0.15), (-0.05 + i * 0.014, 0.14, 0.06)], 0.0015, M['water']); stream_flow(s, 60, 66, 165, 172)
        key(s, 60, loc=(0, 0, 0)); key(s, 170, loc=(-0.25, 0, 0))
    camera([(1, (0.35, -0.6, 0.45)), (192, (0.15, -0.5, 0.4))], [(1, (0.0, 0.15, 0.05)), (192, (0.0, 0.15, 0.05))], lens=34, fstop=4, frames=192)


@demo('produce_crates')
def produce_crates():
    base(wall=(0.92, 0.9, 0.82))
    tom = mat('tomato', (0.8, 0.08, 0.04), 0.25, sss=0.4, coat=0.5); pep = mat('pepper', (0.85, 0.15, 0.05), 0.3, coat=0.6)
    for c in range(3):
        x = -0.32 + c * 0.32
        ph('plastic_crate_01', loc=(x, 0.15, 0.0), rot_z=math.radians(90), scale=0.9)
        random.seed(24 + c)
        for i in range(40):
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.028 if c != 1 else 0.02, location=(x + random.uniform(-0.12, 0.12), 0.15 + random.uniform(-0.08, 0.08), 0.2 + random.uniform(0, 0.04)))
            o = bpy.context.object; o.data.materials.append([tom, pep, mat('onion', (0.75, 0.45, 0.2), 0.4)][c])
    camera([(1, (-0.35, -0.75, 0.6)), (192, (0.3, -0.7, 0.6))], [(1, (-0.1, 0.15, 0.18)), (192, (0.1, 0.15, 0.18))], lens=32, fstop=4, frames=192)


@demo('grain_sacks')
def grain_sacks():
    base(wall=(0.9, 0.88, 0.8))
    pal = box('pallet', (0.8, 0.45, 0.07), (0.0, 0.35, 0.035), M['wood_light'], bevel=0.003)
    for i in range(3):
        for j in range(2):
            s = box('sack', (0.24, 0.38, 0.11), (-0.26 + i * 0.26, 0.35, 0.13 + j * 0.11), sack_mat(), bevel=0.04)
            d = s.modifiers.new('d', 'DISPLACE'); tx = bpy.data.textures.new('gs%d%d' % (i, j), 'CLOUDS'); tx.noise_scale = 0.08; d.texture = tx; d.strength = 0.015
    pile = flakes_pile((0.0, -0.05), 0.12, 0.05, n=450, seed=25, kind='pearl', zbase=0.002, mat_=mat('maize', (0.95, 0.75, 0.15), 0.5, sss=0.2))
    for o in pile: o.scale = (0.9, 0.7, 0.6)
    camera([(1, (0.35, -0.9, 0.55)), (192, (0.15, -0.8, 0.5))], [(1, (0.0, 0.2, 0.12)), (192, (0.0, 0.2, 0.12))], lens=32, fstop=4.5, frames=192)


@demo('water_tank')
def water_tank():
    outdoor()
    tank = cyl('tank', 0.35, 0.9, (0.2, 0.9, 0.85), mat('tankm', (0.1, 0.1, 0.12), 0.4), verts=64, bevel=0.03)
    stand = box('tstand', (0.8, 0.8, 0.4), (0.2, 0.9, 0.2), M['steel'], bevel=0.01)
    pipe = cyl('pipe', 0.02, 1.2, (-0.4, 0.4, 0.04), mat('pipe', (0.15, 0.15, 0.15), 0.5), rot=(0, math.radians(90), 0.6), verts=16)
    for r in range(3):
        for i in range(8):
            s = seedling((-0.8 + i * 0.12, 0.0 + r * 0.25, 0.0), h=0.08); key(s, 1, scale=(0.7, 0.7, 0.7)); key(s, 190, scale=(1, 1, 1))
    camera([(1, (-0.9, -2.4, 1.1)), (192, (-0.6, -2.1, 1.0))], [(1, (0.0, 0.5, 0.55)), (192, (0.0, 0.5, 0.55))], lens=30, fstop=8, frames=192)


@demo('solar_panel')
def solar_panel():
    outdoor()
    cells = mat('cells', (0.05, 0.1, 0.25), 0.15, coat=1.0, metal=0.3)
    for i in range(2):
        p = box('panel', (0.7, 0.45, 0.03), (-0.4 + i * 0.8, 0.6, 0.55), cells, bevel=0.004, rot=(math.radians(-30), 0, 0))
        for k in range(5): box('grid', (0.7, 0.004, 0.032), (0, 0, 0), M['steel'], bevel=0).parent = p
        box('pole', (0.04, 0.04, 0.5), (-0.4 + i * 0.8, 0.65, 0.25), M['steel'], bevel=0.003)
    camera([(1, (0.6, -1.2, 0.6)), (192, (0.2, -1.0, 0.55))], [(1, (0.0, 0.6, 0.45)), (192, (0.0, 0.6, 0.45))], lens=30, fstop=6, frames=192)


@demo('first_aid_kit')
def first_aid_kit():
    base(wall=(0.92, 0.95, 0.95))
    kit_ = ph('medical_box', loc=(0.0, 0.15, 0.0), scale=0.6)
    for i in range(3): box('bandage', (0.08, 0.05, 0.03), (-0.25 + i * 0.1, -0.05, 0.015), M['paper'], bevel=0.005)
    ph('vintage_flashlight', loc=(0.3, -0.05, 0.0), scale=0.8)
    eb, ec, el, elab = bottle((0.3, 0.15, 0.0), h=0.16, r=0.035, mat_=M['clear'], cap_mat=M['bucket_blue'], liq=M['water'], fill=0.9, name='aidbottle')
    cam_dolly((-0.2, -0.6, 0.4), (0.15, -0.55, 0.38), (0.0, 0.08, 0.08), (0.05, 0.08, 0.08), lens=36, fstop=3.5)


@demo('baby_care')
def baby_care():
    base(wall=(0.96, 0.92, 0.9))
    fb = lathe('feeder', [(0.0, 0.0), (0.03, 0.0), (0.032, 0.12), (0.02, 0.135), (0.008, 0.16)], M['clear'], thick=0.002, loc=(-0.15, 0.1, 0.0))
    liquid('milk', 0.028, 0.03, 0.09, M['cream'], loc=(-0.15, 0.1, 0.0))
    cloth_sheet((0.25, 0.2), (0.12, 0.08, 0.004), mat('babycloth', (0.95, 0.8, 0.85), 0.9))
    ph('modified_thermos', loc=(0.32, 0.18, 0.0), scale=0.7)
    for i in range(3):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.02, location=(-0.32 + i * 0.05, -0.05, 0.02)); bpy.context.object.data.materials.append(mat('fruit%d' % i, [(0.95, 0.75, 0.1), (0.8, 0.1, 0.1), (0.3, 0.6, 0.15)][i], 0.4))
    cam_dolly((-0.2, -0.5, 0.32), (0.1, -0.45, 0.3), (0.0, 0.08, 0.06), (0.0, 0.08, 0.06), lens=40, fstop=3)


@demo('broom_clean')
def broom_clean():
    base(wall=(0.9, 0.92, 0.9))
    floor_tiles = box('floor', (1.4, 1.0, 0.004), (0.0, 0.3, 0.002), mat('tile', (0.85, 0.85, 0.82), 0.3), bevel=0)
    br = ph('wooden_broom', loc=(0.0, 0.2, 0.0)) or ph('plastic_broom', loc=(0.0, 0.2, 0.0))
    if br:
        for f in range(1, 193, 30): key(br, f, loc=(-0.2, 0.2, 0.0), rot=(0, math.radians(-20), 0)); key(br, f + 15, loc=(0.2, 0.15, 0.0), rot=(0, math.radians(20), 0))
    ph('dustpan', loc=(0.4, -0.05, 0.0))
    bucket((-0.4, 0.3, 0.0), r=0.12, h=0.22, mat_=M['bucket_blue'])
    camera([(1, (0.3, -1.0, 0.7)), (192, (0.15, -0.85, 0.65))], [(1, (0.0, 0.25, 0.1)), (192, (0.0, 0.25, 0.1))], lens=30, fstop=5, frames=192)


# ───────────────────────── business places and things ─────────────────────────
@demo('cash_count')
def cash_count():
    base()
    random.seed(26)
    src = cash_notes((-0.12, 0.05, 0.0), n=10)
    for i, o in enumerate(src[::-1]):
        f = 10 + i * 16
        key(o, f, loc=o.location[:]); key(o, f + 10, loc=(0.12 + random.uniform(-0.005, 0.005), 0.05, 0.0009 * i + 0.004))
    coins((0.0, -0.1, 0.0), n=10)
    notebook((0.3, 0.12, 0), rot_z=math.radians(-8)); pen((0.25, -0.05, 0), rot_z=math.radians(30))
    cam_dolly((0.1, -0.45, 0.4), (0.02, -0.38, 0.36), (0.0, 0.03, 0.0), (0.0, 0.03, 0.0), lens=42, fstop=3)


@demo('receipts_records')
def receipts_records():
    base()
    notebook((-0.05, 0.05, 0), rot_z=math.radians(-4))
    random.seed(27)
    for i in range(5):
        r = box('receipt', (0.07, 0.14, 0.0005), (0.25 + random.uniform(-0.03, 0.03), 0.05 + random.uniform(-0.04, 0.04), 0.0005 + i * 0.0006), M['paper'], bevel=0, rot=(0, 0, random.uniform(-0.3, 0.3)))
    pn = pen((0.0, 0.0, 0.015), rot_z=math.radians(30))
    for i, f in enumerate(range(1, 193, 8)): key(pn, f, loc=(-0.1 + (i % 8) * 0.02, -0.05 + (i // 8) * 0.03, 0.016))
    calculator((-0.3, -0.05, 0), rot_z=math.radians(8))
    cam_dolly((0.05, -0.42, 0.45), (0.0, -0.35, 0.42), (0.0, 0.05, 0.0), (0.0, 0.05, 0.0), lens=40, fstop=3.5)


@demo('meeting_table')
def meeting_table():
    base(wall=(0.9, 0.9, 0.88))
    for i in range(4):
        a = i / 4 * math.tau + 0.4
        notebook((0.35 * math.cos(a), 0.5 + 0.3 * math.sin(a), 0.0), rot_z=a)
        mug((0.25 * math.cos(a + 0.4), 0.5 + 0.22 * math.sin(a + 0.4), 0.0))
    laptop((0.0, 0.5, 0.0), 'dashboard', rot_z=math.radians(180))
    camera([(1, (-0.45, -0.05, 0.42)), (192, (0.4, -0.05, 0.42))], [(1, (0.0, 0.45, 0.04)), (192, (0.0, 0.45, 0.04))], lens=32, fstop=3.5, frames=192)


@demo('flipchart')
def flipchart():
    base(wall=(0.92, 0.92, 0.9))
    board = box('flip', (0.6, 0.01, 0.8), (0.0, 0.55, 0.75), mat('flippaper', (0.98, 0.98, 0.97), 0.85), bevel=0.003)
    for i, (h, c) in enumerate([(0.2, M['magenta']), (0.32, M['lemon']), (0.45, M['bucket_blue']), (0.38, M['magenta'])]):
        b = box('barc', (0.08, 0.004, h), (-0.18 + i * 0.12, 0.543, 0.45 + h / 2), c, bevel=0)
        key(b, 1, scale=(1, 1, 0.01), loc=(-0.18 + i * 0.12, 0.543, 0.45)); key(b, 40 + i * 30, scale=(1, 1, 0.01), loc=(-0.18 + i * 0.12, 0.543, 0.45)); key(b, 70 + i * 30, scale=(1, 1, 1), loc=(-0.18 + i * 0.12, 0.543, 0.45 + h / 2))
    for s in (-1, 1): cyl('easel', 0.012, 1.3, (s * 0.25, 0.6, 0.6), M['wood_light'], rot=(0, s * 0.15, 0), verts=12)
    camera([(1, (0.3, -0.9, 0.8)), (192, (0.1, -0.75, 0.78))], [(1, (0.0, 0.55, 0.7)), (192, (0.0, 0.55, 0.7))], lens=34, fstop=4, frames=192)


@demo('kanban_board')
def kanban_board():
    base(wall=(0.95, 0.95, 0.93))
    wb = box('whiteboard', (1.0, 0.02, 0.6), (0.0, 1.07, 0.75), mat('wbm', (0.98, 0.98, 0.98), 0.15), bevel=0.004)
    for c in range(3): box('col', (0.004, 0.004, 0.5), (-0.17 + c * 0.34, 1.055, 0.75), M['black_plastic'], bevel=0) if c else None
    random.seed(28)
    notes = []
    for i in range(9):
        col = i % 3; row = i // 3
        n = box('sticky', (0.1, 0.004, 0.08), (-0.33 + col * 0.33, 1.055, 0.92 - row * 0.12), mat('st%d' % (i % 4), [(0.98, 0.9, 0.3), (0.95, 0.6, 0.75), (0.6, 0.85, 0.95), (0.7, 0.9, 0.5)][i % 4], 0.8), bevel=0.001)
        notes.append(n)
    mv = notes[0]; key(mv, 1, loc=mv.location[:]); key(mv, 80, loc=mv.location[:]); key(mv, 130, loc=(0.0, 1.055, 0.56)); key(mv, 170, loc=(0.0, 1.055, 0.56))
    mv2 = notes[4]; key(mv2, 1, loc=mv2.location[:]); key(mv2, 120, loc=mv2.location[:]); key(mv2, 170, loc=(0.33, 1.055, 0.56)); ease_all(mv); ease_all(mv2)
    camera([(1, (0.2, -0.3, 0.8)), (192, (0.05, -0.15, 0.78))], [(1, (0.0, 1.05, 0.75)), (192, (0.0, 1.05, 0.75))], lens=32, fstop=5, frames=192)


@demo('shop_shelf')
def shop_shelf():
    base(wall=(0.95, 0.9, 0.82))
    shelf((0.0, 0.95, 0.25), width=1.3, levels=(0.0, 0.35, 0.7), depth=0.28)
    random.seed(29)
    for lv, z in enumerate((0.2625, 0.6125, 0.9625)):
        x = -0.55
        while x < 0.55:
            k = random.random()
            if k < 0.4:
                box('carton', (0.09, 0.07, 0.13), (x, 0.95, z + 0.065), mat('ct%d' % int(x * 100), random.choice([(0.83, 0.0, 0.42), (0.49, 0.71, 0.09), (0.2, 0.4, 0.8), (0.95, 0.75, 0.1)]), 0.6), bevel=0.003); x += 0.1
            elif k < 0.75:
                bottle((x, 0.95, z), h=0.18, r=0.03, mat_=M['hdpe'], cap_mat=random.choice([M['magenta'], M['lemon'], M['bucket_blue']]), name='sb%d' % int(x * 1000)); x += 0.08
            else:
                cyl('tin', 0.035, 0.1, (x, 0.95, z + 0.05), M['steel'], verts=32); x += 0.08
        for t in range(4): box('tag', (0.05, 0.002, 0.025), (-0.45 + t * 0.3, 0.808, z - 0.005), M['label'], bevel=0)
    camera([(1, (-0.4, -0.5, 0.75)), (192, (0.3, -0.45, 0.7))], [(1, (-0.1, 0.95, 0.6)), (192, (0.1, 0.95, 0.6))], lens=30, fstop=4, frames=192)


@demo('delivery_boxes')
def delivery_boxes():
    base(wall=(0.9, 0.88, 0.85))
    def top(o):
        bpy.context.view_layer.update()
        return max((m.matrix_world @ V(c)).z for m in o.children_recursive if m.type == 'MESH' for c in m.bound_box)
    for i in range(3):
        z = 0.0
        for j in range(2 - (i == 2)):
            o = ph('cardboard_box_01', loc=(-0.32 + i * 0.32, 0.32, z), rot_z=math.radians(random.uniform(-6, 6)), size=0.3)
            if not o: o = box('carton', (0.28, 0.22, 0.18), (-0.32 + i * 0.32, 0.32, z + 0.09), mat('cardb', (0.55, 0.38, 0.2), 0.8), bevel=0.004)
            z = top(o) if o.type == 'EMPTY' else z + 0.18
    b = ph('cardboard_box_01', loc=(0.6, -0.1, 0.0), size=0.24) or box('parcel', (0.24, 0.18, 0.12), (0.6, -0.1, 0.06), mat('cardb', (0.55, 0.38, 0.2), 0.8), bevel=0.004)
    z0 = b.location.z
    key(b, 1, loc=(0.6, -0.12, z0)); key(b, 70, loc=(0.3, -0.06, z0)); ease_all(b)
    bpy.context.view_layer.update()
    lab = box('parcellab', (0.1, 0.07, 0.0008), (0, 0, 0), img_mat('pcl', ASSETS + '/label_magenta.png', 0.6), bevel=0)
    lab.parent = b; lab.location = (0, 0, (top(b) - z0) / max(b.scale[2], 1e-6) + 0.0005) if b.type == 'EMPTY' else (0, 0, 0.0605)
    camera([(1, (0.4, -0.85, 0.5)), (192, (0.2, -0.75, 0.47))], [(1, (0.0, 0.2, 0.15)), (192, (0.0, 0.2, 0.15))], lens=32, fstop=4, frames=192)


@demo('documents_stamp')
def documents_stamp():
    base()
    for i in range(3): box('doc', (0.21, 0.297, 0.0005), (-0.05 + i * 0.01, 0.05 + i * 0.005, 0.0005 + i * 0.0006), M['paper'], bevel=0, rot=(0, 0, 0.05 * i))
    page = decal('docpage', ASSETS + '/notebook_page.png', (0.2, 0.28), (-0.03, 0.06, 0.0025), (0, 0, 0.1), alpha=False)
    stamp = cyl('stamp_base', 0.03, 0.025, (0.0, 0.0, 0.2), M['black_plastic'], verts=32); h = cyl('stamp_handle', 0.012, 0.06, (0, 0, 0.04), M['wood_light'], verts=16); h.parent = stamp
    mark = cyl('stampmark', 0.028, 0.0004, (-0.02, 0.0, 0.0028), mat('ink', (0.1, 0.2, 0.7), 0.8, alpha=0.85), verts=32)
    key(stamp, 1, loc=(0.2, -0.05, 0.25)); key(stamp, 70, loc=(-0.02, 0.0, 0.15)); key(stamp, 90, loc=(-0.02, 0.0, 0.016)); key(stamp, 110, loc=(-0.02, 0.0, 0.15)); ease_all(stamp)
    visible(mark, 1, False); visible(mark, 90, True)
    ph('clipboard', loc=(0.32, 0.1, 0.0), rot_z=math.radians(-15))
    cam_dolly((0.1, -0.45, 0.45), (0.03, -0.38, 0.42), (0.0, 0.03, 0.02), (0.0, 0.03, 0.02), lens=40, fstop=3.5)


@demo('calendar_clock')
def calendar_clock():
    base(wall=(0.93, 0.92, 0.9))
    cal = box('calendar', (0.3, 0.01, 0.36), (0.0, 1.07, 0.75), M['paper'], bevel=0.002)
    grid = uv_plane('calgrid', (0.28, 0.3), (0.0, 1.063, 0.73), (math.radians(90), 0, 0), screen_mat('calendar_phone'))
    grid.rotation_euler = (math.radians(90), 0, math.radians(180))
    ph('alarm_clock_01', loc=(0.25, 0.05, 0.0), rot_z=math.radians(-20))
    notebook((-0.2, 0.0, 0), rot_z=math.radians(10))
    camera([(1, (0.25, -0.5, 0.45)), (192, (0.1, -0.4, 0.5))], [(1, (0.1, 0.4, 0.3)), (192, (0.0, 0.8, 0.6))], lens=34, fstop=4, frames=192)


@demo('savings_box')
def savings_box():
    base()
    tin = cyl('savebox', 0.07, 0.14, (0.0, 0.08, 0.07), mat('tinm', (0.83, 0.0, 0.42), 0.3, metal=0.6), verts=48, bevel=0.004)
    slot = box('slot', (0.05, 0.006, 0.002), (0.0, 0.08, 0.141), M['black_plastic'], bevel=0)
    gold = mat('coin', (0.85, 0.65, 0.3), 0.3, metal=1.0)
    for i in range(6):
        c = cyl('coinf', 0.012, 0.002, (0.0, 0.08, 0.3), gold, rot=(math.radians(90), 0, 0), verts=24)
        f = 10 + i * 28; key(c, 1, loc=(0.0, 0.08, 0.3)); key(c, f, loc=(0.0, 0.08, 0.3)); key(c, f + 12, loc=(0.0, 0.08, 0.13)); visible(c, f + 13, False)
    cash_notes((0.25, 0.0, 0.0), n=4); coins((-0.22, 0.0, 0.0), n=6)
    cam_dolly((0.15, -0.45, 0.32), (0.05, -0.38, 0.28), (0.0, 0.06, 0.08), (0.0, 0.06, 0.08), lens=42, fstop=2.8)


@demo('pos_terminal')
def pos_terminal():
    base()
    body = box('pos', (0.08, 0.17, 0.035), (0.0, 0.08, 0.0175), M['black_plastic'], bevel=0.01, rot=(math.radians(8), 0, 0))
    sc = uv_plane('posscreen', (0.065, 0.075), (0.0, 0.12, 0.037), (math.radians(8), 0, 0), screen_mat('pos_phone'))
    for i in range(4):
        for j in range(3): box('k', (0.018, 0.012, 0.004), (-0.022 + j * 0.022, 0.06 - i * 0.017, 0.036), M['hdpe'], bevel=0.002)
    card = box('card', (0.085, 0.054, 0.001), (0.2, 0.0, 0.0005), mat('cardm', (0.2, 0.4, 0.8), 0.3, coat=0.8), bevel=0.003)
    key(card, 1, loc=(0.25, -0.05, 0.0005)); key(card, 80, loc=(0.0, 0.18, 0.06), rot=(math.radians(60), 0, 0)); key(card, 150, loc=(0.0, 0.18, 0.06), rot=(math.radians(60), 0, 0)); ease_all(card)
    phone((-0.25, 0.05, 0.004), 'payment_phone', rot=(0, 0, math.radians(15)))
    cam_dolly((0.15, -0.4, 0.35), (0.05, -0.32, 0.3), (0.0, 0.08, 0.03), (0.0, 0.08, 0.03), lens=42, fstop=2.8)


@demo('security_lock')
def security_lock():
    base(wall=(0.88, 0.9, 0.93))
    lock = box('lockbody', (0.09, 0.03, 0.08), (0.12, 0.08, 0.04), mat('brass', (0.8, 0.6, 0.25), 0.3, metal=1.0), bevel=0.01)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.03, minor_radius=0.007, location=(0.12, 0.08, 0.09), rotation=(math.radians(90), 0, 0)); sh = bpy.context.object; sh.data.materials.append(M['steel'])
    key(sh, 1, loc=(0.12, 0.08, 0.11)); key(sh, 90, loc=(0.12, 0.08, 0.11)); key(sh, 120, loc=(0.12, 0.08, 0.09)); ease_all(sh)
    phone((-0.1, 0.05, 0.004), 'security_phone', rot=(0, 0, math.radians(-10)))
    cam_dolly((0.15, -0.42, 0.3), (0.05, -0.35, 0.26), (0.0, 0.07, 0.04), (0.0, 0.07, 0.04), lens=42, fstop=2.8)


@demo('globe_export')
def globe_export():
    base(wall=(0.9, 0.9, 0.9))
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.12, location=(0.0, 0.15, 0.2), segments=64, ring_count=32); g = bpy.context.object
    g.data.materials.append(mat('globe', (0.2, 0.45, 0.75), 0.3, coat=0.8))
    d = g.modifiers.new('d', 'DISPLACE'); tx = bpy.data.textures.new('gl', 'CLOUDS'); tx.noise_scale = 0.3; d.texture = tx; d.strength = 0.004
    stand = cyl('gstand', 0.06, 0.08, (0.0, 0.15, 0.04), M['wood_light'], verts=32)
    key(g, 1, rot=(0, 0, 0)); key(g, 192, rot=(0, 0, math.radians(120)))
    for i in range(3): box('carton', (0.18, 0.14, 0.12), (-0.35 + (i % 2) * 0.05, -0.05 + i * 0.0, 0.06 + i * 0.12), M['paper_brown'], bevel=0.004) if i < 2 else None
    cam_dolly((0.25, -0.65, 0.35), (0.1, -0.55, 0.32), (0.0, 0.12, 0.15), (0.0, 0.12, 0.15), lens=38, fstop=3.5)


@demo('workshop_floor')
def workshop_floor():
    base(wall=(0.88, 0.88, 0.85))
    for i in range(3):
        tb = box('worktable', (0.6, 0.35, 0.02), (-0.7 + i * 0.7, 0.6, 0.75), M['wood_light'], bevel=0.003)
        for sx in (-1, 1):
            for sy in (-1, 1): box('leg', (0.03, 0.03, 0.75), (-0.7 + i * 0.7 + sx * 0.27, 0.6 + sy * 0.15, 0.375), M['steel'], bevel=0.002)
        bucket((-0.8 + i * 0.7, 0.6, 0.76), r=0.08, h=0.15, mat_=[M['bucket_blue'], M['bucket_white'], M['bucket_blue']][i])
        for k in range(3): bottle((-0.6 + i * 0.7 + k * 0.06, 0.6, 0.76), h=0.15, r=0.025, mat_=M['hdpe'], cap_mat=M['magenta'], name='wb%d%d' % (i, k))
    shelf((0.0, 1.0, 0.0), width=1.6, levels=(1.1,), depth=0.25)
    camera([(1, (-0.8, -1.4, 1.3)), (192, (0.6, -1.3, 1.25))], [(1, (-0.2, 0.6, 0.7)), (192, (0.2, 0.6, 0.7))], lens=26, fstop=6, frames=192)


@demo('quality_check')
def quality_check():
    base()
    for i in range(5): bottle((-0.25 + i * 0.1, 0.12, 0.0), h=0.18, r=0.03, mat_=M['clear'], cap_mat=M['magenta'], liq=M['liquid_soap'], fill=0.9, name='qc%d' % i)
    cb = ph('clipboard', loc=(0.0, -0.08, 0.0), rot_z=math.radians(5))
    mg = ph('magnifying_glass_01', loc=(0.25, -0.05, 0.08))
    if mg:
        key(mg, 1, loc=(0.3, -0.1, 0.12)); key(mg, 192, loc=(-0.15, 0.02, 0.12))
    cam_dolly((0.2, -0.5, 0.38), (0.05, -0.42, 0.33), (0.0, 0.05, 0.06), (0.0, 0.05, 0.06), lens=40, fstop=3.2)


@demo('presentation_screen')
def presentation_screen():
    base(wall=(0.9, 0.9, 0.9))
    scr = uv_plane('projscreen', (1.0, 0.62), (0.0, 1.07, 0.9), (math.radians(90), 0, 0), screen_mat('dashboard'))
    scr.rotation_euler = (math.radians(90), 0, math.radians(180))
    for i in range(3):
        for j in range(2):
            box('chairseat', (0.3, 0.3, 0.03), (-0.5 + i * 0.5, -0.1 - j * 0.45, 0.43), M['bucket_blue'], bevel=0.01)
            box('chairback', (0.3, 0.03, 0.3), (-0.5 + i * 0.5, 0.03 - j * 0.45, 0.6), M['bucket_blue'], bevel=0.01)
    camera([(1, (0.3, -1.5, 0.95)), (192, (0.1, -1.3, 0.9))], [(1, (0.0, 1.0, 0.8)), (192, (0.0, 1.0, 0.85))], lens=30, fstop=6, frames=192)


@demo('phone_camera')
def phone_camera():
    base(wall=(0.95, 0.92, 0.9))
    backdrop = box('backdrop', (0.7, 0.01, 0.45), (0.0, 0.48, 0.225), mat('bd', (0.98, 0.95, 0.93), 0.9), bevel=0)
    prods = [soap_bar((-0.12 + i * 0.12, 0.3, 0.0), mat_=[M['soap_bar'], M['soap_green'], M['soap_blue']][i]) for i in range(3)]
    for i in range(2): bottle((-0.2 + i * 0.4, 0.38, 0.0), h=0.2, r=0.035, mat_=M['hdpe'], cap_mat=[M['magenta'], M['lemon']][i], name='pb%d' % i)
    for a in (0, 120, 240):
        r = math.radians(a)
        cyl('tripod', 0.0022, 0.2, (0.06 * math.sin(r), 0.0 + 0.06 * math.cos(r), 0.095), M['black_plastic'], rot=(-0.3 * math.cos(r), 0.3 * math.sin(r), 0), verts=8)
    cyl('tripodhead', 0.012, 0.03, (0.0, 0.0, 0.2), M['black_plastic'], verts=16)
    phone((0.0, 0.0, 0.29), 'social_phone', rot=(math.radians(-4), 0, 0))
    area((0.5, -0.1, 0.6), (0.0, 0.3, 0.1), 50, 0.7, (1, 0.97, 0.92))
    cam_dolly((0.3, -0.62, 0.42), (0.22, -0.52, 0.4), (0.0, 0.12, 0.2), (0.0, 0.14, 0.2), lens=36, fstop=3.2)


@demo('microphone_record')
def microphone_record():
    base(wall=(0.9, 0.88, 0.9))
    stand = cyl('micbase', 0.05, 0.01, (0.0, 0.1, 0.005), M['black_plastic'], verts=32)
    pole = cyl('micpole', 0.005, 0.18, (0.0, 0.1, 0.1), M['steel'], verts=12)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.03, location=(0.0, 0.1, 0.21)); m = bpy.context.object; m.scale = (1, 1, 1.4); m.data.materials.append(mat('grille', (0.2, 0.2, 0.22), 0.5, metal=0.7))
    phone((0.2, 0.0, 0.004), 'chat_phone', rot=(0, 0, math.radians(-15)))
    for i in range(10):
        b = box('wave', (0.008, 0.004, 0.02), (-0.25 + i * 0.012, -0.05, 0.03), M['magenta'], bevel=0)
        for f in range(1, 193, 6): key(b, f, scale=(1, 1, 0.3 + random.random() * 2.2))
    cam_dolly((0.15, -0.45, 0.3), (0.05, -0.38, 0.27), (0.0, 0.08, 0.1), (0.0, 0.08, 0.1), lens=42, fstop=2.8)
