"""WODDI demo kit: builds realistic workshop scenes in Blender (Cycles) for the v2 teaching videos.
Everything is procedural or from Poly Haven (CC0). No people; objects move as if handled.
Units: metres. The table top is z = 0, camera looks towards +y."""
import bpy, bmesh, math, random, os, mathutils
from mathutils import Vector, Euler

ASSETS = os.environ.get('WODDI_ASSETS', '/home/claude/vid2/assets')
PH = ASSETS + '/ph'
FPS = 24
V = Vector


# ───────────────────────── scene ─────────────────────────
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.samples = int(os.environ.get('WODDI_SAMPLES', '10'))
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.03
    sc.cycles.use_denoising = True
    sc.cycles.denoiser = 'OPENIMAGEDENOISE'
    sc.cycles.max_bounces = 8
    sc.cycles.transmission_bounces = 8
    sc.cycles.glossy_bounces = 2
    sc.cycles.diffuse_bounces = 1
    sc.render.use_persistent_data = True
    sc.cycles.use_light_tree = True
    sc.cycles.volume_bounces = 1
    sc.cycles.transparent_max_bounces = 32
    sc.cycles.caustics_reflective = False
    sc.cycles.caustics_refractive = False
    sc.cycles.blur_glossy = 1.0
    sc.render.resolution_x = int(os.environ.get('WODDI_W', '640'))
    sc.render.resolution_y = int(os.environ.get('WODDI_H', '360'))
    sc.render.fps = FPS
    sc.render.film_transparent = False
    sc.view_settings.view_transform = 'AgX'
    sc.view_settings.look = 'AgX - Medium High Contrast'
    sc.render.use_motion_blur = True
    sc.render.motion_blur_shutter = 0.4
    sc.frame_start = 1
    return sc


def world(hdri='brown_photostudio_02', strength=0.9, rot=0.0):
    sc = bpy.context.scene
    w = bpy.data.worlds.new('world'); sc.world = w; w.use_nodes = True
    nt = w.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputWorld'); bg = nt.nodes.new('ShaderNodeBackground')
    env = nt.nodes.new('ShaderNodeTexEnvironment')
    env.image = bpy.data.images.load(PH + '/hdri/' + hdri + '.hdr')
    mp = nt.nodes.new('ShaderNodeMapping'); tc = nt.nodes.new('ShaderNodeTexCoord')
    mp.inputs['Rotation'].default_value[2] = rot
    nt.links.new(tc.outputs['Generated'], mp.inputs['Vector']); nt.links.new(mp.outputs[0], env.inputs[0])
    nt.links.new(env.outputs[0], bg.inputs[0]); bg.inputs[1].default_value = strength
    nt.links.new(bg.outputs[0], out.inputs[0])


def tex_mat(name, folder, scale=1.0, tint=None, rough_mul=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (scale, scale, scale)
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
    base = PH + '/tex/' + folder + '/' + folder + '_'
    def img(suffix, non_color=False):
        n = nt.nodes.new('ShaderNodeTexImage'); n.image = bpy.data.images.load(base + suffix)
        if non_color: n.image.colorspace_settings.name = 'Non-Color'
        n.projection = 'BOX'; n.projection_blend = 0.2
        nt.links.new(mp.outputs[0], n.inputs[0]); return n
    d = img('diff_2k.jpg')
    if tint:
        mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'
        mix.inputs['Factor'].default_value = 1.0
        nt.links.new(d.outputs[0], mix.inputs[6]); mix.inputs[7].default_value = (*tint, 1)
        nt.links.new(mix.outputs[2], b.inputs['Base Color'])
    else:
        nt.links.new(d.outputs[0], b.inputs['Base Color'])
    r = img('rough_2k.jpg', True)
    if rough_mul != 1.0:
        mt = nt.nodes.new('ShaderNodeMath'); mt.operation = 'MULTIPLY'; mt.inputs[1].default_value = rough_mul
        nt.links.new(r.outputs[0], mt.inputs[0]); nt.links.new(mt.outputs[0], b.inputs['Roughness'])
    else:
        nt.links.new(r.outputs[0], b.inputs['Roughness'])
    n = img('nor_gl_2k.jpg', True); nm = nt.nodes.new('ShaderNodeNormalMap'); nm.inputs['Strength'].default_value = 0.6
    nt.links.new(n.outputs[0], nm.inputs['Color']); nt.links.new(nm.outputs[0], b.inputs['Normal'])
    return m


def room(table='wood_table_001', wall_color=(0.93, 0.86, 0.78), table_size=(3.0, 2.0), wall_y=1.1, window=True):
    """Workshop table + plastered wall behind + soft window light."""
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0.3, 0))
    t = bpy.context.object; t.name = 'table'; t.scale = (table_size[0], table_size[1], 1)
    bpy.ops.object.transform_apply(scale=True)
    t.data.materials.append(tex_mat('table', table, 1.2))
    # front edge thickness so the table reads as a table
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0.3 - table_size[1] / 2 - 0.0, -0.025))
    e = bpy.context.object; e.scale = (table_size[0], 0.02, 0.05); e.data.materials.append(t.data.materials[0])
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, wall_y, 1.0), rotation=(math.radians(90), 0, 0))
    w = bpy.context.object; w.name = 'wall'; w.scale = (6, 2.4, 1)
    w.data.materials.append(tex_mat('wall', 'plastered_wall', 0.8, tint=wall_color, rough_mul=1.0))
    # key light from a "window" on the left, soft fill on the right
    area(( -1.6, -0.2, 1.4), (0, 0.2, 0.1), 380, 1.6, (1.0, 0.95, 0.88))
    area((1.4, -1.2, 1.2), (0, 0.2, 0.1), 90, 2.0, (0.9, 0.93, 1.0))
    area((0.0, 0.6, 2.2), (0, 0.2, 0), 60, 2.5, (1, 1, 1))
    if window:   # warm patch of light on the wall
        area((-1.2, 0.9, 1.6), (0.6, 1.1, 0.4), 120, 0.8, (1.0, 0.9, 0.75), spot=True)


def area(loc, target, energy, size, color=(1, 1, 1), spot=False):
    if spot:
        bpy.ops.object.light_add(type='SPOT', location=loc); L = bpy.context.object
        L.data.energy = energy * 3; L.data.spot_size = math.radians(55); L.data.spot_blend = 1.0; L.data.shadow_soft_size = size
    else:
        bpy.ops.object.light_add(type='AREA', location=loc); L = bpy.context.object
        L.data.energy = energy; L.data.size = size
    L.data.color = color
    d = V(target) - V(loc); L.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    return L


