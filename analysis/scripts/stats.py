import bpy, sys, json, collections, time, mathutils
bpy.ops.wm.open_mainfile(filepath=sys.argv[-1])
H = json.load(open(sys.argv[-2]))['rows']
keys = ['Bays X','Bays Y','Floors','Roof','Shopfront','Engawa','Balcony','Lanterns','Gate','Fence']
combo = collections.Counter(tuple(r['mod_inputs'][k] for k in keys) for r in H)
print("structural combos (excluding Seed/Props/Ground):", len(combo))
for c,n in combo.most_common(): print("  ", dict(zip(keys,c)), "x", n)
dg = bpy.context.evaluated_depsgraph_get()
out = []
t0=time.time()
for r in H:
    o = bpy.data.objects[r['obj']]
    eo = o.evaluated_get(dg)
    me = eo.to_mesh()
    me.calc_loop_triangles()
    tris = len(me.loop_triangles)
    mats = sorted({(me.materials[p.material_index].name if p.material_index < len(me.materials) and me.materials[p.material_index] else 'NONE') for p in me.polygons})
    bb = [eo.matrix_world @ mathutils.Vector(c) for c in eo.bound_box]
    dim = [round(max(v[i] for v in bb)-min(v[i] for v in bb),2) for i in range(3)]
    inst = None
    out.append(dict(obj=r['obj'], tris=tris, verts=len(me.vertices), mats=mats, dim=dim, uv=[u.name for u in me.uv_layers], attrs=[a.name for a in me.attributes if not a.name.startswith('.')][:12]))
    eo.to_mesh_clear()
print("eval time", round(time.time()-t0,1), "s")
json.dump(out, open(sys.argv[-3], 'w'))
import statistics
tr=[x['tris'] for x in out]
print("tris per house: min", min(tr), "median", int(statistics.median(tr)), "max", max(tr), "total", sum(tr))
mc=collections.Counter(m for x in out for m in x['mats']); print("materials used by houses:", dict(mc))
print("uv layers:", collections.Counter(tuple(x['uv']) for x in out))
print("sample attrs:", out[0]['attrs'])
for x in sorted(out, key=lambda x:-x['tris'])[:5]: print("  top", x['obj'], x['tris'], x['dim'])
for x in sorted(out, key=lambda x:x['tris'])[:3]: print("  low", x['obj'], x['tris'], x['dim'])
