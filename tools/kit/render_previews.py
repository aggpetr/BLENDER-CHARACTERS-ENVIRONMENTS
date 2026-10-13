"""Preview renders of the kit test houses (Cycles, CPU).

    python -I tools/kit/render_previews.py <kit.blend> <out_dir> [shot ...] [--quick]
"""
import sys, os, math, bpy, mathutils
from mathutils import Vector

args = [a for a in sys.argv[sys.argv.index('--') + 1:]] if '--' in sys.argv else sys.argv[1:]
quick = '--quick' in args; args = [a for a in args if a != '--quick']
kit, out = os.path.abspath(args[0]), os.path.abspath(args[1]); shots = args[2:]
os.makedirs(out, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=kit)
sc = bpy.context.scene

# ---------------------------------------------------------------- render settings
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'
sc.cycles.samples = 24 if quick else 64
sc.cycles.use_denoising = True
try: sc.cycles.denoiser = 'OPENIMAGEDENOISE'
except Exception: pass
sc.cycles.max_bounces = 6
sc.render.resolution_x, sc.render.resolution_y = (960, 540) if quick else (1600, 900)
sc.render.image_settings.file_format = 'PNG'
try: sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
except Exception: pass
sc.view_settings.exposure = -0.35

# ---------------------------------------------------------------- sky + sun
w = bpy.data.worlds.new('PreviewSky'); w.use_nodes = True; sc.world = w
nt = w.node_tree; bg = nt.nodes['Background']
sky = nt.nodes.new('ShaderNodeTexSky')
for t in ('MULTIPLE_SCATTERING', 'NISHITA', 'SINGLE_SCATTERING', 'HOSEK_WILKIE'):
    try: sky.sky_type = t; break
    except Exception: continue
for attr, val in (('sun_elevation', math.radians(32)), ('sun_rotation', math.radians(215)), ('air_density', 1.0), ('dust_density', 2.5), ('sun_disc', False)):
    if hasattr(sky, attr): setattr(sky, attr, val)
nt.links.new(sky.outputs['Color'], bg.inputs['Color']); bg.inputs['Strength'].default_value = 0.22
sun = bpy.data.lights.new('PreviewSun', 'SUN'); sun.energy = 2.4; sun.angle = math.radians(1.2); sun.color = (1.0, 0.93, 0.84)
so = bpy.data.objects.new('PreviewSun', sun); sc.collection.objects.link(so)
so.rotation_euler = (math.radians(58), 0, math.radians(215 - 180))

# ---------------------------------------------------------------- ground material (packed earth with moss patches)
gm = bpy.data.materials.new('M_Preview_Ground'); gm.use_nodes = True
g = gm.node_tree; b = g.nodes['Principled BSDF']
tc = g.nodes.new('ShaderNodeTexCoord'); n1 = g.nodes.new('ShaderNodeTexNoise'); n1.inputs['Scale'].default_value = 0.35; n1.inputs['Detail'].default_value = 8
g.links.new(tc.outputs['Object'], n1.inputs['Vector'])
ramp = g.nodes.new('ShaderNodeValToRGB'); g.links.new(n1.outputs['Fac'], ramp.inputs['Fac'])
ramp.color_ramp.elements[0].position = 0.42; ramp.color_ramp.elements[0].color = (0.16, 0.13, 0.09, 1)
ramp.color_ramp.elements[1].position = 0.62; ramp.color_ramp.elements[1].color = (0.13, 0.15, 0.07, 1)
g.links.new(ramp.outputs['Color'], b.inputs['Base Color']); b.inputs['Roughness'].default_value = 0.95
n2 = g.nodes.new('ShaderNodeTexNoise'); n2.inputs['Scale'].default_value = 9; n2.inputs['Detail'].default_value = 10
g.links.new(tc.outputs['Object'], n2.inputs['Vector'])
bump = g.nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 0.25; g.links.new(n2.outputs['Fac'], bump.inputs['Height']); g.links.new(bump.outputs['Normal'], b.inputs['Normal'])
for ob in bpy.data.objects:
    if ob.name.startswith('TEST_Ground'):
        ob.data.materials.clear(); ob.data.materials.append(gm)
        if ob.name == 'TEST_Ground_Flat':
            ob.scale = (25, 25, 1)          # reach the horizon (preview only; houses sample it the same way)

cam = bpy.data.cameras.new('PreviewCam'); co = bpy.data.objects.new('PreviewCam', cam); sc.collection.objects.link(co); sc.camera = co

def look(loc, target, lens=35):
    co.location = Vector(loc); cam.lens = lens
    co.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()

SHOTS = {
    'hero':     ((-13.5, -15.5, 7.5), (0.3, 0.0, 2.8), 30),
    'street':   ((-6.5, -10.8, 1.65), (0.6, -1.5, 2.9), 24),
    'eave':     ((-5.8, -5.6, 1.7), (-3.6, -3.0, 3.3), 20),
    'back':     ((12.0, 14.0, 6.0), (0.0, 0.0, 2.6), 30),
    'variants': ((2.0, -42.0, 15.0), (1.0, 0.0, 2.5), 32),
    'slope':    ((-14.0, 62.0, 6.0), (0.0, 80.0, 3.0), 30),
}
for name in (shots or list(SHOTS)):
    loc, tgt, lens = SHOTS[name]
    look(loc, tgt, lens)
    sc.render.filepath = os.path.join(out, f'{name}.png')
    bpy.ops.render.render(write_still=True)
    print('rendered', name, flush=True)
