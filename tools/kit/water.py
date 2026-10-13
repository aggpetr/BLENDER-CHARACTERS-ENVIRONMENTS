"""Water plan: a thin river drawn by the user, plus the link that joins the canal to the big river.

    python -I tools/kit/water.py            # plans the branch, prints a report, writes kit/village/village_water.json

  * LINK: the canal (WT_Channel, 2 m) ends at (-6, -279) just short of the big river; the link carries it on into the river.
  * BRANCH: a 2 m river that follows the line you drew (canal corner at the north-west -> north of the district ring -> down the east side ->
    the upper river near the south-east). The drawn line cuts through the hospital and a few ring houses, so the route is found on a 1 m grid:
    it stays as close to your line as it can while keeping 3.5 m away from every plot, field and paddy, off the existing canal and the big river,
    and inside the village border. Every street it has to cross gets a small timber bridge (Flat4 / Flat6, the same modules as over the canal).
"""
import sys, os, json, math, heapq
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import town, additions as A
from district import polyline_samples, point_poly_dist

WIDTH = 2.0                                                    # same as the canal
LINK = [(-6.0, -279.0), (-7.0, -282.5), (-8.0, -286.5)]        # canal end -> into the big river (centre line at x=-8 is y about -287)
DRAWN = [(-178.0, -40.0), (-182.5, -35.0), (-138.0, -38.0), (-88.0, -46.0), (-38.0, -42.5), (0.0, -70.0), (50.0, -117.0), (72.0, -154.0), (94.0, -217.0), (116.0, -256.0)]
START = (-178.0, -40.0)                                         # the corner of the canal
END = (117.0, -263.0)                                           # on the upper river centre line (it runs (125,-266) -> (110,-262))
CLEAR = 2.0                                                     # from every plot / field to the water's centre line
CELL = 1.0
X0, Y0, X1, Y1 = -205.0, -300.0, 135.0, 5.0
ROAD_PENALTY = 30.0                                              # extra cost per cell on a street (crossing is allowed, running along one is not wanted)
STRAYING = 1.0 / 14.0                                           # extra cost per metre away from the line you drew
ROOM = 4.6                                                      # a bridge needs this much clear ground each side of the river (half the 9.2 m span)


def _dist_to_poly_line(p, S):
    return min(math.hypot(p[0] - q[0], p[1] - q[1]) for q in S)


