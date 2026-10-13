"""Export the village terrain as a 16-bit heightmap for an Unreal Landscape.

    python -I tools/kit/export_heightmap.py <village.blend> <out_dir> [x0 y_top]      (default x0 = -400, y_top = 140; 1009 x 1009 samples, 1 m apart)

The height at every sample is taken from the surface the houses were placed on: EDO_Ground_Village, then EDO_Ground_Town, then
EDO_Terrain. Writes <out_dir>/Edo_Heightmap_1009.png (16-bit), Edo_Heightmap_1009.r16 (raw little endian, the same data) and
heightmap_info.json with the Landscape import settings (location, scale). Image rows run north to south, columns west to east:
Blender (x, y) -> pixel (x - x0, y_top - y); Unreal location = (x0 * 100, -y_top * 100, 0) cm with scale (100, 100, z_scale).
Value = z / (z_scale / 100) * 128 + 32768 (the Landscape range is +-256 m at z scale 100).
"""
import sys, os, json, math, bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from PIL import Image

bpy.ops.wm.open_mainfile(filepath=os.path.abspath(sys.argv[1])); OUT = os.path.abspath(sys.argv[2]); os.makedirs(OUT, exist_ok=True)
X0 = float(sys.argv[3]) if len(sys.argv) > 3 else -400.0
YT = float(sys.argv[4]) if len(sys.argv) > 4 else 140.0
N = 1009
dg = bpy.context.evaluated_depsgraph_get()
trees = []
for name in ('EDO_Ground_Village', 'EDO_Ground_Town', 'EDO_Terrain'):
    ob = bpy.data.objects[name]; me = ob.evaluated_get(dg).to_mesh(); me.transform(ob.matrix_world)
    trees.append(BVHTree.FromPolygons([v.co[:] for v in me.vertices], [p.vertices[:] for p in me.polygons]))
    print('loaded', name, flush=True)
H = np.zeros((N, N), dtype=np.float32); down = Vector((0, 0, -1)); miss = 0
for j in range(N):
    y = YT - j
    for i in range(N):
        x = X0 + i; o = Vector((x, y, 5000.0)); z = None
        for t in trees:
            h = t.ray_cast(o, down)
            if h[0] is not None: z = h[0].z; break
        if z is None: z = float(H[j, i - 1]) if i else 0.0; miss += 1
        H[j, i] = z
    if j % 200 == 0: print('row', j, flush=True)
zmin, zmax = float(H.min()), float(H.max())
zscale = max(100.0, math.ceil(max(abs(zmin), abs(zmax) + 1.0) / 255.0 * 100.0))
V = np.clip(H / (zscale / 100.0) * 128.0 + 32768.0, 0, 65535).astype(np.uint16)
Image.fromarray(V, mode='I;16').save(os.path.join(OUT, 'Edo_Heightmap_1009.png'))
V.astype('<u2').tofile(os.path.join(OUT, 'Edo_Heightmap_1009.r16'))
info = dict(size=[N, N], metres_per_quad=1.0, x0_blender=X0, y_top_blender=YT, z_min_m=round(zmin, 2), z_max_m=round(zmax, 2), samples_without_surface=miss,
            landscape=dict(location_cm=[X0 * 100.0, -YT * 100.0, 0.0], scale=[100.0, 100.0, zscale], resolution=[N, N], section_quads=63, sections_per_component=1, components=[16, 16],
                           note='import Edo_Heightmap_1009.png (or .r16 little endian); Sections 63x63 quads, 1 section/component, 16 x 16 components = 1009 x 1009'))
json.dump(info, open(os.path.join(OUT, 'heightmap_info.json'), 'w'), indent=1)
print(json.dumps(info))
