"""Edo house kit modules (prototype set for dwellA and its size variants).

Conventions (all modules):
  * metres, Z up; wall/side modules face their exterior toward local -Y
  * origin on the floor top of the storey the module belongs to (fence/props/footings: on the ground)
  * bay modules are centred on their bay; grid = 1 bay (B = 1.82 m)
"""
import math
from mathutils import Vector, Matrix
from kit_lib import (MB, B, STOREY, KETA_TOP, EAVE_Z, ROOF_O, PITCH, ROOF_P, CORNER_RISE, RIB, RIB_A, MAX_DEPTH)

H = B / 2           # half bay
POST = 0.16         # storey post section
IN = H - POST / 2   # infill half-width between posts (0.83)


# ======================================================================= foundation and floor
def footing(variant):
    mb = MB(f'SM_Edo_Footing_{variant}')
    rnd = mb.rng
    segs, rings = 8, 4
    rx, ry = 0.20 + rnd.uniform(-0.02, 0.02), 0.19 + rnd.uniform(-0.02, 0.02)
    prof = []
    for i in range(rings + 1):
        a = -0.35 * math.pi + (0.73 * math.pi) * i / rings          # from below ground up to a flattened top
        prof.append((math.cos(a), math.sin(a)))
    jit = [1 + rnd.uniform(-0.10, 0.10) for _ in range(segs)]
    grid = []
    for i, (c, s) in enumerate(prof):
        ring = []
        for k in range(segs):
            t = 2 * math.pi * k / segs
            j = jit[k] * (1 + rnd.uniform(-0.04, 0.04))
            z = 0.06 + s * 0.15
            ring.append((rx * c * j * math.cos(t), ry * c * j * math.sin(t), z))
        grid.append(ring)
    grid[-1] = [(x, y, 0.20) for x, y, _ in grid[-1]]
    mb.loft(grid, 'Stone', closed=True, smooth=True, cap1=True, want_out=lambda m: Vector((m.x, m.y, m.z - 0.05)), uv_scale=1.0)
    return mb


def post(name, section, length, top=0.0):
    mb = MB(name)
    s = section / 2
    mb.box((-s, -s, top - length), (s, s, top), 'Timber', grain=2, skip=('-z',))
    return mb


def floor_beam():
    mb = MB('SM_Edo_FloorBeam')                 # along local X, one bay; top 3 cm below the floor top
    mb.box((-H, -0.065, -0.25), (H, 0.065, -0.03), 'Timber', grain=0)
    return mb


def floor_deck():
    mb = MB('SM_Edo_FloorDeck')
    mb.box((-H, -H, -0.03), (H, H, 0.0), 'Planks', grain=0)
    return mb


def storey_post():
    mb = MB('SM_Edo_Post_Storey')
    s = POST / 2
    mb.box((-s, -s, -0.25), (s, s, KETA_TOP), 'Timber', grain=2, skip=('-z',))
    return mb


# ======================================================================= walls (one bay, between posts)
def _wall_top(mb, plaster_from):
    mb.box((-IN, -0.065, KETA_TOP - 0.22), (IN, 0.065, KETA_TOP), 'Timber', grain=0)            # keta (top beam)
    mb.box((-IN, -0.085, 1.80), (IN, -0.045, 1.92), 'Timber', grain=0)                         # nageshi (outer tie beam)
    mb.box((-IN, -0.045, plaster_from), (IN, 0.045, KETA_TOP - 0.22), 'Plaster')               # upper wall (komakabe)


def _wainscot(mb, top):
    mb.box((-IN, -0.045, 0.0), (IN, 0.045, top), 'Plaster')                                     # wall core
    mb.box((-IN, -0.075, 0.0), (IN, -0.045, top), 'Planks', grain=2)                            # vertical boards (koshi-ita)
    mb.box((-IN, -0.092, top - 0.05), (IN, -0.045, top), 'Timber', grain=0)                     # capping rail
    for x in (-0.42, 0.42):
        mb.box((x - 0.02, -0.088, 0.0), (x + 0.02, -0.075, top - 0.05), 'Timber', grain=2)      # battens


def wall_A():   # plaster over wooden wainscot
    mb = MB('SM_Edo_Wall_A_Plaster')
    _wainscot(mb, 0.95)
    mb.box((-IN, -0.045, 0.95), (IN, 0.045, 1.80), 'Plaster')
    _wall_top(mb, 1.80)
    return mb


