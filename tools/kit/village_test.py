"""Place kit houses where the original dwellA houses stand, compare floor heights, render before/after.

    python -I tools/kit/village_test.py <original.blend> <kit.blend> <out_dir> [--quick]
"""
import sys, os, math, json, collections, bpy, bmesh, mathutils
from mathutils import Vector

args = sys.argv[1:]
quick = '--quick' in args; args = [a for a in args if a != '--quick']
SRC, KIT, OUT = [os.path.abspath(a) for a in args[:3]]
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=SRC)
sc = bpy.context.scene

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
originals = [o for o in bpy.data.objects if o.name.endswith('_dwellA') and any(m.type == 'NODES' and m.node_group == src_gn for m in o.modifiers)]
coll = bpy.data.collections.new('KIT_Village_dwellA'); sc.collection.children.link(coll)
pairs = []
for o in originals:
    m = next(m for m in o.modifiers if m.type == 'NODES' and m.node_group == src_gn)
    get = lambda k: m.properties.inputs[sid[k]]['value']
    k = bpy.data.objects.new(o.name.replace('_dwellA', '_KIT_dwellA'), bpy.data.meshes.new('kit')); coll.objects.link(k)
    k.matrix_world = o.matrix_world.copy()
    km = k.modifiers.new('EdoKitHouse', 'NODES'); km.node_group = gn
    for name in ('Ground', 'Bays X', 'Bays Y', 'Floors', 'Roof', 'Engawa', 'Seed', 'Props'):
        km.properties.inputs[kid[name]]['value'] = get(name)
    km.properties.inputs[kid['Fence']]['value'] = 1 if get('Fence') else 0
    pairs.append((o, k))

dg = bpy.context.evaluated_depsgraph_get()
def floor_original(o):
    eo = o.evaluated_get(dg); me = eo.to_mesh()
    idx = [i for i, mt in enumerate(me.materials) if mt and mt.name == 'MAT_Edo_Plaster']
    zs = [(o.matrix_world @ me.vertices[v].co).z for p in me.polygons if p.material_index in idx for v in p.vertices]
    eo.to_mesh_clear(); return min(zs)
kitF = {}
for inst in dg.object_instances:
    if inst.is_instance and inst.parent and inst.instance_object and inst.instance_object.original.name == 'SM_Edo_Post_Storey':
        kitF.setdefault(inst.parent.original.name, []).append(inst.matrix_world.translation.z)
rows = []
for o, k in pairs:
    fo = floor_original(o); fk = min(kitF.get(k.name, [float('nan')]))
    rows.append(dict(house=o.name, x=round(o.location.x, 2), y=round(o.location.y, 2), rot_z=round(math.degrees(o.rotation_euler.z)),
                     floor_original=round(fo, 3), floor_kit=round(fk, 3), diff=round(fk - fo, 3)))
    print(f"{o.name:16s} at ({o.location.x:8.2f},{o.location.y:8.2f}) rot {math.degrees(o.rotation_euler.z):5.0f}  floor original {fo:7.3f}  kit {fk:7.3f}  diff {fk - fo:+.3f}")
json.dump(rows, open(os.path.join(OUT, 'village_floor_check.json'), 'w'), indent=1)

# ---------------------------------------------------------------- render setup (same look as the kit previews)
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 24 if quick else 64
sc.cycles.use_denoising = True
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

# camera on the densest cluster of dwellA houses
pos = [o.matrix_world.translation for o, _ in pairs]
best = max(pos, key=lambda p: sum(1 for q in pos if (q - p).length < 30))
near = [q for q in pos if (q - best).length < 30]
ctr = sum(near, Vector()) / len(near)
ctr.z = max(rows, key=lambda r: 0)['floor_original'] if False else sum(r['floor_original'] for r in rows) / len(rows) + 2.5
for name, off, lens in (('village_close', Vector((-17, -21, 10)), 30), ('village_wide', Vector((-40, -48, 30)), 28)):
    co.location = ctr + off; cam.lens = lens
    co.rotation_euler = (ctr - co.location).to_track_quat('-Z', 'Y').to_euler()
    for state in ('before', 'after'):
        for o, k in pairs:
            o.hide_render = (state == 'after'); k.hide_render = (state == 'before')
        sc.render.filepath = os.path.join(OUT, f'{name}_{state}.png')
        bpy.ops.render.render(write_still=True)
        print('rendered', name, state, flush=True)
