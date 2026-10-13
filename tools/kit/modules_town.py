"""Town modules: bridges, market stall, canal bank stones and cobbles, field ridges and crops, paddy bunds.

Same conventions as modules.py: metric, Z up, origin where the module touches the ground (bridges: deck centre, top of deck = z 0).
"""
import math
import bmesh
from mathutils import Vector, Matrix
from kit_lib import MB

PI = math.pi


# ======================================================================= bridges
def _rail_side(mb, y, x0, x1, z0=0.0, post_gap=1.15):
    """Timber railing along X at lateral position y: posts with caps, top / mid / low rails and balusters."""
    n = max(2, round((x1 - x0) / post_gap))
    xs = [x0 + i * (x1 - x0) / n for i in range(n + 1)]
    for i, x in enumerate(xs):
        mb.box((x - 0.07, y - 0.07, z0), (x + 0.07, y + 0.07, z0 + 1.06), 'Timber', grain=2, skip=('-z',))
        mb.box((x - 0.09, y - 0.09, z0 + 1.06), (x + 0.09, y + 0.09, z0 + 1.10), 'Timber', grain=0)
        if i in (0, n):                                           # onion-shaped end caps (giboshi)
            s = len(mb.bm.verts)
            mb.lathe([(0.05, 0.0), (0.075, 0.04), (0.06, 0.11), (0.03, 0.17), (0.0, 0.22)], 8, 'Timber', cap_top=False, smooth=True)
            for v in list(mb.bm.verts)[s:]:
                v.co += Vector((x, y, z0 + 1.10))
    for zr, h in ((z0 + 0.98, 0.10), (z0 + 0.60, 0.07), (z0 + 0.20, 0.07)):
        mb.box((x0 - 0.05, y - 0.04, zr), (x1 + 0.05, y + 0.04, zr + h), 'Timber', grain=0)
    nb = int((x1 - x0) / 0.20)
    for i in range(nb):
        x = x0 + (i + 0.5) * (x1 - x0) / nb
        if min(abs(x - px) for px in xs) < 0.12:
            continue
        mb.box((x - 0.015, y - 0.025, z0 + 0.27), (x + 0.015, y + 0.025, z0 + 0.98), 'Timber', grain=2)


def bridge_flat(width, name):
    mb = MB(name)
    L = 9.2; hw = width / 2.0
    for sx in (-1, 1):                                            # stone abutments down to the stream bed, wing stones
        a, b = sorted((sx * (L / 2 - 1.1), sx * (L / 2 + 0.25)))
        mb.box((a, -hw - 0.30, -2.6), (b, hw + 0.30, -0.12), 'StoneWall')
        mb.box((a - 0.05 * sx, -hw - 0.34, -0.30), (b + 0.05 * sx, hw + 0.34, -0.12), 'Stone')
        for k in (-1, 1):
            c, d = sorted((sx * (L / 2 + 0.25), sx * (L / 2 + 1.35)))
            mb.box((c, k * (hw + 0.30) - 0.20, -1.4), (d, k * (hw + 0.30) + 0.20, -0.15), 'StoneWall')
    nb = max(3, round(width / 1.0) + 1)                           # main beams and cross ties
    for i in range(nb):
        y = -hw + 0.35 + i * (width - 0.7) / (nb - 1)
        mb.box((-L / 2 + 0.55, y - 0.15, -0.46), (L / 2 - 0.55, y + 0.15, -0.09), 'Timber', grain=0)
    for x in (-2.2, 0.0, 2.2):
        mb.box((x - 0.07, -hw + 0.1, -0.56), (x + 0.07, hw - 0.1, -0.46), 'Timber', grain=1)
    for sx in (-1, 1):                                            # knee braces from the abutments to the beams
        for k in (-1, 1):
            yb = k * (hw - 0.35)
            M = Matrix.Translation((sx * 3.55, yb, -0.46)) @ Matrix.Rotation(sx * 0.80, 4, 'Y')
            mb.box((-0.07, -0.07, -1.05), (0.07, 0.07, 0.0), 'Timber', grain=2, M=M)
    n = int((L - 0.9) / 0.30)                                     # deck planks, across the span
    for i in range(n):
        xc = -L / 2 + 0.45 + (i + 0.5) * (L - 0.9) / n
        mb.box((xc - 0.138, -hw, -0.09), (xc + 0.138, hw, 0.0), 'Planks', grain=1)
    for k in (-1, 1):                                             # kerb + railings
        mb.box((-L / 2 + 0.45, k * (hw - 0.04) - 0.06, 0.0), (L / 2 - 0.45, k * (hw - 0.04) + 0.06, 0.09), 'Timber', grain=0)
        _rail_side(mb, k * (hw - 0.12), -L / 2 + 0.6, L / 2 - 0.6, z0=0.09)
    return mb


