"""Draw the water plan over a top-down render: python -I tools/kit/plot_water.py <base_topdown.png> <out.png> [px_per_m x_min y_max]  (default 3.0, -390, 160)"""
import sys, os, json
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
W = json.load(open(os.path.join(HERE, '..', '..', 'kit', 'village', 'village_water.json')))
base = Image.open(sys.argv[1]).convert('RGBA')
S = float(sys.argv[3]) if len(sys.argv) > 3 else 3.0
X0 = float(sys.argv[4]) if len(sys.argv) > 4 else -390.0
Y1 = float(sys.argv[5]) if len(sys.argv) > 5 else 160.0
P = lambda x, y: ((x - X0) * S, (Y1 - y) * S)
ov = Image.new('RGBA', base.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
d.line([P(*p) for p in W['branch']], fill=(0, 200, 255, 255), width=max(4, int(W['width_m'] * S)))
d.line([P(*p) for p in W['link']], fill=(0, 255, 120, 255), width=max(4, int(W['width_m'] * S)))
for n, mod, x, y, rot, w in W['branch_bridges']:
    cx, cy = P(x, y); d.ellipse((cx - 9, cy - 9, cx + 9, cy + 9), outline=(255, 0, 0, 255), width=4)
Image.alpha_composite(base, ov).convert('RGB').save(sys.argv[2])