def wall_B():   # lattice window (koshi-mado) with paper behind
    mb = MB('SM_Edo_Wall_B_Lattice')
    _wainscot(mb, 0.90)
    mb.box((-IN, -0.105, 0.90), (IN, 0.05, 0.95), 'Timber', grain=0)                           # sill
    mb.box((-IN, -0.075, 1.74), (IN, 0.06, 1.80), 'Timber', grain=0)                           # head (kamoi)
    for x in (-IN, IN - 0.045):
        mb.box((x, -0.10, 0.95), (x + 0.045, -0.04, 1.74), 'Timber', grain=2)                  # frame stiles
    n = 19; span = 2 * IN - 0.09
    for i in range(1, n + 1):
        x = -IN + 0.045 + span * i / (n + 1)
        mb.box((x - 0.015, -0.098, 0.95), (x + 0.015, -0.062, 1.74), 'Timber', grain=2)        # lattice slats
    mb.box((-IN + 0.045, -0.062, 1.33), (IN - 0.045, -0.045, 1.36), 'Timber', grain=0)         # nuki rail
    mb.box((-IN, -0.02, 0.95), (IN, 0.0, 1.74), 'Paper')                                       # shoji paper behind
    _wall_top(mb, 1.80)
    return mb


def wall_C():   # pair of sliding board doors (itado)
    mb = MB('SM_Edo_Wall_C_Door')
    mb.box((-IN, -0.10, 0.0), (IN, 0.06, 0.03), 'Timber', grain=0)                             # threshold (shikii)
    mb.box((-IN, -0.10, 1.80), (IN, 0.06, 1.86), 'Timber', grain=0)                            # head (kamoi)
    for x0, x1, y0 in ((-IN, 0.03, -0.085), (-0.03, IN, -0.045)):
        y1 = y0 + 0.035
        mb.box((x0, y0, 0.03), (x1, y1, 1.80), 'Planks', grain=2)
        for xs in (x0, x1 - 0.045):
            mb.box((xs, y0 - 0.012, 0.03), (xs + 0.045, y1 + 0.004, 1.80), 'Timber', grain=2)  # stiles
        for z in (0.12, 0.92, 1.68):
            mb.box((x0 + 0.045, y0 - 0.02, z), (x1 - 0.045, y0, z + 0.06), 'Timber', grain=0)  # battens
    mb.box((-IN, -0.045, 1.86), (IN, 0.045, 1.92), 'Plaster')
    _wall_top(mb, 1.86)
    return mb


def wall_D():   # shoji screens (behind the engawa)
    mb = MB('SM_Edo_Wall_D_Shoji')
    mb.box((-IN, -0.06, 0.0), (IN, 0.06, 0.03), 'Timber', grain=0)
    mb.box((-IN, -0.06, 1.80), (IN, 0.06, 1.86), 'Timber', grain=0)
    for x0, x1, y0 in ((-IN, 0.02, -0.045), (-0.02, IN, 0.005)):
        y1 = y0 + 0.032
        mb.box((x0, y0, 0.03), (x1, y1, 0.28), 'Planks', grain=0)                              # koshi board
        for xs in (x0, x1 - 0.03):
            mb.box((xs, y0, 0.03), (xs + 0.03, y1, 1.80), 'Timber', grain=2)
        for z0, z1 in ((0.28, 0.32), (1.76, 1.80)):
            mb.box((x0 + 0.03, y0, z0), (x1 - 0.03, y1, z1), 'Timber', grain=0)
        w = (x1 - x0 - 0.06)
        for k in range(1, 4):                                                                  # kumiko grid
            x = x0 + 0.03 + w * k / 4
            mb.box((x - 0.006, y0 + 0.004, 0.32), (x + 0.006, y1 - 0.012, 1.76), 'Timber', grain=2)
        for k in range(1, 7):
            z = 0.32 + 1.44 * k / 7
            mb.box((x0 + 0.03, y0 + 0.004, z - 0.006), (x1 - 0.03, y1 - 0.012, z + 0.006), 'Timber', grain=0)
        mb.box((x0 + 0.03, y1 - 0.012, 0.32), (x1 - 0.03, y1 - 0.009, 1.76), 'Paper')
    mb.box((-IN, -0.045, 1.86), (IN, 0.045, 1.92), 'Plaster')
    _wall_top(mb, 1.86)
    return mb


