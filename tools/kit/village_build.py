"""Rebuild the whole village with the kit: one GN_EdoKitHouse object per original GN_EdoHouse house.

Headless:  python -I tools/kit/village_build.py <original.blend> <kit.blend> <out_dir> [--render] [--quick] [--save <file.blend>]
In Blender: open your village .blend, set KIT_PATH below, run this file from the Text Editor (keeps your originals, hides them).

Writes <out_dir>/village_manifest.json (houses, parameters, every module instance with its world transform, lantern
light positions) and <out_dir>/village_floor_check.json (original vs kit floor height for every house).
"""
import sys, os, math, json, bpy
from mathutils import Vector

KIT_PATH = '//kit/Edo_Kit.blend'      # used when run inside Blender
in_ui = not bpy.app.background
args = [] if in_ui else sys.argv[1:]
flags = {a for a in args if a.startswith('--')}
pos = [a for a in args if not a.startswith('--')]
save_to = None
if '--save' in args:
    save_to = os.path.abspath(args[args.index('--save') + 1]); pos = [p for p in pos if os.path.abspath(p) != save_to]
if in_ui:
    KIT = bpy.path.abspath(KIT_PATH); OUT = bpy.path.abspath('//kit_village_out')
else:
    SRC, KIT, OUT = [os.path.abspath(a) for a in pos[:3]]
    bpy.ops.wm.open_mainfile(filepath=SRC)
os.makedirs(OUT, exist_ok=True)
sc = bpy.context.scene

if 'GN_EdoKitHouse' not in bpy.data.node_groups:
    with bpy.data.libraries.load(KIT, link=False) as (df, dt):
        dt.node_groups = ['GN_EdoKitHouse']
gn = bpy.data.node_groups['GN_EdoKitHouse']
kdir = os.path.dirname(KIT)
for im in bpy.data.images:
    if im.filepath.startswith('//textures'):
        im.filepath = os.path.join(kdir, im.filepath[2:])

src_gn = bpy.data.node_groups['GN_EdoHouse']
sid = {s.name: s.identifier for s in src_gn.interface.items_tree if s.item_type == 'SOCKET' and s.in_out == 'INPUT'}
kid = {s.name: s.identifier for s in gn.interface.items_tree if s.item_type == 'SOCKET' and s.in_out == 'INPUT'}
coll = bpy.data.collections.get('KIT_Village') or bpy.data.collections.new('KIT_Village')
if coll.name not in sc.collection.children: sc.collection.children.link(coll)

pairs = []
for o in [o for o in bpy.data.objects if any(m.type == 'NODES' and m.node_group == src_gn for m in o.modifiers)]:
    m = next(m for m in o.modifiers if m.type == 'NODES' and m.node_group == src_gn)
    get = lambda k: m.properties.inputs[sid[k]]['value']
    name = o.name + '_KIT'
    k = bpy.data.objects.get(name) or bpy.data.objects.new(name, bpy.data.meshes.new(name))
    if k.name not in coll.objects: coll.objects.link(k)
    k.matrix_world = o.matrix_world.copy()
    km = k.modifiers.get('EdoKitHouse') or k.modifiers.new('EdoKitHouse', 'NODES'); km.node_group = gn
    params = {n: get(n) for n in ('Ground', 'Bays X', 'Bays Y', 'Floors', 'Roof', 'Engawa', 'Balcony', 'Shopfront', 'Lanterns', 'Gate', 'Fence', 'Seed', 'Props', 'Raise')}
    params['Balcony'] = bool(params['Balcony']) and params['Floors'] >= 2
    for n, v in params.items():
        km.properties.inputs[kid[n]]['value'] = v
    o.hide_render = True; o.hide_viewport = True
    pairs.append((o, k, params))

dg = bpy.context.evaluated_depsgraph_get()
def floor_original(o):
    eo = o.evaluated_get(dg); me = eo.to_mesh()
    idx = [i for i, mt in enumerate(me.materials) if mt and mt.name == 'MAT_Edo_Plaster']
    m = next(m for m in o.modifiers if m.type == 'NODES' and m.node_group == src_gn)
    hx = m.properties.inputs[sid['Bays X']]['value'] * 0.91 + 0.15; hy = m.properties.inputs[sid['Bays Y']]['value'] * 0.91 + 0.15
    zs = [(o.matrix_world @ me.vertices[v].co).z for p in me.polygons if p.material_index in idx for v in p.vertices
          if abs(me.vertices[v].co.x) < hx and abs(me.vertices[v].co.y) < hy]   # house walls only (not the compound wall)
    eo.to_mesh_clear(); return min(zs) if zs else float('nan')
for o, _, _ in pairs:      # originals must be evaluated while visible
    o.hide_viewport = False
dg.update()
orig_floor = {o.name: floor_original(o) for o, _, _ in pairs}
for o, _, _ in pairs:
    o.hide_viewport = True
