"""Plaza district: planner (layout) + the GN_EdoKitVillage node group built from kit houses.

The district is laid out around a round plaza. Everything is expressed relative to the plaza centre, so the district
object can be moved/rotated as a whole (houses sample the terrain at their placed position).

    plan = district.plan()                    # layout dict (also written to kit/village/district_layout.json)
    district.build_group(house_group)         # creates GN_EdoKitVillage (needs GN_EdoKitHouse and the KIT_* collections)
"""
import math, json, copy
from archetypes import ARCH

B = 1.82
C = (-48.0, -122.0)                 # plaza centre in world coordinates (flat ground, z about -0.05)
PLAZA_R = 20.0
RING1 = dict(c=24.0, w=8.0)         # ring road around the plaza (centre line radius, width)
RING2 = dict(c=52.0, w=5.0)
SPOKES = {                          # angle (deg, from +X around the plaza), road width
    'west': (180.0, 6.0), 'north_west': (112.0, 4.0), 'south_west': (248.0, 4.0), 'trail': (322.0, 2.4), 'north': (62.0, 3.6),
}
OUTWARD = {                         # roads leaving the district from the outer ring: name -> (ring angle deg, width, [further points])
    'EAST':  (24.0, 5.0, [(20.0, -96.0), (40.0, -90.5), (58.0, -88.0)]),
    'SOUTH': (285.0, 5.0, [(-33.0, -190.0), (-31.0, -208.0), (-29.0, -226.0)]),
    'WNW':   (146.0, 4.0, [(-108.0, -88.0), (-130.0, -85.0), (-152.0, -87.0)]),
    'SW2':   (215.0, 4.0, [(-108.0, -160.0), (-130.0, -163.0), (-152.0, -164.0)]),
}
HOSPITAL_C = (-89.0, -32.0)         # centre of the hospital's main building (north-west of the plaza, facing south)
HOSPITAL_ROAD = [(-76.5, -78.5), (-81.0, -70.0), (-86.0, -58.0), (-88.1, -41.7)]   # from the outer ring to the hospital gate
HALL = dict(bx=13, by=8, fl=2, roof=1, eng=1, bal=1, lan=1, fence=2, gate=1)
RING1_SEQ = ['shopB', 'tea', 'shopA', 'restA', 'shopA', 'restB', 'shopB', 'tea', 'dwellB', 'shopA', 'restA', 'tea', 'shopA', 'shopB']
RING2_SEQ = ['dwellA', 'farmhouse', 'dwellC', 'dwellB', 'smithy', 'dwellA', 'kura', 'hutB', 'dwellC', 'farmhouse', 'dwellA', 'dwellB', 'kura', 'hutA',
             'dwellC', 'farmhouse', 'smithy', 'hutB', 'dwellB', 'clinic', 'farmhouse', 'dwellA']
HAMLET_SEQ = ['farmhouse', 'hutA', 'barn', 'dwellC', 'hutB', 'farmhouse', 'barn', 'smithy']


def rot(v, a):
    c, s = math.cos(a), math.sin(a)
    return (v[0] * c - v[1] * s, v[0] * s + v[1] * c)


def plot_rect(p):
    """Plot rectangle (x0, x1, y0, y1) in house-local coordinates, margin included."""
    hW, hD = p['bx'] * 0.91, p['by'] * 0.91
    f = p.get('fence', 0)
    if f == 1:
        r = (-hW - B, hW + B, -hD - 2 * B, hD + B)
    elif f == 2:
        r = (-hW - B - 0.3, hW + B + 0.3, -hD - 2 * B - (1.3 if p.get('gate') else 0.0), hD + B + 0.3)
    else:
        cat = 1 if p.get('cat') else 0
        r = (-hW - 0.7, hW + 0.7, -hD - 0.6 - (1.1 if p.get('eng') else 0.0) - (0.9 if (p.get('shop') or p.get('lan')) else 0.0) - 0.5 * cat,
             hD + 0.6 + (1.5 if p.get('props', 0) > 0.05 else 0.4 * cat))
    return (r[0] - 0.8, r[1] + 0.8, r[2] - 0.8, r[3] + 0.8)


def corners(slot):
    x0, x1, y0, y1 = slot['rect']
    return [tuple(a + b for a, b in zip(rot(c, slot['angle']), slot['pos'])) for c in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))]