def wall_E():   # plain plaster with a low skirting board
    mb = MB('SM_Edo_Wall_E_PlasterFull')
    mb.box((-IN, -0.045, 0.0), (IN, 0.045, 1.80), 'Plaster')
    mb.box((-IN, -0.07, 0.0), (IN, -0.045, 0.30), 'Planks', grain=0)
    _wall_top(mb, 1.80)
    return mb


# ======================================================================= roof (hip roof, tile) -- shared height field
class Roof:
    """Height field of a hip roof whose short side is n bays. Local frame of an END module:
    x' = 0 on the end wall line, the roof edge at x' = -o, the end/mid junction at x' = D/2; y = 0 on the ridge."""

    def __init__(self, n):
        self.n = n; self.D = n * B; self.o = ROOF_O
        self.R = self.D / 2 + self.o; self.H = PITCH * self.R
        self.Lr = min(2.2, self.R)
        steps = 400; self._arc = [0.0]
        for i in range(1, steps + 1):
            d0, d1 = self.R * (i - 1) / steps, self.R * i / steps
            self._arc.append(self._arc[-1] + math.hypot(d1 - d0, self.zs(d1) - self.zs(d0)))

    def zs(self, d):
        s = min(max(d / self.R, 0.0), 1.0)
        return EAVE_Z + self.H * s ** ROOF_P

    def rise(self, t):
        c = max(0.0, 1.0 - t / self.Lr)
        return CORNER_RISE * c * c

    def arc(self, d):
        i = min(max(d / self.R, 0.0), 1.0) * (len(self._arc) - 1)
        i0 = int(i); i1 = min(i0 + 1, len(self._arc) - 1)
        return self._arc[i0] + (self._arc[i1] - self._arc[i0]) * (i - i0)

    def rows(self):
        J = max(3, math.ceil(self.R / 0.55))
        return [self.R * j / J for j in range(J + 1)]

    @staticmethod
    def rip(c):
        return RIB_A * math.cos(2 * math.pi * c / RIB)


def _zipper(mb, A, Bv, mat, want):
    """A, Bv: lists of (along, BMVert, uv). Triangulates the band between two rows."""
    i = j = 0
    while i < len(A) - 1 or j < len(Bv) - 1:
        if j >= len(Bv) - 1 or (i < len(A) - 1 and A[i + 1][0] <= Bv[j + 1][0]):
            tri = [A[i], A[i + 1], Bv[j]]; i += 1
        else:
            tri = [A[i], Bv[j + 1], Bv[j]]; j += 1
        mb.face([t[1] for t in tri], mat, [t[2] for t in tri], smooth=True, want=want)


def _surface(mb, rows, mat='Kawara', want=(0, 0, 1)):
    for a, b in zip(rows[:-1], rows[1:]):
        _zipper(mb, a, b, mat, want)


def _grid(lo, hi, step, anchor):
    """grid values in (lo, hi) aligned to anchor + k*step."""
    k0 = math.ceil((lo - anchor) / step + 1e-9); k1 = math.floor((hi - anchor) / step - 1e-9)
    return [anchor + k * step for k in range(k0, k1 + 1)]


def _side_face(mb, rf, x_lo_of_d, x_hi, sign, end_module):
    """Long-slope face (sign=-1: -Y side, +1: +Y side), between x_lo(d) and x_hi along x."""
    q = RIB / 4
    rows = []; eave_top = []
    for d in rf.rows():
        lo = x_lo_of_d(d)
        xs = [lo] + _grid(lo, x_hi, q, x_hi) + [x_hi] if x_hi - lo > 1e-6 else [x_hi]
        y = sign * (rf.R - d)
        row = []
        for x in xs:
            ax = (x + rf.o) if end_module else 1e9
            z = rf.zs(d) + rf.rise(max(ax, d)) + rf.rip(x - x_hi if end_module else x)
            u = -sign * ((x - x_hi) if end_module else x) / B
            row.append((x, mb.v((x, y, z)), (u, rf.arc(d) / B)))
        rows.append(row)
        if d == 0.0:
            eave_top = [(x, y) for x in xs]
    _surface(mb, rows)
    return eave_top


def _end_face(mb, rf):
    q = RIB / 4
    rows = []; eave_top = []
    for d in rf.rows():
        half = rf.R - d; x = -rf.o + d
        ys = [-half] + _grid(-half, half, q, 0.0) + [half] if half > 1e-6 else [0.0]
        row = []
        for y in ys:
            z = rf.zs(d) + rf.rise(max(d, rf.R - abs(y))) + rf.rip(y)
            row.append((y, mb.v((x, y, z)), (-y / B, rf.arc(d) / B)))
        rows.append(row)
        if d == 0.0:
            eave_top = [(x, y) for y in ys]
    _surface(mb, rows)
    return eave_top


