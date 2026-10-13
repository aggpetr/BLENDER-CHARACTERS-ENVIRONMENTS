"""Render every ARCH_* kit house (one image each) and a labelled contact sheet.

    python -I tools/kit/render_archetypes.py <kit.blend> <out_dir> [--quick] [names...]
"""
import sys, os, math, json, bpy
from mathutils import Vector

args = sys.argv[1:]
quick = '--quick' in args; args = [a for a in args if a != '--quick']
kit, out = os.path.abspath(args[0]), os.path.abspath(args[1]); only = args[2:]
os.makedirs(out, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=kit)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 16 if quick else 64
sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = (640, 400) if quick else (1280, 800)
try: sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
except Exception: pass
sc.view_settings.exposure = -0.35
w = bpy.data.worlds.new('PreviewSky'); w.use_nodes = True; sc.world = w
nt = w.node_tree; bg = nt.nodes['Background']; sky = nt.nodes.new('ShaderNodeTexSky')
for t in ('MULTIPLE_SCATTERING', 'NISHITA', 'SINGLE_SCATTERING', 'HOSEK_WILKIE'):
    try: sky.sky_type = t; break
    except Exception: continue
for attr, val in (('sun_elevation', math.radians(32)), ('sun_rotation', math.radians(215)), ('sun_disc', False)):
    if hasattr(sky, attr): setattr(sky, attr, val)
nt.links.new(sky.outputs['Color'], bg.inputs['Color']); bg.inputs['Strength'].default_value = 0.22
sun = bpy.data.lights.new('S', 'SUN'); sun.energy = 2.4; sun.angle = math.radians(1.2); sun.color = (1.0, 0.93, 0.84)
so = bpy.data.objects.new('S', sun); sc.collection.objects.link(so); so.rotation_euler = (math.radians(58), 0, math.radians(35))
gm = bpy.data.materials.new('G'); gm.use_nodes = True; gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.12, 0.11, 0.08, 1)
for ob in bpy.data.objects:
    if ob.name.startswith('TEST_Ground'):
        ob.data.materials.clear(); ob.data.materials.append(gm)
cam = bpy.data.cameras.new('C'); co = bpy.data.objects.new('C', cam); sc.collection.objects.link(co); sc.camera = co; cam.lens = 32
arch = json.load(open(os.path.join(os.path.dirname(kit), 'archetypes.json')))
houses = [o for o in bpy.data.objects if o.name.startswith(('ARCH_', 'TEST_')) and o.modifiers]
done = []
for name, a in arch.items():
    if only and name not in only: continue
    ob = bpy.data.objects[f'ARCH_{name}']
    for h in houses: h.hide_render = (h != ob)
    size = max(a['bx'], a['by']) * 1.82 + 6
    tgt = ob.location + Vector((0, 0, 3.2 + a.get('fl', 1) * 0.9))
    co.location = tgt + Vector((-1.0, -1.35, 0.75)).normalized() * (size * 1.55 + 4)
    co.rotation_euler = (tgt - co.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(out, f'{name}.png'); bpy.ops.render.render(write_still=True); done.append(name)
    print('rendered', name, flush=True)
try:
    from PIL import Image, ImageDraw
    W, H = 480, 300; cols = 5; rows = (len(done) + cols - 1) // cols
    sheet = Image.new('RGB', (W * cols, H * rows), 'white'); d = ImageDraw.Draw(sheet)
    for i, n in enumerate(done):
        im = Image.open(os.path.join(out, f'{n}.png')).convert('RGB').resize((W, H)); x, y = (i % cols) * W, (i // cols) * H
        sheet.paste(im, (x, y)); d.rectangle((x, y, x + 150, y + 18), fill='black'); d.text((x + 5, y + 4), f'{i + 1}. {n}', fill='white')
    sheet.save(os.path.join(out, 'kit_archetypes_sheet.jpg'), quality=90)
except ImportError:
    pass
