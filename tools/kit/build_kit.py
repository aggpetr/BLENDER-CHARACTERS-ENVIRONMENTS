"""Build the Edo house kit .blend.

    python -I tools/kit/build_kit.py kit/Edo_Kit.blend        (textures expected in kit/textures, see make_textures.py)
"""
import sys, os, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
import kit_lib, modules, gn_house

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
ARCH = {
    'kura':      dict(bx=2, by=2, fl=2, roof=3),
    'shopA':     dict(bx=3, by=3, roof=1, shop=1, lan=1),
    'dwellA':    dict(bx=4, by=3, roof=1, eng=1, fence=1),
    'farmhouse': dict(bx=5, by=3, roof=2, eng=1, fence=1),
    'dwellB':    dict(bx=4, by=3, fl=2, roof=3, bal=1, fence=1),
    'barn':      dict(bx=3, by=4, roof=2),
    'dwellC':    dict(bx=3, by=3, roof=3, eng=1, fence=1),
    'hutB':      dict(bx=4, by=3, roof=2, eng=1, lan=1, fence=1),
    'restA':     dict(bx=5, by=4, roof=1, shop=1, eng=1, lan=1),
    'shopB':     dict(bx=3, by=4, fl=2, roof=3, shop=1, bal=1, lan=1),
    'tea':       dict(bx=3, by=3, roof=2, eng=1, lan=1),
    'hutA':      dict(bx=3, by=3, roof=2, eng=1, fence=1),
    'hutC':      dict(bx=3, by=2, roof=2),
    'inn':       dict(bx=9, by=6, fl=2, roof=1, eng=1, bal=1, lan=1, gate=1, fence=2),
    'restB':     dict(bx=6, by=4, fl=2, roof=3, shop=1, bal=1, lan=1),
    'row':       dict(bx=7, by=2, roof=3),
    'EdoHouse01': dict(bx=4, by=3, fl=2, roof=1, fence=1),
}
for i, (name, a) in enumerate(ARCH.items()):
    house(f'ARCH_{name}', (-96 + (i % 5) * 48, 120 + (i // 5) * 48, 0), flat,
          **{'Bays X': a['bx'], 'Bays Y': a['by'], 'Floors': a.get('fl', 1), 'Roof': a['roof'], 'Engawa': bool(a.get('eng')),
             'Balcony': bool(a.get('bal')), 'Shopfront': bool(a.get('shop')), 'Lanterns': bool(a.get('lan')),
             'Fence': a.get('fence', 0), 'Gate': bool(a.get('gate')), 'Props': 0.6, 'Seed': 10 + i})
json.dump(ARCH, open(os.path.join(os.path.dirname(OUT), 'archetypes.json'), 'w'), indent=1)

bpy.ops.wm.save_as_mainfile(filepath=OUT, relative_remap=True)
json.dump(report, open(os.path.join(os.path.dirname(OUT), 'module_report.json'), 'w'), indent=1)
for r in report:
    print(f"{r['collection']:16s} {r['module']:28s} {r['tris']:6d} tris  {','.join(m.replace('M_Edo_', '') for m in r['materials'])}")
print('saved', OUT)