def bridge_arch(width=6.0, name='SM_Edo_Bridge_Arch'):
    """Stone arch bridge over a stream: span 18.2 m along X, crest 2.0 m above the ends, cobbled deck, parapets."""
    mb = MB(name)
    L = 18.2; H = 2.0; hw = width / 2.0; bed = -2.8; ax = 6.4; zc = -1.4; ry = 2.9
    zd = lambda x: H * (1.0 - (2.0 * x / L) ** 2)
    zb = lambda x: zc + ry * math.sqrt(max(0.0, 1.0 - (x / ax) ** 2))
    xs = sorted(set([round(-L / 2 + i * 0.5, 3) for i in range(int(L / 0.5) + 1)] + [-ax, ax]))
    inside = lambda xa, xb: abs((xa + xb) / 2.0) < ax
    T = 2.0
    for i in range(len(xs) - 1):
        xa, xb = xs[i], xs[i + 1]
        ba, bb = (zb(xa), zb(xb)) if inside(xa, xb) else (bed, bed)
        for y, nrm in ((-hw, (0, -1, 0)), (hw, (0, 1, 0))):
            vs = [mb.v((xa, y, ba)), mb.v((xb, y, bb)), mb.v((xb, y, zd(xb))), mb.v((xa, y, zd(xa)))]
            mb.face(vs, 'StoneWall', [(xa / T, ba / T), (xb / T, bb / T), (xb / T, zd(xb) / T), (xa / T, zd(xa) / T)], want=nrm)
        if inside(xa, xb):                                        # soffit of the arch
            vs = [mb.v((xa, -hw, ba)), mb.v((xb, -hw, bb)), mb.v((xb, hw, bb)), mb.v((xa, hw, ba))]
            mb.face(vs, 'StoneWall', [(xa / T, -hw / T), (xb / T, -hw / T), (xb / T, hw / T), (xa / T, hw / T)], smooth=True, want=(0, 0, -1))
        vs = [mb.v((xa, -hw, zd(xa))), mb.v((xb, -hw, zd(xb))), mb.v((xb, hw, zd(xb))), mb.v((xa, hw, zd(xa)))]    # cobbled deck
        mb.face(vs, 'Stone', [(xa, -hw), (xb, -hw), (xb, hw), (xa, hw)], want=(0, 0, 1))
    for sx in (-1, 1):                                            # inner pier faces and end walls
        x = sx * ax
        mb.face([mb.v((x, -hw, bed)), mb.v((x, hw, bed)), mb.v((x, hw, zc)), mb.v((x, -hw, zc))], 'StoneWall',
                [(-hw / T, bed / T), (hw / T, bed / T), (hw / T, zc / T), (-hw / T, zc / T)], want=(-sx, 0, 0))
        x = sx * L / 2
        mb.face([mb.v((x, -hw, bed)), mb.v((x, hw, bed)), mb.v((x, hw, 0.0)), mb.v((x, -hw, 0.0))], 'StoneWall',
                [(-hw / T, bed / T), (hw / T, bed / T), (hw / T, 0.0), (-hw / T, 0.0)], want=(sx, 0, 0))
    for k in (-1, 1):                                             # parapet walls with coping
        yc = k * (hw - 0.27)
        rings, cop = [], []
        for x in xs:
            z0 = zd(x)
            rings.append([(x, yc - 0.27, z0 - 0.05), (x, yc + 0.27, z0 - 0.05), (x, yc + 0.27, z0 + 0.92), (x, yc - 0.27, z0 + 0.92)])
            cop.append([(x, yc - 0.34, z0 + 0.92), (x, yc + 0.34, z0 + 0.92), (x, yc + 0.34, z0 + 1.04), (x, yc - 0.34, z0 + 1.04)])
        mb.loft(rings, 'StoneWall', closed=True, smooth=False, cap0=True, cap1=True, want_out=lambda m, yc=yc: Vector((0, m.y - yc, m.z - zd(m.x) - 0.45)))
        mb.loft(cop, 'Stone', closed=True, smooth=False, cap0=True, cap1=True, want_out=lambda m, yc=yc: Vector((0, m.y - yc, m.z - zd(m.x) - 0.98)))
    for i in range(1, 8):                                         # stone posts with caps on the crown of the parapet
        x = -L / 2 + i * L / 8
        for k in (-1, 1):
            z = zd(x) + 1.04
            mb.box((x - 0.2, k * (hw - 0.27) - 0.2, z), (x + 0.2, k * (hw - 0.27) + 0.2, z + 0.16), 'Stone')
    return mb


