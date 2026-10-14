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


# ======================================================================= pent roof (hisashi) between storeys 1 and 2
PENT_O, PENT_ZE, PENT_ZW, PENT_RISE = 1.05, 2.39, 2.93, 0.10   # depth from wall line, eave z, z at the wall, corner upturn


def _pent_z(d):
    return PENT_ZE + (PENT_ZW - PENT_ZE) * min(max(d / PENT_O, 0.0), 1.0)


def _pent_rise(t):
    c = max(0.0, 1.0 - t / PENT_O)
    return PENT_RISE * c * c


def pent_side():
    """One bay of pent roof on the storey-1 wall (local wall frame, exterior -Y, origin storey-1 floor)."""
    mb = MB('SM_Edo_PentSide')
    q = RIB / 4
    xs = [-H + k * q for k in range(29)]
    rip = lambda x: RIB_A * math.cos(2 * math.pi * (x + H) / RIB)
    rows = []
    for d in (0.0, PENT_O + 0.03):
        y = -PENT_O + d
        rows.append([(x, mb.v((x, y, _pent_z(d) + rip(x))), ((x + H) / B, d / B)) for x in xs])
    _surface(mb, rows)
    for x0, x1 in zip(xs[:-1], xs[1:]):
        quad = [mb.v((x0, -PENT_O, PENT_ZE + rip(x0))), mb.v((x1, -PENT_O, PENT_ZE + rip(x1))),
                mb.v((x1, -PENT_O, PENT_ZE - 0.12)), mb.v((x0, -PENT_O, PENT_ZE - 0.12))]
        mb.face(quad, 'Kawara', [((x0 + H) / B, 0.0), ((x1 + H) / B, 0.0), ((x1 + H) / B, -0.07), ((x0 + H) / B, -0.07)], want=(0, -1, 0))
    zw = _pent_z(PENT_O - 0.045) - 0.12
    soff = [mb.v((-H, -PENT_O, PENT_ZE - 0.12)), mb.v((H, -PENT_O, PENT_ZE - 0.12)), mb.v((H, -0.045, zw)), mb.v((-H, -0.045, zw))]
    mb.face(soff, 'Planks', [(0, -H / 2), (0, H / 2), (PENT_O / 2, H / 2), (PENT_O / 2, -H / 2)], want=(0, 0, -1))
    a = math.atan2(PENT_ZW - PENT_ZE, PENT_O); L = (PENT_O - 0.09) / math.cos(a)
    for i in range(4):
        x = -H + B / 8 + i * B / 4
        M = Matrix.Translation((x, -PENT_O + 0.04, PENT_ZE - 0.12 + 0.02 * math.tan(a))) @ Matrix.Rotation(a, 4, 'X')
        mb.box((-0.03, 0.0, -0.075), (0.03, L, 0.0), 'Timber', grain=1, M=M)
    mb.box((-H, -0.11, PENT_ZW - 0.03), (H, -0.045, PENT_ZW + 0.06), 'Kawara', grain=0)     # flashing against the upper wall
    return mb


