import bpy, sys, json, collections, math, mathutils
bpy.ops.wm.open_mainfile(filepath=sys.argv[-1])
H = json.load(open(sys.argv[-2]))['rows']
g = bpy.data.node_groups['GN_EdoHouse']
ids = {it.name: it.identifier for it in g.interface.items_tree if it.item_type=='SOCKET' and it.in_out=='INPUT'}
out=[]; issues=collections.Counter()
for r in H:
    o = bpy.data.objects[r['obj']]
    e = o.rotation_euler; mw = o.matrix_world
    if o.parent: issues['has parent']+=1
    if o.rotation_mode!='XYZ': issues['rot mode '+o.rotation_mode]+=1
    if abs(e.x)>1e-4 or abs(e.y)>1e-4: issues['tilted']+=1
    if any(abs(s-1)>1e-4 for s in o.scale): issues['scaled']+=1
    if any(abs(v)>1e-6 for v in o.delta_location) or any(abs(v)>1e-6 for v in o.delta_rotation_euler): issues['delta transform']+=1
    if o.animation_data: issues['animated']+=1
    wl = mw.translation
    out.append(dict(obj=o.name, loc=[round(v,4) for v in wl], rot_z_deg=round(math.degrees(e.z),3), scale=[round(v,4) for v in o.scale],
                    ground=r['mod_inputs'].get('Ground'), collection=r['coll'][0] if r['coll'] else None))
print("placement issues:", dict(issues) or "none")
zs=[p['loc'][2] for p in out]; print("loc z range:", min(zs), max(zs)); 
print("rotations (deg) distinct:", sorted({round(p['rot_z_deg']) for p in out})[:40])
print("ground objects:", collections.Counter(p['ground'] for p in out))
json.dump(out, open(sys.argv[-3],'w'), indent=1)
# ground interaction test on a typical house
src = bpy.data.objects['TWN_'+[x['obj'] for x in H if x['obj'].startswith('TWN_') and x['obj'].endswith('dwellA')][0].split('_',1)[1]] if any(x['obj'].startswith('TWN_') and x['obj'].endswith('dwellA') for x in H) else bpy.data.objects[H[0]['obj']]
m = next(m for m in src.modifiers if m.type=='NODES' and m.node_group==g)
dg = bpy.context.evaluated_depsgraph_get()
def meas(o):
    dg.update(); eo=o.evaluated_get(dg); me=eo.to_mesh(); zs=[v.co.z for v in me.vertices]; r=(round(min(zs),3), round(max(zs),3), len(me.loop_triangles) if False else len(me.polygons)); eo.to_mesh_clear(); return r
print("\nground test on", src.name, "at z=", round(src.location.z,3), "ground=", m.properties.inputs[ids['Ground']]['value'])
print(" local z min/max/faces as placed:", meas(src))
orig_z = src.location.z
src.location.z = orig_z + 3.0; bpy.context.view_layer.update(); print(" after raising object +3 m:", meas(src))
src.location.z = orig_z
gr = bpy.data.objects.get('EDO_Ground_KitFlat')
if gr:
    old = m.properties.inputs[ids['Ground']]['value']; m.properties.inputs[ids['Ground']]['value']=gr; src.update_tag(); print(" with Ground=EDO_Ground_KitFlat:", meas(src)); m.properties.inputs[ids['Ground']]['value']=old