# ======================================================================= market stall
def stall():
    mb = MB('SM_Edo_Stall')                                       # plaza stall: gable cloth roof, counter, goods
    for x in (-1.5, 1.5):
        for y in (-1.0, 1.0):
            mb.box((x - 0.05, y - 0.05, 0.0), (x + 0.05, y + 0.05, 2.30), 'Timber', grain=2, skip=('-z',))
    for y in (-1.0, 1.0):
        mb.box((-1.6, y - 0.05, 2.20), (1.6, y + 0.05, 2.30), 'Timber', grain=0)
    mb.box((-1.6, -0.05, 2.55), (1.6, 0.05, 2.62), 'Timber', grain=0)
    for sy in (-1, 1):
        a = math.atan2(0.30, 1.0)
        M = Matrix.Translation((0.0, sy * 0.5, 2.40)) @ Matrix.Rotation(-sy * a, 4, 'X')
        mb.box((-1.65, -0.62, 0.0), (1.65, 0.62, 0.015), 'Cloth' if sy < 0 else 'ClothRed', M=M, grain=0)
    mb.box((-1.45, -0.30, 0.0), (1.45, 0.30, 0.84), 'Planks', grain=2, skip=('-z',))
    mb.box((-1.55, -0.40, 0.84), (1.55, 0.40, 0.90), 'Timber', grain=0)
    for x in (-1.1, -0.45, 0.2):                                  # baskets with produce
        s = len(mb.bm.verts)
        mb.lathe([(0.16, 0.0), (0.21, 0.07), (0.23, 0.15), (0.21, 0.16), (0.0, 0.16)], 10, 'Thatch', cap_top=False)
        mb.lathe([(0.20, 0.13), (0.15, 0.24), (0.07, 0.29), (0.0, 0.30)], 8, 'Leaf', cap_top=False)
        for v in list(mb.bm.verts)[s:]:
            v.co += Vector((x, 0.0, 0.90))
    for x in (0.85, 1.2):
        s = len(mb.bm.verts)
        prof = [(0.15, 0.0), (0.25, 0.10), (0.30, 0.30), (0.28, 0.50), (0.19, 0.61), (0.175, 0.65), (0.20, 0.68)]
        mb.lathe([(r * 0.5, h * 0.5) for r, h in prof], 10, 'Ceramic', cap_top=False)
        for v in list(mb.bm.verts)[s:]:
            v.co += Vector((x, 0.0, 0.90))
    for x in (-1.2, -0.4, 0.4, 1.2):                              # hanging goods under the ridge
        mb.box((x - 0.01, -0.01, 1.45), (x + 0.01, 0.01, 2.55), 'Thatch', grain=2)
        mb.box((x - 0.07, -0.05, 1.20), (x + 0.07, 0.05, 1.46), 'ClothRed' if x > 0 else 'Cloth')
    return mb


# ======================================================================= canal bank: curb, cobbles, rocks
def _bevel(mb, off=0.03):
    bmesh.ops.bevel(mb.bm, geom=list(mb.bm.edges), offset=off, segments=1, affect='EDGES')


def embank_curb():
    mb = MB('SM_Edo_EmbankCurb')                                  # 2 m of rough ashlar curb, two courses, joints staggered
    rnd = mb.rng
    for course, (z0, z1, w, off) in enumerate(((-0.20, 0.27, 0.58, 0.0), (0.27, 0.56, 0.50, 0.04))):
        x = -1.0 + (0.0 if course == 0 else 0.22)
        while x < 0.99:
            ln = rnd.uniform(0.42, 0.62)
            x1 = min(x + ln, 1.0 if course == 0 else 1.0)
            if 1.0 - x1 < 0.25:
                x1 = 1.0
            mb.box((x + 0.012, off - w / 2 + rnd.uniform(-0.02, 0.02), z0 + 0.005), (x1 - 0.012, off + w / 2 + rnd.uniform(-0.02, 0.02), z1 - rnd.uniform(0.0, 0.025)), 'StoneWall', grain=0)
            x = x1
    _bevel(mb, 0.025)
    return mb