def pent_corner():
    """Corner of the pent roof: origin on the corner of the wall lines, covers the outer quadrant x<0, y<0."""
    mb = MB('SM_Edo_PentCorner')
    q = RIB / 4; O = PENT_O
    rip = lambda c: RIB_A * math.cos(2 * math.pi * c / RIB)
    for face in ('front', 'side'):
        rows = []; eave = []
        for d in (0.0, O * 0.5, O):
            lo = -O + d
            al = [lo] + _grid(lo, 0.0, q, 0.0) + [0.0] if -lo > 1e-6 else [0.0]
            row = []
            for a in al:
                t = max(a + O, d)
                z = _pent_z(d) + _pent_rise(t) + rip(a)
                co = (a, -O + d, z) if face == 'front' else (-O + d, a, z)
                u = a / B if face == 'front' else -a / B
                row.append((a, mb.v(co), (u, d / B)))
            rows.append(row)
            if d == 0.0: eave = al
        _surface(mb, rows)
        outward = (0, -1, 0) if face == 'front' else (-1, 0, 0)
        for a0, a1 in zip(eave[:-1], eave[1:]):
            pts = []
            for a, top in ((a0, 1), (a1, 1), (a1, 0), (a0, 0)):
                z = PENT_ZE + _pent_rise(a + O) + (rip(a) if top else -0.12)
                pts.append(mb.v((a, -O, z) if face == 'front' else (-O, a, z)))
            mb.face(pts, 'Kawara', [(a0 / B, 0), (a1 / B, 0), (a1 / B, -0.07), (a0 / B, -0.07)], want=outward)
        srows = []
        for d in (0.0, O - 0.045):
            lo = -O + d
            al = [lo] + _grid(lo, 0.0, B / 8, 0.0) + [0.0] if -lo > 1e-6 else [0.0]
            srows.append([(a, mb.v(((a, -O + d, _pent_z(d) + _pent_rise(max(a + O, d)) - 0.12) if face == 'front'
                                    else (-O + d, a, _pent_z(d) + _pent_rise(max(a + O, d)) - 0.12))), (d / 2, a / 2)) for a in al])
        for r0, r1 in zip(srows[:-1], srows[1:]):
            _zipper(mb, r0, r1, 'Planks', (0, 0, -1))
    path = []
    for i in range(7):
        t = 0.03 + 0.97 * i / 6
        p = Vector((-O + O * t, -O + O * t, 0)); d = t * O
        p.z = _pent_z(d) + _pent_rise(d) + RIB_A + 0.005
        path.append((p, Vector((1, 1, 0)).normalized()))
    _sweep(mb, path, [(s * 0.75, h * 0.75) for s, h in CAP_HIP], cap0=True)
    return mb


# ======================================================================= balcony, shopfront, lanterns
def balcony_bracket():
    mb = MB('SM_Edo_BalconyBracket')        # diagonal strut under the upper-floor balcony, at a post
    a = math.atan2(0.60, 0.85); L = math.hypot(0.60, 0.85)
    M = Matrix.Translation((0.0, -0.08, DECK - 0.95)) @ Matrix.Rotation(-a, 4, 'X') @ Matrix.Rotation(math.pi, 4, 'Z')
    mb.box((-0.04, 0.0, -0.05), (0.04, L, 0.05), 'Timber', grain=1, M=M)
    return mb


def noren():
    mb = MB('SM_Edo_Noren')                 # shop curtain over the door bay
    mb.box((-0.74, -0.135, 1.78), (0.74, -0.105, 1.83), 'Timber', grain=0)
    for x in (-0.70, 0.70):
        mb.box((x - 0.02, -0.135, 1.80), (x + 0.02, -0.045, 1.84), 'Timber', grain=1)
    for x in (-0.45, 0.0, 0.45):
        mb.box((x - 0.21, -0.125, 0.94), (x + 0.21, -0.115, 1.76), 'Cloth', grain=2)
    return mb


def shop_sign():
    mb = MB('SM_Edo_ShopSign')              # hanging sign board, perpendicular to the facade
    for z in (2.22, 1.12):
        mb.box((-0.03, -0.80, z), (0.03, -0.045, z + 0.06), 'Timber', grain=1)
    mb.box((-0.025, -0.72, 1.18), (0.025, -0.30, 2.22), 'Planks', grain=2)
    mb.box((-0.035, -0.74, 1.15), (0.035, -0.28, 1.19), 'Timber', grain=1)
    mb.box((-0.035, -0.74, 2.21), (0.035, -0.28, 2.25), 'Timber', grain=1)
    return mb


def lantern():
    mb = MB('SM_Edo_Lantern')               # paper lantern (chochin) on a wall arm
    mb.box((-0.025, -0.64, 2.23), (0.025, -0.045, 2.28), 'Timber', grain=1)
    mb.box((-0.01, -0.59, 2.17), (0.01, -0.57, 2.23), 'Timber', grain=2)
    body = [(0.09, 1.73), (0.15, 1.77), (0.17, 1.86), (0.17, 2.04), (0.15, 2.13), (0.09, 2.17)]
    start = len(mb.bm.verts)
    mb.lathe(body, 12, 'Lantern', cap_top=False)
    for r0, z0, z1 in ((0.095, 1.71, 1.75), (0.095, 2.15, 2.19)):
        mb.lathe([(r0, z0), (r0, z1)], 12, 'Timber', cap_top=True, cap_bottom=True, smooth=False)
    for v in mb.bm.verts:
        v.co.y += -0.58
    # undo the shift on the arm/hook boxes (first 16 verts)
    for v in list(mb.bm.verts)[:16]:
        v.co.y += 0.58
    return mb


