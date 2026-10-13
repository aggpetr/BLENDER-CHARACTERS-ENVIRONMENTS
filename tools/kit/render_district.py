"""Render the DISTRICT_TEST object of the kit file (or EdoKitVillage_01 of a village file).

    python -I tools/kit/render_district.py <blend> <out_dir> [--quick] [shot ...]
"""
import sys, os, math, bpy
from mathutils import Vector

args = sys.argv[1:]; quick = '--quick' in args; args = [a for a in args if a != '--quick']
blend, out = os.path.abspath(args[0]), os.path.abspath(args[1]); shots = args[2:]
os.makedirs(out, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=blend)
sc = bpy.context.scene

def hide_unviewed():
    """Mimic the viewport: objects in excluded/hidden collections are not rendered."""
    def walk(lc, hidden):
        h = hidden or lc.exclude or lc.hide_viewport
        for o in lc.collection.objects:
            if h: o.hide_render = True
        for c in lc.children: walk(c, h)
    walk(bpy.context.view_layer.layer_collection, False)
    for o in bpy.data.objects:
        if o.name not in bpy.context.scene.objects: o.hide_render = True
hide_unviewed()
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 16 if quick else 64; sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = (800, 450) if quick else (1600, 900)
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
for attr, val in (('sun_elevation', math.radians(38)), ('sun_rotation', math.radians(215)), ('sun_disc', False)):
    if hasattr(sky, attr): setattr(sky, attr, val)
nt.links.new(sky.outputs['Color'], bg.inputs['Color']); bg.inputs['Strength'].default_value = 0.25
sun = bpy.data.lights.new('S', 'SUN'); sun.energy = 2.6; sun.angle = math.radians(1.2); sun.color = (1.0, 0.93, 0.84)
so = bpy.data.objects.new('S', sun); sc.collection.objects.link(so); so.rotation_euler = (math.radians(52), 0, math.radians(35))
gm = bpy.data.materials.new('G'); gm.use_nodes = True; gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.13, 0.115, 0.08, 1)
dobj = bpy.data.objects.get('DISTRICT_TEST') or bpy.data.objects['EdoKitVillage_01']
if dobj.name == 'DISTRICT_TEST':
    for ob in bpy.data.objects:
        if ob.type == 'MESH':
            ob.hide_render = not (ob == dobj or ob.name == 'TEST_Ground_District')
    g = bpy.data.objects['TEST_Ground_District']; g.data.materials.clear(); g.data.materials.append(gm)
O = dobj.matrix_world.translation.copy()
cam = bpy.data.cameras.new('C'); co = bpy.data.objects.new('C', cam); sc.collection.objects.link(co); sc.camera = co
SH = {
    'overview':   (Vector((-100, -120, 95)), Vector((10, 0, 0)), 27),
    'plaza_hall': (Vector((-33, -3, 2.3)), Vector((38, 0, 5.5)), 24),
    'hall_front': (Vector((10, -26, 5.5)), Vector((46, 0, 6.5)), 30),
    'street':     (Vector((-62, 22, 2.0)), Vector((-28, -6, 4.0)), 26),
    'north_lane': (Vector((-26, 8, 3.0)), Vector((-22, 52, 3.5)), 28),
}
for name in (shots or list(SH)):
    loc, tgt, lens = SH[name]
    co.location = O + loc; cam.lens = lens
    co.rotation_euler = ((O + tgt) - co.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(out, f'{name}.png'); bpy.ops.render.render(write_still=True); print('rendered', name, flush=True)
