"""Proposed additions to finish the village (a planning map only, nothing is built from this yet).

    python -I tools/kit/plot_additions.py <base_topdown.png> <out.png>      # draws the proposals over a top-down render
    python -I tools/kit/additions.py                                        # checks every footprint against houses, streets, fields

Each item: id, name, group, area (in / out of the village), centre (x, y) in Blender metres, footprint (width, depth) and a note.
Footprints are checked against the 91 + 34 + 94 houses, the district plots, fields, paddies, the canal and all streets.
"""
import sys, os, json, math
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import town
from district import corners, sat_overlap, point_poly_dist, polyline_samples

# group: landmark, civic, work, water, farm, trail, street
ITEMS = [
    # ---- inside the village
    dict(id=1, name='Fire-watch tower (hinomi yagura)', group='landmark', area='in', c=(-61.0, -108.0), size=(6, 6), plaza=True, note='at the plaza edge, 12 m tall, bell + ladder'),
    dict(id=2, name='Temple + pagoda / bell tower', group='landmark', area='in', c=(-100.0, 94.0), size=(46, 40), note='north-west, stone stairs, own street (TEMPLE_ST)'),
    dict(id=3, name='Graveyard', group='landmark', area='in', c=(-148.0, 96.0), size=(24, 16), note='beside the temple, stone markers, Jizo statues'),
    dict(id=4, name='Samurai quarter (3 walled compounds)', group='civic', area='in', c=(-48.0, 58.0), size=(64, 28), note='long walls + gate houses along a new street (LANE_NORTH)'),
    dict(id=5, name='Public bathhouse (sento)', group='civic', area='in', c=(-124.0, -142.0), size=(16, 12), note='west of the district, by the canal'),
    dict(id=6, name='School (terakoya)', group='civic', area='in', c=(-72.0, -50.0), size=(16, 12), note='next to the hospital, small yard, bell'),
    dict(id=7, name='Stable + horse yard', group='civic', area='in', c=(38.0, -66.0), size=(22, 16), note='east entrance, hitching rails, troughs'),
    dict(id=8, name='North gate (checkpoint)', group='civic', area='in', c=(-212.0, 52.0), size=(10, 6), on_street=True, note='on RD_Main, guard house'),
    dict(id=9, name='South gate at the arch bridge', group='civic', area='in', c=(-212.0, -268.0), size=(10, 6), on_street=True, note='on RD_Main'),
    dict(id=10, name='East gate', group='civic', area='in', c=(38.0, -91.0), size=(10, 6), on_street=True, note='on the district east street'),
    dict(id=11, name='Watermill', group='water', area='in', c=(-178.0, -96.0), size=(14, 8), plaza=True, note='on the canal, wheel in the water'),
    dict(id=12, name='Sake brewery (large kura, cedar ball)', group='work', area='in', c=(-238.0, -268.0), size=(24, 16), note='west of RD_Main'),
    dict(id=13, name='Indigo dye works + cloth poles', group='work', area='in', c=(-196.0, -280.0), size=(20, 14), note='canal end, cloth drying over the water'),
    # ---- outside the village
    dict(id=14, name='Hill shrine + torii avenue + stairs', group='landmark', area='out', c=(126.0, -62.0), size=(30, 22), note='on the rise east of the district, path from EAST_TRAIL'),
    dict(id=15, name='Hill watchtower', group='landmark', area='out', c=(150.0, 18.0), size=(8, 8), note='over the plain, path from NE_ROAD'),
    dict(id=16, name='Mountain temple on the trail', group='landmark', area='out', c=(220.0, 8.0), size=(30, 26), note='next to PATH_p3_p4'),
    dict(id=17, name='Hot spring (onsen)', group='trail', area='out', c=(188.0, -113.0), size=(18, 14), note='stone pool + bath hut by PATH_p2_p3'),
    dict(id=18, name='Charcoal kilns + logging camp', group='trail', area='out', c=(137.0, -206.0), size=(26, 18), note='by PATH_p2_p1'),
    dict(id=19, name='Mill pond + waterwheel', group='water', area='out', c=(-8.0, -283.0), size=(14, 12), note='where the channel (WT_Channel) ends'),
    dict(id=20, name='Ferry pier + fisher hut', group='water', area='out', c=(-70.2, -289.0), size=(10, 8), note='on the river, footpath between the paddies'),
]
TERRACES = [
    dict(id=21, name='Rice terraces + stone retaining walls (south-east foothills)', poly=[(72, -172), (118, -178), (125, -215), (78, -222)]),
    dict(id=22, name='Rice terraces + stone retaining walls (north-east foothills)', poly=[(105, 20), (150, 22), (155, 58), (108, 60)]),
]
STREETS = [      # new streets / paths the additions need (dashed in the map)
    dict(name='LANE_NORTH', pts=[(-128, 27), (-95, 30), (-55, 31), (-28, 27), (-28, -6), (-28, -22)], note='links FIELD_RING, the samurai quarter and the north street'),
    dict(name='TEMPLE_ST', pts=[(-96, 30), (-99, 52), (-100, 73)], note='stone paved, to the temple'),
    dict(name='SHRINE_PATH', pts=[(103, -104), (116, -82), (124, -72)], note='torii avenue'),
    dict(name='WATCH_PATH', pts=[(138, -11), (148, 4), (150, 14)], note=''),
    dict(name='FERRY_PATH', pts=[(-70.2, -228), (-70.2, -285)], note='3 m footpath between the paddies'),
    dict(name='ONSEN_PATH', pts=[(187, -90), (188, -106)], note=''),
    dict(name='KILN_PATH', pts=[(158, -196), (146, -203)], note=''),
]
FURNITURE = dict(                                    # small things, drawn as dots
    lanterns=[('RD_Main', [(-212, -283), (-212, 66)]), ('RD_VillageRoad', [(-228, -130), (-122, -130)]), ('Lane1', [(-262, -60), (-128, -60)]),
              ('Lane2', [(-262, -180), (-128, -180)]), ('Lane3', [(-262, -229), (-150, -229)])],
    jizo=[(-254, -268), (110, -108), (100, -9), (105, -250), (198, -10), (144, -136), (-128, 27), (22.5, -150.3)],
    footbridges=[(-178, -95), (-178, -155), (-178, -205)],
    washing_steps=[(-172, -45), (-172, -118), (-172, -168), (-184, -118)],
    field_sheds=[(-262, 8), (-226, 22), (-130, -32), (-268, -48), (-268, -196), (-132, 18)],
)
NOTES_OUT = ['terrace steps + retaining walls under the houses on the slopes along NE_ROAD (x 100 to 140)', 'irrigation ditches from the channel to the paddies',
             'stone steps and switchbacks where the trails climb', 'wooden log bridges over the small streams']