def _eave_strip(mb, rf, pts, outward, end_module, tile_rip):
    """Vertical tile-end strip under the eave edge, following the ribs (pts: plan points of the d=0 row)."""
    for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
        quad = []; uvs = []
        for (x, y), top in (((x0, y0), True), ((x1, y1), True), ((x1, y1), False), ((x0, y0), False)):
            ax = (x + rf.o) if end_module else 1e9
            ay = rf.R - abs(y)
            t = max(ax, ay)
            z = rf.zs(0.0) + rf.rise(t) + (tile_rip(x, y) if top else -0.13)
            quad.append(mb.v((x, y, z))); uvs.append(((x + y) / B, z / B))
        mb.face(quad, 'Kawara', uvs, want=outward)


def _soffit_and_rafters(mb, rf, face, x_hi=None):
    """Underside boards, rafters and the frieze closing the gap down to the top beam.
    face: 'side-' / 'side+' (end module), 'end', 'mid-' / 'mid+'."""
    o = rf.o; dmax = o + 0.12
    ds = [0.0, dmax * 0.5, dmax]
    end_module = face.startswith('side') or face == 'end'

    def zsof(d, t):
        return rf.zs(d) + rf.rise(t) - 0.13

    rows = []
    for d in ds:
        if face == 'end':
            half = rf.R - d; x = -o + d
            alongs = [-half] + _grid(-half, half, B / 8, 0.0) + [half]
            row = [(a, mb.v((x, a, zsof(d, max(d, rf.R - abs(a))))), (d / 2.0, a / 2.0)) for a in alongs]
        else:
            sign = -1 if face.endswith('-') else 1
            y = sign * (rf.R - d)
            if end_module:
                lo = -o + d
                alongs = [lo] + _grid(lo, x_hi, B / 8, x_hi) + [x_hi]
            else:
                alongs = [k * B / 8 for k in range(9)]
            row = [(a, mb.v((a, y, zsof(d, max((a + o) if end_module else 1e9, d)))), (d / 2.0, a / 2.0)) for a in alongs]
        rows.append(row)
    for a, b in zip(rows[:-1], rows[1:]):
        _zipper(mb, a, b, 'Planks', (0, 0, -1))

    # frieze: plaster strip on the wall line from the top beam up to the soffit
    dw = o - 0.05
    if face == 'end':
        half = rf.R - dw; xw = -o + dw
        alongs = [-half] + _grid(-half, half, B / 8, 0.0) + [half]
        pts = [((xw, a), max(dw, rf.R - abs(a))) for a in alongs]; outward = (-1, 0, 0)
    else:
        sign = -1 if face.endswith('-') else 1
        yw = sign * (rf.R - dw)
        if end_module:
            lo = -o + dw; alongs = [lo] + _grid(lo, x_hi, B / 8, x_hi) + [x_hi]
        else:
            alongs = [k * B / 8 for k in range(9)]
        pts = [((a, yw), max((a + o) if end_module else 1e9, dw)) for a in alongs]; outward = (0, sign, 0)
    for ((p0, t0), (p1, t1)) in zip(pts[:-1], pts[1:]):
        quad = [mb.v((p0[0], p0[1], KETA_TOP - 0.05)), mb.v((p1[0], p1[1], KETA_TOP - 0.05)),
                mb.v((p1[0], p1[1], zsof(dw, t1) + 0.01)), mb.v((p0[0], p0[1], zsof(dw, t0) + 0.01))]
        uvs = [((p0[0] + p0[1]) / 2, quad[0].co.z / 2), ((p1[0] + p1[1]) / 2, quad[1].co.z / 2),
               ((p1[0] + p1[1]) / 2, quad[2].co.z / 2), ((p0[0] + p0[1]) / 2, quad[3].co.z / 2)]
        mb.face(quad, 'Plaster', uvs, want=outward)

    # rafters (taruki), 4 per bay, clipped at the hip line
    def rafter(path):
        rings = []
        for (px, py, d, t, dirv) in path:
            z = zsof(d, t)
            side = Vector((-dirv[1], dirv[0], 0)) * 0.03
            c = Vector((px, py, z))
            rings.append([tuple(c - side), tuple(c + side), tuple(c + side - Vector((0, 0, 0.075))), tuple(c - side - Vector((0, 0, 0.075)))])
        axis = [sum((Vector(p) for p in r), Vector()) / 4 for r in rings]
        mb.loft(rings, 'Timber', closed=True, smooth=False, cap0=True, want_out=_axis_want(axis))
    if face == 'end':
        ys = []
        k = 0
        while B / 8 + k * B / 4 < rf.R:
            ys += [B / 8 + k * B / 4, -(B / 8 + k * B / 4)]; k += 1
        for yr in ys:
            ay = rf.R - abs(yr); L = min(dmax, ay - 0.03)
            if L < 0.12: continue
            path = [(-o + d, yr, d, max(d, ay), (1, 0)) for d in (0.04, L * 0.5, L)]
            rafter(path)
    else:
        sign = -1 if face.endswith('-') else 1
        if end_module:
            xs = []; k = 0
            while x_hi - (B / 8 + k * B / 4) > -o + 0.05:
                xs.append(x_hi - (B / 8 + k * B / 4)); k += 1
        else:
            xs = [B / 8 + k * B / 4 for k in range(4)]
        for xr in xs:
            ax = (xr + o) if end_module else 1e9
            L = min(dmax, ax - 0.03)
            if L < 0.12: continue
            path = [(xr, sign * (rf.R - d), d, max(ax, d), (0, -sign)) for d in (0.04, L * 0.5, L)]
            rafter(path)


