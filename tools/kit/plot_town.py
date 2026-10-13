"""Draw the town extension plan: python tools/kit/plot_town.py out.png"""
import sys, os, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import town, district
from PIL import Image, ImageDraw
pl = town.plan(); ctx, lay, man = town.load_context()
X0, X1, Y0, Y1 = -300, 70, -285, 70; S = 4.0
im = Image.new('RGB', (int((X1 - X0) * S), int((Y1 - Y0) * S)), (226, 222, 210)); d = ImageDraw.Draw(im)
P = lambda x, y: ((x - X0) * S, (Y1 - y) * S)
for b in ctx['fields']: d.rectangle((*P(b[0], b[3]), *P(b[1], b[2])), fill=(190, 170, 110))
for b in ctx['paddies']: d.rectangle((*P(b[0], b[3]), *P(b[1], b[2])), fill=(150, 190, 170))
for r in ctx['streams']: d.line([P(*p) for p in r['pts']], fill=(110, 150, 190), width=max(2, int(r['width'] * S)))
for r in ctx['roads'] + lay['roads']: d.line([P(*p) for p in r['pts']], fill=(170, 150, 120), width=max(2, int(r['width'] * S)))
for r in pl['roads']: d.line([P(*p) for p in r['pts']], fill=(210, 80, 60), width=max(2, int(r['width'] * S)))
d.line([P(*p) for p in pl['canal']['pts']], fill=(60, 60, 120), width=int(11 * S))
for z in pl['zones']: d.polygon([P(*p) for p in z['poly']], outline=(0, 120, 200))
for h in man['houses']:
    if h['house'].startswith(('K_', 'MT_')) or h['house'] == 'EdoHouse_01': continue
    x, y = h['location'][:2]; d.rectangle((*P(x - 3, y + 3), *P(x + 3, y - 3)), outline=(90, 90, 90))
for s in lay['slots']: d.polygon([P(*c) for c in s['plot_corners_world']], outline=(90, 90, 90))
for s in pl['slots']:
    d.polygon([P(*c) for c in district.corners(s)], outline=(0, 140, 0), width=2); x, y = P(*s['pos']); d.text((x - 10, y - 5), s['arch'][:6], fill=(0, 0, 0))
for gx in range(-300, 71, 50): d.text((P(gx, Y1)[0] + 2, 2), str(gx), fill=(0, 0, 160)); d.line((*P(gx, Y1), *P(gx, Y0)), fill=(200, 205, 220))
for gy in range(-280, 71, 50): d.text((2, P(X0, gy)[1] + 2), str(gy), fill=(0, 0, 160)); d.line((*P(X0, gy), *P(X1, gy)), fill=(200, 205, 220))
im.save(sys.argv[1])