# ───────────────────────── materials ─────────────────────────
def mat(name, col=(0.8, 0.8, 0.8), rough=0.5, trans=0.0, ior=1.45, metal=0.0, sss=0.0, coat=0.0, alpha=1.0, emit=None, spec=0.5):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*col, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Transmission Weight'].default_value = trans
    b.inputs['IOR'].default_value = ior
    b.inputs['Metallic'].default_value = metal
    b.inputs['Coat Weight'].default_value = coat
    b.inputs['Specular IOR Level'].default_value = spec
    if sss:
        b.inputs['Subsurface Weight'].default_value = sss
        b.inputs['Subsurface Radius'].default_value = (0.02, 0.015, 0.01)
        b.inputs['Subsurface Scale'].default_value = 0.05
    if alpha < 1:
        b.inputs['Alpha'].default_value = alpha
    if emit:
        b.inputs['Emission Color'].default_value = (*emit[0], 1); b.inputs['Emission Strength'].default_value = emit[1]
    return m


M = {}
def materials():
    M['clear'] = thin_mat('clear_plastic', (0.97, 0.98, 1.0), 0.05, 0.0, 0.12)
    M['frosted'] = thin_mat('frosted_plastic', (0.95, 0.96, 0.97), 0.25, 0.55, 0.2)
    M['hdpe'] = mat('hdpe_white', (0.88, 0.88, 0.86), 0.42, 0.0, 1.5, sss=0.15)
    M['steel'] = mat('steel', (0.78, 0.78, 0.80), 0.18, 0, 1.45, 1.0)
    M['enamel'] = mat('enamel', (0.9, 0.9, 0.88), 0.12, coat=0.6)
    M['water'] = mat('water', (0.95, 0.98, 1.0), 0.0, 1.0, 1.333)
    M['lye_sol'] = mat('lye_solution', (0.97, 0.98, 0.98), 0.02, 1.0, 1.36)
    M['flake'] = mat('caustic_flake', (0.97, 0.97, 0.96), 0.14, 0.35, 1.5, sss=0.25, coat=0.4)
    M['palm'] = mat('palm_oil', (0.9, 0.25, 0.02), 0.12, 0.0, 1.47, sss=0.8, coat=0.6)
    M['pko'] = mat('pko', (0.98, 0.88, 0.55), 0.1, 0.0, 1.47, sss=0.8, coat=0.6)
    M['coco'] = mat('coconut_solid', (0.97, 0.97, 0.94), 0.35, 0.0, 1.47, sss=0.8)
    M['shea'] = mat('shea', (0.93, 0.87, 0.70), 0.5, 0, 1.47, sss=0.5)
    M['batter'] = mat('soap_batter', (0.95, 0.88, 0.70), 0.45, 0, 1.45, sss=0.5)
    M['batter_thin'] = mat('soap_batter_thin', (0.97, 0.80, 0.42), 0.15, 0.35, 1.46, sss=0.3)
    M['soap_bar'] = mat('soap_bar', (0.95, 0.91, 0.80), 0.55, 0, 1.45, sss=0.5)
    M['soap_blue'] = mat('laundry_blue', (0.22, 0.45, 0.85), 0.45, 0, 1.45, sss=0.3)
    M['soap_green'] = mat('soap_green', (0.45, 0.72, 0.25), 0.45, 0, 1.45, sss=0.3)
    M['liquid_soap'] = mat('liquid_soap', (0.95, 0.6, 0.12), 0.08, 0.0, 1.4, sss=0.9, coat=0.7)
    M['dish_green'] = mat('dish_green', (0.2, 0.75, 0.28), 0.08, 0.0, 1.4, sss=0.9, coat=0.7)
    M['softener'] = mat('softener', (0.75, 0.85, 1.0), 0.2, 0.0, 1.4, sss=0.8)
    M['cream'] = mat('conditioner', (0.98, 0.97, 0.95), 0.35, 0, 1.4, sss=0.7)
    M['glove'] = mat('rubber_glove', (0.95, 0.75, 0.05), 0.28, coat=0.2, sss=0.1)
    M['rubber_black'] = mat('rubber_black', (0.03, 0.03, 0.03), 0.5)
    M['lens'] = thin_mat('goggle_lens', (0.85, 0.93, 1.0), 0.04, 0.0, 0.2)
    M['apron'] = mat('apron', (0.08, 0.18, 0.42), 0.8)
    M['wood_light'] = mat('wood_light', (0.62, 0.45, 0.28), 0.55)
    M['paper'] = mat('paper', (0.93, 0.90, 0.84), 0.85, sss=0.1)
    M['paper_brown'] = mat('kraft', (0.62, 0.46, 0.30), 0.8)
    M['label'] = mat('label', (0.98, 0.98, 0.96), 0.6)
    M['black_plastic'] = mat('black_plastic', (0.02, 0.02, 0.02), 0.35)
    M['lcd'] = mat('lcd', (0.12, 0.16, 0.12), 0.2, emit=((0.35, 0.65, 0.4), 0.6))
    M['lcd_text'] = mat('lcd_text', (0.02, 0.02, 0.02), 0.5)
    M['steam'] = steam_mat()
    M['silicone'] = mat('silicone', (0.85, 0.25, 0.35), 0.4, sss=0.3)
    M['bucket_blue'] = mat('bucket_blue', (0.08, 0.32, 0.72), 0.35, sss=0.1)
    M['bucket_white'] = mat('bucket_white', (0.9, 0.9, 0.88), 0.35, sss=0.2)
    M['red'] = mat('red_plastic', (0.75, 0.06, 0.05), 0.35)
    M['amber_glass'] = thin_mat('amber_glass', (0.55, 0.28, 0.06), 0.04, 0.0, 0.15)
    M['thermo'] = thin_mat('thermometer_glass', (0.97, 0.97, 1.0), 0.03, 0.0, 0.15)
    M['thermo_red'] = mat('thermo_red', (0.8, 0.05, 0.05), 0.3)
    M['strip'] = mat('ph_strip', (0.95, 0.85, 0.2), 0.7)
    M['magenta'] = mat('magenta', (0.83, 0.0, 0.42), 0.4)
    M['lemon'] = mat('lemon', (0.49, 0.71, 0.09), 0.4)
    M['foam'] = mat('foam', (0.98, 0.98, 0.98), 0.7, sss=0.5)
    return M


def thin_mat(name, tint=(1, 1, 1), rough=0.04, frost=0.0, edge=0.08):
    """Thin-walled clear plastic/glass: see-through without refraction darkening, glossy at grazing angles."""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); tr.inputs[0].default_value = (*tint, 1)
    gl = nt.nodes.new('ShaderNodeBsdfGlossy'); gl.inputs['Roughness'].default_value = rough
    lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = edge
    mx = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(lw.outputs['Fresnel'], mx.inputs[0]); nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(gl.outputs[0], mx.inputs[2])
    if frost:
        df = nt.nodes.new('ShaderNodeBsdfTranslucent'); df.inputs[0].default_value = (0.95, 0.96, 0.97, 1)
        mx2 = nt.nodes.new('ShaderNodeMixShader'); mx2.inputs[0].default_value = frost
        nt.links.new(mx.outputs[0], mx2.inputs[1]); nt.links.new(df.outputs[0], mx2.inputs[2]); nt.links.new(mx2.outputs[0], out.inputs[0])
    else:
        nt.links.new(mx.outputs[0], out.inputs[0])
    return m