def _axis_want(pts, up=0.0):
    """want-normal function: away from the nearest point of a polyline axis (raised by `up`)."""
    P = [Vector(p) for p in pts]
    def f(m):
        best, bd = P[0], 1e18
        for a, b in zip(P[:-1], P[1:]):
            ab = b - a; t = max(0.0, min(1.0, (m - a).dot(ab) / max(ab.length_squared, 1e-12)))
            c = a + ab * t; dd = (m - c).length_squared
            if dd < bd: bd, best = dd, c
        return m - (best + Vector((0, 0, up)))
    return f


CAP_HIP = [(-0.13, -0.06), (-0.13, 0.10), (-0.08, 0.17), (0.0, 0.19), (0.08, 0.17), (0.13, 0.10), (0.13, -0.06)]
CAP_RIDGE = [(-0.15, -0.07), (-0.15, 0.20), (-0.11, 0.28), (0.0, 0.31), (0.11, 0.28), (0.15, 0.20), (0.15, -0.07)]
ONI = [(-0.24, 0.0), (-0.24, 0.32), (-0.16, 0.47), (0.0, 0.54), (0.16, 0.47), (0.24, 0.32), (0.24, 0.0)]


def _sweep(mb, path, profile, cap0=False, cap1=False):
    """path: list of (point Vector, plan direction Vector(unit, z=0)); profile (s, h) in the vertical plane across the path."""
    rings = []
    for p, dirv in path:
        perp = Vector((-dirv.y, dirv.x, 0.0))
        rings.append([tuple(p + perp * s + Vector((0, 0, h))) for s, h in profile])
    mb.loft(rings, 'Kawara', closed=False, smooth=True, cap0=cap0, cap1=cap1,
            want_out=_axis_want([p for p, _ in path], up=0.07), uv_scale=B)


def _prism(mb, front, back, mat='Kawara'):
    """Closed prism between two equal polygons (lists of tuples)."""
    rings = [front, back]
    mb.loft(rings, mat, closed=True, smooth=False, cap0=True, cap1=True,
            want_out=lambda m, c=sum((Vector(p) for p in front + back), Vector()) / (2 * len(front)): m - c, uv_scale=B)


def _hips(mb, rf, corner_oni=True):
    for sign in (-1, 1):
        C = Vector((-rf.o, sign * rf.R, 0)); J = Vector((rf.D / 2, 0, 0))
        dirv = (J - C); dirv.z = 0; dirv.normalize()
        path = []
        for i in range(13):
            t = 0.03 + 0.97 * i / 12
            p = C + (J - C) * t
            d = t * rf.R
            p.z = rf.zs(d) + rf.rise(d) + RIB_A + 0.005
            path.append((p, dirv))
        _sweep(mb, path, CAP_HIP, cap0=True)
        if corner_oni:
            p = path[0][0]; f = p - dirv * 0.02; bk = p + dirv * 0.10
            perp = Vector((-dirv.y, dirv.x, 0.0))
            sil = [(-0.14, 0.0), (-0.14, 0.18), (-0.09, 0.27), (0.0, 0.31), (0.09, 0.27), (0.14, 0.18), (0.14, 0.0)]
            front = [tuple(f + perp * s + Vector((0, 0, h - 0.04 + 0.12 * (h / 0.31)))) for s, h in sil]
            back = [tuple(bk + perp * s + Vector((0, 0, h - 0.02))) for s, h in sil]
            _prism(mb, front, back)


