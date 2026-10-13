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

import bmesh
NO_COLLISION = {'SM_Edo_Noren', 'SM_Edo_Lantern', 'SM_Edo_BalconyBracket', 'SM_Edo_ShopSign',
                'SM_Edo_EmbankCobble', 'SM_Edo_CropRidge', 'SM_Edo_PaddyBund', 'SM_Edo_CropDaikon', 'SM_Edo_CropCabbage_A', 'SM_Edo_CropCabbage_B',
                'SM_Edo_CropBarley_A', 'SM_Edo_CropBarley_B', 'SM_Edo_CropRice_A', 'SM_Edo_CropRice_B',
                'SM_Edo_BorderRope', 'SM_Edo_Home_Laundry', 'SM_Edo_Farm_DryingRack', 'SM_Edo_Cln_HerbRack', 'SM_Edo_Smi_AxeRack', 'SM_Edo_Smi_SwordRack'}   # hanging / thin props: no blocking volume
def _flat_bridge(hw):
    return [((-4.6, -hw, -0.46), (4.6, hw, 0.0)), ((-4.85, -hw - 0.3, -2.6), (-3.5, hw + 0.3, -0.1)), ((3.5, -hw - 0.3, -2.6), (4.85, hw + 0.3, -0.1)),
            ((-4.6, hw - 0.2, 0.0), (4.6, hw, 1.2)), ((-4.6, -hw, 0.0), (4.6, -hw + 0.2, 1.2))]


BOXES = {'SM_Edo_Torii': [((-4.0, -0.5, 0.0), (-3.0, 0.5, 5.2)), ((3.0, -0.5, 0.0), (4.0, 0.5, 5.2))],      # the two pillars only: the opening stays free
         'SM_Edo_Bridge_Flat4': _flat_bridge(2.0), 'SM_Edo_Bridge_Flat6': _flat_bridge(3.2),
         'SM_Edo_Tea_Parasol': [((-0.8, -0.55, 0.0), (0.8, -0.15, 0.47)), ((-0.4, -0.13, 0.0), (0.4, 0.63, 0.25))],
         'SM_Edo_Gate': [((-1.25, -0.27, -0.30), (-0.85, 0.27, 3.30)), ((0.85, -0.27, -0.30), (1.25, 0.27, 3.30)),
                         ((-1.75, -1.20, 3.00), (1.75, 1.20, 4.05))]}

def _hull(points, name):
    bm = bmesh.new()
    for p in points: bm.verts.new(p)
    bmesh.ops.convex_hull(bm, input=bm.verts)
    for v in [v for v in bm.verts if not v.link_faces]: bm.verts.remove(v)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    return bpy.data.objects.new(name, me)

def collisions(ob):
    """Unreal simple collision: UCX_<mesh>_NN convex hulls (one per module, boxes for the gate)."""
    if ob.name in NO_COLLISION: return []
    if ob.name == 'SM_Edo_Bridge_Arch':        # arch: one convex hull per 2 m column (walkable deck, open arch for the water)
        import math
        L, H, hw, ax, zc, ry, bed = 18.2, 2.0, 3.0, 6.4, -1.4, 2.9, -2.8
        zd = lambda x: H * (1.0 - (2.0 * x / L) ** 2)
        zb = lambda x: zc + ry * math.sqrt(max(0.0, 1.0 - (x / ax) ** 2))
        out = []
        xs = [-9.1 + i * 1.3 for i in range(15)]
        for i in range(len(xs) - 1):
            a, b = xs[i], xs[i + 1]; mid = (a + b) / 2
            bot = min(zb(a), zb(b)) if abs(mid) < ax else bed
            out.append(_hull([(x, y, z) for x in (a, b) for y in (-hw, hw) for z in (bot, max(zd(a), zd(b)) + 0.9)], f'UCX_{ob.name}_{i:02d}'))
        return out
    if ob.name in BOXES:
        return [_hull([(x, y, z) for x in (a[0], b[0]) for y in (a[1], b[1]) for z in (a[2], b[2])], f'UCX_{ob.name}_{i:02d}') for i, (a, b) in enumerate(BOXES[ob.name])]
    pts = [tuple(v.co) for v in ob.data.vertices]
    for q in (0.0, 0.05, 0.10, 0.20):          # keep the hull small: snap to a coarser grid until under 120 vertices
        P = pts if q == 0 else list({(round(x / q) * q, round(y / q) * q, round(z / q) * q) for x, y, z in pts})
        h = _hull(P, f'UCX_{ob.name}_00')
        if len(h.data.vertices) <= 120: break
    return [h]

def export(ob, path, extra=()):
    objs = [ob] + list(extra)
    tmp = [o for o in objs if o.name not in sc.collection.objects]
    for o in tmp: sc.collection.objects.link(o)
    for o in bpy.context.view_layer.objects: o.select_set(False)
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.export_scene.fbx(filepath=path, **FBX)
    for o in tmp: sc.collection.objects.unlink(o)

manifest = []
for c in bpy.data.collections['KIT_Modules'].children:
    for ob in sorted(c.objects, key=lambda o: o.name):
        p = os.path.join(out, 'modules', c.name, ob.name + '.fbx'); os.makedirs(os.path.dirname(p), exist_ok=True)
        ucx = collisions(ob)
        export(ob, p, ucx)
        manifest.append(dict(collection=c.name, module=ob.name, file=os.path.relpath(p, out),
                             tris=sum(len(q.vertices) - 2 for q in ob.data.polygons), materials=[m.name for m in ob.data.materials],
                             collision=[dict(name=u.name, verts=len(u.data.vertices)) for u in ucx]))

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