# ======================================================================= thatched gable roof (Roof 2)
TH_O, TH_ZE, TH_PITCH, TH_E, TH_R = 1.19, 2.49, 0.888, 0.55, 0.30


class Thatch:
    def __init__(self, n):
        self.n = n; self.D = n * B; self.R = self.D / 2 + TH_O; self.H = TH_PITCH * self.R

    def zt(self, d):
        s = min(max(d / self.R, 0.0), 1.0)
        return TH_ZE + self.H * (1 - (1 - s) ** 1.12)

    def th(self, d):
        s = min(max(d / self.R, 0.0), 1.0)
        return TH_E + (TH_R - TH_E) * s

    def bump(self, x, d):
        s = min(max(d / self.R, 0.0), 1.0)
        return 0.035 * math.sin(2 * math.pi * 2 * x / B + 1.3) * math.sin(math.pi * min(1.0, s * 1.2)) + 0.02 * math.sin(2 * math.pi * 3 * x / B + 2.0 * s)


def _thatch_slab(mb, tf, xs, sign, eave=True):
    """Both surfaces of one slope (sign -1: -Y side) between the x values in xs."""
    ds = [tf.R * j / 5 for j in range(6)]
    top, und = [], []
    for d in ds:
        y = sign * (tf.R - d)
        top.append([(x, mb.v((x, y, tf.zt(d) + tf.bump(x, d))), (x / 2.0, d / 2.0)) for x in xs])
        und.append([(x, mb.v((x, y, tf.zt(d) - tf.th(d))), (x / 2.0, d / 2.0)) for x in xs])
    for r0, r1 in zip(top[:-1], top[1:]):
        _zipper(mb, r0, r1, 'Thatch', (0, 0, 1))
    for r0, r1 in zip(und[:-1], und[1:]):
        _zipper(mb, r0, r1, 'Thatch', (0, 0, -1))
    if eave:
        y = sign * tf.R; yi = sign * (tf.R - 0.12)
        for x0, x1 in zip(xs[:-1], xs[1:]):
            q = [mb.v((x0, y, tf.zt(0) + tf.bump(x0, 0))), mb.v((x1, y, tf.zt(0) + tf.bump(x1, 0))),
                 mb.v((x1, yi, tf.zt(0.12) - tf.th(0.12))), mb.v((x0, yi, tf.zt(0.12) - tf.th(0.12)))]
            mb.face(q, 'Thatch', [(x0 / 2, 0), (x1 / 2, 0), (x1 / 2, 0.3), (x0 / 2, 0.3)], want=(0, sign, -0.3))
    return ds


def _thatch_frieze(mb, tf, x0, x1, sign):
    dw = TH_O - 0.05; y = sign * (tf.R - dw)
    zt = tf.zt(dw) - tf.th(dw) + 0.02
    q = [mb.v((x0, y, KETA_TOP - 0.05)), mb.v((x1, y, KETA_TOP - 0.05)), mb.v((x1, y, zt)), mb.v((x0, y, zt))]
    mb.face(q, 'Plaster', [(x0 / 2, 0), (x1 / 2, 0), (x1 / 2, 0.3), (x0 / 2, 0.3)], want=(0, sign, 0))


def _ridge_log(mb, tf, x0, x1, cap0=False):
    z = tf.zt(tf.R) + 0.18; r = 0.26
    ring = lambda x: [(x, r * math.cos(2 * math.pi * k / 8), z + r * math.sin(2 * math.pi * k / 8)) for k in range(8)]
    mb.loft([ring(x0), ring(x1)], 'Timber', closed=True, smooth=True, cap0=cap0, want_out=_axis_want([(x0, 0, z), (x1, 0, z)]))


def thatch_mid(n):
    tf = Thatch(n); mb = MB(f'SM_Edo_ThatchMid_D{n}')
    xs = [B * k / 6 for k in range(7)]
    for sign in (-1, 1):
        _thatch_slab(mb, tf, xs, sign)
        _thatch_frieze(mb, tf, 0.0, B, sign)
    _ridge_log(mb, tf, 0.0, B)
    return mb


