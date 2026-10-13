import bpy, sys, json, collections, re
bpy.ops.wm.open_mainfile(filepath=sys.argv[-1])
H = json.load(open(sys.argv[-2]))
hn = {r['obj'] for r in H['rows']}
st = {x['obj']:x for x in json.load(open(sys.argv[-3]))}
arch = collections.Counter()
for r in H['rows']:
    m = re.match(r'^(?:[A-Za-z]+_)?(?:\d+_)?(.+)$', r['obj']); arch[m.group(1)] += 1
print("-- house archetype suffixes:", dict(arch.most_common()))
print("-- house prefixes:", dict(collections.Counter(r['obj'].split('_')[0] for r in H['rows'])))
print("-- house collections:", dict(collections.Counter(c for r in H['rows'] for c in r['coll'])))
print("-- NON-house objects by collection")
by = collections.defaultdict(list)
for o in bpy.data.objects:
    if o.name in hn or o.type=='LIGHT': continue
    mods=[(m.type, m.node_group.name if getattr(m,'node_group',None) else '') for m in o.modifiers]
    by[o.users_collection[0].name if o.users_collection else '-'].append((o.name,o.type,mods[:2], o.data.name if o.data else ''))
for c,l in by.items():
    print(" ", c, len(l)); [print("     ", x) for x in l[:30]]
print("-- materials")
for m in bpy.data.materials:
    types = collections.Counter(n.bl_idname.replace('ShaderNode','') for n in (m.node_tree.nodes if m.use_nodes and m.node_tree else []))
    print(" ", m.name, "users", m.users, dict(types.most_common(8)))
print("-- images:", [(i.name, i.size[:], i.filepath, i.packed_file is not None) for i in bpy.data.images])
print("-- texts:", [(t.name, len(t.as_string())) for t in bpy.data.texts])
print("-- lights:", collections.Counter((l.type, round(l.energy,1)) for l in bpy.data.lights).most_common(5))
sc = bpy.context.scene
print("-- scene: unit", sc.unit_settings.system, sc.unit_settings.scale_length, "render", sc.render.engine, "frame", sc.frame_start, sc.frame_end)