def steam_mat():
    m = bpy.data.materials.new('steam'); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial'); vol = nt.nodes.new('ShaderNodeVolumePrincipled')
    vol.inputs['Color'].default_value = (1, 1, 1, 1)
    noise = nt.nodes.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value = 9; noise.inputs['Detail'].default_value = 3
    noise.noise_dimensions = '4D'
    tc = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping')
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector']); nt.links.new(mp.outputs[0], noise.inputs['Vector'])
    # fade towards the top and sides of the box (object coords -1..1)
    sep = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Object'], sep.inputs[0])
    gz = nt.nodes.new('ShaderNodeMapRange'); gz.inputs['From Min'].default_value = -0.5; gz.inputs['From Max'].default_value = 0.5
    gz.inputs['To Min'].default_value = 1; gz.inputs['To Max'].default_value = 0
    nt.links.new(sep.outputs[2], gz.inputs[0])
    ramp = nt.nodes.new('ShaderNodeValToRGB'); ramp.color_ramp.elements[0].position = 0.5; ramp.color_ramp.elements[1].position = 0.75
    nt.links.new(noise.outputs['Fac'], ramp.inputs[0])
    # radial falloff (soft column instead of a box)
    cxy = nt.nodes.new('ShaderNodeCombineXYZ'); nt.links.new(sep.outputs[0], cxy.inputs[0]); nt.links.new(sep.outputs[1], cxy.inputs[1])
    ln = nt.nodes.new('ShaderNodeVectorMath'); ln.operation = 'LENGTH'; nt.links.new(cxy.outputs[0], ln.inputs[0])
    gr = nt.nodes.new('ShaderNodeMapRange'); gr.inputs['From Min'].default_value = 0.08; gr.inputs['From Max'].default_value = 0.48
    gr.inputs['To Min'].default_value = 1; gr.inputs['To Max'].default_value = 0
    nt.links.new(ln.outputs['Value'], gr.inputs[0])
    gzr = nt.nodes.new('ShaderNodeMath'); gzr.operation = 'MULTIPLY'; nt.links.new(gz.outputs[0], gzr.inputs[0]); nt.links.new(gr.outputs[0], gzr.inputs[1])
    # also fade at the very bottom so it rises out of the liquid
    gb = nt.nodes.new('ShaderNodeMapRange'); gb.inputs['From Min'].default_value = -0.5; gb.inputs['From Max'].default_value = -0.38
    nt.links.new(sep.outputs[2], gb.inputs[0])
    g2 = nt.nodes.new('ShaderNodeMath'); g2.operation = 'MULTIPLY'; nt.links.new(gzr.outputs[0], g2.inputs[0]); nt.links.new(gb.outputs[0], g2.inputs[1])
    mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'
    nt.links.new(ramp.outputs[0], mul.inputs[0]); nt.links.new(g2.outputs[0], mul.inputs[1])
    dens = nt.nodes.new('ShaderNodeMath'); dens.operation = 'MULTIPLY'; dens.name = 'density'; dens.inputs[1].default_value = 0.0
    nt.links.new(mul.outputs[0], dens.inputs[0]); nt.links.new(dens.outputs[0], vol.inputs['Density'])
    nt.links.new(vol.outputs[0], out.inputs['Volume'])
    m['noise'] = noise.name; m['mapping'] = mp.name
    return m


# ───────────────────────── geometry helpers ─────────────────────────
def obj_from_bm(name, bm, mat_=None, smooth=True):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o)
    if smooth:
        for p in me.polygons: p.use_smooth = True
    if mat_: me.materials.append(mat_)
    return o


def lathe(name, prof, mat_=None, seg=72, thick=0.0, cap_top=False, loc=(0, 0, 0)):
    """Spin a (radius, z) profile around Z. thick > 0 gives a container wall."""
    bm = bmesh.new()
    vs = [bm.verts.new((r, 0, z)) for r, z in prof]
    for a, b in zip(vs, vs[1:]): bm.edges.new((a, b))
    if cap_top:
        c = bm.verts.new((0, 0, prof[-1][1])); bm.edges.new((vs[-1], c))
    bmesh.ops.spin(bm, geom=bm.verts[:] + bm.edges[:], angle=math.tau, steps=seg, axis=(0, 0, 1), cent=(0, 0, 0))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = obj_from_bm(name, bm, mat_)
    o.location = loc
    if thick:
        s = o.modifiers.new('wall', 'SOLIDIFY'); s.thickness = thick; s.offset = -1
    sub = o.modifiers.new('sub', 'SUBSURF'); sub.levels = 1; sub.render_levels = 2
    return o


def liquid(name, radius_bottom, radius_top, height, mat_, loc=(0, 0, 0), seg=72, z0=0.004, meniscus=True):
    """Solid body of liquid sitting in a container; origin at its bottom so scale.z animates the level."""
    prof = [(0.0, 0), (radius_bottom, 0), (radius_top, height)]
    if meniscus: prof += [(radius_top * 0.97, height + 0.002)]
    prof += [(0.0, height + 0.002)]
    bm = bmesh.new()
    vs = [bm.verts.new((r, 0, z)) for r, z in prof]
    for a, b in zip(vs, vs[1:]): bm.edges.new((a, b))
    bmesh.ops.spin(bm, geom=bm.verts[:] + bm.edges[:], angle=math.tau, steps=seg, axis=(0, 0, 1), cent=(0, 0, 0))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = obj_from_bm(name, bm, mat_)
    o.location = (loc[0], loc[1], loc[2] + z0)
    return o


def box(name, size, loc, mat_=None, bevel=0.002, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object; o.name = name; o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    if bevel:
        b = o.modifiers.new('bevel', 'BEVEL'); b.width = bevel; b.segments = 3
    if mat_: o.data.materials.append(mat_)
    for p in o.data.polygons: p.use_smooth = True
    o.data.shade_auto_smooth() if hasattr(o.data, 'shade_auto_smooth') else None
    return o


def cyl(name, r, h, loc, mat_=None, rot=(0, 0, 0), verts=48, bevel=0.0):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=h, location=loc, rotation=rot)
    o = bpy.context.object; o.name = name
    if bevel:
        b = o.modifiers.new('bevel', 'BEVEL'); b.width = bevel; b.segments = 3
    if mat_: o.data.materials.append(mat_)
    for p in o.data.polygons: p.use_smooth = True
    return o


