"""Merge the lantern light positions of the village manifest into a few real lights for Unreal.

    python tools/kit/cluster_lights.py [radius_m]        # default 30 m; reads kit/village/village_manifest.json

The lantern glow itself is the emissive material (T_Edo_Lantern); the lights only add warmth to the street. Writes
kit/village/lights_clustered.json: [{x, y, z, count, radius}] in Blender metres (tools/kit/unreal_import.py converts to Unreal).
"""
import json, math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); V = os.path.join(HERE, '..', '..', 'kit', 'village')
R = float(sys.argv[1]) if len(sys.argv) > 1 else 30.0
man = json.load(open(os.path.join(V, 'village_manifest.json')))
pts = [tuple(p) for h in man['houses'] for p in h['lantern_lights']]
clusters = []                                        # [sum_x, sum_y, sum_z, n, members]
for p in sorted(pts):
    best = None
    for c in clusters:
        d = math.hypot(p[0] - c[0] / c[3], p[1] - c[1] / c[3])
        if d < R and (best is None or d < best[0]): best = (d, c)
    if best is None: clusters.append([p[0], p[1], p[2], 1, [p]])
    else:
        c = best[1]; c[0] += p[0]; c[1] += p[1]; c[2] += p[2]; c[3] += 1; c[4].append(p)
lights = []
for c in clusters:
    cx, cy, cz = c[0] / c[3], c[1] / c[3], c[2] / c[3]
    lights.append(dict(x=round(cx, 2), y=round(cy, 2), z=round(cz + 0.5, 2), count=c[3], radius=round(max(math.hypot(m[0] - cx, m[1] - cy) for m in c[4]), 1)))
json.dump(dict(radius_m=R, source_lanterns=len(pts), lights=lights), open(os.path.join(V, 'lights_clustered.json'), 'w'), indent=1)
print(f'{len(pts)} lantern positions -> {len(lights)} lights (radius {R} m)')