dg = bpy.context.evaluated_depsgraph_get(); dg.update()

inst = {}
for i in dg.object_instances:
    if i.is_instance and i.parent and i.instance_object:
        inst.setdefault(i.parent.original.name, []).append((i.instance_object.original.name, i.matrix_world.copy()))
houses, check = [], []
for o, k, p in pairs:
    items = inst.get(k.name, [])
    fk = min([M.translation.z for n, M in items if n == 'SM_Edo_Post_Storey'] or [float('nan')])
    lights = [list(map(lambda v: round(v, 3), M @ Vector((0, -0.58, 1.95)))) for n, M in items if n == 'SM_Edo_Lantern']
    mods = []
    for n, M in items:
        loc, rot, scl = M.decompose()
        e = rot.to_euler()
        mods.append(dict(module=n, location=[round(v, 4) for v in loc], rotation_deg=[round(math.degrees(a), 3) for a in e], scale=[round(v, 4) for v in scl]))
    arche = o.name.split('_', 2)[-1] if o.name.count('_') >= 2 else o.name
    houses.append(dict(house=o.name, archetype=arche, location=[round(v, 4) for v in o.matrix_world.translation],
                       rotation_z_deg=round(math.degrees(o.rotation_euler.z), 3),
                       params={kk: (vv.name if hasattr(vv, 'name') else vv) for kk, vv in p.items()},
                       floor_z=round(fk, 4), lantern_lights=lights, modules=mods))
    check.append(dict(house=o.name, floor_original=round(orig_floor[o.name], 3), floor_kit=round(fk, 3), diff=round(fk - orig_floor[o.name], 3)))
json.dump(dict(units='metres, Blender world space (Z up, right-handed)', houses=houses), open(os.path.join(OUT, 'village_manifest.json'), 'w'))
json.dump(check, open(os.path.join(OUT, 'village_floor_check.json'), 'w'), indent=1)
d = [abs(c['diff']) for c in check if c['diff'] == c['diff']]
print(f"houses {len(houses)}, module instances {sum(len(h['modules']) for h in houses)}, lantern lights {sum(len(h['lantern_lights']) for h in houses)}")
print(f"floor diff vs original: max {max(d):.3f} m, mean {sum(d) / len(d):.3f} m, houses over 2 cm: {[c['house'] for c in check if abs(c['diff']) > 0.02]}")

if '--render' in flags:
    quick = '--quick' in flags
    sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 16 if quick else 64; sc.cycles.use_denoising = True
    sc.render.resolution_x, sc.render.resolution_y = (960, 540) if quick else (1600, 900)
    try: sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
    except Exception: pass
    sc.view_settings.exposure = -0.35
    for ob in bpy.data.objects:
        if ob.type == 'LIGHT': ob.hide_render = True
    w = bpy.data.worlds.new('PreviewSky'); w.use_nodes = True; sc.world = w
    nt = w.node_tree; bg = nt.nodes['Background']; sky = nt.nodes.new('ShaderNodeTexSky')
    for t in ('MULTIPLE_SCATTERING', 'NISHITA', 'SINGLE_SCATTERING', 'HOSEK_WILKIE'):
        try: sky.sky_type = t; break
        except Exception: continue
    for attr, val in (('sun_elevation', math.radians(32)), ('sun_rotation', math.radians(215)), ('sun_disc', False)):
        if hasattr(sky, attr): setattr(sky, attr, val)
    nt.links.new(sky.outputs['Color'], bg.inputs['Color']); bg.inputs['Strength'].default_value = 0.22
    sun = bpy.data.lights.new('PreviewSun', 'SUN'); sun.energy = 2.4; sun.angle = math.radians(1.2); sun.color = (1.0, 0.93, 0.84)
    so = bpy.data.objects.new('PreviewSun', sun); sc.collection.objects.link(so); so.rotation_euler = (math.radians(58), 0, math.radians(35))
    cam = bpy.data.cameras.new('VCam'); co = bpy.data.objects.new('VCam', cam); sc.collection.objects.link(co); sc.camera = co
    town = [o.matrix_world.translation for o, _, _ in pairs if o.name.startswith('TWN_')]
    ctr = sum(town, Vector()) / len(town); ctr.z = 2.0
    for name, off, lens in (('village_town', Vector((-70, -85, 55)), 30), ('village_street', Vector((-22, -30, 9)), 26)):
        co.location = ctr + off; cam.lens = lens
        co.rotation_euler = (ctr - co.location).to_track_quat('-Z', 'Y').to_euler()
        for state in ('before', 'after'):
            for o, k, _ in pairs:
                o.hide_render = (state == 'after'); k.hide_render = (state == 'before')
            sc.render.filepath = os.path.join(OUT, f'{name}_{state}.png'); bpy.ops.render.render(write_still=True)
            print('rendered', name, state, flush=True)
if save_to:
    bpy.ops.wm.save_as_mainfile(filepath=save_to)