def _ridge(mb, rf, x0, x1, cap0=False):
    z = rf.zs(rf.R) + RIB_A + 0.005
    path = [(Vector((x0, 0, z)), Vector((1, 0, 0))), (Vector((x1, 0, z)), Vector((1, 0, 0)))]
    _sweep(mb, path, CAP_RIDGE, cap0=cap0)


def roof_end(n, apex=False):
    rf = Roof(n)
    mb = MB(f'SM_Edo_Roof{"EndApex" if apex else "End"}_D{n}')
    xh = rf.D / 2
    tops = {}
    tops['-'] = _side_face(mb, rf, lambda d: -rf.o + d, xh, -1, True)
    tops['+'] = _side_face(mb, rf, lambda d: -rf.o + d, xh, 1, True)
    tops['e'] = _end_face(mb, rf)
    _eave_strip(mb, rf, tops['-'], (0, -1, 0), True, lambda x, y: rf.rip(x - xh))
    _eave_strip(mb, rf, tops['+'], (0, 1, 0), True, lambda x, y: rf.rip(x - xh))
    _eave_strip(mb, rf, tops['e'], (-1, 0, 0), True, lambda x, y: rf.rip(y))
    for f in ('side-', 'side+'):
        _soffit_and_rafters(mb, rf, f, x_hi=xh)
    _soffit_and_rafters(mb, rf, 'end')
    _hips(mb, rf)
    if not apex:
        _ridge(mb, rf, xh - 0.20, xh, cap0=True)
        z = rf.zs(rf.R) + RIB_A - 0.05
        front = [(xh - 0.34, s, z + h) for s, h in ONI]
        back = [(xh - 0.20, s, z + h) for s, h in ONI]
        _prism(mb, front, back)
    return mb


def roof_mid(n):
    rf = Roof(n)
    mb = MB(f'SM_Edo_RoofMid_D{n}')
    for sign, key in ((-1, 'mid-'), (1, 'mid+')):
        top = _side_face(mb, rf, lambda d: 0.0, B, sign, False)
        _eave_strip(mb, rf, top, (0, sign, 0), False, lambda x, y: rf.rip(x))
        _soffit_and_rafters(mb, rf, key)
    _ridge(mb, rf, 0.0, B)
    return mb


def roof_apex(n):
    rf = Roof(n)
    mb = MB(f'SM_Edo_RoofApex_D{n}')
    z = rf.zs(rf.R) + RIB_A - 0.02
    mb.box((-0.21, -0.21, z), (0.21, 0.21, z + 0.16), 'Kawara')
    mb.lathe([(0.17, z + 0.16), (0.21, z + 0.24), (0.15, z + 0.34), (0.06, z + 0.43), (0.01, z + 0.47)], 10, 'Kawara', cap_top=True, uv_scale=B)
    return mb


# ======================================================================= engawa (veranda), railings, steps
DECK = -0.15        # engawa deck top below the floor
EDGE = -1.03        # engawa front edge (from the wall line)


def engawa_deck():
    mb = MB('SM_Edo_EngawaDeck')
    w = (abs(EDGE) - 0.085) / 6
    for i in range(6):
        y1 = -0.085 - i * w; y0 = y1 - w + 0.006
        mb.box((-H, y0, DECK - 0.04), (H, y1, DECK), 'Planks', grain=0)
    mb.box((-H, EDGE, DECK - 0.22), (H, EDGE + 0.12, DECK - 0.04), 'Timber', grain=0)          # front beam (engawa-geta)
    mb.box((-H, -0.14, DECK - 0.16), (H, -0.08, DECK - 0.04), 'Timber', grain=0)               # ledger on the house
    for x in (-H + 0.03, 0.0):
        mb.box((x - 0.035, EDGE + 0.12, DECK - 0.16), (x + 0.035, -0.14, DECK - 0.04), 'Timber', grain=1)   # joists
    return mb


def engawa_post(length, tag):
    mb = MB(f'SM_Edo_EngawaPost_{tag}')
    s = 0.075
    y = EDGE + 0.06
    mb.box((-s, y - s, DECK - 0.22 - length), (s, y + s, DECK - 0.22), 'Timber', grain=2, skip=('-z',))
    return mb


