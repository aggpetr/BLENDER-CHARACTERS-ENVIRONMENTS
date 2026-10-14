"""Draw the proposed additions (tools/kit/additions.py) over a top-down render.

    python -I tools/kit/plot_additions.py <base_topdown.png> <out.png> [px_per_m x_min y_max]     (default 3.2, -335, 135: render_topdown.py -335 235 -385 135 3.2)
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import additions as A
from PIL import Image, ImageDraw, ImageFont

base = Image.open(sys.argv[1]).convert('RGBA')
S = float(sys.argv[3]) if len(sys.argv) > 3 else 3.2
X0 = float(sys.argv[4]) if len(sys.argv) > 4 else -335.0
Y1 = float(sys.argv[5]) if len(sys.argv) > 5 else 135.0
P = lambda x, y: ((x - X0) * S, (Y1 - y) * S)
def font(sz, bold=False):
    for f in ('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',):
        if os.path.exists(f): return ImageFont.truetype(f, sz)
    return ImageFont.load_default()
F, FB, FS, FT = font(15), font(17, True), font(13), font(24, True)
COL = dict(landmark=(200, 40, 40), civic=(40, 90, 200), work=(230, 130, 20), water=(20, 150, 190), trail=(120, 80, 160), farm=(60, 150, 60))
ov = Image.new('RGBA', base.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov)

for t in A.TERRACES:                                               # terraces: green hatched polygons
    poly = [P(*p) for p in t['poly']]
    d.polygon(poly, fill=(60, 150, 60, 70), outline=(40, 120, 40, 230))
    xs = [p[0] for p in poly]; ys = [p[1] for p in poly]
    for k in range(6):
        y = min(ys) + (k + 0.5) * (max(ys) - min(ys)) / 6
        d.line([(min(xs) + 6, y), (max(xs) - 6, y)], fill=(40, 120, 40, 200), width=2)
    cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
    d.ellipse((cx - 13, cy - 13, cx + 13, cy + 13), fill=(40, 120, 40, 255), outline=(255, 255, 255, 255), width=2)
    d.text((cx, cy), str(t['id']), fill=(255, 255, 255, 255), font=FB, anchor='mm')

def dashed(pts, col, width=4, dash=14, gap=9):
    for a, b in zip(pts[:-1], pts[1:]):
        (x0, y0), (x1, y1) = P(*a), P(*b); L = math.hypot(x1 - x0, y1 - y0)
        n = max(1, int(L // (dash + gap)))
        for k in range(n + 1):
            s0 = k * (dash + gap) / L
            if s0 >= 1: break
            s1 = min(1.0, s0 + dash / L)
            d.line([(x0 + (x1 - x0) * s0, y0 + (y1 - y0) * s0), (x0 + (x1 - x0) * s1, y0 + (y1 - y0) * s1)], fill=col, width=width)
for st in A.STREETS: dashed(st['pts'], (200, 30, 160, 255))

for it in A.ITEMS:                                                 # footprints
    w, dd = it['size']; c = it['c']; col = COL[it['group']]
    x0, y0 = P(c[0] - w / 2, c[1] + dd / 2); x1, y1 = P(c[0] + w / 2, c[1] - dd / 2)
    d.rectangle((x0, y0, x1, y1), fill=col + (95,), outline=col + (255,), width=3)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    d.ellipse((cx - 14, cy - 14, cx + 14, cy + 14), fill=col + (255,), outline=(255, 255, 255, 255), width=2)
    d.text((cx, cy), str(it['id']), fill=(255, 255, 255, 255), font=FB, anchor='mm')

for name, pts in A.FURNITURE['lanterns']:                          # street lanterns every 30 m
    for a, b in zip(pts[:-1], pts[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        for k in range(int(L // 30) + 1):
            t = k * 30 / L
            x, y = P(a[0] + (b[0] - a[0]) * t + 3.2, a[1] + (b[1] - a[1]) * t)
            d.ellipse((x - 5, y - 5, x + 5, y + 5), fill=(255, 215, 40, 255), outline=(120, 90, 0, 255))
for x, y in A.FURNITURE['jizo']:
    px, py = P(x, y); d.rectangle((px - 6, py - 6, px + 6, py + 6), fill=(190, 40, 40, 255), outline=(255, 255, 255, 255))
for x, y in A.FURNITURE['footbridges']:
    px, py = P(x, y); d.rectangle((px - 11, py - 4, px + 11, py + 4), fill=(110, 70, 30, 255), outline=(255, 255, 255, 255))
for x, y in A.FURNITURE['washing_steps']:
    px, py = P(x, y); d.polygon([(px, py - 7), (px - 7, py + 6), (px + 7, py + 6)], fill=(120, 200, 240, 255), outline=(20, 90, 140, 255))
for x, y in A.FURNITURE['field_sheds']:
    px, py = P(x, y); d.rectangle((px - 6, py - 6, px + 6, py + 6), fill=(60, 150, 60, 255), outline=(255, 255, 255, 255))

# short labels next to the footprints
for it in A.ITEMS:
    w, dd = it['size']; short = it['name'].split(' (')[0].split(' +')[0]; tw = d.textlength(short, font=FS)
    side = {'Sake brewery (large kura, cedar ball)': 'left', 'Indigo dye works + cloth poles': 'down'}.get(it['name'], 'right')
    if side == 'right': x, y = P(it['c'][0] + w / 2 + 1.5, it['c'][1]); x0 = x + 2
    elif side == 'left': x, y = P(it['c'][0] - w / 2 - 1.5, it['c'][1]); x0 = x - tw - 12
    elif side == 'up': x, y = P(it['c'][0], it['c'][1] + dd / 2 + 4); x0 = x - tw / 2 - 5
    else: x, y = P(it['c'][0], it['c'][1] - dd / 2 - 4); x0 = x - tw / 2 - 5
    d.rectangle((x0, y - 9, x0 + tw + 8, y + 9), fill=(255, 255, 255, 215))
    d.text((x0 + 4, y), short, fill=(20, 20, 20, 255), font=FS, anchor='lm')

composed = Image.alpha_composite(base, ov)
# legend panel
LW = 800
out = Image.new('RGBA', (base.width + LW, base.height), (248, 246, 240, 255)); out.paste(composed, (0, 0))
g = ImageDraw.Draw(out); x = base.width + 24; y = 22
g.text((x, y), 'Proposed additions (planning map)', fill=(20, 20, 20, 255), font=FT); y += 44
g.text((x, y), 'Nothing here is built yet. Footprints are checked against all houses,', fill=(70, 70, 70, 255), font=FS); y += 17
g.text((x, y), 'streets, fields, paddies and the canal bank. North is up.', fill=(70, 70, 70, 255), font=FS); y += 30
def section(title, area):
    global y
    g.text((x, y), title, fill=(20, 20, 20, 255), font=FB); y += 28
    for it in [i for i in A.ITEMS if i['area'] == area]:
        col = COL[it['group']]
        g.ellipse((x, y - 2, x + 22, y + 20), fill=col + (255,)); g.text((x + 11, y + 9), str(it['id']), fill=(255, 255, 255, 255), font=FS, anchor='mm')
        g.text((x + 32, y), it['name'], fill=(20, 20, 20, 255), font=F)
        g.text((x + 32, y + 18), it['note'], fill=(90, 90, 90, 255), font=FS); y += 42
    y += 6
section('Inside the village', 'in')
section('Outside the village', 'out')
for t in A.TERRACES:
    g.ellipse((x, y - 2, x + 22, y + 20), fill=(40, 120, 40, 255)); g.text((x + 11, y + 9), str(t['id']), fill=(255, 255, 255, 255), font=FS, anchor='mm')
    g.text((x + 32, y + 2), t['name'], fill=(20, 20, 20, 255), font=F); y += 30
y += 8
g.text((x, y), 'Symbols', fill=(20, 20, 20, 255), font=FB); y += 28
keys = [('ellipse', (255, 215, 40), 'street lanterns every 30 m on the main streets'), ('rect', (190, 40, 40), 'roadside Jizo shrines / milestones at the street ends'),
        ('rect', (110, 70, 30), 'footbridges over the canal'), ('tri', (120, 200, 240), 'washing steps (kawato) down to the canal'), ('rect', (60, 150, 60), 'field sheds + scarecrows'),
        ('dash', (200, 30, 160), 'new streets and paths the additions need')]
for kind, col, text in keys:
    if kind == 'ellipse': g.ellipse((x + 2, y + 2, x + 16, y + 16), fill=col)
    elif kind == 'rect': g.rectangle((x + 2, y + 2, x + 16, y + 16), fill=col)
    elif kind == 'tri': g.polygon([(x + 9, y + 1), (x + 1, y + 16), (x + 17, y + 16)], fill=col)
    else: g.line([(x, y + 9), (x + 18, y + 9)], fill=col, width=4)
    g.text((x + 30, y), text, fill=(20, 20, 20, 255), font=F); y += 24
y += 8
g.text((x, y), 'Also on the list (not drawn)', fill=(20, 20, 20, 255), font=FB); y += 26
for n in A.NOTES_OUT:
    g.text((x, y), '- ' + n, fill=(60, 60, 60, 255), font=FS); y += 18
out.convert('RGB').save(sys.argv[2], quality=92)
print('saved', sys.argv[2], out.size)