def import_ph(name, loc=(0, 0, 0), rot_z=0.0, scale=1.0, recolor=None):
    bpy.ops.import_scene.gltf(filepath=PH + '/' + name + '/' + name + '.gltf')
    objs = [o for o in bpy.context.selected_objects]
    root = bpy.data.objects.new(name + '_root', None); bpy.context.collection.objects.link(root)
    for o in objs:
        if o.parent is None: o.parent = root
        if recolor and o.type == 'MESH':
            o.data.materials.clear(); o.data.materials.append(recolor)
    meshes = [o for o in objs if o.type == 'MESH']
    bpy.context.view_layer.update()
    zmin = min((o.matrix_world @ V(c)).z for o in meshes for c in o.bound_box)
    root.location = (loc[0], loc[1], loc[2] - zmin * scale); root.rotation_euler = (0, 0, rot_z); root.scale = (scale,) * 3
    return root


def text_obj(txt, loc, size=0.02, mat_=None, rot=(math.radians(90), 0, 0), align='CENTER', font=None):
    bpy.ops.object.text_add(location=loc, rotation=rot)
    o = bpy.context.object; o.data.body = txt; o.data.size = size; o.data.align_x = align; o.data.align_y = 'CENTER'
    o.data.extrude = 0.0003
    if font: o.data.font = bpy.data.fonts.load(font)
    if mat_: o.data.materials.append(mat_)
    return o


# ───────────────────────── props ─────────────────────────
def measuring_jug(loc=(0, 0, 0), h=0.2, r=0.075, fill=0.6, liq_mat=None, name='jug'):
    """Clear plastic measuring jug with handle and printed scale marks."""
    prof = [(0.0, 0.0), (r * 0.92, 0.0), (r * 0.97, 0.006), (r, 0.02), (r * 1.06, h)]
    j = lathe(name, prof, M['clear'], thick=0.003, loc=loc)
    # handle
    bpy.ops.curve.primitive_bezier_curve_add(location=(0, 0, 0))
    hc = bpy.context.object; hc.name = name + '_handle'
    sp = hc.data.splines[0]; p0, p1 = sp.bezier_points
    p0.co = (r * 1.04, 0, h * 0.85); p0.handle_left = (r * 1.0, 0, h * 0.9); p0.handle_right = (r * 1.9, 0, h * 0.95)
    p1.co = (r * 1.0, 0, h * 0.25); p1.handle_left = (r * 1.9, 0, h * 0.15); p1.handle_right = (r * 0.9, 0, h * 0.2)
    hc.data.bevel_depth = 0.008; hc.data.bevel_resolution = 4; hc.data.materials.append(M['clear'])
    hc.parent = j
    # scale marks
    for i in range(1, 5):
        z = h * i / 5
        m_ = box(name + '_mark%d' % i, (0.0006, 0.018 if i % 2 == 0 else 0.01, 0.0012), (0, 0, 0), M['black_plastic'], bevel=0)
        m_.parent = j; ang = -math.radians(90)
        rr = r + (r * 0.06) * z / h + 0.0015
        m_.location = (rr * math.cos(ang), rr * math.sin(ang), z); m_.rotation_euler = (0, 0, ang)
    lq = None
    if fill > 0 and liq_mat:
        lq = liquid(name + '_liquid', r * 0.92 - 0.004, r + r * 0.06 * fill - 0.004, h * fill, liq_mat, loc=loc)
    return j, lq


def bowl(loc=(0, 0, 0), r=0.1, h=0.06, mat_=None, name='bowl'):
    prof = [(0.0, 0.0), (r * 0.5, 0.0), (r * 0.85, h * 0.45), (r, h)]
    return lathe(name, prof, mat_ or M['steel'], thick=0.003, loc=loc)


def pot(loc=(0, 0, 0), r=0.14, h=0.16, mat_=None, name='pot', handles=True):
    prof = [(0.0, 0.0), (r * 0.96, 0.0), (r, 0.015), (r, h), (r * 1.03, h + 0.004)]
    p = lathe(name, prof, mat_ or M['steel'], thick=0.003, loc=loc)
    if handles:
        for s in (-1, 1):
            hnd = cyl(name + '_h', 0.007, 0.07, (s * (r + 0.03), 0, h * 0.85), mat_ or M['steel'], rot=(0, math.radians(90), 0))
            hnd.parent = p; hnd.location = (s * (r + 0.03), 0, h * 0.85)
    return p


def bucket(loc=(0, 0, 0), r=0.16, h=0.3, mat_=None, name='bucket'):
    prof = [(0.0, 0.0), (r * 0.85, 0.0), (r * 0.86, 0.01), (r, h), (r * 1.04, h + 0.004), (r * 1.04, h - 0.012)]
    b = lathe(name, prof, mat_ or M['bucket_white'], thick=0.003, loc=loc)
    bpy.ops.curve.primitive_bezier_circle_add(radius=r * 1.06, location=(0, 0, 0))
    hc = bpy.context.object; hc.data.bevel_depth = 0.003; hc.data.materials.append(M['steel'])
    hc.rotation_euler = (math.radians(90), 0, 0); hc.scale = (1, 1.3, 1); hc.location = (0, 0, h * 0.78); hc.parent = b
    hc.data.splines[0].use_cyclic_u = True
    return b


def flakes_pile(center, radius, height, n=320, seed=1, kind='flake', name='flakes', zbase=0.0, mat_=None):
    """Caustic soda flakes (thin irregular discs) or pearls (small beads) in a heap."""
    random.seed(seed)
    if kind == 'pearl':
        bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=0.0042)
    else:
        bpy.ops.mesh.primitive_circle_add(vertices=9, radius=0.0085, fill_type='NGON')
        p = bpy.context.object
        for v in p.data.vertices: v.co *= 0.75 + random.random() * 0.5
        s = p.modifiers.new('t', 'SOLIDIFY'); s.thickness = 0.0007
    proto = bpy.context.object; proto.name = name + '_proto'
    proto.data.materials.append(mat_ or M['flake'])
    for p in proto.data.polygons: p.use_smooth = True
    out = []
    for i in range(n):
        rr = (random.random() ** 0.6) * radius; a = random.random() * math.tau
        top = height * (1 - (rr / radius) ** 1.6)
        z = zbase + 0.003 + random.random() * max(top, 0.002)
        o = proto.copy(); o.data = proto.data; bpy.context.collection.objects.link(o)
        o.location = (center[0] + rr * math.cos(a), center[1] + rr * math.sin(a), z)
        o.rotation_euler = (random.uniform(-0.8, 0.8), random.uniform(-0.8, 0.8), random.random() * math.tau)
        s = 0.7 + random.random() * 0.6; o.scale = (s, s * random.uniform(0.7, 1.0), s)
        out.append(o)
    bpy.data.objects.remove(proto) if False else proto.hide_render.__class__  # keep proto data alive
    proto.hide_render = True; proto.hide_viewport = True
    return out


