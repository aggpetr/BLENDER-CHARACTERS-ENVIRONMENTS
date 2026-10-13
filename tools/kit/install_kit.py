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
from mathutils import Vector

KIT_PATH = '//kit/Edo_Kit.blend'        # <-- when run inside Blender: path to kit/Edo_Kit.blend
OLD_VILLAGE = 'EdoVillage_01'           # the compound village the district replaces
LIGHTS = True                           # warm point lights at the new lanterns
VILLAGE_BORDER = True                   # standing stones + sacred rope around the village, torii gates north / west / south, the river is the south border; the river is made wider
TOWN_EXTENSION = True                   # new streets, houses in the marked areas, farmhouses, fields, canal bank, kit bridges and props
CATEGORY_PROPS = True                   # per house type props (kitchen/furnace, forge, herb racks ...) on the kit twins of your town houses

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
ARCH = json.load(open(os.path.join(KIT_DIR, 'archetypes.json')))
LAYOUT = json.load(open(os.path.join(KIT_DIR, 'village', 'district_layout.json')))
TOWN = json.load(open(os.path.join(KIT_DIR, 'village', 'town_layout.json')))
BORDER = json.load(open(os.path.join(KIT_DIR, 'village', 'village_border.json')))
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
    if o.name in ('EdoKitVillage_01', 'EdoKitTown_01', 'EdoKitTownOuter_01', 'EdoKitBorder_01') or o.name.startswith(('KITROAD_', 'KITLIGHT_', 'EdoKitField_', 'KITEMBANK_', 'KITRIVER_')) or \
            (o.name.endswith('_KIT') and o.type == 'MESH' and o.data and o.data.name.startswith('SM_Edo_')):      # kit bridges and props
        D.objects.remove(o, do_unlink=True)
twins = [o for o in D.objects if o.name.endswith('_KIT')]
for o in twins:
    for m in list(o.modifiers): o.modifiers.remove(m)
for c in list(D.collections):
    if c.name == 'KIT_Modules' or (c.name.startswith('KIT_') and c.name not in ('KIT_Village',)):
        for ob in list(c.objects): D.objects.remove(ob, do_unlink=True)
        D.collections.remove(c)
for n in ('GN_EdoKitVillage', 'GN_EdoKitTown', 'GN_EdoKitTownOuter', 'GN_EdoKitField', 'GN_EdoKitEmbank', 'GN_EdoKitBorder', 'GN_EdoKitHouse'):
    if n in D.node_groups: D.node_groups.remove(D.node_groups[n])
for m in [m for m in D.materials if m.name.startswith('M_Edo_')]: D.materials.remove(m)
for im in [i for i in D.images if i.name.startswith('T_Edo_')]: D.images.remove(im)
for me in [m for m in D.meshes if m.name.startswith('SM_Edo_') and m.users == 0]: D.meshes.remove(me)

with D.libraries.load(KIT, link=False) as (df, dt):
    dt.node_groups = ['GN_EdoKitHouse', 'GN_EdoKitVillage', 'GN_EdoKitTown', 'GN_EdoKitTownOuter', 'GN_EdoKitField', 'GN_EdoKitEmbank', 'GN_EdoKitBorder']
    dt.collections = ['KIT_Modules']      # all kit modules (bridges, props, crops, stones too)
house_gn, village_gn = D.node_groups['GN_EdoKitHouse'], D.node_groups['GN_EdoKitVillage']
town_gn, field_gn, embank_gn = D.node_groups['GN_EdoKitTown'], D.node_groups['GN_EdoKitField'], D.node_groups['GN_EdoKitEmbank']
outer_gn = D.node_groups['GN_EdoKitTownOuter']
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
        sig = lambda a: (a['bx'], a['by'], a.get('fl', 1), a['roof'], bool(a.get('eng')), bool(a.get('bal')), bool(a.get('shop')), bool(a.get('lan')), a.get('fence', 0), bool(a.get('gate')))
        mine = (params['Bays X'], params['Bays Y'], params['Floors'], params['Roof'], bool(get('Engawa')), params['Balcony'], bool(get('Shopfront')), bool(get('Lanterns')), params['Fence'], bool(params['Gate']))
        params['Category'] = next((a.get('cat', 0) for a in ARCH.values() if sig(a) == mine), 0) if CATEGORY_PROPS else 0
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