def sat_overlap(P, Q):
    for poly in (P, Q):
        for i in range(len(poly)):
            a, b = poly[i], poly[(i + 1) % len(poly)]
            n = (-(b[1] - a[1]), b[0] - a[0])
            pa = [p[0] * n[0] + p[1] * n[1] for p in P]; pb = [q[0] * n[0] + q[1] * n[1] for q in Q]
            if max(pa) < min(pb) or max(pb) < min(pa):
                return False
    return True


def point_poly_dist(pt, poly):
    inside = True; best = 1e9
    for i in range(len(poly)):
        a, b = poly[i], poly[(i + 1) % len(poly)]
        ab = (b[0] - a[0], b[1] - a[1]); ap = (pt[0] - a[0], pt[1] - a[1])
        t = max(0.0, min(1.0, (ap[0] * ab[0] + ap[1] * ab[1]) / max(ab[0] ** 2 + ab[1] ** 2, 1e-9)))
        d = math.hypot(pt[0] - (a[0] + ab[0] * t), pt[1] - (a[1] + ab[1] * t)); best = min(best, d)
        if ab[0] * ap[1] - ab[1] * ap[0] < 0: inside = False
    return 0.0 if inside else best


def polyline_samples(pts, step=1.0):
    out = []
    for a, b in zip(pts[:-1], pts[1:]):
        n = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) / step))
        out += [(a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n) for k in range(n)]
    return out + [pts[-1]]


def arc(cx, cy, r, a0, a1, n=None):
    n = n or max(8, int(abs(a1 - a0) / 3.0))
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * k / n)), cy + r * math.sin(math.radians(a0 + (a1 - a0) * k / n))) for k in range(n + 1)]


def roads():
    cx, cy = C
    ring1 = RING1['c']
    at = lambda ang, r=ring1: (cx + r * math.cos(math.radians(ang)), cy + r * math.sin(math.radians(ang)))
    R = []
    R.append(dict(name='RING1', pts=arc(cx, cy, ring1, 0, 362, 120), width=RING1['w'], kind='road'))
    R.append(dict(name='RING2', pts=arc(cx, cy, RING2['c'], 24, 336, 90), width=RING2['w'], kind='road'))
    R.append(dict(name='HALL_APPROACH', pts=[at(0.0), (cx + 34.4, cy)], width=6.0, kind='road'))
    R.append(dict(name='WEST', pts=[(-122.0, -130.0), (-104.0, -129.5), (-88.0, -127.0), at(180.0)], width=SPOKES['west'][1], kind='road'))
    R.append(dict(name='NORTH_WEST', pts=[(-128.0, -60.0), (-108.0, -62.0), (-88.0, -72.0), (-70.0, -88.0), at(112.0)], width=SPOKES['north_west'][1], kind='road'))
    R.append(dict(name='SOUTH_WEST', pts=[(-128.0, -180.0), (-108.0, -178.0), (-88.0, -168.0), (-70.0, -152.0), at(248.0)], width=SPOKES['south_west'][1], kind='road'))
    R.append(dict(name='TRAIL', pts=[at(322.0), (-13.0, -146.0), (10.0, -150.5), (39.0, -150.0)], width=SPOKES['trail'][1], kind='path'))
    R.append(dict(name='NORTH', pts=[at(62.0), (-35.5, -84.0), (-32.0, -64.0), (-30.0, -44.0), (-28.0, -22.0)], width=SPOKES['north'][1], kind='road'))
    for name, (ang, w, rest) in OUTWARD.items():       # roads leaving the district from the outer ring
        R.append(dict(name=name, pts=[at(ang, RING2['c'])] + list(rest), width=w, kind='road'))
    R.append(dict(name='HOSPITAL', pts=list(HOSPITAL_ROAD), width=6.0, kind='road'))
    return R