def scoop(loc, mat_=None, name='scoop'):
    s = lathe(name, [(0.0, 0.0), (0.02, 0.0), (0.028, 0.02), (0.03, 0.035)], mat_ or M['hdpe'], thick=0.002, seg=48, loc=loc)
    hd = cyl(name + '_handle', 0.005, 0.12, (0, 0, 0), mat_ or M['hdpe'], rot=(0, math.radians(90), 0))
    hd.parent = s; hd.location = (0.085, 0, 0.03)
    return s


def tub(loc, r=0.08, h=0.11, mat_=None, lid=True, name='tub', lid_mat=None):
    t = lathe(name, [(0.0, 0.0), (r * 0.94, 0.0), (r, 0.01), (r, h)], mat_ or M['frosted'], thick=0.0025, loc=loc)
    lidobj = None
    if lid:
        lidobj = lathe(name + '_lid', [(0.0, 0.012), (r * 1.03, 0.012), (r * 1.05, 0.0), (r * 1.04, -0.006)], lid_mat or M['red'], loc=(loc[0], loc[1], loc[2] + h + 0.006))
    return t, lidobj


def bottle(loc, h=0.24, r=0.04, mat_=None, cap_mat=None, liq=None, fill=0.85, name='bottle', label=True):
    prof = [(0.0, 0.0), (r * 0.92, 0.0), (r, 0.012), (r, h * 0.7), (r * 0.55, h * 0.85), (r * 0.32, h * 0.9), (r * 0.32, h)]
    b = lathe(name, prof, mat_ or M['clear'], thick=0.002, loc=loc)
    cap = cyl(name + '_cap', r * 0.38, 0.03, (loc[0], loc[1], loc[2] + h + 0.013), cap_mat or M['magenta'], verts=32, bevel=0.002)
    lq = None
    if liq:
        lq = liquid(name + '_liq', r * 0.92 - 0.003, r - 0.003, h * 0.7 * fill, liq, loc=loc)
    lab = None
    if label:
        lab = lathe(name + '_label', [(r + 0.0012, h * 0.2), (r + 0.0012, h * 0.55)], M['label'], seg=64, loc=loc)
        lab.modifiers.clear()
    return b, cap, lq, lab


def soap_bar(loc, size=(0.09, 0.06, 0.03), mat_=None, rot_z=0.0, name='bar'):
    b = box(name, size, (loc[0], loc[1], loc[2] + size[2] / 2), mat_ or M['soap_bar'], bevel=0.004, rot=(0, 0, rot_z))
    return b


def goggles(loc, rot_z=0.0, name='goggles'):
    """Sealed chemical-splash goggles: curved clear visor in a soft black frame, with a strap."""
    root = bpy.data.objects.new(name, None); bpy.context.collection.objects.link(root)
    R, H, A = 0.085, 0.066, 62
    def arc(rr, z0, z1, segs=28):
        bm = bmesh.new(); rows = []
        for z in (z0, z1):
            rows.append([bm.verts.new((rr * math.sin(math.radians(-A + 2 * A * i / segs)), -rr * math.cos(math.radians(-A + 2 * A * i / segs)) + R, z)) for i in range(segs + 1)])
        for i in range(segs): bm.faces.new((rows[0][i], rows[0][i + 1], rows[1][i + 1], rows[1][i]))
        return bm
    v = obj_from_bm(name + '_visor', arc(R, 0.006, H - 0.006), M['lens'])
    s = v.modifiers.new('t', 'SOLIDIFY'); s.thickness = 0.002
    v.parent = root
    for z0, z1 in ((0.0, 0.009), (H - 0.009, H)):
        f = obj_from_bm(name + '_rim', arc(R + 0.002, z0, z1), M['rubber_black'])
        s = f.modifiers.new('t', 'SOLIDIFY'); s.thickness = 0.014; s.offset = 1
        b = f.modifiers.new('b', 'BEVEL'); b.width = 0.003; b.segments = 2
        f.parent = root
    for sgn in (-1, 1):
        a = math.radians(sgn * A)
        side = box(name + '_side', (0.012, 0.02, H), (R * math.sin(a), -R * math.cos(a) + R + 0.004, H / 2), M['rubber_black'], bevel=0.004, rot=(0, 0, a))
        side.parent = root
    # strap lying behind
    bpy.ops.curve.primitive_bezier_curve_add(location=(0, 0, 0)); st = bpy.context.object
    p0, p1 = st.data.splines[0].bezier_points
    p0.co = (-R * 0.88, R * 0.55, 0.012); p0.handle_left = (-R * 0.9, R * 0.3, 0.012); p0.handle_right = (-R * 0.8, R * 1.6, 0.006)
    p1.co = (R * 0.88, R * 0.55, 0.012); p1.handle_left = (R * 0.8, R * 1.6, 0.006); p1.handle_right = (R * 0.9, R * 0.3, 0.012)
    st.data.extrude = 0.012; st.data.bevel_depth = 0.0015; st.data.materials.append(M['apron']); st.parent = root
    for i in range(4):
        vb = cyl(name + '_vent', 0.006, 0.006, (R * math.sin(math.radians(-45 + 30 * i)), -R * math.cos(math.radians(-45 + 30 * i)) + R - 0.004, H + 0.002), M['rubber_black'], verts=16); vb.parent = root
    root.location = loc; root.rotation_euler = (0, 0, rot_z)
    return root


def scale_device(loc, display='0', name='scale'):
    base = box(name, (0.2, 0.2, 0.03), (loc[0], loc[1], loc[2] + 0.015), M['steel'], bevel=0.006)
    plat = box(name + '_plat', (0.18, 0.16, 0.004), (loc[0], loc[1] + 0.012, loc[2] + 0.033), M['steel'], bevel=0.003)
    panel = box(name + '_panel', (0.2, 0.035, 0.022), (loc[0], loc[1] - 0.086, loc[2] + 0.02), M['black_plastic'], bevel=0.004, rot=(math.radians(-20), 0, 0))
    lcd = box(name + '_lcd', (0.08, 0.002, 0.016), (loc[0], loc[1] - 0.105, loc[2] + 0.026), M['lcd'], bevel=0.0, rot=(math.radians(70), 0, 0))
    t = text_obj(display, (loc[0] + 0.03, loc[1] - 0.1065, loc[2] + 0.0262), size=0.012, mat_=M['lcd_text'], rot=(math.radians(70), 0, 0), align='RIGHT')
    return base, plat, t


def thermometer(loc, rot=(0, 0, 0), name='thermo'):
    t = cyl(name, 0.0035, 0.26, (0, 0, 0), M['thermo'], verts=16)
    bulb = cyl(name + '_red', 0.0012, 0.14, (0, 0, -0.05), M['thermo_red'], verts=8); bulb.parent = t
    t.location = loc; t.rotation_euler = rot
    return t