def thatch_end(n):
    """Gable end: the thatch overhang beyond the end wall (x' = 0), verge, gable wall, ridge log end and crossed finials."""
    tf = Thatch(n); mb = MB(f'SM_Edo_ThatchEnd_D{n}')
    xs = [-TH_O + TH_O * k / 4 for k in range(5)]
    for sign in (-1, 1):
        ds = _thatch_slab(mb, tf, xs, sign)
        _thatch_frieze(mb, tf, -0.05, 0.0, sign)
        for d0, d1 in zip(ds[:-1], ds[1:]):                       # verge (cut edge of the gable overhang)
            y0, y1 = sign * (tf.R - d0), sign * (tf.R - d1); x = -TH_O
            q = [mb.v((x, y0, tf.zt(d0) + tf.bump(x, d0))), mb.v((x, y1, tf.zt(d1) + tf.bump(x, d1))),
                 mb.v((x, y1, tf.zt(d1) - tf.th(d1))), mb.v((x, y0, tf.zt(d0) - tf.th(d0)))]
            mb.face(q, 'Thatch', [(d0 / 2, 0.3), (d1 / 2, 0.3), (d1 / 2, 0), (d0 / 2, 0)], want=(-1, 0, 0))
    # gable wall (plaster) on the end wall line, under the thatch
    prof = [(-tf.D / 2, KETA_TOP)]
    for j in range(9):
        d = TH_O + (tf.R - TH_O) * j / 8
        prof.append((-(tf.R - d), tf.zt(d) - tf.th(d) - 0.02))
    prof += [(-y, z) for y, z in reversed(prof[1:-1])] + [(tf.D / 2, KETA_TOP)]
    _prism(mb, [(-0.045, y, z) for y, z in prof], [(0.045, y, z) for y, z in prof], mat='Plaster')
    ztop = tf.zt(tf.R) - tf.th(tf.R)
    mb.box((-0.07, -0.07, KETA_TOP), (0.07, 0.07, ztop), 'Timber', grain=2)                  # king post
    zb = KETA_TOP + 0.55; half = tf.R - TH_O - 0.1
    mb.box((-0.075, -half * 0.85, zb), (0.075, half * 0.85, zb + 0.14), 'Timber', grain=1)  # tie beam
    _ridge_log(mb, tf, -TH_O - 0.18, 0.0, cap0=True)
    z = tf.zt(tf.R) + 0.18
    for ang in (math.radians(38), -math.radians(38)):                                         # crossed finials (X)
        M = Matrix.Translation((-TH_O + 0.12, 0.0, z)) @ Matrix.Rotation(ang, 4, 'X')
        mb.box((-0.05, -0.08, -0.55), (0.05, 0.08, 0.95), 'Timber', grain=2, M=M)
    return mb


# ======================================================================= stone compound wall (Fence 2) and gate
def _coping(mb, half_len, half_w, z_eave, z_ridge, xs=None):
    """Small tiled gable coping along local X (ripples aligned to the bay grid)."""
    q = RIB / 2
    xs = xs or [-half_len + k * q for k in range(int(round(2 * half_len / q)) + 1)]
    rip = lambda x: RIB_A * 0.8 * math.cos(2 * math.pi * (x + half_len) / RIB)
    for sign in (-1, 1):
        rows = []
        for d, z in ((0.0, z_eave), (half_w, z_ridge)):
            y = sign * (half_w - d)
            rows.append([(x, mb.v((x, y, z + rip(x))), ((x + half_len) / B, d / B)) for x in xs])
        _surface(mb, rows)
        y = sign * half_w
        for x0, x1 in zip(xs[:-1], xs[1:]):
            qd = [mb.v((x0, y, z_eave + rip(x0))), mb.v((x1, y, z_eave + rip(x1))), mb.v((x1, y, z_eave - 0.08)), mb.v((x0, y, z_eave - 0.08))]
            mb.face(qd, 'Kawara', [(x0 / B, 0), (x1 / B, 0), (x1 / B, -0.04), (x0 / B, -0.04)], want=(0, sign, 0))
    soff = [mb.v((-half_len, -half_w, z_eave - 0.08)), mb.v((half_len, -half_w, z_eave - 0.08)), mb.v((half_len, half_w, z_eave - 0.08)), mb.v((-half_len, half_w, z_eave - 0.08))]
    mb.face(soff, 'Planks', [(0, 0), (1, 0), (1, 0.3), (0, 0.3)], want=(0, 0, -1))
    path = [(Vector((-half_len, 0, z_ridge + RIB_A * 0.8)), Vector((1, 0, 0))), (Vector((half_len, 0, z_ridge + RIB_A * 0.8)), Vector((1, 0, 0)))]
    _sweep(mb, path, [(s * 0.7, h * 0.6) for s, h in CAP_RIDGE], cap0=True, cap1=True)


