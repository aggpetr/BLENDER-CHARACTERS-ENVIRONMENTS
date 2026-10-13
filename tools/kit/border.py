"""Village border: a closed, irregular line outside all houses that meets four torii gates (north, south, east, west).

    python -I tools/kit/border.py [seed]        # prints a summary and writes kit/village/village_border.json

How the shape is made (nothing is built from it yet, it is a plan):
  1. every plot corner of the 94 original houses, the district, the town extension, the fields, paddies and the canal bank is a point that must lie inside;
  2. around the village centre, for every angle, the distance to the farthest such point (plus 20 m) is smoothed and given a smooth random bulge (a few low
     harmonics), so the outline is irregular but always outside everything;
  3. on the south the border is capped at the north bank of the river, so the river is the natural border there and the arch bridge becomes the south gate;
  4. at each of the four gates the border is straightened for 16 m on both sides, perpendicular to the road, so the line enters the torii straight and
     leaves it straight; between the gates the outline can wander (four arcs: north-east, south-east, south-west, north-west);
  5. every other street that crosses the border gets a small side gate (a stone marker or a small torii).
"""
import sys, os, json, math, random
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import town, additions as A
from district import polyline_samples

MARGIN = 20.0            # clearance between the farthest house plot and the border
STRAIGHT = 16.0          # the border runs straight and square to the road for this far on each side of a gate
GATES = [                # name, a point on the road inside the village, direction of travel out of the village, road, kind
    ('north', (-212.0, 40.0), (0.0, 1.0), 'RD_Main', 'torii'),
    ('south', (-212.0, -200.0), (0.0, -1.0), 'RD_Main (arch bridge)', 'torii'),
    ('west', (-228.0, -130.0), (-1.0, 0.0), 'WEST_ROAD (new)', 'torii'),
    ('east', (60.0, -150.0), (1.0, 0.0), 'PATH_hub_p2 (mountain trail)', 'open'),        # no gate: the trail just passes through a gap in the border
]
RIVER_WIDTH = 12.0       # the river is made wider (it was 7 m); the border stays 5 m back from its bank on the south
GAP_TORII = 11.2         # border stones stop this far from a torii gate centre (the stone piers stand 5.2 m out, the rope runs pier to stone)
GAP_OPEN = 3.4           # open door / side gate: a stone on each side of the road
SPACING = 6.0            # stones every 6 m, a 6 m rope between them


def seg_hit(p, d, a, b):
    """ray p + t d (t > 0) against the segment a-b; returns t or None"""
    ex, ey = b[0] - a[0], b[1] - a[1]
    den = d[0] * ey - d[1] * ex
    if abs(den) < 1e-9: return None
    t = ((a[0] - p[0]) * ey - (a[1] - p[1]) * ex) / den
    u = ((a[0] - p[0]) * d[1] - (a[1] - p[1]) * d[0]) / den
    return t if t > 0 and 0 <= u <= 1 else None


def poly_hit(p, d, poly):
    ts = [seg_hit(p, d, poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly))]
    ts = [t for t in ts if t is not None]
    return min(ts) if ts else None


def inpoly(pt, poly):
    c = False
    for i in range(len(poly)):
        a, b = poly[i], poly[(i + 1) % len(poly)]
        if (a[1] > pt[1]) != (b[1] > pt[1]) and pt[0] < (b[0] - a[0]) * (pt[1] - a[1]) / (b[1] - a[1]) + a[0]: c = not c
    return c


def resample(poly, step):
    out = []
    for i in range(len(poly)):
        a, b = poly[i], poly[(i + 1) % len(poly)]
        n = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) / step))
        out += [(a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n) for k in range(n)]
    return out


