import bpy, sys, json, mathutils, math, collections
bpy.ops.wm.open_mainfile(filepath=sys.argv[-1])
H = json.load(open(sys.argv[-2]))['rows']
out = sys.argv[-3]
sc = bpy.context.scene
sc.render.engine='CYCLES'; sc.cycles.device='CPU'; sc.cycles.samples=24; sc.cycles.use_denoising=False
sc.render.resolution_x=640; sc.render.resolution_y=480; sc.render.image_settings.file_format='PNG'
# clean world light
w = bpy.data.worlds.new('W'); w.use_nodes=True; w.node_tree.nodes['Background'].inputs[0].default_value=(0.75,0.82,0.95,1); w.node_tree.nodes['Background'].inputs[1].default_value=1.0; sc.world=w
sun = bpy.data.lights.new('S','SUN'); sun.energy=4; so=bpy.data.objects.new('S',sun); sc.collection.objects.link(so); so.rotation_euler=(math.radians(50),0,math.radians(35))
cam = bpy.data.cameras.new('C'); co = bpy.data.objects.new('C',cam); sc.collection.objects.link(co); sc.camera=co; cam.lens=45
A = collections.OrderedDict()
for r in H:
    n = r['obj']; a = n.split('_',2)[-1] if n.count('_')>=2 else n.split('_',1)[-1]
    if a=='01': continue
    A.setdefault(a, r['obj'])
all_objs = list(bpy.data.objects)
dg = bpy.context.evaluated_depsgraph_get()
for a,name in A.items():
    for o in all_objs:
        if o.type in ('MESH','CURVE'): o.hide_render = (o.name != name)
    o = bpy.data.objects[name]; eo = o.evaluated_get(dg)
    pts = [eo.matrix_world @ mathutils.Vector(c) for c in eo.bound_box]
    mn = mathutils.Vector([min(p[i] for p in pts) for i in range(3)]); mx = mathutils.Vector([max(p[i] for p in pts) for i in range(3)])
    c = (mn+mx)/2; d = (mx-mn).length
    dirv = mathutils.Vector((1.0,-1.25,0.75)).normalized()
    co.location = c + dirv*d*1.35
    co.rotation_euler = (c-co.location).to_track_quat('-Z','Y').to_euler()
    sc.render.filepath = f"{out}/{a}.png"; bpy.ops.render.render(write_still=True)
    print("rendered", a, name)
