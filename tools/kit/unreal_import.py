"""Unreal Engine 5 editor script: import the Edo house kit and (optionally) rebuild the village.

UNTESTED (written without access to Unreal). Run it in the Unreal Editor: Tools > Execute Python Script
(enable the "Python Editor Script Plugin" first). Edit the settings below first.

What it does
  1. imports kit/textures (BaseColor sRGB, Normal_DX as normal map, ORM as masks)
  2. creates the master material M_EdoKit_Master (BaseColor, Normal, ORM, optional up-facing moss, emissive)
     and one instance MI_Edo_<Set> per texture set
  3. imports every kit/export/modules/**.fbx as a Nanite static mesh with its UCX_ collision, assigns MI_Edo_* by slot name
  4. imports the plaza district ground (plaza + new streets) from kit/export/district and places it at the origin
  5. optional: places houses from kit/village/village_manifest.json (one StaticMeshActor per module instance, grouped in
     World Outliner folders per house: DISTRICT_* = the new plaza district, TWN_*/FARM_*/MT_*/K_* = the town) and a point
     light at every lantern

Coordinates: the manifest is Blender world space in metres (Z up, right-handed). Unreal = (x, -y, z) * 100 cm, yaw = -z rotation.
Bring your terrain over from Blender with the same world origin so the houses sit on it.
"""
import os, json, fnmatch, unreal

KIT_DIR = r'C:/path/to/BLENDER-CHARACTERS-ENVIRONMENTS/kit'   # <-- set this
DEST = '/Game/EdoKit'
IMPORT_TEXTURES = True
IMPORT_MESHES = True
IMPORT_DISTRICT_GROUND = True  # the new plaza district: plaza + streets meshes from kit/export/district/*.fbx
PLACE_GROUND = True            # put the plaza and street meshes at the world origin (they are exported in world space)
PLACE_VILLAGE = False          # place the houses from the manifest as actors (25,000 module actors for everything: start small)
HOUSES = ['DISTRICT_*', 'TOWN_*', 'BRIDGE_*', 'PROP_*']   # fnmatch patterns on house names in the manifest, e.g. ['DISTRICT_*'], ['TWN_1*', 'DISTRICT_HALL'], None = all
PLACE_FIELDS = False           # crops, paddies and canal bank from village/fields_manifest.json (about 50,000 instances, always instanced)
LANTERN_LIGHTS = 'clustered'   # 'clustered' (about 30 real lights, recommended), 'all' (one point light per lantern, about 100) or False
PLACE_AS = 'instances'         # 'instances': hierarchical instanced meshes per module and 128 m cell (about 1,200 actors for the houses), 'actors': one actor per module instance (40,000+, slow)
CELL_M = 128.0                 # cell size (m) for the instanced actors = the default World Partition cell (12800 cm)

MOSS = {'Kawara': 0.50, 'Stone': 0.38, 'Timber': 0.10, 'Planks': 0.08, 'Thatch': 0.30, 'StoneWall': 0.40}
EMISSIVE = {'Lantern': 6.0}

tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
eal = unreal.EditorAssetLibrary
log = unreal.log


def import_file(path, dest, options=None, name=None):
    t = unreal.AssetImportTask()
    t.set_editor_property('filename', path)
    t.set_editor_property('destination_path', dest)
    if name: t.set_editor_property('destination_name', name)
    t.set_editor_property('automated', True)
    t.set_editor_property('replace_existing', True)
    t.set_editor_property('save', True)
    if options is not None: t.set_editor_property('options', options)
    tools.import_asset_tasks([t])
    paths = list(t.get_editor_property('imported_object_paths') or [])
    return unreal.load_asset(paths[0]) if paths else None


# ------------------------------------------------------------------ textures
tex_root = os.path.join(KIT_DIR, 'textures')
sets = sorted(d for d in os.listdir(tex_root) if d.startswith('T_Edo_'))
textures = {}
if IMPORT_TEXTURES:
    for s in sets:
        name = s[len('T_Edo_'):]
        for kind in ('BaseColor', 'Normal_DX', 'ORM'):
            f = os.path.join(tex_root, s, kind + '.jpg')
            if not os.path.exists(f): continue
            tex = import_file(f, f'{DEST}/Textures/{s}', name=f'{s}_{kind}')
            if tex is None: unreal.log_warning(f'texture import failed: {f}'); continue
            if kind == 'Normal_DX':
                tex.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_NORMALMAP)
                tex.set_editor_property('srgb', False)
            elif kind == 'ORM':
                tex.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_MASKS)
                tex.set_editor_property('srgb', False)
            eal.save_loaded_asset(tex)
            textures[(name, kind)] = tex