def stream(name, pts, radius, mat_, frames=None):
    """A pour stream along points; animate with stream_flow()."""
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = radius; cu.bevel_resolution = 4
    sp = cu.splines.new('NURBS'); sp.points.add(len(pts) - 1)
    for p, c in zip(sp.points, pts): p.co = (*c, 1)
    sp.use_endpoint_u = True; sp.order_u = 3
    o = bpy.data.objects.new(name, cu); bpy.context.collection.objects.link(o); cu.materials.append(mat_)
    # taper: thinner at the end
    return o


def stream_flow(o, f_start, f_full, f_stop, f_end):
    cu = o.data
    cu.bevel_factor_start = 0; cu.bevel_factor_end = 0
    cu.keyframe_insert('bevel_factor_end', frame=f_start); cu.keyframe_insert('bevel_factor_start', frame=f_start)
    cu.bevel_factor_end = 1; cu.keyframe_insert('bevel_factor_end', frame=f_full)
    cu.bevel_factor_start = 0; cu.keyframe_insert('bevel_factor_start', frame=f_stop)
    cu.bevel_factor_start = 1; cu.keyframe_insert('bevel_factor_start', frame=f_end)


def steam(loc, size=(0.1, 0.1, 0.25), f_on=1, f_peak=30, f_off=None, peak=1.6, name='steam'):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(loc[0], loc[1], loc[2] + size[2] / 2))
    o = bpy.context.object; o.name = name; o.scale = size
    o.data.materials.append(M['steam'])
    m = M['steam']; nt = m.node_tree
    d = nt.nodes['density']; mp = nt.nodes[m['mapping']]; nz = nt.nodes[m['noise']]
    d.inputs[1].default_value = 0; d.inputs[1].keyframe_insert('default_value', frame=f_on)
    d.inputs[1].default_value = peak; d.inputs[1].keyframe_insert('default_value', frame=f_peak)
    if f_off:
        d.inputs[1].default_value = 0; d.inputs[1].keyframe_insert('default_value', frame=f_off)
    # rising, swirling noise
    mp.inputs['Location'].default_value = (0, 0, 0); mp.inputs['Location'].keyframe_insert('default_value', frame=1)
    mp.inputs['Location'].default_value = (0, 0, -6); mp.inputs['Location'].keyframe_insert('default_value', frame=400)
    nz.inputs['W'].default_value = 0; nz.inputs['W'].keyframe_insert('default_value', frame=1)
    nz.inputs['W'].default_value = 4; nz.inputs['W'].keyframe_insert('default_value', frame=400)
    for fc in fcurves(m.node_tree):
        for k in fc.keyframe_points: k.interpolation = 'LINEAR' if 'Location' in fc.data_path or 'W' in fc.data_path else 'BEZIER'
    return o


# ───────────────────────── animation helpers ─────────────────────────
def fcurves(idblock):
    ad = getattr(idblock, 'animation_data', None)
    if not ad or not ad.action: return []
    act = ad.action
    if hasattr(act, 'fcurves') and not hasattr(act, 'layers'):
        return list(act.fcurves)
    try:
        from bpy_extras import anim_utils
        cb = anim_utils.action_get_channelbag_for_slot(act, ad.action_slot)
        return list(cb.fcurves) if cb else []
    except Exception:
        out = []
        for L in act.layers:
            for s in L.strips:
                for cb in s.channelbags: out += list(cb.fcurves)
        return out

def key(o, f, loc=None, rot=None, scale=None):
    if loc is not None: o.location = loc; o.keyframe_insert('location', frame=f)
    if rot is not None: o.rotation_euler = rot; o.keyframe_insert('rotation_euler', frame=f)
    if scale is not None: o.scale = scale; o.keyframe_insert('scale', frame=f)


def visible(o, f, on):
    o.hide_render = not on; o.keyframe_insert('hide_render', frame=f)
    o.hide_viewport = not on; o.keyframe_insert('hide_viewport', frame=f)


def ease_all(o, kind='BEZIER'):
    for fc in fcurves(o):
        for k in fc.keyframe_points: k.interpolation = kind


def camera(path, look, lens=40, fstop=2.8, frames=240, handheld=0.0015, name='cam'):
    """path: list of (frame, (x,y,z)); look: list of (frame, (x,y,z)) focus/aim points."""
    sc = bpy.context.scene
    bpy.ops.object.camera_add(location=path[0][1]); cam = bpy.context.object; cam.name = name; sc.camera = cam
    cam.data.lens = lens; cam.data.sensor_width = 36
    cam.data.dof.use_dof = True; cam.data.dof.aperture_fstop = fstop
    tgt = bpy.data.objects.new(name + '_target', None); bpy.context.collection.objects.link(tgt)
    for f, p in look: key(tgt, f, loc=p)
    for f, p in path: key(cam, f, loc=p)
    c = cam.constraints.new('TRACK_TO'); c.target = tgt; c.track_axis = 'TRACK_NEGATIVE_Z'; c.up_axis = 'UP_Y'
    cam.data.dof.focus_object = tgt
    # gentle hand-held drift so it feels filmed, not computer-perfect
    if handheld:
        cam.keyframe_insert('location', frame=1)
        for fc in fcurves(cam):
            for k in fc.keyframe_points: k.interpolation = 'BEZIER'; k.easing = 'EASE_IN_OUT'
            n = fc.modifiers.new('NOISE'); n.scale = 55; n.strength = handheld * 2; n.phase = random.random() * 100
    sc.frame_end = frames
    return cam, tgt


def render(out_dir, frames=None, step=1):
    sc = bpy.context.scene
    os.makedirs(out_dir, exist_ok=True)
    sc.render.image_settings.file_format = 'JPEG'; sc.render.image_settings.quality = 92
    f0, f1 = sc.frame_start, sc.frame_end
    rng = frames if frames else range(f0, f1 + 1, step)
    for f in rng:
        p = os.path.join(out_dir, 'f%04d.jpg' % f)
        if os.path.exists(p): continue
        sc.frame_set(f); sc.render.filepath = p; bpy.ops.render.render(write_still=True)


def spoon(name='spoon', recolor=None):
    """Spoon standing upright (wooden, or stainless with recolor=M['steel']); the empty is at the bowl tip."""
    piv = bpy.data.objects.new(name, None); bpy.context.collection.objects.link(piv)
    bpy.ops.import_scene.gltf(filepath=PH + '/wooden_spoon/wooden_spoon.gltf')
    for o in bpy.context.selected_objects:
        if recolor and o.type == 'MESH':
            o.data.materials.clear(); o.data.materials.append(recolor)
        if o.parent is None:
            o.parent = piv; o.rotation_euler = (math.radians(90), 0, 0); o.location = (0, 0, 0.084)
    return piv


