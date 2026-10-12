import bpy, sys, collections
bpy.ops.wm.open_mainfile(filepath=sys.argv[-1])
def walk(tree, depth, seen, maxd=3):
    kids = [n for n in tree.nodes if n.bl_idname=='GeometryNodeGroup' and n.node_tree]
    cnt = collections.Counter(n.node_tree.name for n in kids)
    for name,c in sorted(cnt.items()):
        sub = bpy.data.node_groups[name]
        flag = "" if depth<maxd else " ..."
        print("  "*depth + f"- {name} x{c} ({len(sub.nodes)} nodes){flag}")
        if depth<maxd and name not in seen: walk(sub, depth+1, seen|{name}, maxd)
g = bpy.data.node_groups['GN_EdoHouse']
print("== GN_EdoHouse top level: frames and what they contain")
frames = {n.name:(n.label or n.name) for n in g.nodes if n.bl_idname=='NodeFrame'}
by = collections.defaultdict(list)
for n in g.nodes:
    if n.bl_idname=='NodeFrame': continue
    fr = frames.get(n.parent.name) if n.parent else '(no frame)'
    by[fr].append(n)
for fr, ns in by.items():
    gs = collections.Counter(n.node_tree.name for n in ns if n.bl_idname=='GeometryNodeGroup' and n.node_tree)
    other = collections.Counter(n.bl_idname.replace('GeometryNode','') for n in ns if n.bl_idname!='GeometryNodeGroup')
    print(f"[{fr}] {len(ns)} nodes; groups: {dict(gs)}; types: {dict(other.most_common(8))}")
print("\n== subgroup hierarchy")
walk(g, 0, {'GN_EdoHouse'})
print("\n== node labels containing keywords (top level, all depths)")
import re
kw = re.compile(r'collision|ucx|wall|window|door|shoji|pillar|post|beam|roof|tile|eave|floor|stair|rail|engawa|fence|gate|lantern|noren|sign|barrel', re.I)
names=set()
for t in [g]+[bpy.data.node_groups[n] for n in bpy.data.node_groups.keys() if n.startswith('EDO_')]:
    for n in t.nodes:
        for s in (n.label, n.name):
            if s and kw.search(s) and n.bl_idname in ('NodeFrame','GeometryNodeGroup'): names.add((t.name, s))
for t,s in sorted(names)[:150]: print("  ", t, "|", s)
