"""Export every kit module (and a merged test house) to FBX for Unreal Engine.

    python -I tools/kit/export_fbx.py <kit.blend> <out_dir>

One FBX per module, object at the origin, metric scale (Unreal imports 1 m = 100 cm), smoothing groups and tangents
included, no texture paths. Materials are referenced by name (M_Edo_*); textures are imported separately.
"""
import sys, os, json, bpy, addon_utils

kit, out = os.path.abspath(sys.argv[-2]), os.path.abspath(sys.argv[-1])
os.makedirs(out, exist_ok=True)
addon_utils.enable('io_scene_fbx', default_set=True)
bpy.ops.wm.open_mainfile(filepath=kit)
sc = bpy.context.scene
FBX = dict(use_selection=True, apply_unit_scale=True, apply_scale_options='FBX_SCALE_ALL', mesh_smooth_type='FACE',
           use_tspace=True, add_leaf_bones=False, path_mode='STRIP', object_types={'MESH'}, use_mesh_modifiers=True)

def export(ob, path):
    tmp = ob.name not in sc.collection.objects
    if tmp: sc.collection.objects.link(ob)
    for o in bpy.context.view_layer.objects: o.select_set(False)
    ob.select_set(True); bpy.context.view_layer.objects.active = ob
    bpy.ops.export_scene.fbx(filepath=path, **FBX)
    if tmp: sc.collection.objects.unlink(ob)

manifest = []
for c in bpy.data.collections['KIT_Modules'].children:
    for ob in sorted(c.objects, key=lambda o: o.name):
        p = os.path.join(out, 'modules', c.name, ob.name + '.fbx'); os.makedirs(os.path.dirname(p), exist_ok=True)
        export(ob, p)
        manifest.append(dict(collection=c.name, module=ob.name, file=os.path.relpath(p, out),
                             tris=sum(len(q.vertices) - 2 for q in ob.data.polygons), materials=[m.name for m in ob.data.materials]))

# merged dwellA test house (realized geometry nodes output), for a quick look in Unreal
src = bpy.data.objects['TEST_dwellA_4x3']
gn = src.modifiers['EdoKitHouse'].node_group
rid = next(s.identifier for s in gn.interface.items_tree if s.item_type == 'SOCKET' and s.in_out == 'INPUT' and s.name == 'Realize')
src.modifiers['EdoKitHouse'].properties.inputs[rid]['value'] = True
src.location = (0, 0, 0)
dg = bpy.context.evaluated_depsgraph_get()
me = bpy.data.meshes.new_from_object(src.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
house = bpy.data.objects.new('SM_Edo_House_dwellA_4x3_test', me)
export(house, os.path.join(out, 'SM_Edo_House_dwellA_4x3_test.fbx'))
manifest.append(dict(collection='TEST', module=house.name, file='SM_Edo_House_dwellA_4x3_test.fbx',
                     tris=sum(len(q.vertices) - 2 for q in me.polygons), materials=[m.name for m in me.materials if m]))
json.dump(manifest, open(os.path.join(out, 'fbx_manifest.json'), 'w'), indent=1)
print('exported', len(manifest), 'files; test house tris', manifest[-1]['tris'], 'materials', manifest[-1]['materials'])