def wall2_segment():
    mb = MB('SM_Edo_Wall2Seg')              # stone base, plaster wall, tiled coping (nerikabe)
    mb.box((-H, -0.25, -0.75), (H, 0.25, 0.31), 'StoneWall', skip=('-z',))
    mb.box((-H, -0.17, 0.31), (H, 0.17, 1.60), 'Plaster')
    mb.box((-H, -0.19, 1.60), (H, 0.19, 1.66), 'Timber', grain=0)
    _coping(mb, H, 0.36, 1.92, 2.20)
    return mb


def wall2_pier():
    mb = MB('SM_Edo_Wall2Pier')             # pier at segment joints / gate sides (hides height steps on slopes)
    mb.box((-0.30, -0.30, -0.75), (0.30, 0.30, 0.36), 'StoneWall', skip=('-z',))
    mb.box((-0.22, -0.22, 0.36), (0.22, 0.22, 1.75), 'Plaster')
    mb.box((-0.26, -0.26, 1.75), (0.26, 0.26, 1.82), 'Timber', grain=0)
    mb.lathe([(0.40, 1.82), (0.30, 2.05), (0.12, 2.28), (0.0, 2.34)], 4, 'Kawara', cap_top=False, phase=math.pi / 4, smooth=False, uv_scale=B)
    return mb


def gate():
    mb = MB('SM_Edo_Gate')                  # roofed gate in the compound wall, doors open inward (+Y)
    for x in (-1.05, 1.05):
        mb.box((x - 0.15, -0.15, -0.30), (x + 0.15, 0.15, 3.30), 'Timber', grain=2, skip=('-z',))
        mb.box((x - 0.25, -0.25, -0.20), (x + 0.25, 0.25, 0.12), 'Stone')
    mb.box((-1.50, -0.09, 2.45), (1.50, 0.09, 2.65), 'Timber', grain=0)
    mb.box((-1.62, -0.16, 3.00), (1.62, 0.16, 3.22), 'Timber', grain=0)
    for x in (-0.95, 0.95):                                                      # ridge-direction purlins
        mb.box((x - 0.06, -1.05, 3.22), (x + 0.06, 1.05, 3.30), 'Timber', grain=1)
    _coping(mb, 1.68, 1.15, 3.32, 3.92)
    for sx in (-1, 1):                                                           # door leaves
        piv = Vector((sx * 0.90, 0.02, 0.0)); ang = sx * math.radians(78)
        M = Matrix.Translation(piv) @ Matrix.Rotation(ang, 4, 'Z')
        x0, x1 = (0.0, 0.88) if sx < 0 else (-0.88, 0.0)
        mb.box((x0, 0.0, 0.05), (x1, 0.05, 2.35), 'Planks', grain=2, M=M)
        for z in (0.35, 1.25, 2.05):
            mb.box((x0 + 0.04, 0.05, z), (x1 - 0.04, 0.09, z + 0.10), 'Timber', grain=0, M=M)
    return mb


# ======================================================================= plaza furniture
def toro():
    mb = MB('SM_Edo_Toro')                  # stone lantern
    mb.box((-0.26, -0.26, 0.0), (0.26, 0.26, 0.16), 'Stone', skip=('-z',))
    mb.lathe([(0.11, 0.16), (0.095, 0.30), (0.095, 0.62), (0.11, 0.76)], 8, 'Stone', cap_top=False, phase=math.pi / 8, smooth=False)
    mb.lathe([(0.30, 0.76), (0.30, 0.84), (0.20, 0.88)], 8, 'Stone', cap_top=True, phase=math.pi / 8, smooth=False)
    mb.box((-0.17, -0.17, 0.88), (0.17, 0.17, 1.22), 'Stone')
    for sx, sy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        cx, cy = sx * 0.172, sy * 0.172
        if sx: mb.box((cx - 0.004, -0.085, 0.95), (cx + 0.004, 0.085, 1.14), 'Lantern')
        else: mb.box((-0.085, cy - 0.004, 0.95), (0.085, cy + 0.004, 1.14), 'Lantern')
    mb.lathe([(0.34, 1.22), (0.40, 1.24), (0.34, 1.34), (0.16, 1.52), (0.05, 1.62)], 8, 'Stone', cap_top=True, phase=math.pi / 8, smooth=False)
    mb.lathe([(0.04, 1.62), (0.07, 1.68), (0.035, 1.78), (0.0, 1.82)], 8, 'Stone', cap_top=False, smooth=False)
    return mb