RAIL_Y = EDGE + 0.04


def _rails(mb, a0, a1, along_x=True, balusters=True):
    """Rails between a0..a1 along x (front) or along y (end returns, at x=0)."""
    def bx(lo, hi, y0, y1, z0, z1, grain):
        if along_x: mb.box((lo, y0, z0), (hi, y1, z1), 'Timber', grain=grain)
        else: mb.box((y0, lo, z0), (y1, hi, z1), 'Timber', grain=grain)
    g = 0 if along_x else 1
    c = RAIL_Y if along_x else 0.0
    bx(a0, a1, c - 0.05, c + 0.05, DECK + 0.80, DECK + 0.87, g)      # top rail (kasagi)
    bx(a0, a1, c - 0.025, c + 0.025, DECK + 0.48, DECK + 0.53, g)    # mid rail
    bx(a0, a1, c - 0.03, c + 0.03, DECK, DECK + 0.07, g)             # bottom rail
    if balusters:
        n = max(1, int((a1 - a0) / 0.13))
        for i in range(n):
            a = a0 + (a1 - a0) * (i + 0.5) / n
            if along_x: mb.box((a - 0.0125, c - 0.0125, DECK + 0.07), (a + 0.0125, c + 0.0125, DECK + 0.80), 'Timber', grain=2)
            else: mb.box((c - 0.0125, a - 0.0125, DECK + 0.07), (c + 0.0125, a + 0.0125, DECK + 0.80), 'Timber', grain=2)


def _rail_post(mb, x):
    mb.box((x - 0.04, RAIL_Y - 0.04, DECK), (x + 0.04, RAIL_Y + 0.04, DECK + 0.90), 'Timber', grain=2)


def railing_bay():
    mb = MB('SM_Edo_Railing_Bay'); _rail_post(mb, -H); _rails(mb, -H + 0.04, H - 0.04); return mb


def railing_open():
    mb = MB('SM_Edo_Railing_Open'); _rail_post(mb, -H); return mb


def railing_end():
    mb = MB('SM_Edo_RailingEnd'); _rails(mb, RAIL_Y + 0.04, -0.09, along_x=False); return mb


def rail_post():
    mb = MB('SM_Edo_RailPost'); _rail_post(mb, 0.0); return mb


RISER, GOING = 0.19, 0.27


def steps(n):
    mb = MB(f'SM_Edo_Steps_N{n:02d}')
    top = DECK; w = 0.65
    for i in range(1, n):
        z = top - i * RISER
        y1 = EDGE - (i - 1) * GOING + 0.02; y0 = EDGE - i * GOING
        mb.box((-w, y0, z - 0.045), (w, y1, z), 'Planks', grain=0)
    run = n * GOING + 0.10; drop = n * RISER + 0.10
    ang = math.atan2(drop, run); L = math.hypot(run, drop)
    for sx in (-w - 0.03, w + 0.03):
        M = Matrix.Translation((sx, EDGE + 0.02, top + 0.02)) @ Matrix.Rotation(ang, 4, 'X')
        mb.box((-0.025, -L, -0.24), (0.025, 0.0, 0.0), 'Timber', grain=1, M=M)
    return mb


# ======================================================================= fence (type 1: board fence)
def fence_segment():
    mb = MB('SM_Edo_FenceSeg')
    n = 12; pitch = B / n
    for i in range(n):
        x = -H + (i + 0.5) * pitch; y0 = -0.03 if i % 2 == 0 else 0.005
        mb.box((x - 0.085, y0, -0.50), (x + 0.085, y0 + 0.025, 1.22), 'Planks', grain=2, skip=('-z',))
    for z in (0.30, 0.86):
        mb.box((-H + 0.065, 0.03, z), (H - 0.065, 0.08, z + 0.08), 'Timber', grain=0)
    mb.box((-H + 0.065, -0.06, 1.22), (H - 0.065, 0.06, 1.26), 'Timber', grain=0)
    return mb


def fence_post():
    mb = MB('SM_Edo_FencePost')
    mb.box((-0.065, -0.065, -0.60), (0.065, 0.065, 1.36), 'Timber', grain=2, skip=('-z',))
    mb.box((-0.08, -0.08, 1.36), (0.08, 0.08, 1.40), 'Timber', grain=0)
    return mb


