import bpy, sys, json, mathutils, math
bpy.ops.wm.open_mainfile(filepath=sys.argv[-1])
g = bpy.data.node_groups['GN_EdoHouse']
ids = {it.name: it.identifier for it in g.interface.items_tree if it.item_type=='SOCKET' and it.in_out=='INPUT'}
src = bpy.data.objects['TWN_10_dwellA']
o = src.copy(); o.data = src.data.copy(); o.name='ROOFTEST'; bpy.context.scene.collection.objects.link(o)
m = next(m for m in o.modifiers if m.type=='NODES' and m.node_group==g)
def setp(**kw):
    for k,v in kw.items(): m.properties.inputs[ids[k]]['value']=v
    o.update_tag(); bpy.context.view_layer.update()
sc = bpy.context.scene; sc.render.engine='CYCLES'; sc.cycles.device='CPU'; sc.cycles.samples=16; sc.cycles.use_denoising=False
sc.render.resolution_x=480; sc.render.resolution_y=360
w = bpy.data.worlds.new('W'); w.use_nodes=True; w.node_tree.nodes['Background'].inputs[0].default_value=(0.75,0.82,0.95,1); sc.world=w
sun = bpy.data.lights.new('S','SUN'); sun.energy=4; so=bpy.data.objects.new('S',sun); sc.collection.objects.link(so); so.rotation_euler=(math.radians(50),0,math.radians(35))
cam = bpy.data.cameras.new('C'); co = bpy.data.objects.new('C',cam); sc.collection.objects.link(co); sc.camera=co; cam.lens=45
for ob in bpy.data.objects:
    if ob.type in ('MESH','CURVE'): ob.hide_render = (ob.name!='ROOFTEST')
base = {'Bays X':4,'Bays Y':3,'Shopfront':False,'Engawa':False,'Balcony':False,'Lanterns':False,'Gate':False,'Fence':0,'Props':0.0,'Seed':100}
for fl in (1,2):
    for roof in (0,1,2,3):
        setp(**base, **{'Floors':fl,'Roof':roof})
        dg = bpy.context.evaluated_depsgraph_get(); eo=o.evaluated_get(dg); me=eo.to_mesh()
        pts=[o.matrix_world@v.co for v in me.vertices]; tris=len(me.polygons); eo.to_mesh_clear()
        mn=mathutils.Vector([min(p[i] for p in pts) for i in range(3)]); mx=mathutils.Vector([max(p[i] for p in pts) for i in range(3)])
        c=(mn+mx)/2; d=(mx-mn).length; dv=mathutils.Vector((1,-1.25,0.75)).normalized()
        co.location=c+dv*d*1.35; co.rotation_euler=(c-co.location).to_track_quat('-Z','Y').to_euler()
        sc.render.filepath=f"{sys.argv[-2]}/F{fl}_R{roof}.png"; bpy.ops.render.render(write_still=True); print("rendered F",fl,"R",roof)