def make(seed=11):
    C = A._setup(); ctx = town.load_context()[0]
    pts = [p for name, poly in C['polys'] for p in poly]
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    c0 = ((min(xs) + max(xs)) / 2.0, (min(ys) + max(ys)) / 2.0)
    river = [tuple(p) for p in next(r for r in ctx['streams'] if r['name'] == 'WT_Stream')['pts']]
    rnd = random.Random(seed); NA = 180
    ang = [2 * math.pi * k / NA for k in range(NA)]
    need = []
    for th in ang:
        ct, st = math.cos(th), math.sin(th); best = 0.0
        for p in pts:
            dx, dy = p[0] - c0[0], p[1] - c0[1]
            t = dx * ct + dy * st
            if t > 0 and abs(-dx * st + dy * ct) < 18.0: best = max(best, t)
        need.append(best)
    r0 = [n + MARGIN for n in need]
    r1 = [max(r0[(k + j) % NA] for j in range(-5, 6)) for k in range(NA)]               # never inside a house
    r1 = [sum(r1[(k + j) % NA] for j in range(-4, 5)) / 9.0 for k in range(NA)]
    r1 = [max(a, b) for a, b in zip(r1, r0)]
    ph = [rnd.uniform(0, 2 * math.pi) for _ in range(8)]
    noise = [sum((10.0 / (h ** 0.9)) * math.cos(h * th + ph[h]) for h in range(2, 8)) for th in ang]
    lo = min(noise); noise = [n - lo for n in noise]; hi = max(noise); noise = [n * min(1.0, 22.0 / hi) for n in noise]
    r = [a + 3.0 + n for a, n in zip(r1, noise)]
    rv = polyline_samples(river, 1.0)
    capv = [None] * NA
    for k, th in enumerate(ang):                                                        # the river is the south border
        d = (math.cos(th), math.sin(th)); best = None
        for q in rv:
            dx, dy = q[0] - c0[0], q[1] - c0[1]; t = dx * d[0] + dy * d[1]
            if t > 0 and abs(-dx * d[1] + dy * d[0]) < 1.5 and t > r0[k] - 6.0: best = t if best is None else min(best, t)
        capv[k] = None if best is None else max(best - (RIVER_WIDTH / 2.0 + 5.0), r0[k] - 4.0)
        if best is not None: r[k] = min(r[k], capv[k])
    # the river cap is jagged where the ray grazes the river: smooth the radius, then keep it outside the houses and on this side of the river
    for _ in range(3):
        r = [sum(r[(k + j) % NA] for j in range(-3, 4)) / 7.0 for k in range(NA)]
        r = [max(r0[k] + 2.0, min(r[k], capv[k]) if capv[k] is not None else r[k]) for k in range(NA)]
    poly = [(c0[0] + r[k] * math.cos(th), c0[1] + r[k] * math.sin(th)) for k, th in enumerate(ang)]
    P = resample(poly, 3.0)
    # ---- gates: where each road leaves the village, the border is straight and square to the road
    gates = []
    for name, p0, d, road, gkind in GATES:
        t = poly_hit(p0, d, P)
        g = (p0[0] + d[0] * t, p0[1] + d[1] * t)
        gates.append(dict(name=name, pos=g, dir=d, road=road, kind=gkind))
    for gt in gates:
        u = (-gt['dir'][1], gt['dir'][0]); g = gt['pos']
        i0 = min(range(len(P)), key=lambda i: math.hypot(P[i][0] - g[0], P[i][1] - g[1]))
        keep = [(i, p) for i, p in enumerate(P) if math.hypot(p[0] - g[0], p[1] - g[1]) > STRAIGHT + 1.0]
        prev = P[(i0 - 3) % len(P)]; nxt = P[(i0 + 3) % len(P)]
        tdir = (nxt[0] - prev[0], nxt[1] - prev[1])
        if u[0] * tdir[0] + u[1] * tdir[1] < 0: u = (-u[0], -u[1])
        line = [(g[0] + u[0] * s, g[1] + u[1] * s) for s in [x * 2.0 for x in range(-int(STRAIGHT / 2), int(STRAIGHT / 2) + 1)]]
        # order the border so that it starts just after the straight part, then append the straight part
        order = sorted(range(len(P)), key=lambda i: (i - i0) % len(P))
        rest = [P[i] for i in order if math.hypot(P[i][0] - g[0], P[i][1] - g[1]) > STRAIGHT + 1.0]
        P = line + rest; gt['u'] = u
    # ---- smooth (not near a gate)
    def near_gate(p): return any(math.hypot(p[0] - gt['pos'][0], p[1] - gt['pos'][1]) < STRAIGHT + 6.0 for gt in gates)
    for _ in range(6):
        Q = []
        for i, p in enumerate(P):
            a, b = P[i - 1], P[(i + 1) % len(P)]
            Q.append(p if near_gate(p) else (p[0] * 0.5 + (a[0] + b[0]) * 0.25, p[1] * 0.5 + (a[1] + b[1]) * 0.25))
        P = Q
    outside = [p for p in pts if not inpoly(p, P)]
    # ---- other streets crossing the border get side gates
    roads = [(r['name'], r['pts']) for r in ctx['roads'] + town.NEW_ROADS + town.OUTER_ROADS + town.LINK_ROADS] + [(s['name'], s['pts']) for s in A.STREETS]
    side = []
    for name, rp in roads:
        rp = [tuple(p) for p in rp]
        for a, b in zip(rp[:-1], rp[1:]):
            for i in range(len(P)):
                c, d = P[i], P[(i + 1) % len(P)]
                den = (b[0] - a[0]) * (d[1] - c[1]) - (b[1] - a[1]) * (d[0] - c[0])
                if abs(den) < 1e-9: continue
                t = ((c[0] - a[0]) * (d[1] - c[1]) - (c[1] - a[1]) * (d[0] - c[0])) / den
                s = ((c[0] - a[0]) * (b[1] - a[1]) - (c[1] - a[1]) * (b[0] - a[0])) / den
                if 0 <= t <= 1 and 0 <= s <= 1:
                    pos = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
                    if all(math.hypot(pos[0] - g['pos'][0], pos[1] - g['pos'][1]) > 22 for g in gates) and all(math.hypot(pos[0] - q['pos'][0], pos[1] - q['pos'][1]) > 14 for q in side):
                        side.append(dict(name=name, pos=pos))
    # ---- boundary stones every ~36 m
    L = [0.0]
    for i in range(len(P)): L.append(L[-1] + math.hypot(P[(i + 1) % len(P)][0] - P[i][0], P[(i + 1) % len(P)][1] - P[i][1]))
    stones = []; nxt = 18.0
    for i in range(len(P)):
        if L[i] >= nxt:
            if all(math.hypot(P[i][0] - g['pos'][0], P[i][1] - g['pos'][1]) > 14 for g in gates): stones.append(P[i])
            nxt += 36.0
    return dict(center=c0, points=P, gates=gates, side_gates=side, stones=stones, length=L[-1], outside=len(outside), margin=MARGIN, straight=STRAIGHT, river=river)


