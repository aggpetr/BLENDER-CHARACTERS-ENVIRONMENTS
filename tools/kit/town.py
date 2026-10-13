"""Town extension planner: new streets, houses in the marked infill areas, extra farmhouses, fields, canal bank, bridges.

    python -I tools/kit/town.py      # prints a summary; build_kit.py writes kit/village/town_layout.json

Everything is planned in world coordinates from kit/village/town_context.json (extracted from the village .blend by
extract_context.py) and kit/village/district_layout.json, so the planner needs no Blender. Houses are placed along the streets
(fronts to the street) and in the zones, never on a street, a field, the canal or each other (checked in code).
"""
import json, math, os, copy, random
from archetypes import ARCH
from district import rot, plot_rect, corners, sat_overlap, point_poly_dist, polyline_samples

HERE = os.path.dirname(os.path.abspath(__file__))
VILLAGE = os.path.join(HERE, '..', '..', 'kit', 'village')
PXM = 3.187                                                    # pixels per metre of the marked top-down image (north up)
px = lambda p: (round(-300.0 + p[0] / PXM, 2), round(35.0 - p[1] / PXM, 2))

# ---- streets drawn in red
NEW_ROADS = [
    dict(name='OUTER_WEST', pts=[(-254, -33), (-254, -90), (-254, -150), (-254, -210), (-254, -262)], width=4.5),
    dict(name='NORTH_LINK', pts=[(-286, -12), (-287.5, -22), (-285, -32.5), (-254, -32.5), (-212, -32.5), (-170, -32.5), (-128, -32.5)], width=4.0),
    dict(name='FIELD_RING', pts=[(-128, -44), (-128, -32.5), (-128, -5), (-128, 27), (-150, 26.7), (-170, 26.5)], width=3.5),
    dict(name='HOSPITAL_WEST', pts=[(-88.1, -41.7), (-100, -46), (-115, -46), (-128, -44)], width=4.5),
    dict(name='LANE_SOUTH1', pts=[(-172, -201.3), (-140, -201.0), (-100, -201.5), (-60, -201.0), (-20, -201.3), (22.5, -201.0)], width=4.0),
    dict(name='EAST_LINK', pts=[(22.5, -150.3), (22.5, -175), (22.5, -201), (22.5, -226)], width=4.0),
    dict(name='LANE3_EAST', pts=[(-150, -229), (-110, -228.5), (-60, -227.5), (-20, -226.5), (22.5, -226)], width=3.5),
]
# ---- streets from the district towards the mountain trail (ground = the full terrain beyond x = OUTER_X), lined with farms and huts
OUTER_X = 62.0                   # the town ground patch ends at x = 68: houses and streets east of this use EDO_Terrain
OUTER_ROADS = [
    dict(name='EAST_TRAIL', pts=[(58, -88), (85, -95), (110, -108), (128, -122), (144, -136)], width=3.5, mix=['hutB', 'hutA', 'hutC', 'farmhouse']),
    dict(name='NE_ROAD', pts=[(-28, -22), (-10, -14), (20, -10), (60, -10), (100, -9), (140, -11), (170, -11), (198, -10)], width=3.5,
         mix=['farmhouse', 'hutA', 'barn', 'hutC', 'farmhouse', 'hutB', 'kura', 'hutA']),
    dict(name='SE_ROAD', pts=[(22.5, -226), (50, -238), (80, -246), (105, -250)], width=3.5, mix=['farmhouse', 'barn', 'hutA', 'farmhouse', 'hutC', 'kura']),
]
LINK_ROADS = [dict(name='SW2_LINK', pts=[(-152, -164), (-151, -172), (-150, -179.5)], width=3.5)]
# ---- areas drawn in blue (pixel polygons of the marked image) and the farm areas
ZONES = [
    dict(id='Z1', px=[(925, 205), (1000, 200), (1045, 250), (1052, 330), (1005, 365), (950, 330), (918, 265)],
         mix=['farmhouse', 'hutA', 'dwellC', 'barn', 'hutB', 'farmhouse', 'hutC', 'dwellA']),
    dict(id='Z2', px=[(548, 320), (600, 314), (650, 340), (642, 366), (560, 366)], mix=['dwellA', 'dwellC', 'dwellB', 'hutB']),
    dict(id='Z3', px=[(535, 400), (595, 395), (598, 440), (572, 486), (535, 482)], mix=['dwellC', 'dwellA', 'hutA', 'dwellB']),
    dict(id='Z4', px=[(595, 700), (660, 678), (760, 690), (840, 712), (842, 744), (600, 746)], mix=['dwellA', 'smithy', 'dwellC', 'farmhouse', 'dwellB', 'hutA']),
    dict(id='Z5', px=[(430, 780), (520, 765), (830, 768), (836, 805), (600, 816), (435, 810)], mix=['farmhouse', 'dwellA', 'barn', 'dwellC', 'hutB', 'farmhouse', 'smithy', 'dwellB']),
    dict(id='Z6', px=[(895, 705), (935, 680), (990, 622), (1018, 640), (1020, 722), (960, 748)], mix=['farmhouse', 'dwellA', 'hutA', 'dwellC', 'barn']),
    dict(id='Z7', px=[(1045, 600), (1090, 585), (1150, 610), (1158, 720), (1140, 830), (1060, 835), (1035, 740)],
         mix=['farmhouse', 'barn', 'dwellA', 'farmhouse', 'hutB', 'dwellC', 'kura', 'hutA']),
]
FARM_ZONES = [                                                   # more farmhouses around the village (world rectangles x0, x1, y0, y1)
    dict(id='F1', rect=(-278, -232, -228, -56), mix=['farmhouse', 'barn', 'hutC', 'kura', 'farmhouse', 'hutB', 'farmhouse', 'hutA']),
    dict(id='F2', rect=(-178, -120, 30, 66), mix=['farmhouse', 'barn', 'hutA', 'farmhouse', 'kura']),
    dict(id='F3', rect=(-124, -92, -30, 6), mix=['farmhouse', 'hutC', 'barn']),
]
CANAL = dict(pts=[(-178.0, -42.0), (-178.0, -150.0), (-178.0, -270.0)], half_width=1.15)
BRIDGES = {                                                      # original bridge -> kit module, centre, rotation, span axis
    'BR_chan_y60': ('SM_Edo_Bridge_Flat4', (-178.0, -60.0), 0.0),
    'BR_chan_y130': ('SM_Edo_Bridge_Flat6', (-178.0, -130.0), 0.0),
    'BR_chan_y180': ('SM_Edo_Bridge_Flat4', (-178.0, -180.0), 0.0),
    'BR_chan_y229': ('SM_Edo_Bridge_Flat4', (-178.0, -229.0), 0.0),
    'BR_chan_main': ('SM_Edo_Bridge_Flat6', (-212.0, -40.0), 90.0),
    'BR_arch_main': ('SM_Edo_Bridge_Arch', (-212.0, -290.0), 90.0),
}
PROP_MAP = {'PR_well': 'SM_Edo_Well', 'PR_board': 'SM_Edo_Board', 'PR_stall': 'SM_Edo_Stall', 'PR_bench': 'SM_Edo_Bench', 'PR_toro': 'SM_Edo_Toro'}
CROPS = [0, 1, 0, 1, 1, 0]                                       # crop of each farmland patch (0 vegetables, 1 barley)