# ======================================================================= props
def prop_barrel():
    mb = MB('SM_Edo_Prop_Barrel')
    prof = [(0.245, 0.0), (0.27, 0.18), (0.278, 0.36), (0.27, 0.54), (0.245, 0.72)]
    mb.lathe(prof, 14, 'Planks', cap_top=False)
    mb.lathe([(0.235, 0.70), (0.235, 0.70)], 14, 'Planks', cap_top=True)
    for z in (0.12, 0.58):
        r = 0.265 if z < 0.3 else 0.268
        mb.lathe([(r + 0.012, z), (r + 0.016, z + 0.025), (r + 0.012, z + 0.05)], 14, 'Thatch', cap_top=False)
    return mb


def prop_jar():
    mb = MB('SM_Edo_Prop_Jar')
    prof = [(0.15, 0.0), (0.25, 0.10), (0.30, 0.30), (0.28, 0.50), (0.19, 0.61), (0.175, 0.65), (0.20, 0.68)]
    mb.lathe(prof, 12, 'Ceramic', cap_top=False)
    mb.lathe([(0.215, 0.675), (0.215, 0.705)], 12, 'Planks', cap_top=True, smooth=False)
    return mb


def prop_bale():
    mb = MB('SM_Edo_Prop_Bale')
    prof = [(0.10, -0.38), (0.19, -0.36), (0.22, -0.30), (0.225, 0.0), (0.22, 0.30), (0.19, 0.36), (0.10, 0.38)]
    vs = mb.lathe([(r, x) for r, x in prof], 12, 'Thatch', axis='x', cap_top=True, cap_bottom=True)
    for x in (-0.22, 0.0, 0.22):
        mb.lathe([(0.228, x - 0.02), (0.234, x), (0.228, x + 0.02)], 12, 'Thatch', axis='x', cap_top=False)
    for v in mb.bm.verts:
        v.co.z += 0.215
    return mb


def prop_firewood():
    mb = MB('SM_Edo_Prop_Firewood')
    rnd = mb.rng
    for row in range(3):
        for i in range(4 - (row % 2)):
            r = rnd.uniform(0.05, 0.065)
            x = -0.23 + i * 0.15 + (0.075 if row % 2 else 0)
            z = 0.06 + row * 0.115
            L = rnd.uniform(0.55, 0.62)
            prof = [(r, -L / 2), (r * rnd.uniform(0.95, 1.05), L / 2)]
            start = len(mb.bm.verts)
            mb.lathe([(a, b) for a, b in prof], 6, 'Timber', axis='x', cap_top=True, cap_bottom=True, smooth=False, phase=rnd.random())
            for v in list(mb.bm.verts)[start:]:
                yy, zz = v.co.y, v.co.z
                v.co = Vector((yy + x, v.co.x, zz + z))      # logs run along local Y
    return mb


# ======================================================================= registry
def build_all():
    """Returns {collection name: [MB, ...]} -- children are named so alphabetical order = variant index."""
    kit = {
        'KIT_Footing': [footing(v) for v in 'ABC'],
        'KIT_Stilt': [post(f'SM_Edo_Stilt_L{i + 1}', 0.18, L, top=-0.25) for i, L in enumerate((1.30, 2.60, 5.20))],
        'KIT_FloorBeam': [floor_beam()],
        'KIT_FloorDeck': [floor_deck()],
        'KIT_PostStorey': [storey_post()],
        'KIT_Wall': [wall_A(), wall_B(), wall_C(), wall_D(), wall_E()],
        'KIT_RoofEnd': [roof_end(n) for n in range(1, MAX_DEPTH + 1)],
        'KIT_RoofEndApex': [roof_end(n, apex=True) for n in range(1, MAX_DEPTH + 1)],
        'KIT_RoofMid': [roof_mid(n) for n in range(1, MAX_DEPTH + 1)],
        'KIT_RoofApex': [roof_apex(n) for n in range(1, MAX_DEPTH + 1)],
        'KIT_EngawaDeck': [engawa_deck()],
        'KIT_EngawaPost': [engawa_post(L, f'L{i + 1}') for i, L in enumerate((1.30, 2.60, 5.20))],
        'KIT_Railing': [railing_bay(), railing_open()],
        'KIT_RailingEnd': [railing_end()],
        'KIT_RailPost': [rail_post()],
        'KIT_Steps': [steps(n) for n in range(2, 15)],
        'KIT_FenceSeg': [fence_segment()],
        'KIT_FencePost': [fence_post()],
        'KIT_Props': [prop_bale(), prop_barrel(), prop_firewood(), prop_jar()],
    }
    return kit