def embank_cobble():
    mb = MB('SM_Edo_EmbankCobble')                                # 2 x 2 m cobblestone paving: slab + individual rounded stones
    rnd = mb.rng
    mb.box((-1.0, -1.0, -0.10), (1.0, 1.0, 0.02), 'StoneWall', skip=('-z',))
    n = 7; step = 2.0 / n
    for i in range(n):
        for j in range(n):
            r = rnd.uniform(0.105, 0.135)
            cx = -1.0 + (i + 0.5) * step + (0.5 * step if j % 2 else 0.0) - (0.25 * step) + rnd.uniform(-0.02, 0.02)
            cy = -1.0 + (j + 0.5) * step + rnd.uniform(-0.02, 0.02)
            if abs(cx) > 1.0 - r * 0.6:
                continue
            s = len(mb.bm.verts)
            h = rnd.uniform(0.07, 0.10)
            mb.lathe([(0.0, 0.0), (r, 0.0), (r * 1.02, h * 0.45), (r * 0.78, h * 0.9), (0.0, h)], 7, 'Stone' if rnd.random() < 0.4 else 'StoneWall', cap_top=False, smooth=True, phase=rnd.random() * 3)
            for v in list(mb.bm.verts)[s:]:
                v.co += Vector((cx, cy, 0.0))
    return mb


def embank_rock(seed):
    mb = MB(f'SM_Edo_EmbankRock_{"ABC"[seed]}')                   # irregular boulder, flat bottom
    rnd = mb.rng
    bm = mb.bm
    geom = bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0)
    sx, sy, sz = (0.55, 0.42, 0.30) if seed == 0 else (0.38, 0.34, 0.26) if seed == 1 else (0.72, 0.5, 0.36)
    for v in geom['verts']:
        k = 1.0 + rnd.uniform(-0.18, 0.18)
        v.co = Vector((v.co.x * sx * k, v.co.y * sy * k, max(v.co.z, -0.35) * sz * k))
        v.co.z = max(v.co.z, -0.05) + 0.0
    for f in bm.faces:
        f.material_index = mb.mi('StoneWall'); f.smooth = True
        for lp in f.loops:
            lp[mb.uv].uv = (lp.vert.co.x / 2.0 + lp.vert.co.z / 3.0, lp.vert.co.y / 2.0)
    return mb


# ======================================================================= fields: ridges, crops, paddy bund
def _blade(mb, base, ang, h, bend, w0, mat, segs=3, v_scale=0.5):
    ca, sa = math.cos(ang), math.sin(ang)
    px, py = -sa, ca
    L, R = [], []
    for k in range(segs + 1):
        t = k / segs
        w = w0 * (1.0 - 0.85 * t ** 1.4)
        d = bend * t * t
        c = (base[0] + ca * d, base[1] + sa * d, base[2] + h * t * (1.0 - 0.12 * t))
        L.append((c[0] - px * w, c[1] - py * w, c[2])); R.append((c[0] + px * w, c[1] + py * w, c[2]))
    for k in range(segs):
        uv = [(0.0, k / segs * h / v_scale), (1.0, k / segs * h / v_scale), (1.0, (k + 1) / segs * h / v_scale), (0.0, (k + 1) / segs * h / v_scale)]
        a = [mb.v(L[k]), mb.v(R[k]), mb.v(R[k + 1]), mb.v(L[k + 1])]
        mb.face(a, mat, uv, smooth=True)
        b = [mb.v((p[0], p[1], p[2] + 0.0004)) for p in (L[k], R[k], R[k + 1], L[k + 1])]
        mb.face(list(reversed(b)), mat, list(reversed(uv)), smooth=True)


def crop_ridge():
    mb = MB('SM_Edo_CropRidge')                                   # 2 m of earth ridge (0.8 m wide, 0.22 m high) with a furrow either side
    rnd = mb.rng
    prof = [(-0.46, -0.03), (-0.40, 0.0), (-0.30, 0.10), (-0.14, 0.19), (0.0, 0.22), (0.14, 0.19), (0.30, 0.10), (0.40, 0.0), (0.46, -0.03)]
    rings = []
    for i in range(9):
        x = -1.0 + i * 0.25
        j = rnd.uniform(0.0, 0.02) if 0 < i < 8 else 0.0
        rings.append([(x, y, z + j * (0.4 if abs(y) > 0.3 else 1.0)) for y, z in prof])
    mb.loft(rings, 'Soil', closed=False, smooth=True, want_out=lambda m: Vector((0, 0, 1)), uv_scale=1.0)
    return mb


