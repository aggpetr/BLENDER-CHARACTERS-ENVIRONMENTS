"""Village border modules: torii gate, stone pier, boundary stones, sacred rope (shimenawa with paper streamers), Jizo statue.

Metric, Z up, origin on the ground. The torii spans local X (pillar centres at +-3.5 m, the road runs along local Y); the rope is 6 m long along X.
"""
import math, random
from mathutils import Vector
from kit_lib import MB

PI = math.pi
TORII_S = 3.5                         # pillar centre distance from the gate centre


def torii():
    mb = MB('SM_Edo_Torii'); S = TORII_S
    for sx in (-1, 1):
        s = len(mb.bm.verts)
        mb.lathe([(0.0, 0.0), (0.50, 0.0), (0.52, 0.10), (0.50, 0.32), (0.0, 0.34)], 16, 'Stone', cap_top=False, smooth=False)      # base stone
        mb.lathe([(0.32, 0.34), (0.33, 0.8), (0.30, 2.6), (0.26, 5.0)], 16, 'Vermilion', cap_top=True, smooth=True)
        mb.lathe([(0.335, 0.34), (0.335, 0.62)], 16, 'Lacquer', cap_top=False, smooth=True)                                         # black foot ring
        for v in list(mb.bm.verts)[s:]: v.co.x += sx * S
    rings = []                                                                           # kasagi: the top beam, ends swept up
    for i in range(41):
        x = -5.3 + i * 10.6 / 40; z = 5.18 + 0.9 * (abs(x) / 5.3) ** 2.6
        rings.append([(x, -0.36, z - 0.14), (x, 0.36, z - 0.14), (x, 0.30, z + 0.18), (x, -0.30, z + 0.18)])
    mb.loft(rings, 'Lacquer', closed=True, smooth=False, cap0=True, cap1=True, want_out=lambda m: Vector((0, m.y, m.z - 5.3 - 0.9 * (abs(m.x) / 5.3) ** 2.6)))
    mb.box((-4.7, -0.27, 4.9), (4.7, 0.27, 5.14), 'Vermilion', grain=0)                      # shimaki
    mb.box((-4.2, -0.18, 4.15), (4.2, 0.18, 4.50), 'Vermilion', grain=0)                     # nuki
    mb.box((-0.30, -0.12, 4.50), (0.30, 0.12, 4.90), 'Lacquer', grain=2)                     # gakuzuka (plaque post)
    mb.box((-0.62, -0.17, 4.52), (0.62, -0.13, 4.88), 'Planks', grain=0)                     # name plaque
    for sx in (-1, 1):
        mb.box((sx * S - 0.40, -0.23, 4.08), (sx * S + 0.40, 0.23, 4.56), 'Lacquer', grain=0)  # pillar collars
        mb.box((sx * S - 0.36, -0.30, 4.86), (sx * S + 0.36, 0.30, 5.0), 'Lacquer', grain=0)
    return mb


def pier():
    mb = MB('SM_Edo_ToriiPier')                                      # stone gate pier with a pyramid cap
    mb.box((-0.45, -0.45, 0.0), (0.45, 0.45, 0.35), 'Stone')
    mb.box((-0.38, -0.38, 0.35), (0.38, 0.38, 1.85), 'StoneWall')
    mb.box((-0.50, -0.50, 1.85), (0.50, 0.50, 2.02), 'Stone')
    mb.lathe([(0.52, 2.02), (0.34, 2.28), (0.0, 2.58)], 4, 'Stone', cap_top=False, phase=PI / 4, smooth=False)
    return mb


def stone_marker(v):
    mb = MB(f'SM_Edo_BorderStone_{"ABC"[v]}'); rnd = mb.rng           # tall standing boundary stone (2.1 to 2.6 m), a little different each time
    h = (2.2, 1.9, 2.6)[v]; w = (0.72, 0.85, 0.62)[v]
    prof = [(0.0, 0.0), (w * 0.95, 0.0), (w, h * 0.30), (w * 0.88, h * 0.62), (w * 0.62, h * 0.86), (w * 0.28, h * 0.97), (0.0, h)]
    s = len(mb.bm.verts)
    mb.lathe(prof, 9, 'StoneWall', cap_top=False, smooth=True, phase=rnd.random() * 3)
    for vv in list(mb.bm.verts)[s:]:
        vv.co.x *= 1.0 + rnd.uniform(-0.12, 0.12); vv.co.y *= 0.75 + rnd.uniform(-0.1, 0.15); vv.co.z += rnd.uniform(-0.02, 0.03) * vv.co.z
    s = len(mb.bm.verts)                                                       # a carved band where the rope is tied
    mb.lathe([(w * 1.0, h * 0.60), (w * 1.07, h * 0.64), (w * 1.07, h * 0.70), (w * 0.98, h * 0.74)], 9, 'Stone', cap_top=False, smooth=True)
    return mb


def rope():
    mb = MB('SM_Edo_BorderRope'); L = 6.0; sag = 0.55; z0 = 1.55; R = 0.13       # thick white sacred rope (26 cm), hung between two stones
    rings = []
    for i in range(41):
        t = i / 40; x = -L / 2 + t * L; z = z0 - sag * 4 * t * (1 - t)
        rings.append([(x, R * math.cos(a), z + R * math.sin(a)) for a in [j * PI / 4 for j in range(8)]])
    mb.loft(rings, 'RopeWhite', closed=True, smooth=True, cap0=True, cap1=True, want_out=lambda m: Vector((0, m.y, m.z - z0 + 0.3)), uv_scale=0.5)
    for x0 in (-L / 2, L / 2 - 0.0):                                           # tassel at each knot
        pass
    for t in (0.15, 0.3, 0.45, 0.6, 0.75, 0.9):                                # paper streamers (shide): three zig-zag folds each, bigger
        x = -L / 2 + t * L; z = z0 - sag * 4 * t * (1 - t) - R
        for k in range(3):
            zz = z - 0.03 - k * 0.27
            mb.box((x - 0.11 + 0.05 * (k % 2), -0.02, zz - 0.25), (x + 0.11 + 0.05 * (k % 2), 0.02, zz), 'Paper')
    return mb


def jizo():
    mb = MB('SM_Edo_Jizo')                                                     # roadside Jizo statue on a stone base, red bib
    mb.box((-0.32, -0.32, 0.0), (0.32, 0.32, 0.30), 'StoneWall')
    mb.lathe([(0.0, 0.30), (0.26, 0.30), (0.24, 0.55), (0.19, 0.78), (0.16, 0.86), (0.0, 0.88)], 10, 'StoneWall', cap_top=False, smooth=True)          # body
    mb.lathe([(0.0, 0.86), (0.13, 0.88), (0.15, 1.0), (0.12, 1.12), (0.0, 1.16)], 10, 'StoneWall', cap_top=False, smooth=True)                      # head
    mb.box((-0.17, -0.20, 0.72), (0.17, -0.17, 0.88), 'ClothRed')                                                                                      # bib
    mb.box((-0.17, -0.20, 0.55), (0.17, -0.18, 0.72), 'ClothRed')
    return mb


def build_border():
    return {
        'KIT_Torii': [torii()], 'KIT_ToriiPier': [pier()],
        'KIT_BorderStone': [stone_marker(0), stone_marker(1), stone_marker(2)],
        'KIT_BorderRope': [rope()], 'KIT_Jizo': [jizo()],
    }