def paddle(name='paddle', length=0.6):
    piv = bpy.data.objects.new(name, None); bpy.context.collection.objects.link(piv)
    blade = box(name + '_blade', (0.05, 0.008, 0.12), (0, 0, 0.06), M['wood_light'], bevel=0.003); blade.parent = piv
    shaft = cyl(name + '_shaft', 0.009, length, (0, 0, 0.12 + length / 2), M['wood_light'], verts=16); shaft.parent = piv
    return piv


# ───────────────────────── more props ─────────────────────────
def img_mat(name, path, rough=0.5, alpha=False):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(path)
    nt.links.new(t.outputs['Color'], b.inputs['Base Color']); b.inputs['Roughness'].default_value = rough
    if alpha: nt.links.new(t.outputs['Alpha'], b.inputs['Alpha'])
    return m


def decal(name, path, size, loc, rot, alpha=True):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object; o.name = name; o.scale = (size[0], size[1], 1)
    o.data.materials.append(img_mat(name, path, 0.5, alpha))
    return o


def wrap_label(obj_loc, r, z0, z1, path, name='lab', arc_deg=150, rot_z=0.0, alpha=False):
    """A printed label wrapped around part of a round container (UV-mapped cylinder segment)."""
    bm = bmesh.new(); segs = 32; rows = []
    uv_layer = bm.loops.layers.uv.new()
    for j, z in enumerate((z0, z1)):
        rows.append([bm.verts.new(((r) * math.cos(math.radians(-90 - arc_deg / 2 + arc_deg * i / segs)), (r) * math.sin(math.radians(-90 - arc_deg / 2 + arc_deg * i / segs)), z)) for i in range(segs + 1)])
    for i in range(segs):
        f = bm.faces.new((rows[0][i], rows[0][i + 1], rows[1][i + 1], rows[1][i]))
        for lp, (u, v) in zip(f.loops, ((i / segs, 0), ((i + 1) / segs, 0), ((i + 1) / segs, 1), (i / segs, 1))): lp[uv_layer].uv = (u, v)
    o = obj_from_bm(name, bm, img_mat(name, path, 0.55, alpha))
    o.location = obj_loc; o.rotation_euler = (0, 0, rot_z)
    return o


def shelf(loc, width=1.2, levels=(0.0, 0.32), depth=0.28, name='shelf'):
    parts = []
    for i, z in enumerate(levels):
        parts.append(box(name + '_plank%d' % i, (width, depth, 0.025), (loc[0], loc[1], loc[2] + z), M['wood_light'], bevel=0.003))
        for s in (-1, 1):
            parts.append(box(name + '_br', (0.02, depth * 0.8, 0.06), (loc[0] + s * width * 0.42, loc[1] + 0.02, loc[2] + z - 0.04), M['steel'], bevel=0.002))
    return parts


def window(loc=(-0.9, 1.09, 1.1), w=0.9, h=0.8):
    fr = []
    for dx, dz, sx, sz in ((0, h / 2, w + 0.06, 0.05), (0, -h / 2, w + 0.06, 0.05), (-w / 2, 0, 0.05, h), (w / 2, 0, 0.05, h), (0, 0, 0.03, h)):
        fr.append(box('win_frame', (sx, 0.05, sz), (loc[0] + dx, loc[1] - 0.02, loc[2] + dz), M['hdpe'], bevel=0.004))
    bpy.ops.mesh.primitive_plane_add(size=1, location=(loc[0], loc[1] - 0.005, loc[2]), rotation=(math.radians(90), 0, 0))
    p = bpy.context.object; p.scale = (w, h, 1); p.data.materials.append(mat('sky', (0.8, 0.9, 1.0), 0.5, emit=((0.85, 0.93, 1.0), 6.0)))
    area((loc[0], loc[1] - 0.3, loc[2]), (loc[0] + 0.6, 0, 0.2), 250, 0.9, (0.95, 0.97, 1.0))
    return p


def curtain(loc, w=0.5, h=0.9, col=(0.95, 0.92, 0.85), f_end=240):
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=40, y_subdivisions=30, size=1, location=loc, rotation=(math.radians(90), 0, 0))
    c = bpy.context.object; c.scale = (w, h, 1); c.data.materials.append(mat('curtain', col, 0.8, sss=0.2, trans=0.2))
    wv = c.modifiers.new('wave', 'WAVE'); wv.use_x = True; wv.use_y = False; wv.height = 0.03; wv.width = 0.25; wv.speed = 0.012; wv.narrowness = 1.2
    s = c.modifiers.new('t', 'SOLIDIFY'); s.thickness = 0.003
    for p in c.data.polygons: p.use_smooth = True
    return c


def sink_tap(loc, name='sink'):
    basin = lathe(name, [(0.0, 0.0), (0.12, 0.0), (0.2, 0.08), (0.22, 0.1)], M['enamel'], thick=0.006, loc=loc)
    bpy.ops.curve.primitive_bezier_curve_add(location=(0, 0, 0)); t = bpy.context.object; t.name = name + '_tap'
    p0, p1 = t.data.splines[0].bezier_points
    p0.co = (loc[0], loc[1] + 0.26, loc[2] + 0.0); p0.handle_right = (loc[0], loc[1] + 0.26, loc[2] + 0.4)
    p0.handle_left = (loc[0], loc[1] + 0.26, loc[2] - 0.1)
    p1.co = (loc[0], loc[1] + 0.03, loc[2] + 0.34); p1.handle_left = (loc[0], loc[1] + 0.16, loc[2] + 0.42); p1.handle_right = (loc[0], loc[1] - 0.02, loc[2] + 0.3)
    t.data.bevel_depth = 0.014; t.data.bevel_resolution = 6; t.data.materials.append(M['steel'])
    knob = cyl(name + '_knob', 0.022, 0.03, (loc[0], loc[1] + 0.26, loc[2] + 0.2), M['steel'], rot=(math.radians(90), 0, 0))
    return basin, t


def knife(loc, rot=(0, 0, 0), name='knife'):
    piv = bpy.data.objects.new(name, None); bpy.context.collection.objects.link(piv)
    bl = box(name + '_blade', (0.22, 0.0015, 0.05), (0.0, 0, 0.025), M['steel'], bevel=0.0006); bl.parent = piv
    hd = box(name + '_handle', (0.11, 0.018, 0.026), (0.165, 0, 0.04), M['black_plastic'], bevel=0.006); hd.parent = piv
    piv.location = loc; piv.rotation_euler = rot
    return piv


