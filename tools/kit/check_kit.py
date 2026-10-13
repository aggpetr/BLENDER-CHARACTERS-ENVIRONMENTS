"""Evaluate the kit test houses: instance counts, triangles, extents, floor level vs ground."""
import sys, collections, bpy, mathutils
bpy.ops.wm.open_mainfile(filepath=sys.argv[-1])
dg = bpy.context.evaluated_depsgraph_get()
tri = {}
def tris(me):
    if me.name not in tri: tri[me.name] = sum(len(p.vertices) - 2 for p in me.polygons)
    return tri[me.name]
for ob in bpy.data.objects:
    if not ob.name.startswith('TEST_') or ob.type != 'MESH' or not ob.modifiers: continue
    cnt = collections.Counter(); total = 0; mn = [1e9]*3; mx = [-1e9]*3
    fam = collections.Counter()
    for inst in dg.object_instances:
        if not inst.is_instance or inst.parent is None or inst.parent.original != ob: continue
        src = inst.instance_object.original if inst.instance_object else None
        if src is None or src.type != 'MESH': continue
        cnt[src.name] += 1; t = tris(src.data); total += t
        fam[src.users_collection[0].name if src.users_collection else '?'] += t
        M = inst.matrix_world.copy()
        for c in src.bound_box:
            w = M @ mathutils.Vector(c)
            for i in range(3): mn[i] = min(mn[i], w[i]); mx[i] = max(mx[i], w[i])
    print(f"\n== {ob.name}: {sum(cnt.values())} instances, {total} triangles; extent {[round(mx[i]-mn[i],2) for i in range(3)]} z {round(mn[2],2)}..{round(mx[2],2)}")
    for k, v in sorted(fam.items(), key=lambda kv: -kv[1]): print(f"   {k:16s} {v:6d} tris")
    walls = {k: v for k, v in cnt.items() if 'Wall' in k}; print("   walls:", walls)
    print("   steps/roof:", {k: v for k, v in cnt.items() if 'Steps' in k or 'Roof' in k or 'Stilt' in k or 'EngawaPost' in k})