def bridge_gaps():
    """(lo, hi) ranges along Y of the bridges over the vertical canal: no bank is built there"""
    out = []
    for name, (mod, (x, y), rotd) in BRIDGES.items():
        if rotd == 0.0:
            half = (6.4 if 'Flat6' in mod else 4.0) / 2.0 + 0.8
            out.append((y - half, y + half))
    return out


KEYMAP = dict(bx='Bays X', by='Bays Y', fl='Floors', roof='Roof', eng='Engawa', bal='Balcony', shop='Shopfront', lan='Lanterns', fence='Fence', gate='Gate', props='Props')


def inpoly(pt, poly):
    c = False
    for i in range(len(poly)):
        a, b = poly[i], poly[(i + 1) % len(poly)]
        if (a[1] > pt[1]) != (b[1] > pt[1]) and pt[0] < (b[0] - a[0]) * (pt[1] - a[1]) / (b[1] - a[1]) + a[0]:
            c = not c
    return c


def load_context():
    ctx = json.load(open(os.path.join(VILLAGE, 'town_context.json')))
    lay = json.load(open(os.path.join(VILLAGE, 'district_layout.json')))
    man = json.load(open(os.path.join(VILLAGE, 'village_manifest.json')))
    return ctx, lay, man


def zones_world():
    return [dict(z, poly=[px(p) for p in z['px']]) for z in ZONES] + \
           [dict(z, poly=[(z['rect'][0], z['rect'][2]), (z['rect'][1], z['rect'][2]), (z['rect'][1], z['rect'][3]), (z['rect'][0], z['rect'][3])]) for z in FARM_ZONES]