def instances(b):
    """stones, ropes, torii, piers, lanterns and Jizo statues along the border as [kind, x, y, yaw, sx] rows:
    kind 0 stone, 1 rope (sx = length / 6 m), 2 torii, 3 pier, 4 stone lantern, 5 Jizo. The river (south) has no stones, the east trail only an open gap."""
    P = b['points']; n = len(P); out = []
    river = polyline_samples(b['river'], 2.0)
    def near_river(p): return min(math.hypot(p[0] - q[0], p[1] - q[1]) for q in river) < RIVER_WIDTH / 2.0 + 14.0
    cuts = []                                                 # (centre, radius) where the border is interrupted
    for g in b['gates']:
        cuts.append((g['pos'], GAP_TORII if g['kind'] == 'torii' else GAP_OPEN))
    for sg in b['side_gates']: cuts.append((sg['pos'], GAP_OPEN))
    def cut(p): return near_river(p) or any(math.hypot(p[0] - c[0], p[1] - c[1]) < r for c, r in cuts)
    flags = [cut(p) for p in P]
    if all(flags): return out
    start = next(i for i in range(n) if flags[i])             # begin at a cut so that runs do not wrap
    runs = []; run = []
    for k in range(1, n + 1):
        i = (start + k) % n
        if not flags[i]: run.append(P[i])
        elif run: runs.append(run); run = []
    if run: runs.append(run)
    for run in runs:
        L = [0.0]
        for a, c in zip(run[:-1], run[1:]): L.append(L[-1] + math.hypot(c[0] - a[0], c[1] - a[1]))
        if L[-1] < 4.0: continue
        m = max(1, round(L[-1] / SPACING)); step = L[-1] / m; pos = []
        for j in range(m + 1):
            d = j * step; i = max(k for k in range(len(L)) if L[k] <= d + 1e-9)
            if i >= len(run) - 1: pos.append(run[-1]); continue
            t = (d - L[i]) / max(L[i + 1] - L[i], 1e-9); a, c = run[i], run[i + 1]
            pos.append((a[0] + (c[0] - a[0]) * t, a[1] + (c[1] - a[1]) * t))
        for p in pos: out.append([0, p[0], p[1], 0.0, 1.0])
        for p, q in zip(pos[:-1], pos[1:]):
            out.append([1, (p[0] + q[0]) / 2, (p[1] + q[1]) / 2, math.atan2(q[1] - p[1], q[0] - p[0]), math.hypot(q[0] - p[0], q[1] - p[1]) / 6.0])
    for g in b['gates']:
        u = g['u']; d = g['dir']; gp = g['pos']; yaw = math.atan2(u[1], u[0])
        if g['kind'] == 'torii':
            if g['name'] == 'south': gp = (gp[0], gp[1] + 4.0)                                    # on the road, just north of the bridge
            out.append([2, gp[0], gp[1], yaw, 1.0])
            for sgn in (-1, 1):
                out.append([4, gp[0] + u[0] * sgn * 3.5 - d[0] * 4.5, gp[1] + u[1] * sgn * 3.5 - d[1] * 4.5, yaw, 1.0])               # lanterns on the village side
                if g['name'] != 'south':
                    pier = (gp[0] + u[0] * sgn * 5.2, gp[1] + u[1] * sgn * 5.2); out.append([3, pier[0], pier[1], yaw, 1.0])
                    st = (gp[0] + u[0] * sgn * GAP_TORII, gp[1] + u[1] * sgn * GAP_TORII)                                             # rope from the pier to the first stone
                    out.append([1, (pier[0] + st[0]) / 2, (pier[1] + st[1]) / 2, math.atan2(st[1] - pier[1], st[0] - pier[0]), math.hypot(st[0] - pier[0], st[1] - pier[1]) / 6.0])
        else:
            for sgn in (-1, 1): out.append([0, gp[0] + u[0] * sgn * GAP_OPEN, gp[1] + u[1] * sgn * GAP_OPEN, 0.0, 1.0])
    for sg in b['side_gates']:                                                                    # side gaps: a stone each side, a Jizo beside one of them
        out.append([5, sg['pos'][0] + 2.2, sg['pos'][1] + 2.2, 0.0, 1.0])
    return out


