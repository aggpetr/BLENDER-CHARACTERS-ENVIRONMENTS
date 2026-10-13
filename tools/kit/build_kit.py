"""Build the Edo house kit .blend.

    python -I tools/kit/build_kit.py kit/Edo_Kit.blend        (textures expected in kit/textures, see make_textures.py)
"""
import sys, os, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
import kit_lib, modules, gn_house, district

OUT = os.path.abspath(sys.argv[-1])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.save_as_mainfile(filepath=OUT)          # saved first so '//textures' resolves next to the .blend
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'

kit_lib.make_materials('//textures')
root = bpy.data.collections.new('KIT_Modules'); scene.collection.children.link(root)
report = []
for cname, mbs in modules.build_all().items():
    c = bpy.data.collections.new(cname); root.children.link(c)
    for mb in mbs:
        ob = mb.to_object(c)
        report.append(dict(collection=cname, module=ob.name, tris=kit_lib.tri_count(ob), materials=[m.name for m in ob.data.materials]))
bpy.context.view_layer.layer_collection.children['KIT_Modules'].exclude = True

gn = gn_house.build()
plan = district.plan()
dgroup = district.build_group(gn, plan_data=plan)

# ---------------------------------------------------------------- test houses (dwellA and size variants)
tests = bpy.data.collections.new('KIT_TestHouses'); scene.collection.children.link(tests)
def ground(name, size, loc, tilt_deg=0.0):
    me = bpy.data.meshes.new(name)
    s = size / 2
    me.from_pydata([(-s, -s, 0), (s, -s, 0), (s, s, 0), (-s, s, 0)], [], [(0, 1, 2, 3)])
    ob = bpy.data.objects.new(name, me); tests.objects.link(ob)
    ob.location = loc; ob.rotation_euler = (math.radians(tilt_deg), 0, 0)
    return ob
flat = ground('TEST_Ground_Flat', 700, (0, 150, 0))
slope = ground('TEST_Ground_Slope', 60, (0, 80, 0), tilt_deg=8.0)

def house(name, loc, ground_ob, **kw):
    me = bpy.data.meshes.new(name); ob = bpy.data.objects.new(name, me); tests.objects.link(ob)
    ob.location = loc
    m = ob.modifiers.new('EdoKitHouse', 'NODES'); m.node_group = gn
    ids = {s.name: s.identifier for s in gn.interface.items_tree if s.item_type == 'SOCKET' and s.in_out == 'INPUT'}
    m.properties.inputs[ids['Ground']]['value'] = ground_ob
    for k, v in kw.items():
        m.properties.inputs[ids[k]]['value'] = v
    return ob

dwellA = dict(**{'Bays X': 4, 'Bays Y': 3, 'Floors': 1, 'Roof': 1, 'Engawa': True, 'Fence': 1, 'Props': 1.0, 'Seed': 7})
house('TEST_dwellA_4x3', (0, 0, 0), flat, **dwellA)
house('TEST_3x3', (-22, 0, 0), flat, **{**dwellA, 'Bays X': 3, 'Seed': 3})
house('TEST_5x3', (24, 0, 0), flat, **{**dwellA, 'Bays X': 5, 'Seed': 11})
house('TEST_dwellA_slope', (0, 80, 0), slope, **dwellA)
house('TEST_3x4_rotatedRidge', (0, -26, 0), flat, **{**dwellA, 'Bays X': 3, 'Bays Y': 4, 'Engawa': False, 'Fence': 0})

# all 17 original house types with their original parameters (analysis/KIT_ANALYSIS.md)
from archetypes import ARCH
for i, (name, a) in enumerate(ARCH.items()):
    house(f'ARCH_{name}', (-96 + (i % 5) * 48, 120 + (i // 5) * 48, 0), flat,
          **{'Bays X': a['bx'], 'Bays Y': a['by'], 'Floors': a.get('fl', 1), 'Roof': a['roof'], 'Engawa': bool(a.get('eng')),
             'Balcony': bool(a.get('bal')), 'Shopfront': bool(a.get('shop')), 'Lanterns': bool(a.get('lan')),
             'Fence': a.get('fence', 0), 'Gate': bool(a.get('gate')), 'Props': 0.6, 'Seed': 10 + i})
json.dump(ARCH, open(os.path.join(os.path.dirname(OUT), 'archetypes.json'), 'w'), indent=1)

# district test: the whole plaza district on its own flat ground
dg_ground = ground('TEST_Ground_District', 400, (0, 900, 0))
dobj = bpy.data.objects.new('DISTRICT_TEST', bpy.data.meshes.new('DISTRICT_TEST')); tests.objects.link(dobj)
dobj.location = (0, 900, 0)
dm = dobj.modifiers.new('EdoKitVillage', 'NODES'); dm.node_group = dgroup
did = {x.name: x.identifier for x in dgroup.interface.items_tree if x.item_type == 'SOCKET' and x.in_out == 'INPUT'}
dm.properties.inputs[did['Ground']]['value'] = dg_ground
os.makedirs(os.path.join(os.path.dirname(OUT), 'village'), exist_ok=True)
json.dump(district.to_json(plan), open(os.path.join(os.path.dirname(OUT), 'village', 'district_layout.json'), 'w'), indent=1)

bpy.ops.wm.save_as_mainfile(filepath=OUT, relative_remap=True)
json.dump(report, open(os.path.join(os.path.dirname(OUT), 'module_report.json'), 'w'), indent=1)
for r in report:
    print(f"{r['collection']:16s} {r['module']:28s} {r['tris']:6d} tris  {','.join(m.replace('M_Edo_', '') for m in r['materials'])}")
print('saved', OUT)