def plan(seed=7):
    ctx, lay, man = load_context()
    rnd = random.Random(seed)
    obstacles = []          # polygons (4 corners) houses must not overlap
    for h in man['houses']:
        if not h['house'].startswith(('TWN_', 'FARM_')):       # your original town and farm houses only (not our own earlier output)
            continue
        p = h['params']
        d = dict(bx=p['Bays X'], by=p['Bays Y'], eng=p['Engawa'], shop=p['Shopfront'], lan=p['Lanterns'], fence=p['Fence'], gate=p['Gate'], props=p['Props'], cat=p.get('Category', 0))
        slot = dict(pos=h['location'][:2], angle=math.radians(h['rotation_z_deg']), rect=plot_rect(d))
        obstacles.append(corners(slot))
    for s in lay['slots']:
        obstacles.append([tuple(c) for c in s['plot_corners_world']])
    for b in ctx['fields']:
        obstacles.append([(b[0] - 2.5, b[2] - 2.5), (b[1] + 2.5, b[2] - 2.5), (b[1] + 2.5, b[3] + 2.5), (b[0] - 2.5, b[3] + 2.5)])
    for b in ctx['paddies']:
        obstacles.append([(b[0] - 3, b[2] - 3), (b[1] + 3, b[2] - 3), (b[1] + 3, b[3] + 3), (b[0] - 3, b[3] + 3)])
    cx, cy = CANAL['pts'][0][0], CANAL['pts'][-1][1]
    obstacles.append([(-186.5, -270.0), (-169.5, -270.0), (-169.5, -38.0), (-186.5, -38.0)])        # canal and its stone banks
    obstacles.append([(-296.0, -47.0), (-170.0, -47.0), (-170.0, -33.5), (-296.0, -33.5)])           # the stream along y = -40
    for br in ctx['bridges']:
        b = br['bbox']; obstacles.append([(b[0] - 1, b[2] - 1), (b[1] + 1, b[2] - 1), (b[1] + 1, b[3] + 1), (b[0] - 1, b[3] + 1)])
    for pr in ctx['props']:
        x, y = pr['loc'][:2]; obstacles.append([(x - 2.5, y - 2.5), (x + 2.5, y - 2.5), (x + 2.5, y + 2.5), (x - 2.5, y + 2.5)])

    roads = [dict(r, kind='road') for r in NEW_ROADS + LINK_ROADS + OUTER_ROADS]
    all_roads = [(r['pts'], r['width']) for r in ctx['roads']] + [(r['pts'], r['width']) for r in lay['roads'] if r['name'] not in ('RING1',)] + \
                [(r['pts'], r['width']) for r in roads] + [(r['pts'], r['width'] + 2.0) for r in ctx['streams'] if r['name'] != 'WT_Stream']
    road_polys = [(polyline_samples([tuple(p) for p in pts], 2.0), w / 2.0) for pts, w in all_roads]
    ring1 = [r for r in lay['roads'] if r['name'] == 'RING1']
    road_polys += [(polyline_samples([tuple(p) for p in r['pts']], 2.0), r['width'] / 2.0) for r in ring1]
    zones = zones_world()
    slots = []

    TER = ctx.get('terrain')

    def terrain_z(x, y):
        if not TER: return 0.0
        fx, fy = (x - TER['x0']) / TER['step'], (y - TER['y0']) / TER['step']
        i, j = int(math.floor(fx)), int(math.floor(fy))
        if i < 0 or j < 0 or i >= TER['nx'] - 1 or j >= TER['ny'] - 1: return None
        v = [TER['rows'][j][i], TER['rows'][j][i + 1], TER['rows'][j + 1][i], TER['rows'][j + 1][i + 1]]
        if any(a is None for a in v): return None
        u, w = fx - i, fy - j
        return (v[0] * (1 - u) + v[1] * u) * (1 - w) + (v[2] * (1 - u) + v[3] * u) * w

    def too_steep(P, pos):
        if pos[0] < OUTER_X - 20: return False
        zs = [terrain_z(*q) for q in P + [pos]]
        zs = [z for z in zs if z is not None]
        return bool(zs) and max(zs) - min(zs) > 3.6

    def fits(slot):
        P = corners(slot)
        if too_steep(P, slot['pos']):
            return False
        for Q in obstacles + [corners(o) for o in slots]:
            if abs(slot['pos'][0] - Q[0][0]) < 90 and sat_overlap(P, Q):
                return False
        for samples, hw in road_polys:
            for pt in samples:
                if abs(pt[0] - slot['pos'][0]) < 60 and abs(pt[1] - slot['pos'][1]) < 60 and point_poly_dist(pt, P) < hw + 0.8:
                    return False
        return True

    def make(name, props):
        p = copy.deepcopy(ARCH[name])
        d = dict(bx=p['bx'], by=p['by'], fl=p.get('fl', 1), roof=p['roof'], eng=bool(p.get('eng')), bal=bool(p.get('bal')), shop=bool(p.get('shop')),
                 lan=bool(p.get('lan')), fence=p.get('fence', 0), gate=bool(p.get('gate')), cat=p.get('cat', 0))
        if name in ('farmhouse', 'hutA', 'hutB', 'hutC', 'dwellC', 'dwellA') and d['fence'] == 0:
            d['fence'] = 1
        d['props'] = props
        return d

    counters = {z['id']: 0 for z in zones}
    counters.update({'O' + r['name'][:2]: 0 for r in OUTER_ROADS})

    def try_place(zone, pos_fn, nx, ny, name):
        d = make(name, 0.5 if name in ('farmhouse', 'barn', 'hutC', 'kura') else 0.35)
        rect = plot_rect(d)
        pos = pos_fn(rect)
        ang = math.atan2(-nx, ny)
        slot = dict(id='', arch=name, ring=zone['id'], **d, pos=pos, angle=ang, rect=rect, seed=3000 + len(slots) * 7)
        if (zone['poly'] is None or inpoly(pos, zone['poly'])) and fits(slot):
            slot['id'] = f"T_{zone['id']}_{len([s for s in slots if s['ring'] == zone['id']]):02d}"
            slots.append(slot)
            return slot
        return None

    # ---- 1. frontage along the streets: both sides, fronts to the street
    for pts, w in all_roads:
        L = [tuple(p) for p in pts]
        cum = [0.0]
        for a, b in zip(L[:-1], L[1:]): cum.append(cum[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
        if cum[-1] < 20:
            continue
        for side in (1, -1):
            s = 8.0
            while s < cum[-1] - 8.0:
                i = max(k for k in range(len(L) - 1) if cum[k] <= s)
                t = (s - cum[i]) / max(cum[i + 1] - cum[i], 1e-9); a, b = L[i], L[i + 1]
                T = ((b[0] - a[0]) / (cum[i + 1] - cum[i]), (b[1] - a[1]) / (cum[i + 1] - cum[i]))
                pt = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
                n = (-T[1] * side, T[0] * side)
                probe = (pt[0] + n[0] * 12.0, pt[1] + n[1] * 12.0)
                zone = next((z for z in zones if inpoly(probe, z['poly'])), None)
                if zone is None:
                    s += 4.0; continue
                name = zone['mix'][counters[zone['id']] % len(zone['mix'])]
                got = try_place(zone, lambda rect: (pt[0] + n[0] * (w / 2.0 + 1.4 - rect[2]), pt[1] + n[1] * (w / 2.0 + 1.4 - rect[2])), n[0], n[1], name)
                if got:
                    counters[zone['id']] += 1
                    s += (got['rect'][1] - got['rect'][0]) * 0.5 + 2.5
                else:
                    s += 3.0

    # ---- 1b. farms and huts along the streets towards the trail
    for r in OUTER_ROADS:
        L = [tuple(p) for p in r['pts']]
        cum = [0.0]
        for a, b in zip(L[:-1], L[1:]): cum.append(cum[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
        zone = dict(id='O' + r['name'][:2], poly=None)
        for side, k in ((1, 0), (-1, 3)):
            s = 14.0
            while s < cum[-1] - 4.0:
                i = max(kk for kk in range(len(L) - 1) if cum[kk] <= s)
                t = (s - cum[i]) / max(cum[i + 1] - cum[i], 1e-9); a, b = L[i], L[i + 1]
                Tn = ((b[0] - a[0]) / (cum[i + 1] - cum[i]), (b[1] - a[1]) / (cum[i + 1] - cum[i]))
                pt = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
                n = (-Tn[1] * side, Tn[0] * side)
                got = try_place(zone, lambda rect: (pt[0] + n[0] * (r['width'] / 2.0 + 1.4 - rect[2]), pt[1] + n[1] * (r['width'] / 2.0 + 1.4 - rect[2])), n[0], n[1], r['mix'][k % len(r['mix'])])
                if got:
                    k += 1; s += (got['rect'][1] - got['rect'][0]) * 0.5 + 7.0
                else:
                    s += 4.0

    # ---- 2. infill: houses in the rest of every area, turned towards the nearest street
    def nearest_road(pt):
        best = (1e9, None, None)
        for samples, hw in road_polys:
            for q in samples:
                d = math.hypot(q[0] - pt[0], q[1] - pt[1])
                if d < best[0]: best = (d, q, hw)
        return best
    for zone in zones:
        xs = [p[0] for p in zone['poly']]; ys = [p[1] for p in zone['poly']]
        cands = [(x + rnd.uniform(-2, 2), y + rnd.uniform(-2, 2)) for x in [min(xs) + 4 + i * 11.0 for i in range(int((max(xs) - min(xs)) / 11.0))]
                 for y in [min(ys) + 4 + j * 11.0 for j in range(int((max(ys) - min(ys)) / 11.0))]]
        rnd.shuffle(cands)
        for c in cands:
            if not inpoly(c, zone['poly']): continue
            d, q, hw = nearest_road(c)
            if q is None or d > 60: continue
            nx, ny = (c[0] - q[0]) / max(d, 1e-6), (c[1] - q[1]) / max(d, 1e-6)
            name = zone['mix'][counters[zone['id']] % len(zone['mix'])]
            got = try_place(zone, lambda rect: (c[0] - nx * 0.0, c[1]), nx, ny, name)
            if got: counters[zone['id']] += 1
    for sl in slots:
        sl['pos_local'] = tuple(sl['pos']); sl['outer'] = sl['pos'][0] > OUTER_X
    fields = []
    for i, b in enumerate(ctx['fields']):
        fields.append(dict(id=f'FIELD_{i:02d}', center=[(b[0] + b[1]) / 2, (b[2] + b[3]) / 2], size=[b[1] - b[0] - 0.4, b[3] - b[2] - 0.4], crop=CROPS[i % len(CROPS)], seed=500 + i))
    for i, b in enumerate(ctx['paddies']):
        fields.append(dict(id=f'PADDY_{i:02d}', center=[(b[0] + b[1]) / 2, (b[2] + b[3]) / 2], size=[b[1] - b[0] - 0.6, b[3] - b[2] - 0.6], crop=2, seed=600 + i))
    props = []
    for pr in ctx['props']:
        mod = next((m for k, m in PROP_MAP.items() if pr['name'].startswith(k)), None)
        if mod: props.append(dict(name=pr['name'], module=mod))
    return dict(center=(0.0, 0.0), slots=slots, roads=roads, fields=fields, canal=CANAL, bridges=BRIDGES, props=props, zones=[dict(id=z['id'], poly=z['poly']) for z in zones])


def to_json(pl):
    out = copy.deepcopy(pl)
    for s in out['slots']:
        s['plot_corners_world'] = [[round(v, 3) for v in c] for c in corners(s)]
        s['pos'] = [round(v, 3) for v in s['pos']]; s['pos_local'] = list(s['pos'])
        s['angle_deg'] = round(math.degrees(s['angle']), 3); s['rect'] = [round(v, 3) for v in s['rect']]
    for r in out['roads']: r['pts'] = [[round(a, 3), round(b, 3)] for a, b in r['pts']]
    out['center'] = list(out['center'])
    return out


if __name__ == '__main__':
    pl = plan()
    c = {}
    for s in pl['slots']: c[s['ring']] = c.get(s['ring'], 0) + 1
    print('slots', len(pl['slots']), c)
    a = {}
    for s in pl['slots']: a[s['arch']] = a.get(s['arch'], 0) + 1
    print(a)