# ------------------------------------------------------------------ 4b. town extension: streets, houses, fields, canal bank, bridges, props
n_town = n_fields = n_br = n_pr = 0
town_obj = outer_obj = None
if TOWN_EXTENSION:
    tground = D.objects.get('EDO_Ground_Town') or ground
    tid = {s.name: s.identifier for s in town_gn.interface.items_tree if s.item_type == 'SOCKET' and s.in_out == 'INPUT'}
    town_obj = D.objects.new('EdoKitTown_01', D.meshes.new('EdoKitTown_01'))
    tm = town_obj.modifiers.new('EdoKitTown', 'NODES'); tm.node_group = town_gn
    tm.properties.inputs[tid['Ground']]['value'] = tground
    (D.collections.get('EDO_Generator') or sc.collection).objects.link(town_obj)
    terrain = D.objects.get('EDO_Terrain') or tground
    outer_obj = D.objects.new('EdoKitTownOuter_01', D.meshes.new('EdoKitTownOuter_01'))      # houses beyond x = 62 stand on the full terrain
    om = outer_obj.modifiers.new('EdoKitTownOuter', 'NODES'); om.node_group = outer_gn
    om.properties.inputs[tid['Ground']]['value'] = terrain
    (D.collections.get('EDO_Generator') or sc.collection).objects.link(outer_obj)
    n_town = len(TOWN['slots'])
    if ribbon is not None:
        for k, r in enumerate(TOWN['roads']):
            cu = D.curves.new('KITROAD_T_' + r['name'], 'CURVE'); cu.dimensions = '3D'
            sp = cu.splines.new('POLY'); sp.points.add(len(r['pts']) - 1)
            for p, (x, y) in zip(sp.points, r['pts']): p.co = (x, y, 0.0, 1.0)
            ob = D.objects.new('KITROAD_T_' + r['name'], cu); road_coll.objects.link(ob)
            rm = ob.modifiers.new('EdoRibbon', 'NODES'); rm.node_group = ribbon
            for kk, v in (('Ground', terrain if (max(p[0] for p in r['pts']) > 62.0 or min(p[0] for p in r['pts']) < -318.0 or max(p[1] for p in r['pts']) > 66.0) else town_ground), ('Width', r['width']), ('Offset Z', 0.030 + 0.004 * (len(LAYOUT['roads']) + k)), ('Resample', 2.0), ('Material', D.materials.get('MAT_Edo_Road'))):
                rm.properties.inputs[rid[kk]]['value'] = v
            n_roads += 1
    # fields: kit crops replace the flat crop meshes (the soil and paddy water meshes stay)
    fid = {s.name: s.identifier for s in field_gn.interface.items_tree if s.item_type == 'SOCKET' and s.in_out == 'INPUT'}
    for f in TOWN['fields']:
        ob = D.objects.new('EdoKitField_' + f['id'], D.meshes.new('EdoKitField_' + f['id'])); ob.location = (f['center'][0], f['center'][1], 0.0)
        fm = ob.modifiers.new('EdoKitField', 'NODES'); fm.node_group = field_gn
        for kk, v in (('Ground', tground), ('Size X', f['size'][0]), ('Size Y', f['size'][1]), ('Crop', f['crop']), ('Seed', f['seed'])):
            fm.properties.inputs[fid[kk]]['value'] = v
        (D.collections.get('EdoTown_Land') or sc.collection).objects.link(ob); n_fields += 1
    for name in ('LD_FieldCrop', 'LD_PaddyCrop'):
        o = D.objects.get(name)
        if o is not None: o.hide_viewport = True; o.hide_render = True
    # canal bank: curb, cobbles and boulders along both sides of the canal
    eid = {s.name: s.identifier for s in embank_gn.interface.items_tree if s.item_type == 'SOCKET' and s.in_out == 'INPUT'}
    cu = D.curves.new('KITEMBANK_Canal', 'CURVE'); cu.dimensions = '3D'
    sp = cu.splines.new('POLY'); sp.points.add(len(TOWN['canal']['pts']) - 1)
    for p, (x, y) in zip(sp.points, TOWN['canal']['pts']): p.co = (x, y, 0.0, 1.0)
    eo = D.objects.new('KITEMBANK_Canal', cu); (D.collections.get('EdoTown_Roads') or sc.collection).objects.link(eo)
    em = eo.modifiers.new('EdoKitEmbank', 'NODES'); em.node_group = embank_gn
    em.properties.inputs[eid['Ground']]['value'] = tground
    em.properties.inputs[eid['Half Width']]['value'] = TOWN['canal']['half_width']
    # kit bridges and props replace the originals (same place, originals hidden)
    dgz = bpy.context.evaluated_depsgraph_get()
    def zat(x, y):
        hit = tground.ray_cast(Vector((x, y, 500.0)), Vector((0, 0, -1)), distance=2000.0, depsgraph=dgz)
        return hit[1].z if hit[0] else 0.0
    bcoll = D.collections.get('EdoTown_Bridges') or sc.collection
    for oname, (mod, (bx_, by_), rotd) in TOWN['bridges'].items():
        orig = D.objects.get(oname); src = D.objects.get(mod)
        if src is None: continue
        half = 9.1 if 'Arch' in mod else 4.6
        ca, sa = math.cos(math.radians(rotd)), math.sin(math.radians(rotd))
        ends = (zat(bx_ + ca * half, by_ + sa * half), zat(bx_ - ca * half, by_ - sa * half))
        z = (min(ends) + 0.05) if 'Arch' in mod else (max(ends) + 0.18)      # the arch sinks into the higher bank, a flat bridge sits on the higher end
        ob = D.objects.new(oname + '_KIT', src.data); ob.location = (bx_, by_, z); ob.rotation_euler = (0, 0, math.radians(rotd)); bcoll.objects.link(ob)
        if orig is not None: orig.hide_viewport = True; orig.hide_render = True
        n_br += 1
    pcoll = D.collections.get('EdoTown_Props') or sc.collection
    for pr in TOWN['props']:
        orig = D.objects.get(pr['name']); src = D.objects.get(pr['module'])
        if orig is None or src is None: continue
        ob = D.objects.new(pr['name'] + '_KIT', src.data); ob.location = orig.location; ob.rotation_euler = orig.rotation_euler; pcoll.objects.link(ob)
        orig.hide_viewport = True; orig.hide_render = True; n_pr += 1


