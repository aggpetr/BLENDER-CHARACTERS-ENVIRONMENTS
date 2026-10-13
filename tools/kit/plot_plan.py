"""Draw the district plan (plaza, roads, house plots) as an image: python tools/kit/plot_plan.py out.png"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import district
from PIL import Image, ImageDraw
pl = district.plan(); cx, cy = pl['center']
X0, X1, Y0, Y1 = -140, 45, -215, 10; S = 5.0
W, H = int((X1 - X0) * S), int((Y1 - Y0) * S)
im = Image.new('RGB', (W, H), (226, 222, 210)); d = ImageDraw.Draw(im)
P = lambda x, y: ((x - X0) * S, (Y1 - y) * S)
# existing context: town streets west, trail east, old red-area envelope
for pts, w, col in (([(-262, -60), (-128, -60)], 3.5, (170, 150, 120)), ([(-262, -180), (-128, -180)], 3.5, (170, 150, 120)),
                    ([(-228, -130), (-122, -130)], 6, (170, 150, 120)), ([(39, -150), (130, -150)], 1.4, (150, 130, 100))):
    d.line([P(*p) for p in pts], fill=col, width=max(1, int(w * S)))
d.rectangle((*P(-119, 27), *P(36, -212)), outline=(220, 60, 60), width=2)
d.ellipse((*P(cx - pl['plaza_radius'], cy + pl['plaza_radius']), *P(cx + pl['plaza_radius'], cy - pl['plaza_radius'])), fill=(205, 185, 150), outline=(120, 100, 70))
for r in pl['roads']:
    d.line([P(*p) for p in r['pts']], fill=(150, 120, 90) if r['kind'] == 'road' else (130, 105, 75), width=max(2, int(r['width'] * S)))
cols = {'hall': (120, 40, 40), 'R1': (60, 90, 150), 'R2': (70, 120, 70), 'H': (150, 120, 40)}
for s in pl['slots']:
    c = district.corners(s); d.polygon([P(*p) for p in c], outline=cols[s['ring']], fill=None, width=2)
    x, y = P(*s['pos']); d.text((x - 14, y - 5), s['arch'][:8], fill=(30, 30, 30))
    fx, fy = district.rot((0, s['rect'][2] + 0.5), s['angle']); a, b = P(s['pos'][0] + fx, s['pos'][1] + fy); d.ellipse((a - 3, b - 3, a + 3, b + 3), fill=(200, 0, 0))
for gx in range(-140, 46, 20): d.text((P(gx, Y1)[0] + 2, 2), str(gx), fill=(0, 0, 160)); d.line((*P(gx, Y1), *P(gx, Y0)), fill=(190, 200, 220))
for gy in range(-200, 11, 20): d.text((2, P(X0, gy)[1] + 2), str(gy), fill=(0, 0, 160)); d.line((*P(X0, gy), *P(X1, gy)), fill=(190, 200, 220))
im.save(sys.argv[1])
