"""Concept render of a torii gate with the three border styles (not part of the kit, a picture of the idea).

    python -I tools/kit/concept_border.py <out_dir>

Road along Y through the gate at the origin, the border along X: palisade (B) on the left, earth bank + ditch + hedge (A) and then standing stones with a
sacred rope (C) on the right. Uses the kit modules (fence, lantern, curb, textures) plus concept-only shapes for the torii and the pier.
"""
import sys, os, math, random, bpy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit_lib, modules, modules_town
from kit_lib import MB
from mathutils import Vector, Matrix

out = os.path.abspath(sys.argv[1]); os.makedirs(out, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
kit_lib.make_materials(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'kit', 'textures'))
def flat(name, rgb, rough=0.5):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*rgb, 1); b.inputs['Roughness'].default_value = rough; return m
VERM = flat('Vermilion', (0.62, 0.07, 0.04), 0.35); BLACK = flat('BlackLacquer', (0.02, 0.02, 0.02), 0.25); GRASS = flat('Grass', (0.13, 0.22, 0.07), 0.9)
ROAD = flat('Road', (0.36, 0.27, 0.18), 0.95); WATER = flat('Water', (0.08, 0.2, 0.3), 0.08); ROPE = flat('Rope', (0.8, 0.72, 0.5), 0.9); PAPER = flat('Shide', (0.95, 0.95, 0.92), 0.9)


def add(mb, mats, loc=(0, 0, 0), rot=0.0, scale=(1, 1, 1)):
    """finish an MB with explicit materials (name -> bpy material) and place it"""
    bm = mb.bm
    me = bpy.data.meshes.new(mb.name); bm.to_mesh(me); bm.free()
    for m in mb.mats: me.materials.append(mats.get(m) or bpy.data.materials[f'M_Edo_{m}'])
    ob = bpy.data.objects.new(mb.name, me); sc.collection.objects.link(ob)
    ob.location = loc; ob.rotation_euler = (0, 0, rot); ob.scale = scale
    return ob


MATS = {'Vermilion': VERM, 'Black': BLACK, 'Grass': GRASS, 'Road': ROAD, 'Water': WATER, 'Rope': ROPE, 'Shide': PAPER}


def torii():
    mb = MB('torii'); S = 3.0                                      # pillar centres at +-3.0 m
    for sx in (-1, 1):
        mb.lathe([(0.46, 0.0), (0.46, 0.35)], 16, 'Stone', cap_top=True, cap_bottom=False)
        s = len(mb.bm.verts); mb.lathe([(0.30, 0.35), (0.285, 2.5), (0.25, 5.0)], 16, 'Vermilion', cap_top=True, smooth=True)
        for v in list(mb.bm.verts)[s:]: v.co.x += sx * S
        for v in list(mb.bm.verts)[:s]: pass
    # base stones need the same shift: rebuild them explicitly
    return mb


def torii_build():
    mb = MB('torii'); S = 3.0
    for sx in (-1, 1):
        s = len(mb.bm.verts)
        mb.lathe([(0.0, 0.0), (0.46, 0.0), (0.46, 0.35), (0.0, 0.35)], 16, 'Stone', cap_top=False, smooth=False)
        mb.lathe([(0.30, 0.35), (0.285, 2.5), (0.25, 5.0)], 16, 'Vermilion', cap_top=True, smooth=True)
        for v in list(mb.bm.verts)[s:]: v.co.x += sx * S
    rings = []                                                      # kasagi: top beam, ends curving up
    for i in range(33):
        x = -4.6 + i * 9.2 / 32; z = 5.0 + 0.85 * (abs(x) / 4.6) ** 2.6
        rings.append([(x, -0.34, z - 0.12), (x, 0.34, z - 0.12), (x, 0.28, z + 0.2), (x, -0.28, z + 0.2)])
    mb.loft(rings, 'Black', closed=True, smooth=False, cap0=True, cap1=True, want_out=lambda m: Vector((0, m.y, m.z - 5.1 - 0.85 * (abs(m.x) / 4.6) ** 2.6)))
    mb.box((-4.1, -0.26, 4.72), (4.1, 0.26, 4.95), 'Vermilion', grain=0)                     # shimaki
    mb.box((-3.75, -0.17, 3.95), (3.75, 0.17, 4.28), 'Vermilion', grain=0)                    # nuki
    mb.box((-0.25, -0.12, 4.28), (0.25, 0.12, 4.72), 'Black', grain=2)                        # plaque post
    for sx in (-1, 1): mb.box((sx * S - 0.34, -0.2, 3.9), (sx * S + 0.34, 0.2, 4.33), 'Black', grain=0)   # pillar collars
    return mb