def mould_box(loc, size=(0.3, 0.1, 0.08), lined=True, name='mould'):
    x, y, z = size; t = 0.012; parts = []
    parts.append(box(name + '_base', (x + 2 * t, y + 2 * t, t), (loc[0], loc[1], loc[2] + t / 2), M['wood_light'], bevel=0.002))
    for dx, dy, sx, sy in ((0, -(y + t) / 2, x + 2 * t, t), (0, (y + t) / 2, x + 2 * t, t), (-(x + t) / 2, 0, t, y), ((x + t) / 2, 0, t, y)):
        parts.append(box(name + '_side', (sx, sy, z), (loc[0] + dx, loc[1] + dy, loc[2] + t + z / 2), M['wood_light'], bevel=0.002))
    if lined:
        parts.append(box(name + '_liner', (x - 0.002, y - 0.002, 0.001), (loc[0], loc[1], loc[2] + t + 0.001), M['paper'], bevel=0))
    return parts


def wire_rack(loc, w=0.6, d=0.35, name='rack'):
    parts = []
    for i in range(13):
        parts.append(cyl(name + '_w', 0.0018, d, (loc[0] - w / 2 + w * i / 12, loc[1], loc[2] + 0.03), M['steel'], rot=(math.radians(90), 0, 0), verts=8))
    for j in range(3):
        parts.append(cyl(name + '_x', 0.0022, w, (loc[0], loc[1] - d / 2 + d * j / 2, loc[2] + 0.028), M['steel'], rot=(0, math.radians(90), 0), verts=8))
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(cyl(name + '_leg', 0.003, 0.028, (loc[0] + sx * w * 0.48, loc[1] + sy * d * 0.45, loc[2] + 0.014), M['steel'], verts=8))
    return parts


def cup(loc, r=0.035, h=0.07, mat_=None, liq=None, fill=0.7, name='cup'):
    c = lathe(name, [(0.0, 0.0), (r * 0.85, 0.0), (r, h)], mat_ or M['clear'], thick=0.002, loc=loc)
    lq = liquid(name + '_liq', r * 0.85 - 0.002, r * (0.85 + 0.15 * fill) - 0.003, h * fill, liq, loc=loc) if liq else None
    return c, lq


def funnel(loc, name='funnel'):
    return lathe(name, [(0.006, -0.05), (0.008, 0.0), (0.06, 0.06)], M['hdpe'], thick=0.002, loc=loc)


def spray_bottle(loc, liq=None, name='spray', cap_mat=None):
    b, cap, lq, lab = bottle(loc, h=0.2, r=0.038, mat_=M['clear'], cap_mat=cap_mat or M['lemon'], liq=liq, fill=0.8, name=name, label=False)
    bpy.data.objects.remove(cap)
    head = box(name + '_head', (0.03, 0.07, 0.04), (loc[0], loc[1] - 0.015, loc[2] + 0.225), cap_mat or M['lemon'], bevel=0.008)
    trig = box(name + '_trig', (0.012, 0.012, 0.04), (loc[0], loc[1] - 0.035, loc[2] + 0.195), cap_mat or M['lemon'], bevel=0.004, rot=(math.radians(15), 0, 0))
    noz = cyl(name + '_noz', 0.005, 0.015, (loc[0], loc[1] - 0.055, loc[2] + 0.232), M['black_plastic'], rot=(math.radians(90), 0, 0), verts=12)
    return b, head, lq


def grad_cylinder(loc, h=0.25, r=0.025, liq=None, fill=0.6, name='cyl'):
    c = lathe(name, [(0.0, 0.0), (r, 0.0), (r, h), (r * 1.15, h + 0.004)], M['thermo'], thick=0.0015, loc=loc)
    foot = cyl(name + '_foot', r * 2.2, 0.008, (loc[0], loc[1], loc[2] + 0.004), M['clear'], verts=6)
    for i in range(1, 10):
        mk = box(name + '_mk', (0.0004, 0.012 if i % 2 else 0.02, 0.001), (loc[0], loc[1] - r - 0.0008, loc[2] + h * i / 10), M['black_plastic'], bevel=0, rot=(0, 0, math.radians(90)))
    lq = liquid(name + '_liq', r - 0.002, r - 0.002, h * fill, liq, loc=(loc[0], loc[1], loc[2] + 0.006)) if liq else None
    return c, lq


def notebook(loc, rot_z=0.0):
    nb = box('notebook', (0.21, 0.29, 0.012), (loc[0], loc[1], loc[2] + 0.006), M['paper'], bevel=0.002, rot=(0, 0, rot_z))
    page = decal('page', ASSETS + '/notebook_page.png', (0.2, 0.28), (loc[0], loc[1], loc[2] + 0.0122), (0, 0, rot_z), alpha=False)
    page.data.materials[0].node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.85
    return nb


def calculator(loc, rot_z=0.0):
    c = box('calc', (0.085, 0.15, 0.014), (loc[0], loc[1], loc[2] + 0.007), M['black_plastic'], bevel=0.005, rot=(0, 0, rot_z))
    top = decal('calctop', ASSETS + '/calculator_top.png', (0.08, 0.142), (loc[0], loc[1], loc[2] + 0.0142), (0, 0, rot_z), alpha=False)
    return c


def pen(loc, rot_z=0.0):
    return cyl('pen', 0.004, 0.14, (loc[0], loc[1], loc[2] + 0.004), M['bucket_blue'], rot=(0, math.radians(90), rot_z), verts=12)


def burner(loc, f_end=240):
    base = cyl('burner', 0.13, 0.05, (loc[0], loc[1], loc[2] + 0.025), M['black_plastic'], bevel=0.006)
    ring = cyl('burner_ring', 0.06, 0.012, (loc[0], loc[1], loc[2] + 0.056), M['steel'], verts=32)
    flame = mat('flame', (0.2, 0.4, 1.0), 0.5, emit=((0.25, 0.45, 1.0), 25))
    fl = []
    for i in range(16):
        a = i / 16 * math.tau
        bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=0.006, depth=0.03, location=(loc[0] + 0.062 * math.cos(a), loc[1] + 0.062 * math.sin(a), loc[2] + 0.075))
        o = bpy.context.object; o.data.materials.append(flame); fl.append(o)
        for f in range(1, f_end + 1, 6):
            key(o, f, scale=(1, 1, 0.8 + 0.4 * random.random()))
    return base


def towel(loc, size=(0.5, 0.35), col=(0.85, 0.82, 0.75)):
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=40, y_subdivisions=30, size=1, location=loc)
    t = bpy.context.object; t.scale = (size[0], size[1], 1)
    d = t.modifiers.new('d', 'DISPLACE'); tx = bpy.data.textures.new('tw', 'CLOUDS'); tx.noise_scale = 0.3; d.texture = tx; d.strength = 0.02
    s = t.modifiers.new('t', 'SOLIDIFY'); s.thickness = 0.006
    t.data.materials.append(mat('towel', col, 0.95, sss=0.1))
    for p in t.data.polygons: p.use_smooth = True
    return t
