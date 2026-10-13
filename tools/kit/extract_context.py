"""Extract the world context the town planner needs from your village .blend (roads, streams, fields, props, bridges).

    python -I tools/kit/extract_context.py <village.blend> <out.json>

Writes kit/village/town_context.json: road/stream polylines with widths, field patches, props and bridges (bounding boxes),
so tools/kit/town.py can plan new streets, houses, banks and fields without opening Blender.
"""
import sys, os, json, math, bpy
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(sys.argv[1]))
D = bpy.data
out = dict(roads=[], streams=[], fields=[], paddies=[], props=[], bridges=[])
ribbon = D.node_groups.get('GN_EdoRibbon')
sid = {s.name: s.identifier for s in ribbon.interface.items_tree if s.item_type == 'SOCKET' and s.in_out == 'INPUT'} if ribbon else {}
for o in D.objects:
    if o.type == 'CURVE' and any(m.type == 'NODES' and m.node_group == ribbon for m in o.modifiers):
        m = next(m for m in o.modifiers if m.node_group == ribbon)
        pts = [[round(p.co.x + o.location.x, 3), round(p.co.y + o.location.y, 3)] for s in o.data.splines for p in (s.points if s.type == 'POLY' else s.bezier_points)]
        w = m.properties.inputs[sid['Width']]['value'] if 'Width' in sid else 4.0
        (out['streams'] if o.name.startswith('WT_') else out['roads']).append(dict(name=o.name, pts=pts, width=round(float(w), 3)))
def cc(me, key):
    """connected components of a mesh by vertex adjacency -> bounding boxes"""
    par = list(range(len(me.vertices)))
    def f(a):
        while par[a] != a: par[a] = par[par[a]]; a = par[a]
        return a
    for p in me.polygons:
        for a, b in zip(p.vertices, p.vertices[1:]): par[f(a)] = f(b)
    box = {}
    for v in me.vertices:
        r = f(v.index); b = box.setdefault(r, [1e9, -1e9, 1e9, -1e9, 1e9, -1e9]); b[0] = min(b[0], v.co.x); b[1] = max(b[1], v.co.x); b[2] = min(b[2], v.co.y); b[3] = max(b[3], v.co.y); b[4] = min(b[4], v.co.z); b[5] = max(b[5], v.co.z)
    return [[round(x, 2) for x in b] for b in box.values()]
for name in ('LD_FieldSoil',):
    o = D.objects.get(name)
    if o: out['fields'] = cc(o.data, name)
for name in ('LD_PaddyWater',):
    o = D.objects.get(name)
    if o: out['paddies'] = cc(o.data, name)
for o in D.collections['EdoTown_Props'].objects:
    out['props'].append(dict(name=o.name, loc=[round(v, 3) for v in o.location], rot=round(o.rotation_euler.z, 4)))
for o in D.collections['EdoTown_Bridges'].objects:
    xs = [v.co.x for v in o.data.vertices]; ys = [v.co.y for v in o.data.vertices]; zs = [v.co.z for v in o.data.vertices]
    out['bridges'].append(dict(name=o.name, bbox=[round(min(xs), 2), round(max(xs), 2), round(min(ys), 2), round(max(ys), 2), round(min(zs), 2), round(max(zs), 2)]))
# canal cross-sections: ground height across the vertical canal at several y, and across the horizontal stream
import mathutils
from mathutils.bvhtree import BVHTree
g = D.objects['EDO_Ground_Town']; dg = bpy.context.evaluated_depsgraph_get(); ev = g.evaluated_get(dg); me = ev.to_mesh(); me.transform(g.matrix_world)
bvh = BVHTree.FromPolygons([v.co[:] for v in me.vertices], [p.vertices[:] for p in me.polygons])
def z(x, y):
    h = bvh.ray_cast(mathutils.Vector((x, y, 500)), mathutils.Vector((0, 0, -1)))
    return None if h[0] is None else round(h[0].z, 3)
out['canal_profile'] = {str(y): [[x, z(x, y)] for x in range(-196, -160, 2)] for y in (-60, -100, -150, -200)}
out['stream_profile'] = {str(x): [[y, z(x, y)] for y in range(-52, -28, 2)] for x in (-250, -230)}
# terrain heights east and south-east of the village (5 m grid) so the planner can keep houses off steep slopes
t = D.objects['EDO_Terrain']; tev = t.evaluated_get(dg); tme = tev.to_mesh(); tme.transform(t.matrix_world)
tb = BVHTree.FromPolygons([v.co[:] for v in tme.vertices], [p.vertices[:] for p in tme.polygons])
def tz(x, y):
    h = tb.ray_cast(mathutils.Vector((x, y, 2000)), mathutils.Vector((0, 0, -1)))
    return None if h[0] is None else round(h[0].z, 1)
X0, Y0, ST, NX, NY = -40.0, -275.0, 5.0, 52, 70
out['terrain'] = dict(x0=X0, y0=Y0, step=ST, nx=NX, ny=NY, rows=[[tz(X0 + i * ST, Y0 + j * ST) for i in range(NX)] for j in range(NY)])
json.dump(out, open(os.path.abspath(sys.argv[2]), 'w'), indent=1)
print('roads', len(out['roads']), 'streams', len(out['streams']), 'fields', len(out['fields']), 'paddies', len(out['paddies']))