def pier():
    mb = MB('pier')
    mb.box((-0.42, -0.42, 0.0), (0.42, 0.42, 1.9), 'StoneWall')
    mb.box((-0.5, -0.5, 1.9), (0.5, 0.5, 2.05), 'Stone')
    mb.lathe([(0.45, 2.05), (0.3, 2.3), (0.0, 2.55)], 4, 'Stone', cap_top=False, phase=math.pi / 4, smooth=False)
    return mb


def stone_marker(seed):
    mb = MB(f'stone{seed}'); rnd = random.Random(seed)
    mb.lathe([(0.0, 0.0), (0.38, 0.0), (0.42, 0.5), (0.33, 1.0), (0.12, 1.25), (0.0, 1.3)], 7, 'StoneWall', cap_top=False, smooth=True, phase=rnd.random())
    return mb


def bank(length=4.0):
    mb = MB('bank'); rnd = random.Random(3)
    prof = [(-1.9, -0.05), (-1.4, 0.25), (-0.8, 0.85), (0.8, 0.95), (1.4, 0.3), (1.9, -0.05)]
    rings = [[(-length / 2 + i * length / 8, y, z + rnd.uniform(-0.03, 0.03)) for y, z in prof] for i in range(9)]
    mb.loft(rings, 'Soil', closed=False, smooth=True, want_out=lambda m: Vector((0, 0, 1)), uv_scale=2.0)
    return mb


def hedge(length=4.0, seed=1):
    mb = MB(f'hedge{seed}'); rnd = random.Random(seed)
    for k in range(int(length / 0.7)):
        s = len(mb.bm.verts); r = rnd.uniform(0.5, 0.75)
        mb.lathe([(0.0, 0.0), (r, 0.15), (r * 1.1, 0.5), (r * 0.8, 0.95), (0.0, 1.15)], 9, 'Leaf', cap_top=False, smooth=True, phase=rnd.random() * 3)
        for v in list(mb.bm.verts)[s:]: v.co += Vector((-length / 2 + 0.4 + k * 0.7, rnd.uniform(-0.15, 0.15), 0.9))
    return mb


def rope(length=6.0, sag=0.45, shide=True):
    mb = MB('rope'); rings = []
    for i in range(25):
        t = i / 24; x = -length / 2 + t * length; z = 1.05 - sag * 4 * t * (1 - t)
        rings.append([(x + 0.0, 0.05 * math.cos(a), z + 0.05 * math.sin(a)) for a in [j * math.pi / 3 for j in range(6)]])
    mb.loft(rings, 'Rope', closed=True, smooth=True, cap0=True, cap1=True, want_out=lambda m: Vector((0, m.y, m.z - 1.0)), uv_scale=0.3)
    if shide:
        for t in (0.2, 0.4, 0.6, 0.8):
            x = -length / 2 + t * length; z = 1.05 - sag * 4 * t * (1 - t)
            for k in range(3): mb.box((x - 0.07, -0.02, z - 0.1 - k * 0.2), (x + 0.07, 0.02, z - 0.02 - k * 0.2 - (0.04 if k == 1 else 0.0)), 'Shide')
    return mb