else:
    for s in sets:
        for kind in ('BaseColor', 'Normal_DX', 'ORM'):
            a = unreal.load_asset(f'{DEST}/Textures/{s}/{s}_{kind}')
            if a: textures[(s[len('T_Edo_'):], kind)] = a


# ------------------------------------------------------------------ master material + instances
def master_material():
    path = f'{DEST}/Materials/M_EdoKit_Master'
    if eal.does_asset_exist(path):
        return unreal.load_asset(path)
    m = tools.create_asset('M_EdoKit_Master', f'{DEST}/Materials', unreal.Material, unreal.MaterialFactoryNew())
    def tparam(name, x, y, sampler):
        e = mel.create_material_expression(m, unreal.MaterialExpressionTextureSampleParameter2D, x, y)
        e.set_editor_property('parameter_name', name); e.set_editor_property('sampler_type', sampler)
        return e
    def sparam(name, value, x, y):
        e = mel.create_material_expression(m, unreal.MaterialExpressionScalarParameter, x, y)
        e.set_editor_property('parameter_name', name); e.set_editor_property('default_value', value)
        return e
    col = tparam('BaseColor', -900, -200, unreal.MaterialSamplerType.SAMPLERTYPE_COLOR)
    nrm = tparam('Normal', -900, 300, unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    orm = tparam('ORM', -900, 50, unreal.MaterialSamplerType.SAMPLERTYPE_MASKS)
    base = col
    try:   # up-facing moss, broken up by world-space noise (same idea as the Blender preview)
        moss = tparam('MossColor', -900, -500, unreal.MaterialSamplerType.SAMPLERTYPE_COLOR)
        amount = sparam('MossAmount', 0.0, -700, -700)
        nws = mel.create_material_expression(m, unreal.MaterialExpressionVertexNormalWS, -900, -800)
        mask = mel.create_material_expression(m, unreal.MaterialExpressionComponentMask, -750, -800)
        mask.set_editor_property('r', False); mask.set_editor_property('g', False); mask.set_editor_property('b', True)
        sub = mel.create_material_expression(m, unreal.MaterialExpressionSubtract, -600, -800); sub.set_editor_property('const_b', 0.35)
        mul = mel.create_material_expression(m, unreal.MaterialExpressionMultiply, -480, -800); mul.set_editor_property('const_b', 1.7)
        noise = mel.create_material_expression(m, unreal.MaterialExpressionNoise, -600, -950); noise.set_editor_property('scale', 0.006)
        mul2 = mel.create_material_expression(m, unreal.MaterialExpressionMultiply, -360, -850)
        mul3 = mel.create_material_expression(m, unreal.MaterialExpressionMultiply, -240, -800)
        sat = mel.create_material_expression(m, unreal.MaterialExpressionSaturate, -120, -800)
        lerp = mel.create_material_expression(m, unreal.MaterialExpressionLinearInterpolate, -200, -300)
        mel.connect_material_expressions(nws, '', mask, '')
        mel.connect_material_expressions(mask, '', sub, 'A')
        mel.connect_material_expressions(sub, '', mul, 'A')
        mel.connect_material_expressions(mul, '', mul2, 'A'); mel.connect_material_expressions(noise, '', mul2, 'B')
        mel.connect_material_expressions(mul2, '', mul3, 'A'); mel.connect_material_expressions(amount, '', mul3, 'B')
        mel.connect_material_expressions(mul3, '', sat, '')
        mel.connect_material_expressions(col, 'RGB', lerp, 'A'); mel.connect_material_expressions(moss, 'RGB', lerp, 'B')
        mel.connect_material_expressions(sat, '', lerp, 'Alpha')
        base = lerp
        mel.connect_material_property(lerp, '', unreal.MaterialProperty.MP_BASE_COLOR)
    except Exception as e:
        unreal.log_warning(f'moss layer skipped: {e}')
        mel.connect_material_property(col, 'RGB', unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(nrm, 'RGB', unreal.MaterialProperty.MP_NORMAL)
    mel.connect_material_property(orm, 'R', unreal.MaterialProperty.MP_AMBIENT_OCCLUSION)
    mel.connect_material_property(orm, 'G', unreal.MaterialProperty.MP_ROUGHNESS)
    mel.connect_material_property(orm, 'B', unreal.MaterialProperty.MP_METALLIC)
    em = sparam('EmissiveStrength', 0.0, -500, 500)
    emul = mel.create_material_expression(m, unreal.MaterialExpressionMultiply, -250, 450)
    mel.connect_material_expressions(col, 'RGB', emul, 'A'); mel.connect_material_expressions(em, '', emul, 'B')
    mel.connect_material_property(emul, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.recompile_material(m); eal.save_loaded_asset(m)
    return m


master = master_material()
instances = {}
for s in sets:
    name = s[len('T_Edo_'):]
    path = f'{DEST}/Materials/MI_Edo_{name}'
    mi = unreal.load_asset(path) if eal.does_asset_exist(path) else tools.create_asset(
        f'MI_Edo_{name}', f'{DEST}/Materials', unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    mi.set_editor_property('parent', master)
    for kind, param in (('BaseColor', 'BaseColor'), ('Normal_DX', 'Normal'), ('ORM', 'ORM')):
        if (name, kind) in textures:
            mel.set_material_instance_texture_parameter_value(mi, param, textures[(name, kind)])
    if name in MOSS and ('Moss', 'BaseColor') in textures:
        mel.set_material_instance_texture_parameter_value(mi, 'MossColor', textures[('Moss', 'BaseColor')])
        mel.set_material_instance_scalar_parameter_value(mi, 'MossAmount', MOSS[name])
    if name in EMISSIVE:
        mel.set_material_instance_scalar_parameter_value(mi, 'EmissiveStrength', EMISSIVE[name])
    eal.save_loaded_asset(mi)
    instances[f'M_Edo_{name}'] = mi


# ------------------------------------------------------------------ meshes
meshes = {}
mod_root = os.path.join(KIT_DIR, 'export', 'modules')
for coll in sorted(os.listdir(mod_root)):
    for f in sorted(os.listdir(os.path.join(mod_root, coll))):
        if not f.endswith('.fbx'): continue
        mname = f[:-4]; dest = f'{DEST}/Meshes/{coll}'
        if IMPORT_MESHES:
            ui = unreal.FbxImportUI()
            ui.set_editor_property('import_mesh', True)
            ui.set_editor_property('import_as_skeletal', False)
            ui.set_editor_property('import_materials', False)
            ui.set_editor_property('import_textures', False)
            ui.set_editor_property('mesh_type_to_import', unreal.FBXImportType.FBXIT_STATIC_MESH)
            sm = ui.get_editor_property('static_mesh_import_data')
            for k, v in (('combine_meshes', True), ('auto_generate_collision', False), ('generate_lightmap_u_vs', False),
                         ('build_nanite', True), ('import_uniform_scale', 1.0)):
                try: sm.set_editor_property(k, v)
                except Exception as e: unreal.log_warning(f'import option {k}: {e}')
            mesh = import_file(os.path.join(mod_root, coll, f), dest, ui, mname)
        else:
            mesh = unreal.load_asset(f'{dest}/{mname}')
        if mesh is None:
            unreal.log_warning(f'mesh import failed: {f}'); continue
        try:
            ns = mesh.get_editor_property('nanite_settings'); ns.set_editor_property('enabled', True)
            mesh.set_editor_property('nanite_settings', ns)
        except Exception as e:
            unreal.log_warning(f'nanite setting on {mname}: {e}')
        for i, slot in enumerate(mesh.get_editor_property('static_materials')):
            mi = instances.get(str(slot.get_editor_property('material_slot_name')))
            if mi: mesh.set_material(i, mi)
        eal.save_loaded_asset(mesh)
        meshes[mname] = mesh
log(f'EdoKit: {len(meshes)} meshes, {len(instances)} material instances')


# ------------------------------------------------------------------ district ground (plaza + streets)
def color_material(name, rgb, rough=0.9):
    path = f'{DEST}/Materials/{name}'
    if eal.does_asset_exist(path):
        return unreal.load_asset(path)
    m = tools.create_asset(name, f'{DEST}/Materials', unreal.Material, unreal.MaterialFactoryNew())
    c = mel.create_material_expression(m, unreal.MaterialExpressionConstant3Vector, -400, 0)
    c.set_editor_property('constant', unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0))
    mel.connect_material_property(c, '', unreal.MaterialProperty.MP_BASE_COLOR)
    r = mel.create_material_expression(m, unreal.MaterialExpressionConstant, -400, 200)
    r.set_editor_property('r', rough)
    mel.connect_material_property(r, '', unreal.MaterialProperty.MP_ROUGHNESS)
    mel.recompile_material(m); eal.save_loaded_asset(m)
    return m


if IMPORT_DISTRICT_GROUND:
    ground_dir = os.path.join(KIT_DIR, 'export', 'district')
    ground_mats = {'MAT_Edo_Plaza': color_material('M_Edo_Plaza', (0.52, 0.46, 0.34)),
                   'MAT_Edo_Road': color_material('M_Edo_Road', (0.42, 0.34, 0.24)),
                   'MAT_Edo_Path': color_material('M_Edo_Path', (0.38, 0.30, 0.20)),
                   'MAT_Edo_Water': color_material('M_Edo_Water', (0.10, 0.22, 0.30), 0.15),          # flat placeholders: replace water with the Water plugin or a water material
                   'MAT_Edo_PaddyWater': color_material('M_Edo_PaddyWater', (0.12, 0.25, 0.22), 0.15),
                   'MAT_Edo_FieldSoil': color_material('M_Edo_FieldSoil', (0.16, 0.10, 0.06))}
    ground_actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if os.path.isdir(ground_dir):
        for f in sorted(os.listdir(ground_dir)):
            if not f.endswith('.fbx'): continue
            ui = unreal.FbxImportUI()
            ui.set_editor_property('import_mesh', True); ui.set_editor_property('import_materials', False)
            ui.set_editor_property('import_textures', False); ui.set_editor_property('import_as_skeletal', False)
            ui.set_editor_property('mesh_type_to_import', unreal.FBXImportType.FBXIT_STATIC_MESH)
            sm = ui.get_editor_property('static_mesh_import_data')
            for k, v in (('combine_meshes', True), ('auto_generate_collision', False), ('generate_lightmap_u_vs', False), ('build_nanite', True)):
                try: sm.set_editor_property(k, v)
                except Exception as e: unreal.log_warning(f'import option {k}: {e}')
            mesh = import_file(os.path.join(ground_dir, f), f'{DEST}/Meshes/District', ui, f[:-4])
            if mesh is None:
                unreal.log_warning(f'district mesh import failed: {f}'); continue
            for i, slot in enumerate(mesh.get_editor_property('static_materials')):
                mi = ground_mats.get(str(slot.get_editor_property('material_slot_name')))
                if mi: mesh.set_material(i, mi)
            eal.save_loaded_asset(mesh)
            if PLACE_GROUND:
                a = ground_actors.spawn_actor_from_object(mesh, unreal.Vector(0, 0, 0))
                a.set_folder_path('EdoVillage/DistrictGround')
        log('EdoKit: district ground imported')
    else:
        unreal.log_warning(f'no district ground folder: {ground_dir}')


# ------------------------------------------------------------------ placement
actors_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
_warned = set()


def to_ue(x, y, z):
    return unreal.Vector(x * 100.0, -y * 100.0, z * 100.0)           # Blender (x, y, z) m -> Unreal (x, -y, z) cm


def instanced_actor(label, folder, mesh, rows):
    """One actor with a hierarchical instanced mesh. rows: [x, y, z, yaw_deg, sx, sy, sz] in Blender metres / degrees."""
    a = actors_sub.spawn_actor_from_class(unreal.Actor, unreal.Vector(0, 0, 0))
    comp = a.add_component_by_class(unreal.HierarchicalInstancedStaticMeshComponent, False, unreal.Transform(), False)
    comp.set_static_mesh(mesh)
    tf = [unreal.Transform(to_ue(r[0], r[1], r[2]), unreal.Rotator(roll=0.0, pitch=0.0, yaw=-r[3]), unreal.Vector(r[4], r[5], r[6])) for r in rows]
    try:
        comp.add_instances(tf, should_return_indices=False)
    except Exception:
        for t in tf: comp.add_instance(t)
    a.set_actor_label(label); a.set_folder_path(folder)
    return a


def place_rows(label, folder, mesh, rows):
    """rows -> instanced actors per CELL_M square, or one StaticMeshActor per row when PLACE_AS = 'actors' or instancing fails."""
    if PLACE_AS == 'instances':
        try:
            cells = {}
            for r in rows: cells.setdefault((int(r[0] // CELL_M), int(r[1] // CELL_M)), []).append(r)
            for (cx, cy), rs in cells.items():
                instanced_actor(f'{label}_{cx}_{cy}', folder, mesh, rs)
            return len(cells)
        except Exception as e:
            if 'inst' not in _warned: unreal.log_warning(f'instanced placement failed ({e}); using one actor per module'); _warned.add('inst')
    for r in rows:
        a = actors_sub.spawn_actor_from_object(mesh, to_ue(r[0], r[1], r[2]), unreal.Rotator(roll=0.0, pitch=0.0, yaw=-r[3]))
        a.set_actor_scale3d(unreal.Vector(r[4], r[5], r[6])); a.set_folder_path(folder)
    return len(rows)


if PLACE_VILLAGE:
    man = json.load(open(os.path.join(KIT_DIR, 'village', 'village_manifest.json')))
    per_module = {}
    n_mod = 0
    for h in man['houses']:
        if HOUSES and not any(fnmatch.fnmatch(h['house'], pat) for pat in HOUSES): continue
        for m in h['modules']:
            x, y, z = m['location']
            per_module.setdefault(m['module'], []).append([x, y, z, m['rotation_deg'][2], *m['scale']]); n_mod += 1
    n_actors = 0
    for mname, rows in per_module.items():
        mesh = meshes.get(mname)
        if mesh is None: unreal.log_warning(f'no mesh for module {mname}'); continue
        n_actors += place_rows(f'EdoKit_{mname}', 'EdoVillage/Houses', mesh, rows)
    log(f'EdoKit: placed {n_mod} module instances in {n_actors} actors')

# ------------------------------------------------------------------ lights: lantern glow is the emissive material; a few real lights give the warmth
if PLACE_VILLAGE and LANTERN_LIGHTS:
    def add_light(x, y, z, intensity, radius, folder):
        l = actors_sub.spawn_actor_from_class(unreal.PointLight, to_ue(x, y, z))
        c = l.get_component_by_class(unreal.PointLightComponent)
        c.set_editor_property('intensity', intensity); c.set_editor_property('attenuation_radius', radius)
        c.set_editor_property('light_color', unreal.Color(255, 160, 80, 255))
        try: c.set_editor_property('cast_shadows', False)
        except Exception: pass
        l.set_folder_path(folder)
    n = 0
    if LANTERN_LIGHTS == 'clustered':
        lp = os.path.join(KIT_DIR, 'village', 'lights_clustered.json')
        if os.path.exists(lp):
            for L in json.load(open(lp))['lights']:
                add_light(L['x'], L['y'], L['z'], 6.0 * L['count'] ** 0.5, 400.0 + 120.0 * L['radius'], 'EdoVillage/Lights'); n += 1
        else:
            unreal.log_warning(f'{lp} not found: run tools/kit/cluster_lights.py')
    else:
        for h in man['houses']:
            if HOUSES and not any(fnmatch.fnmatch(h['house'], pat) for pat in HOUSES): continue
            for x, y, z in h['lantern_lights']:
                add_light(x, y, z, 6.0, 900.0, 'EdoVillage/Lights'); n += 1
    log(f'EdoKit: {n} lantern lights ({LANTERN_LIGHTS})')

# ------------------------------------------------------------------ fields and canal bank (instanced)
if PLACE_FIELDS:
    fm = json.load(open(os.path.join(KIT_DIR, 'village', 'fields_manifest.json')))
    merged = {}
    for oname, per in fm['objects'].items():
        for mname, rows in per.items():
            merged.setdefault(mname, []).extend(rows)
    total = 0
    for mname, rows in merged.items():
        mesh = meshes.get(mname)
        if mesh is None: unreal.log_warning(f'no mesh for {mname}'); continue
        saved = PLACE_AS
        PLACE_AS = 'instances'
        place_rows(f'EdoKit_{mname}', 'EdoVillage/Fields', mesh, rows); total += len(rows)
        PLACE_AS = saved
    log(f'EdoKit: {total} field and canal bank instances')
