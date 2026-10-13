"""Export the district ground meshes (plaza + the new streets) as FBX for Unreal.

Run in your village .blend after install_kit.py (in Blender: Text Editor, Run Script; or headless):
    python -I tools/kit/export_district_ground.py <village.blend> <out_dir>

Writes <out_dir>/SM_Edo_District_Plaza.fbx and <out_dir>/SM_Edo_District_Roads.fbx in world space (place them at the
origin in Unreal). Material slots: MAT_Edo_Plaza, MAT_Edo_Road, MAT_Edo_Path.
"""
import sys, os, bpy, bmesh, addon_utils

in_ui = not bpy.app.background
if in_ui:
    OUT = bpy.path.abspath('//kit_village_out/district')
else:
    bpy.ops.wm.open_mainfile(filepath=os.path.abspath(sys.argv[1])); OUT = os.path.abspath(sys.argv[2])
os.makedirs(OUT, exist_ok=True)
addon_utils.enable('io_scene_fbx', default_set=True)
D = bpy.data; sc = bpy.context.scene
dg = bpy.context.evaluated_depsgraph_get(); dg.update()
FBX = dict(use_selection=True, apply_unit_scale=True, apply_scale_options='FBX_SCALE_ALL', mesh_smooth_type='FACE',
           use_tspace=False, add_leaf_bones=False, path_mode='STRIP', object_types={'MESH'}, use_mesh_modifiers=False)


def export(name, mats, parts):
    """parts: list of (evaluated object, material index). Builds one mesh in world space."""
    bm = bmesh.new()
    for eo, mi in parts:
        me = D.meshes.new_from_object(eo, preserve_all_data_layers=False, depsgraph=dg)
        me.transform(eo.matrix_world)
        for p in me.polygons: p.material_index = mi
        bm.from_mesh(me); D.meshes.remove(me)
    out = D.meshes.new(name); bm.to_mesh(out); bm.free()
    for m in mats: out.materials.append(m)
    ob = D.objects.new(name, out); sc.collection.objects.link(ob)
    for o in bpy.context.view_layer.objects: o.select_set(False)
    ob.select_set(True); bpy.context.view_layer.objects.active = ob
    path = os.path.join(OUT, name + '.fbx'); bpy.ops.export_scene.fbx(filepath=path, **FBX)
    n = sum(len(p.vertices) - 2 for p in out.polygons)
    sc.collection.objects.unlink(ob); print(f'{name}: {n} triangles -> {path}')


dist = D.objects['EdoKitVillage_01']
export('SM_Edo_District_Plaza', [D.materials['MAT_Edo_Plaza']], [(dist.evaluated_get(dg), 0)])
roads = [o for o in D.objects if o.name.startswith('KITROAD_')]
rm, pm = D.materials['MAT_Edo_Road'], D.materials['MAT_Edo_Path']
export('SM_Edo_District_Roads', [rm, pm], [(o.evaluated_get(dg), 0 if rm in [m for m in o.evaluated_get(dg).data.materials] or True else 1) for o in roads if 'TRAIL' not in o.name]
       + [(o.evaluated_get(dg), 1) for o in roads if 'TRAIL' in o.name])
# ---- the original town ground surfaces: streets and trails, canal / stream water, plazas, field soil (world space, flat colour materials in Unreal)
def mat(name):
    return D.materials.get(name) or D.materials.new(name)
orig_roads = [o for o in D.objects if o.type == 'CURVE' and o.name.startswith('RD_')]
orig_paths = [o for o in D.objects if o.type == 'CURVE' and o.name.startswith('PATH_')]
if orig_roads or orig_paths:
    export('SM_Edo_Town_Roads', [rm, pm], [(o.evaluated_get(dg), 0) for o in orig_roads] + [(o.evaluated_get(dg), 1) for o in orig_paths])
water = [o for o in D.objects if o.type == 'CURVE' and o.name.startswith('WT_')]
paddy = [D.objects[n] for n in ('LD_PaddyWater',) if n in D.objects]
if water or paddy:
    export('SM_Edo_Water', [mat('MAT_Edo_Water'), mat('MAT_Edo_PaddyWater')], [(o.evaluated_get(dg), 0) for o in water] + [(o.evaluated_get(dg), 1) for o in paddy])
plazas = [D.objects[n] for n in ('LD_Plaza1', 'LD_Plaza2') if n in D.objects]
if plazas:
    export('SM_Edo_Town_Plazas', [mat('MAT_Edo_Plaza')], [(o.evaluated_get(dg), 0) for o in plazas])
soil = [D.objects[n] for n in ('LD_FieldSoil',) if n in D.objects]
if soil:
    export('SM_Edo_Town_FieldSoil', [mat('MAT_Edo_FieldSoil')], [(o.evaluated_get(dg), 0) for o in soil])