# ---------------------------------------------------------------- scene
g = bpy.data.objects.new('ground', bpy.data.meshes.new('ground')); sc.collection.objects.link(g)
import bmesh
bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=2, y_segments=2, size=120); bm.to_mesh(g.data); bm.free(); g.data.materials.append(GRASS)
road = bpy.data.objects.new('road', bpy.data.meshes.new('road')); sc.collection.objects.link(road)
bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=1); bm.to_mesh(road.data); bm.free(); road.data.materials.append(ROAD)
road.scale = (2.7, 60, 1); road.location = (0, 0, 0.02)
add(torii_build(), MATS); 
for sx in (-1, 1): add(pier(), MATS, loc=(sx * 4.6, 0, 0))
for sx in (-1, 1):                                              # stone lanterns on the village side (-Y) and the kit lantern posts
    add(modules.toro(), MATS, loc=(sx * 3.4, -4.0, 0), rot=0.0)
# B: palisade on the left, 2 m tall: kit board fence scaled up in height
for i in range(11):
    x = -5.6 - i * 1.82 - 0.91
    add(modules.fence_segment(), MATS, loc=(x, 0, 0), scale=(1, 1, 1.75))
for i in range(12):
    add(modules.fence_post(), MATS, loc=(-5.6 - i * 1.82, 0, 0), scale=(1.15, 1.15, 1.75))
# A: bank + hedge + ditch (right), then C: stones and rope
for i in range(3):
    x = 5.6 + 2.0 + i * 4.0
    add(bank(), MATS, loc=(x, 0, 0)); add(hedge(4.0, i + 1), MATS, loc=(x, 0, 0))
    add(modules_town.embank_curb(), MATS, loc=(x - 1.0, 2.9, 0), rot=0.0); add(modules_town.embank_curb(), MATS, loc=(x + 1.0, 2.9, 0))
    add(modules_town.embank_curb(), MATS, loc=(x - 1.0, 4.3, 0)); add(modules_town.embank_curb(), MATS, loc=(x + 1.0, 4.3, 0))
w = bpy.data.objects.new('water', bpy.data.meshes.new('water')); sc.collection.objects.link(w)
bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=1); bm.to_mesh(w.data); bm.free(); w.data.materials.append(WATER)
w.scale = (6.5, 0.6, 1); w.location = (11.5, 3.6, 0.3)
for i in range(5):
    add(stone_marker(i), MATS, loc=(18.5 + i * 6.0, 0, 0)); 
    if i < 4: add(rope(6.0, 0.45), MATS, loc=(18.5 + i * 6.0 + 3.0, 0, 0.0))
# the lights, sky, camera
sc.render.engine = 'CYCLES'; sc.cycles.samples = 40; sc.cycles.use_denoising = True; sc.render.resolution_x, sc.render.resolution_y = 1600, 900
try: sc.view_settings.view_transform = 'AgX'
except Exception: pass
w_ = bpy.data.worlds.new('W'); w_.use_nodes = True; sc.world = w_
nt = w_.node_tree; sky = nt.nodes.new('ShaderNodeTexSky')
for t in ('MULTIPLE_SCATTERING', 'NISHITA'):
    try: sky.sky_type = t; break
    except Exception: continue
sky.sun_elevation = math.radians(30); sky.sun_rotation = math.radians(200); sky.sun_disc = False
nt.links.new(sky.outputs['Color'], nt.nodes['Background'].inputs['Color']); nt.nodes['Background'].inputs['Strength'].default_value = 0.35
sun = bpy.data.lights.new('S', 'SUN'); sun.energy = 3.2; sun.angle = math.radians(1.5); so = bpy.data.objects.new('S', sun); sc.collection.objects.link(so); so.rotation_euler = (math.radians(55), 0, math.radians(35))
cam = bpy.data.cameras.new('C'); co = bpy.data.objects.new('C', cam); sc.collection.objects.link(co); sc.camera = co
shots = {'gate_front': ((-6, -26, 3.2), (4, 0, 2.6), 30), 'gate_village_side': ((16, 22, 6.5), (6, 0, 1.6), 30), 'border_styles': ((-4, 16, 9.0), (4, 2, 1.0), 26)}
for name, (loc, tgt, lens) in shots.items():
    co.location = loc; cam.lens = lens; co.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(out, name + '.png'); bpy.ops.render.render(write_still=True); print('rendered', name, flush=True)
