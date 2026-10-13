import bpy, sys, collections
bpy.ops.wm.open_mainfile(filepath=sys.argv[-1])
print("Blender", bpy.app.version_string)
print("scenes", [s.name for s in bpy.data.scenes])
print("objects", len(bpy.data.objects), "meshes", len(bpy.data.meshes), "materials", len(bpy.data.materials),
      "images", len(bpy.data.images), "node_groups", len(bpy.data.node_groups), "collections", len(bpy.data.collections))
t = collections.Counter(o.type for o in bpy.data.objects); print("types", dict(t))
print("-- node groups")
for g in bpy.data.node_groups: print(" ", g.bl_idname, g.name, "users", g.users, "nodes", len(g.nodes))
print("-- GN modifier usage")
c = collections.Counter()
for o in bpy.data.objects:
    for m in o.modifiers:
        c[(m.type, m.node_group.name if m.type=='NODES' and m.node_group else '')] += 1
for k,v in c.most_common(): print(" ", k, v)
print("-- collections")
for col in bpy.data.collections: print(" ", col.name, len(col.objects), len(col.children))