def to_json(b):
    r = lambda p: [round(p[0], 2), round(p[1], 2)]
    return dict(center=r(b['center']), length_m=round(b['length'], 1), margin_m=b['margin'], straight_m=b['straight'], points_outside=b['outside'],
                points=[r(p) for p in b['points']], stones=[r(p) for p in b['stones']],
                gates=[dict(name=g['name'], pos=r(g['pos']), road_dir=list(g['dir']), road=g['road']) for g in b['gates']],
                side_gates=[dict(road=s['name'], pos=r(s['pos'])) for s in b['side_gates']],
                river_width_m=RIVER_WIDTH, style='standing stones every 6 m with a shimenawa rope; torii at north, west and south; open gap on the east trail; the river is the south border',
                instances=[[k, round(x, 2), round(y, 2), round(yw, 4), round(sx, 3)] for k, x, y, yw, sx in instances(b)])


if __name__ == '__main__':
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 11
    b = make(seed)
    json.dump(to_json(b), open(os.path.join(HERE, '..', '..', 'kit', 'village', 'village_border.json'), 'w'), indent=1)
    ins = instances(b); print('instances', len(ins), 'stones', sum(1 for r in ins if r[0] == 0), 'ropes', sum(1 for r in ins if r[0] == 1))
    print(f"border: {len(b['points'])} points, {b['length']:.0f} m long, {b['outside']} plot corners outside")
    for g in b['gates']: print('  gate', g['name'], tuple(round(v, 1) for v in g['pos']), g['road'])
    print('  side gates', len(b['side_gates']), [s['name'] for s in b['side_gates']])
