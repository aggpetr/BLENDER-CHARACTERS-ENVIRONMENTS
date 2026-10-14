"""Top-down render of an area: python -I tools/kit/render_topdown.py <blend> <out.png> <xmin> <xmax> <ymin> <ymax> [px_per_m]"""
import sys, os, math, bpy
blend, out = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
x0, x1, y0, y1 = map(float, sys.argv[3:7]); ppm = float(sys.argv[7]) if len(sys.argv) > 7 else 8.0
bpy.ops.wm.open_mainfile(filepath=blend)
sc = bpy.context.scene

def hide_unviewed():
    """Mimic the viewport: objects in excluded/hidden collections are not rendered."""
    def walk(lc, hidden):
        h = hidden or lc.exclude or lc.hide_viewport
        for o in lc.collection.objects:
            if h: o.hide_render = True
        for c in lc.children: walk(c, h)
    walk(bpy.context.view_layer.layer_collection, False)
    for o in bpy.data.objects:
        if o.name not in bpy.context.scene.objects: o.hide_render = True
hide_unviewed()
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 12; sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = int((x1 - x0) * ppm), int((y1 - y0) * ppm)
try: sc.view_settings.view_transform = 'AgX'
except Exception: pass
for ob in bpy.data.objects:
    if ob.type == 'LIGHT': ob.hide_render = True
w = bpy.data.worlds.new('W'); w.use_nodes = True; w.node_tree.nodes['Background'].inputs[1].default_value = 1.1; sc.world = w
sun = bpy.data.lights.new('S', 'SUN'); sun.energy = 2.5; so = bpy.data.objects.new('S', sun); sc.collection.objects.link(so); so.rotation_euler = (math.radians(35), 0, math.radians(-30))
cam = bpy.data.cameras.new('C'); cam.type = 'ORTHO'; co = bpy.data.objects.new('C', cam); sc.collection.objects.link(co); sc.camera = co
cam.ortho_scale = max(x1 - x0, y1 - y0); co.location = ((x0 + x1) / 2, (y0 + y1) / 2, 500); cam.clip_end = 2000
if x1 - x0 < y1 - y0: cam.sensor_fit = 'VERTICAL'
else: cam.sensor_fit = 'HORIZONTAL'
sc.render.filepath = out; bpy.ops.render.render(write_still=True); print('rendered', out)