def _rect(item, ang=0.0):
    w, d = item['size']; return corners(dict(pos=item['c'], angle=ang, rect=(-w / 2, w / 2, -d / 2, d / 2)))


_CACHE = {}


def _setup():
    if _CACHE: return _CACHE
    ctx, lay, man = town.load_context()
    pl = town.plan()
    polys = []
    for h in man['houses']:
        if not h['house'].startswith(('TWN_', 'FARM_')): continue
        p = h['params']
        d = dict(bx=p['Bays X'], by=p['Bays Y'], eng=p['Engawa'], shop=p['Shopfront'], lan=p['Lanterns'], fence=p['Fence'], gate=p['Gate'], props=p['Props'], cat=p.get('Category', 0))
        polys.append(('house ' + h['house'], corners(dict(pos=h['location'][:2], angle=math.radians(h['rotation_z_deg']), rect=town.plot_rect(d)))))
    polys += [('district ' + s['id'], [tuple(c) for c in s['plot_corners_world']]) for s in lay['slots']]
    polys += [('town ' + s['id'], corners(s)) for s in pl['slots']]
    for i, b in enumerate(ctx['fields']): polys.append((f'field {i}', [(b[0], b[2]), (b[1], b[2]), (b[1], b[3]), (b[0], b[3])]))
    for i, b in enumerate(ctx['paddies']): polys.append((f'paddy {i}', [(b[0], b[2]), (b[1], b[2]), (b[1], b[3]), (b[0], b[3])]))
    polys.append(('canal bank', [(-186.5, -270.0), (-169.5, -270.0), (-169.5, -38.0), (-186.5, -38.0)]))
    roads = [(r['pts'], r['width']) for r in ctx['roads'] + lay['roads'] + pl['roads']]
    _CACHE.update(polys=polys, roads=[(polyline_samples([tuple(p) for p in pts], 2.0), w / 2.0) for pts, w in roads])
    return _CACHE


def _conflicts(it):
    C = _setup(); P = _rect(it); bad = []
    for name, Q in C['polys']:
        if it.get('plaza') and name.startswith(('canal', 'district')): continue
        if abs(it['c'][0] - Q[0][0]) < 80 and sat_overlap(P, Q): bad.append(name)
    if not (it.get('plaza') or it.get('on_street')):
        for samples, hw in C['roads']:
            if any(point_poly_dist(pt, P) < hw + 0.5 for pt in samples if abs(pt[0] - it['c'][0]) < 60 and abs(pt[1] - it['c'][1]) < 60):
                bad.append('street'); break
    return bad


def check():
    return [(it, _conflicts(it)) for it in ITEMS]


def free_spot(it, r=45, step=3.0):
    """nearest conflict-free centre around the proposed one (for planning)"""
    best = None
    c0 = it['c']
    for dx in [i * step for i in range(-int(r / step), int(r / step) + 1)]:
        for dy in [i * step for i in range(-int(r / step), int(r / step) + 1)]:
            t = dict(it, c=(c0[0] + dx, c0[1] + dy))
            if not _conflicts(t) and (best is None or math.hypot(dx, dy) < best[0]): best = (math.hypot(dx, dy), t['c'])
    return best


if __name__ == '__main__':
    for it, bad in check():
        line = f"{it['id']:2d} {it['name'][:46]:46s} {it['c']}  {'OK' if not bad else 'CONFLICT: ' + ', '.join(sorted(set(bad)))}"
        if bad:
            fs = free_spot(it); line += f"   -> nearest free spot {fs[1] if fs else None}"
        print(line)