def paddy_bund():
    mb = MB('SM_Edo_PaddyBund')                                   # 2 m earth bund between paddies
    prof = [(-0.34, -0.05), (-0.20, 0.26), (0.20, 0.26), (0.34, -0.05)]
    rings = [[(-1.0 + i * 0.5, y, z + (0.01 if i in (1, 3) else 0.0)) for y, z in prof] for i in range(5)]
    mb.loft(rings, 'Soil', closed=False, smooth=True, want_out=lambda m: Vector((0, 0, 1)), uv_scale=1.0)
    return mb


def crop_cabbage(v):
    mb = MB(f'SM_Edo_CropCabbage_{"AB"[v]}')
    k = 1.0 if v == 0 else 0.82
    mb.lathe([(0.0, 0.0), (0.12 * k, 0.015), (0.21 * k, 0.09), (0.26 * k, 0.19), (0.22 * k, 0.27), (0.14 * k, 0.29)], 10, 'Leaf', cap_top=False, smooth=True, phase=v)
    mb.lathe([(0.15 * k, 0.08), (0.19 * k, 0.17), (0.15 * k, 0.26), (0.07 * k, 0.31), (0.0, 0.32 * k)], 8, 'Leaf', cap_top=False, smooth=True, phase=0.4)
    for i in range(6):                                            # outer leaves flopping out
        a = i * PI / 3 + 0.3 * v
        _blade(mb, (0.10 * math.cos(a), 0.10 * math.sin(a), 0.03), a, 0.10, 0.26 * k, 0.085, 'Leaf', segs=2)
    return mb


def crop_daikon():
    mb = MB('SM_Edo_CropDaikon')                                  # leafy fountain of a radish / turnip
    rnd = mb.rng
    for i in range(9):
        a = i * 2 * PI / 9 + rnd.uniform(-0.2, 0.2)
        _blade(mb, (0.03 * math.cos(a), 0.03 * math.sin(a), 0.0), a, rnd.uniform(0.32, 0.46), rnd.uniform(0.18, 0.30), 0.045, 'Leaf', segs=4)
    s = len(mb.bm.verts)
    mb.lathe([(0.0, 0.0), (0.05, 0.0), (0.05, 0.05), (0.0, 0.06)], 6, 'Ceramic', cap_top=False)
    return mb


def crop_barley(v):
    mb = MB(f'SM_Edo_CropBarley_{"AB"[v]}')
    rnd = mb.rng
    for i in range(16):
        a = rnd.uniform(0, 2 * PI); r = rnd.uniform(0.0, 0.07)
        h = rnd.uniform(0.62, 0.86) * (1.0 if v == 0 else 0.85)
        bend = rnd.uniform(0.05, 0.16)
        base = (r * math.cos(a), r * math.sin(a), 0.0)
        _blade(mb, base, a, h * 0.8, bend * 0.8, 0.014, 'Leaf', segs=3)
        s = len(mb.bm.verts)
        mb.lathe([(0.0, 0.0), (0.016, 0.01), (0.020, 0.05), (0.012, 0.085), (0.0, 0.10)], 5, 'Grain', cap_top=False, smooth=True)
        t = 1.0
        for vv in list(mb.bm.verts)[s:]:
            vv.co += Vector((base[0] + math.cos(a) * bend * 0.8, base[1] + math.sin(a) * bend * 0.8, h * 0.8 * 0.9))
    return mb


def crop_rice(v):
    mb = MB(f'SM_Edo_CropRice_{"AB"[v]}')
    rnd = mb.rng
    for i in range(12):
        a = i * 2 * PI / 12 + rnd.uniform(-0.3, 0.3)
        _blade(mb, (0.02 * math.cos(a), 0.02 * math.sin(a), 0.0), a, rnd.uniform(0.30, 0.46) * (1.0 if v == 0 else 1.2), rnd.uniform(0.10, 0.22), 0.012, 'Leaf' if v == 0 else 'Grain', segs=3)
    return mb


def build_town():
    return {
        'KIT_Bridge': [bridge_arch(), bridge_flat(4.0, 'SM_Edo_Bridge_Flat4'), bridge_flat(6.4, 'SM_Edo_Bridge_Flat6')],
        'KIT_Stall': [stall()],
        'KIT_EmbankCurb': [embank_curb()],
        'KIT_EmbankCobble': [embank_cobble()],
        'KIT_EmbankRock': [embank_rock(0), embank_rock(1), embank_rock(2)],
        'KIT_CropRidge': [crop_ridge()],
        'KIT_PaddyBund': [paddy_bund()],
        'KIT_CropVeg': [crop_cabbage(0), crop_cabbage(1), crop_daikon()],
        'KIT_CropGrain': [crop_barley(0), crop_barley(1)],
        'KIT_CropRice': [crop_rice(0), crop_rice(1)],
    }
