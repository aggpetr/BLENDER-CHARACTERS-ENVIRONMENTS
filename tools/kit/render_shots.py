"""Camera shots of an installed village: python -I tools/kit/render_shots.py <blend> <out_dir> [--quick] name:x,y,z:tx,ty,tz:lens ..."""
import sys, os, math, bpy
from mathutils import Vector
args = sys.argv[1:]; quick = '--quick' in args; args = [a for a in args if a != '--quick']
blend, out, *shots = args; os.makedirs(out, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend)); sc = bpy.context.scene
def walk(lc, hidden):
    h = hidden or lc.exclude or lc.hide_viewport
    for o in lc.collection.objects:
        if h: o.hide_render = True
    for c in lc.children: walk(c, h)
walk(bpy.context.view_layer.layer_collection, False)
for o in bpy.data.objects:
    if o.name not in sc.objects: o.hide_render = True
    if o.type == 'LIGHT': o.hide_render = True
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 16 if quick else 48; sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = (900, 520) if quick else (1600, 900)
try: sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
except Exception: pass
sc.view_settings.exposure = -0.3
w = bpy.data.worlds.new('S'); w.use_nodes = True; sc.world = w
nt = w.node_tree; bg = nt.nodes['Background']; sky = nt.nodes.new('ShaderNodeTexSky')
for t in ('MULTIPLE_SCATTERING', 'NISHITA'):
    try: sky.sky_type = t; break
    except Exception: continue
sky.sun_elevation = math.radians(38); sky.sun_rotation = math.radians(215); sky.sun_disc = False
nt.links.new(sky.outputs['Color'], bg.inputs['Color']); bg.inputs['Strength'].default_value = 0.25
sun = bpy.data.lights.new('S', 'SUN'); sun.energy = 2.6; sun.angle = math.radians(1.2); sun.color = (1.0, 0.93, 0.84)
so = bpy.data.objects.new('S', sun); sc.collection.objects.link(so); so.rotation_euler = (math.radians(52), 0, math.radians(35))
cam = bpy.data.cameras.new('C'); co = bpy.data.objects.new('C', cam); sc.collection.objects.link(co); sc.camera = co; cam.clip_end = 3000
for sh in shots:
    name, loc, tgt, lens = sh.split(':')
    L = Vector(map(float, loc.split(','))); T = Vector(map(float, tgt.split(',')))
    co.location = L; cam.lens = float(lens); co.rotation_euler = (T - L).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(out, name + '.png'); bpy.ops.render.render(write_still=True); print('rendered', name, flush=True)
