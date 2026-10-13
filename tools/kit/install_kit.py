"""Install the Edo kit into your village .blend: kit houses in place of the generated ones, plus the new plaza district.

Run it once from Blender's Text Editor (Open this file, set KIT_PATH below, Run Script). It is safe to run again later:
it replaces the previous kit install each time (kit data, kit houses, district, new roads, new lights).

What it does
  1. removes the previous kit install and appends the current GN_EdoKitHouse / GN_EdoKitVillage (and the KIT_* modules)
  2. makes a kit twin (<name>_KIT, collection KIT_Village) for every GN_EdoHouse house and hides the original
  3. creates EdoKitVillage_01 (the new plaza district: big hall, shops around the plaza, houses, north hamlet, plaza furniture)
  4. creates the district streets as curves with your GN_EdoRibbon group, joined to the existing town streets and trail
  5. hides the old compound village (EdoVillage_01) and its lights, adds warm point lights for the new lanterns

Headless:  python -I tools/kit/install_kit.py <village.blend> <kit/Edo_Kit.blend> --save <out.blend>
"""
import sys, os, json, math, bpy

KIT_PATH = '//kit/Edo_Kit.blend'        # <-- when run inside Blender: path to kit/Edo_Kit.blend
OLD_VILLAGE = 'EdoVillage_01'           # the compound village the district replaces
LIGHTS = True                           # warm point lights at the new lanterns

in_ui = not bpy.app.background
args = [] if in_ui else sys.argv[1:]
save_to = None
if '--save' in args:
    save_to = os.path.abspath(args[args.index('--save') + 1]); args = [a for a in args if a not in ('--save', args[args.index('--save') + 1])]
if in_ui:
    KIT = bpy.path.abspath(KIT_PATH)
else:
    SRC, KIT = os.path.abspath(args[0]), os.path.abspath(args[1])
    bpy.ops.wm.open_mainfile(filepath=SRC)
KIT_DIR = os.path.dirname(KIT)
LAYOUT = json.load(open(os.path.join(KIT_DIR, 'village', 'district_layout.json')))
sc = bpy.context.scene
D = bpy.data


def coll(name, parent=None):
    c = D.collections.get(name) or D.collections.new(name)
    p = parent or sc.collection
    if c.name not in p.children and c not in p.children_recursive and c.name not in [x.name for x in sc.collection.children_recursive]:
        p.children.link(c)
    return c


# ------------------------------------------------------------------ 1. remove the previous kit install, append the new one
for o in list(D.objects):
    if o.name == 'EdoKitVillage_01' or o.name.startswith('KITROAD_') or o.name.startswith('KITLIGHT_'):
        D.objects.remove(o, do_unlink=True)
twins = [o for o in D.objects if o.name.endswith('_KIT')]
for o in twins:
    for m in list(o.modifiers): o.modifiers.remove(m)
for c in list(D.collections):
    if c.name == 'KIT_Modules' or (c.name.startswith('KIT_') and c.name not in ('KIT_Village',)):
        for ob in list(c.objects): D.objects.remove(ob, do_unlink=True)
        D.collections.remove(c)
for n in ('GN_EdoKitVillage', 'GN_EdoKitHouse'):
    if n in D.node_groups: D.node_groups.remove(D.node_groups[n])
for m in [m for m in D.materials if m.name.startswith('M_Edo_')]: D.materials.remove(m)
for im in [i for i in D.images if i.name.startswith('T_Edo_')]: D.images.remove(im)
for me in [m for m in D.meshes if m.name.startswith('SM_Edo_') and m.users == 0]: D.meshes.remove(me)

with D.libraries.load(KIT, link=False) as (df, dt):
    dt.node_groups = ['GN_EdoKitHouse', 'GN_EdoKitVillage']
house_gn, village_gn = D.node_groups['GN_EdoKitHouse'], D.node_groups['GN_EdoKitVillage']
for im in D.images:
    if im.filepath.startswith('//textures'):
        im.filepath = os.path.join(KIT_DIR, im.filepath[2:])
# the district plaza uses your own plaza material, not the kit's placeholder copy
for n in village_gn.nodes:
    if n.bl_idname == 'GeometryNodeSetMaterial':
        mine = D.materials.get('MAT_Edo_Plaza')
        dup = n.inputs['Material'].default_value
        if mine is not None and dup is not None and dup != mine:
            n.inputs['Material'].default_value = mine
            if dup.users == 0: D.materials.remove(dup)
D.materials.get('MAT_Edo_Plaza.001') and D.materials.remove(D.materials['MAT_Edo_Plaza.001'])

hid = {s.name: s.identifier for s in house_gn.interface.items_tree if s.item_type == 'SOCKET' and s.in_out == 'INPUT'}
vid = {s.name: s.identifier for s in village_gn.interface.items_tree if s.item_type == 'SOCKET' and s.in_out == 'INPUT'}

