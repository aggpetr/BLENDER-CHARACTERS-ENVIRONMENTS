import bpy, sys, json, mathutils
bpy.ops.wm.open_mainfile(filepath=sys.argv[-1])
g = bpy.data.node_groups['GN_EdoHouse']
ids = {it.name: it.identifier for it in g.interface.items_tree if it.item_type=='SOCKET' and it.in_out=='INPUT'}
src = next(o for o in bpy.data.objects if o.name.endswith('dwellA') and o.name.startswith('TWN'))
o = src.copy(); o.data = src.data.copy(); o.name='SWEEP'
bpy.context.scene.collection.objects.link(o)
o.location=(0,0,0); o.rotation_euler=(0,0,0); o.scale=(1,1,1)
m = next(m for m in o.modifiers if m.type=='NODES' and m.node_group==g)
def setp(**kw):
    for k,v in kw.items(): m.properties.inputs[ids[k]]['value']=v
    o.update_tag(); bpy.context.view_layer.update()
def meas():
    dg = bpy.context.evaluated_depsgraph_get(); eo=o.evaluated_get(dg); me=eo.to_mesh(); me.calc_loop_triangles()
    xs=[v.co for v in me.vertices]
    if not xs: eo.to_mesh_clear(); return (0,[0,0,0],[0,0,0])
    mn=[min(c[i] for c in xs) for i in range(3)]; mx=[max(c[i] for c in xs) for i in range(3)]
    r=(len(me.loop_triangles), [round(mx[i]-mn[i],2) for i in range(3)], [round(mn[i],2) for i in range(3)])
    eo.to_mesh_clear(); return r
base=dict(**{'Bays X':3,'Bays Y':3,'Floors':1,'Roof':1,'Shopfront':False,'Engawa':False,'Balcony':False,'Lanterns':False,'Gate':False,'Fence':0,'Seed':100,'Props':0.0,'Roof Detail':0.2,'Wear':1.0,'Raise':1.12,'Bay Scale':1.0})
setp(**base); b=meas(); print("BASE 3x3 1F roof1:", b)
def sweep(name, vals):
    print(f"-- {name}")
    for v in vals:
        setp(**base); setp(**{name:v}); t,d,mn=meas(); print(f"   {name}={v}: tris {t} (delta {t-b[0]:+d}) dim {d}")
    setp(**base)
for n,v in [('Bays X',[1,2,4,5,6]),('Bays Y',[1,2,4,5]),('Floors',[2,3]),('Roof',[0,2,3]),('Shopfront',[True]),('Engawa',[True]),('Balcony',[True]),('Lanterns',[True]),('Gate',[True]),('Fence',[1,2]),('Props',[0.5,1.0]),('Roof Detail',[0.1,0.5,1.0]),('Raise',[0.0,2.0]),('Bay Scale',[0.6,1.5]),('Seed',[1,2,3,4])]:
    sweep(n,v)