def plan(seed=0):
    ctx, lay, man = town.load_context()
    C = A._setup()
    nx = int((X1 - X0) / CELL) + 1; ny = int((Y1 - Y0) / CELL) + 1
    forbid = bytearray(nx * ny)
    def cell(p): return int(round((p[0] - X0) / CELL)), int(round((p[1] - Y0) / CELL))
    def mark(poly, clear):
        xs = [q[0] for q in poly]; ys = [q[1] for q in poly]
        i0, j0 = cell((min(xs) - clear, min(ys) - clear)); i1, j1 = cell((max(xs) + clear, max(ys) + clear))
        for j in range(max(0, j0), min(ny - 1, j1) + 1):
            for i in range(max(0, i0), min(nx - 1, i1) + 1):
                p = (X0 + i * CELL, Y0 + j * CELL)
                if town.inpoly(p, poly) or point_poly_dist(p, poly) < clear: forbid[j * nx + i] = 1
    for name, Q in C['polys']:
        if name == 'canal bank': continue                      # the canal is handled below (the river joins it at its corner)
        mark(Q, CLEAR)
    # the existing canal, the big river and its upper course
    chan = next(s for s in ctx['streams'] if s['name'] == 'WT_Channel'); big = next(s for s in ctx['streams'] if s['name'] == 'WT_Stream')
    up = [(255.0, -302.0), (232.0, -296.0), (205.0, -291.0), (175.0, -284.0), (146.0, -273.0), (125.0, -266.0), (110.0, -262.0)]
    water = [(polyline_samples([tuple(p) for p in chan['pts']], 1.0), 3.5), (polyline_samples([tuple(p) for p in big['pts']] + [], 1.0), 6.0 + 3.5),
             (polyline_samples(up, 1.0), 4.5 + 3.5)]
    chan_pts = [(-6.0, -279.0), (-178.0, -279.0), (-178.0, -40.0), (-296.0, -40.0)]
    water[0] = (polyline_samples(chan_pts, 1.0), 3.5)
    for S, r in water:
        for q in S:
            if math.hypot(q[0] - END[0], q[1] - END[1]) < 14.0 or math.hypot(q[0] - START[0], q[1] - START[1]) < 8.0: continue
            i0, j0 = cell((q[0] - r, q[1] - r)); i1, j1 = cell((q[0] + r, q[1] + r))
            for j in range(max(0, j0), min(ny - 1, j1) + 1):
                for i in range(max(0, i0), min(nx - 1, i1) + 1):
                    if math.hypot(X0 + i * CELL - q[0], Y0 + j * CELL - q[1]) <= r: forbid[j * nx + i] = 1
    # inside the village border (checked lazily while searching)
    bj = json.load(open(os.path.join(HERE, '..', '..', 'kit', 'village', 'village_border.json')))
    bpts = [tuple(p) for p in bj['points']]
    bcache = {}
    def border_ok(i, j):
        k = (i, j)
        if k not in bcache:
            p = (X0 + i * CELL, Y0 + j * CELL)
            bcache[k] = math.hypot(p[0] - END[0], p[1] - END[1]) < 22.0 or (town.inpoly(p, bpts) and min(math.hypot(p[0] - q[0], p[1] - q[1]) for q in bpts) >= 6.0)
        return bcache[k]
    # clear the start and the end (they sit on the canal / upper river that were just forbidden)
    for P0 in (START, END):
        i, j = cell(P0)
        for dj in range(-3, 4):
            for di in range(-3, 4): forbid[(j + dj) * nx + i + di] = 0
    # streets: a cost, not a wall
    roadc = [0.0] * (nx * ny)
    for samples, hw in C['roads']:
        pen = ROAD_PENALTY if hw > 1.0 else 2.5
        for q in samples:
            i0, j0 = cell((q[0] - hw - 1.0, q[1] - hw - 1.0)); i1, j1 = cell((q[0] + hw + 1.0, q[1] + hw + 1.0))
            for j in range(max(0, j0), min(ny - 1, j1) + 1):
                for i in range(max(0, i0), min(nx - 1, i1) + 1):
                    if math.hypot(X0 + i * CELL - q[0], Y0 + j * CELL - q[1]) <= hw + 1.0: roadc[j * nx + i] = max(roadc[j * nx + i], pen)
    drawn = polyline_samples(DRAWN, 3.0)
    dcache = {}
    def devf(i, j):
        k = (i, j)
        if k not in dcache: dcache[k] = _dist_to_poly_line((X0 + i * CELL, Y0 + j * CELL), drawn)
        return dcache[k]
    if os.environ.get('WATER_MASK'):
        from PIL import Image
        im = Image.new('RGB', (nx, ny))
        im.putdata([(255, 0, 0) if forbid[(ny - 1 - j) * nx + i] else ((0, 90, 0) if roadc[(ny - 1 - j) * nx + i] else (230, 230, 230)) for j in range(ny) for i in range(nx)])
        im.save(os.environ['WATER_MASK'])
    s = cell(START); g = cell(END)
    dist = {s: 0.0}; prev = {}; pq = [(0.0, s)]
    nbr = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
    while pq:
        d, u = heapq.heappop(pq)
        if u == g: break
        if d > dist.get(u, 1e18): continue
        for di, dj in nbr:
            v = (u[0] + di, u[1] + dj)
            if not (0 <= v[0] < nx and 0 <= v[1] < ny): continue
            k = v[1] * nx + v[0]
            if forbid[k] or not border_ok(*v): continue
            step = math.hypot(di, dj) * CELL
            c = step * (1.0 + devf(*v) * STRAYING) + roadc[k] * step
            nd = d + c
            if nd < dist.get(v, 1e18): dist[v] = nd; prev[v] = u; heapq.heappush(pq, (nd, v))
    if g not in prev:
        far = min(dist, key=lambda c: math.hypot(c[0] - g[0], c[1] - g[1]))
        print('explored', len(dist), 'closest to goal', (X0 + far[0], Y0 + far[1]), 'start forbid', forbid[s[1] * nx + s[0]], 'goal forbid', forbid[g[1] * nx + g[0]], 'goal border_ok', border_ok(*g))
        raise RuntimeError('no route found')
    path = [g]
    while path[-1] != s: path.append(prev[path[-1]])
    path = [(X0 + i * CELL, Y0 + j * CELL) for i, j in reversed(path)]
    # smooth: Chaikin corner cutting on a thinned polyline, then keep clear of the plots
    thin = path[::6] + [path[-1]]
    thin[0] = START; thin[-1] = END
    for _ in range(3):
        nxt = [thin[0]]
        for a, b in zip(thin[:-1], thin[1:]):
            nxt += [(a[0] * 0.75 + b[0] * 0.25, a[1] * 0.75 + b[1] * 0.25), (a[0] * 0.25 + b[0] * 0.75, a[1] * 0.25 + b[1] * 0.75)]
        nxt.append(thin[-1]); thin = nxt
    pts = [thin[0]]
    for p in thin[1:]:
        if math.hypot(p[0] - pts[-1][0], p[1] - pts[-1][1]) >= 5.0: pts.append(p)
    if pts[-1] != END: pts.append(END)
    return dict(path=pts, grid_path=path, C=C)