def well():
    mb = MB('SM_Edo_Well')                  # stone well with a small tiled roof
    segs = 16
    mb.lathe([(0.88, 0.0), (0.88, 0.62)], segs, 'StoneWall', cap_top=False, want='radial')
    mb.lathe([(0.88, 0.62), (0.60, 0.62)], segs, 'StoneWall', cap_top=False, want=(0, 0, 1))
    mb.lathe([(0.60, 0.62), (0.60, -0.35)], segs, 'StoneWall', cap_top=False, want='inward')
    mb.lathe([(0.60, -0.35), (0.0, -0.35)], segs, 'Ceramic', cap_top=False, want=(0, 0, 1))
    for x in (-1.02, 1.02):
        mb.box((x - 0.07, -0.07, 0.0), (x + 0.07, 0.07, 2.35), 'Timber', grain=2, skip=('-z',))
    mb.box((-1.10, -0.06, 2.0), (1.10, 0.06, 2.12), 'Timber', grain=0)
    mb.box((-0.04, -0.04, 1.35), (0.04, 0.04, 2.0), 'Timber', grain=2)
    _coping(mb, 1.30, 1.0, 2.38, 2.82)
    return mb


def bench():
    mb = MB('SM_Edo_Bench')
    mb.box((-0.75, -0.21, 0.40), (0.75, 0.21, 0.45), 'Planks', grain=0)
    for x in (-0.60, 0.60):
        for y in (-0.14, 0.14):
            mb.box((x - 0.035, y - 0.035, 0.0), (x + 0.035, y + 0.035, 0.40), 'Timber', grain=2, skip=('-z',))
        mb.box((x - 0.025, -0.15, 0.16), (x + 0.025, 0.15, 0.20), 'Timber', grain=1)
    return mb


def board():
    mb = MB('SM_Edo_Board')                 # notice board (kosatsu) with a small roof
    for x in (-0.55, 0.55):
        mb.box((x - 0.05, -0.05, 0.0), (x + 0.05, 0.05, 2.0), 'Timber', grain=2, skip=('-z',))
    mb.box((-0.62, -0.025, 0.95), (0.62, 0.025, 1.78), 'Planks', grain=2)
    mb.box((-0.66, -0.04, 0.92), (0.66, 0.04, 0.96), 'Timber', grain=0)
    mb.box((-0.66, -0.04, 1.78), (0.66, 0.04, 1.82), 'Timber', grain=0)
    _coping(mb, 0.80, 0.32, 2.02, 2.16)
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
        'KIT_PentSide': [pent_side()],
        'KIT_PentCorner': [pent_corner()],
        'KIT_BalconyBracket': [balcony_bracket()],
        'KIT_Noren': [noren()],
        'KIT_ShopSign': [shop_sign()],
        'KIT_Lantern': [lantern()],
        'KIT_ThatchEnd': [thatch_end(n) for n in range(1, MAX_DEPTH + 1)],
        'KIT_ThatchMid': [thatch_mid(n) for n in range(1, MAX_DEPTH + 1)],
        'KIT_Wall2Seg': [wall2_segment()],
        'KIT_Wall2Pier': [wall2_pier()],
        'KIT_Gate': [gate()],
        'KIT_Toro': [toro()],
        'KIT_Well': [well()],
        'KIT_Bench': [bench()],
        'KIT_Board': [board()],
    }
    import modules_cat, modules_town, modules_border
    kit.update(modules_cat.build_cat())
    kit.update(modules_town.build_town())
    kit.update(modules_border.build_border())
    return kit