def plan():
    cx, cy = C
    slots = []
    rd = roads()
    road_polys = [(polyline_samples(r['pts'], 1.5), r['width'] / 2.0) for r in rd]

    def make(arch, ring, i, override=None):
        p = copy.deepcopy(ARCH[arch]) if isinstance(arch, str) else copy.deepcopy(arch)
        d = dict(bx=p['bx'], by=p['by'], fl=p.get('fl', 1), roof=p['roof'], eng=bool(p.get('eng')), bal=bool(p.get('bal')),
                 shop=bool(p.get('shop')), lan=bool(p.get('lan')), fence=p.get('fence', 0), gate=bool(p.get('gate')), cat=p.get('cat', 0))
        if override: d.update(override)
        d['props'] = 0.0
        return d

    def fits(slot, others):
        P = corners(slot)
        for o in others:
            if math.hypot(slot['pos'][0] - o['pos'][0], slot['pos'][1] - o['pos'][1]) < 70 and sat_overlap(P, corners(o)):
                return False
        for samples, hw in road_polys:
            for pt in samples:
                if point_poly_dist(pt, P) < hw + 0.8:
                    return False
        return True

    # ---- the big hall east of the plaza, facing it
    h = make(HALL, 'hall', 0); h['props'] = 0.3
    rect = plot_rect(dict(h)); hall_front = 34.0
    rc = hall_front - rect[2]
    hall = dict(id='HALL', arch='hall', ring='hall', **h, pos=(cx + rc, cy), angle=-math.pi / 2, rect=rect, seed=9001)
    slots.append(hall)

    # ---- the hospital: a wide, low main building (16 x 6 bays, one storey) with a walled court and gate, and a ward on each side
    hx, hy = HOSPITAL_C
    hm = make('hospital', 'hosp', 0); hm['props'] = 0.3
    rect = plot_rect(dict(hm)); hosp = dict(id='HOSP', arch='hospital', ring='hosp', **hm, pos=(hx, hy), angle=0.0, rect=rect, seed=9101)
    slots.append(hosp)
    for tag, side, sd in (('HOSP_W', -1, 9111), ('HOSP_E', 1, 9121)):
        wd = make('ward', 'hosp', 0); wd['props'] = 0.3
        wr = plot_rect(dict(wd))
        gap = 1.0
        wx = hx + side * ((rect[1] - rect[0]) / 2.0 + (wr[1] - wr[0]) / 2.0 + gap)
        slots.append(dict(id=tag, arch='ward', ring='hosp', **wd, pos=(wx, hy + (rect[2] + rect[3]) / 2.0 - (wr[2] + wr[3]) / 2.0 + 0.0), angle=0.0, rect=wr, seed=sd))

    def ring(radius_front, seq, tag, alts=(), fence_override=None, props=0.0, start=0.0, shrink=0.0):
        phi = math.radians(start); end = phi + 2 * math.pi; k = 0; guard = 0
        while phi < end and guard < 400:
            guard += 1
            placed = False
            for name in [seq[k % len(seq)]] + list(alts):
                d = make(name, tag, k, dict(fence=fence_override) if (fence_override is not None and ARCH[name].get('fence', 0) == 0 and name != 'barn') else None)
                d['props'] = props
                rect = plot_rect(d)
                width = (rect[1] - rect[0]) + 2.0
                dphi = width / radius_front
                mid = phi + dphi / 2.0
                rcen = radius_front - rect[2]
                ang = mid - math.pi / 2
                pos = (cx + rcen * math.cos(mid), cy + rcen * math.sin(mid))
                slot = dict(id=f'{tag}_{len(slots):02d}', arch=name, ring=tag, **d, pos=pos, angle=ang, rect=rect, seed=1000 + len(slots) * 7)
                if fits(slot, slots) and mid + dphi / 2 <= end - 0.02:
                    slots.append(slot); phi += dphi; k += 1; placed = True
                    break
            if not placed:
                phi += math.radians(1.2)
        return slots

    ring(RING1['c'] + RING1['w'] / 2 + 0.8, RING1_SEQ, 'R1', alts=('tea', 'shopA', 'kura'), props=0.0)
    ring(RING2['c'] + RING2['w'] / 2 + 0.8, RING2_SEQ, 'R2', alts=('hutA', 'kura', 'hutB', 'hutC'), fence_override=1, props=0.5, start=3.0)

    # ---- hamlet along the north road: houses on both sides, fronts to the road
    north = [r for r in rd if r['name'] == 'NORTH'][0]
    pts = north['pts']; hw = north['width'] / 2.0
    cum = [0.0]
    for a, b in zip(pts[:-1], pts[1:]): cum.append(cum[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    def at_s(s):
        for i in range(len(pts) - 1):
            if cum[i] <= s <= cum[i + 1]:
                t = (s - cum[i]) / (cum[i + 1] - cum[i]); a, b = pts[i], pts[i + 1]
                tx, ty = b[0] - a[0], b[1] - a[1]; L = math.hypot(tx, ty)
                return (a[0] + tx * t, a[1] + ty * t), (tx / L, ty / L)
        return pts[-1], (0.0, 1.0)
    s = 26.0; k = 0; side = 1
    while s < cum[-1] - 6 and k < 12:
        name = HAMLET_SEQ[k % len(HAMLET_SEQ)]
        d = make(name, 'H', k, dict(fence=1) if name not in ('barn',) else None); d['props'] = 0.4
        rect = plot_rect(d)
        pt, T = at_s(s); N = (-T[1], T[0])
        nx, ny_ = (N[0] * side, N[1] * side)         # unit vector from the road towards the house
        dist = hw + 1.4 - rect[2]
        pos = (pt[0] + nx * dist, pt[1] + ny_ * dist)
        ang = math.atan2(-nx, ny_) if False else math.atan2(nx, -ny_)   # local -Y must point back to the road: (sin a, -cos a) = (-nx, -ny)
        ang = math.atan2(-nx, ny_)
        slot = dict(id=f'H_{len(slots):02d}', arch=name, ring='H', **d, pos=pos, angle=ang, rect=rect, seed=2000 + len(slots) * 7)
        if fits(slot, slots):
            slots.append(slot); k += 1
        s += (rect[1] - rect[0]) * 0.5 + 3.5 if side > 0 else 2.0
        side = -side
    # local coordinates relative to the plaza centre
    for sl in slots:
        sl['pos_local'] = (sl['pos'][0] - cx, sl['pos'][1] - cy)
    return dict(center=C, plaza_radius=PLAZA_R, slots=slots, roads=rd, spokes=SPOKES)


def to_json(pl):
    out = copy.deepcopy(pl)
    for s in out['slots']:
        s['plot_corners_world'] = [list(map(lambda v: round(v, 3), c)) for c in corners(s)]
        s['pos'] = [round(v, 3) for v in s['pos']]; s['pos_local'] = [round(v, 3) for v in s['pos_local']]
        s['angle_deg'] = round(math.degrees(s['angle']), 3); s['rect'] = [round(v, 3) for v in s['rect']]
    for r in out['roads']: r['pts'] = [[round(a, 3), round(b, 3)] for a, b in r['pts']]
    out['center'] = list(out['center'])
    return out


# ======================================================================= node group
def build_group(house_group, name='GN_EdoKitVillage', plan_data=None):
    import bpy
    from gn_house import GB
    pl = plan_data or plan()
    old = bpy.data.node_groups.get(name)
    if old: bpy.data.node_groups.remove(old)
    t = bpy.data.node_groups.new(name, 'GeometryNodeTree'); t.is_modifier = True
    it = t.interface
    it.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    it.new_socket('Ground', in_out='INPUT', socket_type='NodeSocketObject').description = 'Terrain the district stands on'
    pr = it.new_socket('Plaza Radius', in_out='INPUT', socket_type='NodeSocketFloat'); pr.default_value = PLAZA_R; pr.min_value = 5.0; pr.max_value = 60.0
    rl = it.new_socket('Realize', in_out='INPUT', socket_type='NodeSocketBool'); rl.default_value = False
    it.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    g = GB(t)
    gi = g.node('NodeGroupInput'); go = g.node('NodeGroupOutput')
    G = lambda n: g.O(gi, n)
    oi = g.node('GeometryNodeObjectInfo', transform_space='RELATIVE'); g.L.new(G('Ground'), g.I(oi, 'Object'))
    ground = g.O(oi, 'Geometry')

    def gz():
        x, y, _ = g.pos()
        rc = g.node('GeometryNodeRaycast'); g.L.new(ground, g.I(rc, 'Target Geometry'))
        g.put(rc, 'Source Position', g.vec(x, y, 2000.0)); g.put(rc, 'Ray Direction', g.vec(0.0, 0.0, -1.0)); g.put(rc, 'Ray Length', 5000.0)
        s = g.node('ShaderNodeSeparateXYZ'); g.L.new(g.O(rc, 'Hit Position'), s.inputs[0])
        return g.sw('FLOAT', g.O(rc, 'Is Hit'), 0.0, s.outputs['Z'])

    parts = []
    # ---- houses
    for i, sl in enumerate(pl['slots']):
        n = g.node('GeometryNodeGroup'); n.node_tree = house_group; n.label = sl['id']
        n.location = ((i % 8) * 260 - 1200, -(i // 8) * 420 - 700)
        vals = {'Bays X': sl['bx'], 'Bays Y': sl['by'], 'Floors': sl['fl'], 'Roof': sl['roof'], 'Engawa': sl['eng'], 'Balcony': sl['bal'],
                'Shopfront': sl['shop'], 'Lanterns': sl['lan'], 'Fence': sl['fence'], 'Gate': sl['gate'], 'Props': sl['props'], 'Seed': sl['seed'],
                'Raise': 1.12, 'Angle': sl['angle'], 'Realize': False, 'Category': sl.get('cat', 0)}
        for k, v in vals.items():
            n.inputs[k].default_value = v
        n.inputs['Offset'].default_value = (sl['pos_local'][0], sl['pos_local'][1], 0.0)
        g.L.new(G('Ground'), n.inputs['Ground'])
        parts.append(n.outputs['Geometry'])

    # ---- plaza disc (conforms to the terrain)
    mc = g.node('GeometryNodeMeshCircle', fill_type='TRIANGLE_FAN'); g.put(mc, 'Vertices', 64); g.put(mc, 'Radius', G('Plaza Radius'))
    sub = g.node('GeometryNodeSubdivideMesh'); g.L.new(mc.outputs[0], g.I(sub, 'Mesh')); g.put(sub, 'Level', 3)
    disc = g.set_pos(sub.outputs[0], position=None, offset=g.vec(0.0, 0.0, g.add(gz(), 0.04)))
    # the above offset adds the terrain height to z (the disc is flat at z = 0)
    sm = g.node('GeometryNodeSetMaterial'); g.L.new(disc, g.I(sm, 'Geometry'))
    mat = bpy.data.materials.get('MAT_Edo_Plaza')
    if mat is None:
        mat = bpy.data.materials.new('MAT_Edo_Plaza'); mat.diffuse_color = (0.52, 0.46, 0.34, 1.0)
    sm.inputs['Material'].default_value = mat
    parts.append(sm.outputs[0])

    # ---- plaza furniture
    def circle_points(count, radius):
        c = g.node('GeometryNodeMeshCircle', fill_type='NONE'); g.put(c, 'Vertices', count); g.put(c, 'Radius', radius)
        p = g.node('GeometryNodeMeshToPoints'); g.L.new(c.outputs[0], g.I(p, 'Mesh'))
        return p.outputs[0]
    on_ground = lambda pts: g.set_pos(pts, offset=g.vec(0.0, 0.0, g.add(gz(), 0.04)))
    parts.append(g.inst(on_ground(circle_points(12, g.sub(G('Plaza Radius'), 2.6))), 'KIT_Toro', 0, 0.0))
    ang = g.add(g.mul(g.index(), 2 * math.pi / 8), math.pi / 2)
    parts.append(g.inst(on_ground(circle_points(8, g.sub(G('Plaza Radius'), 6.5))), 'KIT_Bench', 0, ang))
    parts.append(g.inst(on_ground(g.point(g.vec(0.0, 0.0, 0.0))), 'KIT_Well', 0, 0.0))
    bx = g.mul(g.sub(G('Plaza Radius'), 1.4), math.cos(math.radians(150)))
    by = g.mul(g.sub(G('Plaza Radius'), 1.4), math.sin(math.radians(150)))
    parts.append(g.inst(on_ground(g.point(g.vec(bx, by, 0.0))), 'KIT_Board', 0, math.radians(60)))

    allg = g.join(*parts)
    rz = g.node('GeometryNodeRealizeInstances'); g.L.new(allg, g.I(rz, 'Geometry'))
    g.L.new(g.sw('GEOMETRY', G('Realize'), allg, rz.outputs[0]), g.I(go, 'Geometry'))
    return t


if __name__ == '__main__':
    pl = plan()
    c = {}
    for s in pl['slots']: c[s['ring']] = c.get(s['ring'], 0) + 1
    print('slots', len(pl['slots']), c)
    for s in pl['slots']: print(s['id'], s['arch'], tuple(round(v, 1) for v in s['pos']), round(math.degrees(s['angle'])))
