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
import json
LAY = os.environ.get('KIT_LAYOUT') or os.path.join(os.path.dirname(blend), 'village', 'district_layout.json')
if os.path.exists(LAY):
    lay = json.load(open(LAY)); cx, cy = lay['center']
    def front_shot(sl, side=0.0, dist=9.0, h=3.6, lens=24):
        a = math.radians(sl['angle_deg']); R = lambda x, y: Vector((x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a), 0))
        p = Vector((sl['pos'][0] - cx, sl['pos'][1] - cy, 0)); r2 = sl['rect'][2]
        return (p + R(side, r2 - dist) + Vector((0, 0, h)), p + R(side * 0.3, r2 * 0.55) + Vector((0, 0, 1.5)), lens)
    for sl in lay['slots']:
        if sl['arch'] in ('smithy', 'restB', 'tea', 'clinic', 'shopA', 'farmhouse', 'hutA', 'dwellA'):
            SH.setdefault('front_' + sl['arch'], front_shot(sl))
            SH.setdefault('yard_' + sl['arch'], front_shot(sl, 0.0, 4.5, 8.5, 30))
            _a = math.radians(sl['angle_deg']); _p = Vector((sl['pos'][0] - cx, sl['pos'][1] - cy, 0)); _r = sl['rect']
            _c = _p + Vector((-math.sin(_a) * 0.0 + (0 * 1.0), 0, 0))
            _fy = Vector((math.sin(_a), -math.cos(_a), 0)) * (-_r[2] * 0.45)
            SH.setdefault('top_' + sl['arch'], (_p + _fy + Vector((0.01, 0.01, 17.0)), _p + _fy, 35))
        if sl['arch'] == 'hospital':
            SH['hospital_front'] = front_shot(sl, 0.0, 16.0, 7.0, 22)
            _a = math.radians(sl['angle_deg']); _p = Vector((sl['pos'][0] - cx, sl['pos'][1] - cy, 0))
            SH['hospital_court'] = (_p + Vector((0.01, -9.0, 24.0)), _p + Vector((0, -9.0, 0)), 30)
            SH['hospital_wide'] = (Vector((sl['pos'][0] - cx - 60, sl['pos'][1] - cy - 52, 38)), Vector((sl['pos'][0] - cx, sl['pos'][1] - cy, 2)), 26)
for name in (shots or list(SH)):
    loc, tgt, lens = SH[name]
    co.location = O + loc; cam.lens = lens
    co.rotation_euler = ((O + tgt) - co.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(out, f'{name}.png'); bpy.ops.render.render(write_still=True); print('rendered', name, flush=True)