def bridges(pts, C):
    """a timber bridge where the river crosses a street wider than a footpath; returns [name, module, x, y, rot_deg, width]"""
    S = polyline_samples(pts, 0.5); out = []
    for ri, (samples, hw) in enumerate(C['roads']):
        hit = [i for i, p in enumerate(S) if any(math.hypot(p[0] - q[0], p[1] - q[1]) < hw + 0.4 for q in samples if abs(q[0] - p[0]) < 12 and abs(q[1] - p[1]) < 12)]
        if not hit: continue
        # split into runs (a river can cross the same street twice)
        runs = [[hit[0]]]
        for i in hit[1:]:
            if i - runs[-1][-1] > 20: runs.append([i])
            else: runs[-1].append(i)
        for r in runs:
            m = S[(r[0] + r[-1]) // 2]; a = S[max(0, (r[0] + r[-1]) // 2 - 4)]; b = S[min(len(S) - 1, (r[0] + r[-1]) // 2 + 4)]
            ang = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])) - 90.0          # the span axis (x) crosses the river, so it is the river direction - 90
            mod = 'SM_Edo_Bridge_Flat6' if hw * 2.0 >= 4.8 else ('SM_Edo_Bridge_Flat4' if hw * 2.0 >= 3.0 else 'SM_Edo_Bridge_Foot')
            out.append([m[0], m[1], ang, max(hw * 2.0, 1.8), mod])
    out.sort(key=lambda r: (r[0], r[1]))
    merged = []
    for r in out:
        if merged and math.hypot(r[0] - merged[-1][0], r[1] - merged[-1][1]) < 8.0: continue
        merged.append(r)
    return [[f'BR_branch_{k + 1}', r[4], round(r[0], 2), round(r[1], 2), round(r[2], 1), round(r[3], 1)] for k, r in enumerate(merged)]


def kerb_runs(pts, br, step=2.0):
    """the river polyline cut open where a bridge crosses (no stone kerb under a bridge); returns a list of polylines"""
    S = polyline_samples(pts, step); gap = {}
    for b in br: gap[b[0]] = 3.4 if b[1].endswith('Foot') else 5.6
    runs = [[]]
    for p in S:
        if any(math.hypot(p[0] - b[2], p[1] - b[3]) < gap[b[0]] for b in br):
            if runs[-1]: runs.append([])
        else: runs[-1].append(p)
    return [r for r in runs if len(r) >= 3]


def report(pts, C):
    S = polyline_samples(pts, 1.0); bad = {}
    for p in S:
        for name, Q in C['polys']:
            if name == 'canal bank' or abs(p[0] - Q[0][0]) > 60: continue
            d = point_poly_dist(p, Q)
            if d < CLEAR - 0.6 or town.inpoly(p, Q): bad[name] = min(bad.get(name, 99), d)
    return bad


if __name__ == '__main__':
    P = plan()
    pts = P['path']; C = P['C']
    L = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts[:-1], pts[1:]))
    br = bridges(pts, C)
    print(f'branch: {len(pts)} points, {L:.0f} m, {len(br)} bridges')
    for b in br: print('  ', b)
    print('too close to plots:', report(pts, C) or 'none')
    out = dict(width_m=WIDTH, link=[list(p) for p in LINK], branch=[[round(x, 2), round(y, 2)] for x, y in pts], branch_bridges=br,
               kerb_runs=[[[round(x, 2), round(y, 2)] for x, y in r] for r in kerb_runs(pts, br)],
               note='thin river along the drawn line: canal corner -> north of the district ring -> east side -> the upper river; canal link: the canal end joins the big river')
    json.dump(out, open(os.path.join(HERE, '..', '..', 'kit', 'village', 'village_water.json'), 'w'), indent=1)
