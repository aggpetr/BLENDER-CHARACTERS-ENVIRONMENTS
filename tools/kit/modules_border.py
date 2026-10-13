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
    mb = MB(f'SM_Edo_BorderStone_{"ABC"[v]}'); rnd = mb.rng           # standing boundary stone, a little different each time
    h = (1.25, 1.05, 1.45)[v]; w = (0.40, 0.46, 0.34)[v]
    prof = [(0.0, 0.0), (w * 0.95, 0.0), (w, h * 0.35), (w * 0.82, h * 0.75), (w * 0.45, h * 0.95), (0.0, h)]
    s = len(mb.bm.verts)
    mb.lathe(prof, 8, 'StoneWall', cap_top=False, smooth=True, phase=rnd.random() * 3)
    for vv in list(mb.bm.verts)[s:]:
        vv.co.x *= 1.0 + rnd.uniform(-0.12, 0.12); vv.co.y *= 0.8 + rnd.uniform(-0.1, 0.15); vv.co.z += rnd.uniform(-0.02, 0.03) * vv.co.z
    mb.box((-0.06, -0.03, h * 0.62), (0.06, 0.03, h * 0.62 + 0.06), 'Iron')        # an iron ring to hang the rope from (stone is not smooth enough for a clip)
    return mb


def rope():
    mb = MB('SM_Edo_BorderRope'); L = 6.0; sag = 0.42; z0 = 0.95
    rings = []
    for i in range(31):
        t = i / 30; x = -L / 2 + t * L; z = z0 - sag * 4 * t * (1 - t)
        rings.append([(x, 0.055 * math.cos(a), z + 0.055 * math.sin(a)) for a in [j * PI / 3 for j in range(6)]])
    mb.loft(rings, 'Thatch', closed=True, smooth=True, cap0=True, cap1=True, want_out=lambda m: Vector((0, m.y, m.z - z0 + 0.2)), uv_scale=0.4)
    for t in (0.17, 0.33, 0.5, 0.67, 0.83):                                    # paper streamers (shide): three zig-zag folds each
        x = -L / 2 + t * L; z = z0 - sag * 4 * t * (1 - t)
        for k in range(3):
            zz = z - 0.08 - k * 0.17
            mb.box((x - 0.065 + 0.03 * (k % 2), -0.012, zz - 0.15), (x + 0.065 + 0.03 * (k % 2), 0.012, zz), 'Paper')
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