# ------------------------------------------------------------------ 2. kit twins of every generated house
old_gn = D.node_groups.get('GN_EdoHouse')
twin_coll = coll('KIT_Village')
n_twins = 0
if old_gn is not None:
    sid = {s.name: s.identifier for s in old_gn.interface.items_tree if s.item_type == 'SOCKET' and s.in_out == 'INPUT'}
    for o in [o for o in D.objects if any(m.type == 'NODES' and m.node_group == old_gn for m in o.modifiers)]:
        m = next(m for m in o.modifiers if m.type == 'NODES' and m.node_group == old_gn)
        get = lambda k: m.properties.inputs[sid[k]]['value']
        name = o.name + '_KIT'
        k = D.objects.get(name) or D.objects.new(name, D.meshes.new(name))
        if k.name not in twin_coll.objects: twin_coll.objects.link(k)
        k.location = o.location; k.rotation_euler = o.rotation_euler; k.scale = o.scale   # stored values: a hidden object's world matrix can be stale
        km = k.modifiers.new('EdoKitHouse', 'NODES'); km.node_group = house_gn
        params = {n: get(n) for n in ('Ground', 'Bays X', 'Bays Y', 'Floors', 'Roof', 'Engawa', 'Balcony', 'Shopfront', 'Lanterns', 'Gate', 'Fence', 'Seed', 'Props', 'Raise')}
        params['Balcony'] = bool(params['Balcony']) and params['Floors'] >= 2
        for n, v in params.items():
            km.properties.inputs[hid[n]]['value'] = v
        o.hide_viewport = True; o.hide_render = True
        n_twins += 1

# ------------------------------------------------------------------ 3. the district object
cx, cy = LAYOUT['center']
ground = D.objects.get('EDO_Ground_Village') or D.objects.get('EDO_Ground_Town')
dist = D.objects.new('EdoKitVillage_01', D.meshes.new('EdoKitVillage_01'))
dist.location = (cx, cy, 0.0)
dm = dist.modifiers.new('EdoKitVillage', 'NODES'); dm.node_group = village_gn
dm.properties.inputs[vid['Ground']]['value'] = ground
dm.properties.inputs[vid['Plaza Radius']]['value'] = LAYOUT['plaza_radius']
(D.collections.get('EDO_Generator') or sc.collection).objects.link(dist)

# ------------------------------------------------------------------ 4. district streets (your GN_EdoRibbon group)
ribbon = D.node_groups.get('GN_EdoRibbon')
road_coll = D.collections.get('EdoTown_Roads') or sc.collection
town_ground = D.objects.get('EDO_Ground_Town') or ground
n_roads = 0
if ribbon is not None:
    rid = {s.name: s.identifier for s in ribbon.interface.items_tree if s.item_type == 'SOCKET' and s.in_out == 'INPUT'}
    for idx, r in enumerate(LAYOUT['roads']):
        cu = D.curves.new('KITROAD_' + r['name'], 'CURVE'); cu.dimensions = '3D'
        sp = cu.splines.new('POLY'); sp.points.add(len(r['pts']) - 1)
        for p, (x, y) in zip(sp.points, r['pts']): p.co = (x, y, 0.0, 1.0)
        ob = D.objects.new('KITROAD_' + r['name'], cu); road_coll.objects.link(ob)
        rm = ob.modifiers.new('EdoRibbon', 'NODES'); rm.node_group = ribbon
        mat = D.materials.get('MAT_Edo_Road' if r['kind'] == 'road' else 'MAT_Edo_Path')
        for k, v in (('Ground', town_ground), ('Width', r['width']), ('Offset Z', (0.030 + 0.004 * idx) if r['kind'] == 'road' else 0.06), ('Resample', 2.0), ('Material', mat)):   # different heights: overlapping streets must not be coplanar
            rm.properties.inputs[rid[k]]['value'] = v
        n_roads += 1

# ------------------------------------------------------------------ 5. hide the old compound village and its lights, light the new lanterns
old = D.objects.get(OLD_VILLAGE)
if old is not None:
    old.hide_viewport = True; old.hide_render = True
    for m in old.modifiers: m.show_viewport = False; m.show_render = False
lights_old = D.collections.get('EDO_Lights')
if lights_old is not None:
    for o in lights_old.objects: o.hide_viewport = True; o.hide_render = True
n_lights = 0
if LIGHTS:
    dg = bpy.context.evaluated_depsgraph_get(); dg.update()
    lc = coll('EDO_KitLights')
    ld = D.lights.get('EDO_KitLantern') or D.lights.new('EDO_KitLantern', 'POINT')
    ld.color = (1.0, 0.55, 0.2); ld.energy = 60.0; ld.shadow_soft_size = 0.12; ld.use_custom_distance = True; ld.cutoff_distance = 9.0
    for inst in dg.object_instances:
        if inst.is_instance and inst.parent and inst.parent.original == dist and inst.instance_object and inst.instance_object.original.name == 'SM_Edo_Lantern':
            lo = D.objects.new(f'KITLIGHT_{n_lights:03d}', ld); lc.objects.link(lo)
            lo.location = inst.matrix_world @ __import__('mathutils').Vector((0.0, -0.58, 1.95)); n_lights += 1

print(f'kit installed: {n_twins} house twins, district {dist.name} at ({cx}, {cy}), {n_roads} streets, {n_lights} lantern lights; old village hidden')
if save_to:
    bpy.ops.wm.save_as_mainfile(filepath=save_to)