# ------------------------------------------------------------------ 4c. village border and a wider river
n_border = 0
if VILLAGE_BORDER:
    bg = D.node_groups['GN_EdoKitBorder']
    bid = {s.name: s.identifier for s in bg.interface.items_tree if s.item_type == 'SOCKET' and s.in_out == 'INPUT'}
    pts = BORDER['instances']
    me = D.meshes.new('EdoKitBorder_01'); me.vertices.add(len(pts))
    me.vertices.foreach_set('co', [c for r in pts for c in (r[1], r[2], 0.0)])
    ak = me.attributes.new('kind', 'INT', 'POINT'); ak.data.foreach_set('value', [int(r[0]) for r in pts])
    ay = me.attributes.new('yaw', 'FLOAT', 'POINT'); ay.data.foreach_set('value', [float(r[3]) for r in pts])
    ax = me.attributes.new('sx', 'FLOAT', 'POINT'); ax.data.foreach_set('value', [float(r[4]) for r in pts])
    bo = D.objects.new('EdoKitBorder_01', me)
    bm_ = bo.modifiers.new('EdoKitBorder', 'NODES'); bm_.node_group = bg
    bm_.properties.inputs[bid['Ground']]['value'] = D.objects.get('EDO_Terrain') or D.objects.get('EDO_Ground_Town')
    (D.collections.get('EDO_Generator') or sc.collection).objects.link(bo)
    n_border = len(pts)
    river = D.objects.get('WT_Stream')                       # the south border: the river itself, made wider
    if river is not None and ribbon is not None:
        rm_ = next((m for m in river.modifiers if m.type == 'NODES' and m.node_group == ribbon), None)
        if rm_ is not None:
            rm_.properties.inputs[rid['Width']]['value'] = BORDER['river_width_m']
            cu = D.curves.new('KITRIVER_Upper', 'CURVE'); cu.dimensions = '3D'                    # the river continues up into the mountain (own ribbon on the full terrain)
            sp = cu.splines.new('POLY'); up = BORDER['river_upper']; sp.points.add(len(up) - 1)
            for p, (x, y) in zip(sp.points, up): p.co = (x, y, 0.0, 1.0)
            uo = D.objects.new('KITRIVER_Upper', cu); (D.collections.get('EdoTown_Roads') or sc.collection).objects.link(uo)
            um = uo.modifiers.new('EdoRibbon', 'NODES'); um.node_group = ribbon
            for kk in ('Material', 'Offset Z', 'Resample'): um.properties.inputs[rid[kk]]['value'] = rm_.properties.inputs[rid[kk]]['value']
            um.properties.inputs[rid['Ground']]['value'] = D.objects.get('EDO_Terrain') or rm_.properties.inputs[rid['Ground']]['value']
            um.properties.inputs[rid['Width']]['value'] = BORDER['river_upper_width_m']

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
        if inst.is_instance and inst.parent and inst.parent.original in (dist, town_obj, outer_obj) and inst.instance_object and inst.instance_object.original.name == 'SM_Edo_Lantern':
            lo = D.objects.new(f'KITLIGHT_{n_lights:03d}', ld); lc.objects.link(lo)
            lo.location = inst.matrix_world @ __import__('mathutils').Vector((0.0, -0.58, 1.95)); n_lights += 1

print(f'kit installed: {n_twins} house twins, district {dist.name} at ({cx}, {cy}), town extension {n_town} houses, {n_fields} fields, {n_br} bridges, {n_pr} props, {n_roads} streets, border with {n_border} parts, {n_lights} lantern lights; old village hidden')
if save_to:
    bpy.ops.wm.save_as_mainfile(filepath=save_to)
