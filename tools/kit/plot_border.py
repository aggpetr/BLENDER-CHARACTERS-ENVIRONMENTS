"""Draw the village border plan: python -I tools/kit/plot_border.py <base_topdown.png> <out.png> [px_per_m x_min y_max]  (default 3.2, -390, 160)"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import border as BD, additions as A
from PIL import Image, ImageDraw, ImageFont

seed = int(os.environ.get('BORDER_SEED', '11'))
b = BD.make(seed)
base = Image.open(sys.argv[1]).convert('RGBA')
S = float(sys.argv[3]) if len(sys.argv) > 3 else 3.2
X0 = float(sys.argv[4]) if len(sys.argv) > 4 else -390.0
Y1 = float(sys.argv[5]) if len(sys.argv) > 5 else 160.0
P = lambda x, y: ((x - X0) * S, (Y1 - y) * S)
def font(sz, bold=False):
    f = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    return ImageFont.truetype(f, sz) if os.path.exists(f) else ImageFont.load_default()
F, FB, FS, FT, FL = font(15), font(17, True), font(13), font(24, True), font(22, True)
ov = Image.new('RGBA', base.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
pts = b['points']; n = len(pts)
# the area inside the border: a faint tint
d.polygon([P(*p) for p in pts], fill=(255, 245, 210, 38))
RED = (150, 25, 25, 255)
for i in range(n):                                            # the border line with fence ticks
    a, c = pts[i], pts[(i + 1) % n]
    near = any(math.hypot(a[0] - g['pos'][0], a[1] - g['pos'][1]) < BD.STRAIGHT + 1 for g in b['gates'])
    d.line([P(*a), P(*c)], fill=(255, 150, 30, 255) if near else RED, width=7 if near else 6)
for i in range(0, n, 2):
    a, c = pts[i], pts[(i + 1) % n]; dx, dy = c[0] - a[0], c[1] - a[1]; L = math.hypot(dx, dy) or 1
    nx, ny = -dy / L * 2.2, dx / L * 2.2; m = P(*a)
    d.line([(m[0] - nx * S * 0.5, m[1] + ny * S * 0.5), (m[0] + nx * S * 0.5, m[1] - ny * S * 0.5)], fill=(255, 235, 200, 255), width=2)
for s in b['stones']:
    x, y = P(*s); d.rectangle((x - 5, y - 5, x + 5, y + 5), fill=(255, 255, 255, 255), outline=(40, 40, 40, 255), width=2)
for sg in b['side_gates']:
    x, y = P(*sg['pos']); d.ellipse((x - 9, y - 9, x + 9, y + 9), fill=(255, 255, 255, 255), outline=RED, width=4)
for g in b['gates']:                                          # the four torii gates
    x, y = P(*g['pos']); u = g['u']; hw = 3.4 * S
    ax, ay = u[0] * hw, -u[1] * hw
    d.line([(x - ax, y - ay), (x + ax, y + ay)], fill=(220, 30, 30, 255), width=9)
    for sgn in (-1, 1): d.ellipse((x + sgn * ax - 7, y + sgn * ay - 7, x + sgn * ax + 7, y + sgn * ay + 7), fill=(220, 30, 30, 255), outline=(255, 255, 255, 255), width=2)
    ox, oy = g['dir'][0] * 36, -g['dir'][1] * 36
    d.ellipse((x + ox - 20, y + oy - 20, x + ox + 20, y + oy + 20), fill=(220, 30, 30, 255), outline=(255, 255, 255, 255), width=3)
    d.text((x + ox, y + oy), g['name'][0].upper(), fill=(255, 255, 255, 255), font=FL, anchor='mm')
# what the plan keeps outside the border
for it in A.ITEMS:
    if it['name'].startswith(('Temple', 'Graveyard', 'Hill', 'Mountain', 'Hot spring', 'Charcoal', 'Ferry', 'Mill pond')):
        w, dd = it['size']; x0, y0 = P(it['c'][0] - w / 2, it['c'][1] + dd / 2); x1, y1 = P(it['c'][0] + w / 2, it['c'][1] - dd / 2)
        d.rectangle((x0, y0, x1, y1), outline=(90, 90, 90, 200), width=2)
composed = Image.alpha_composite(base, ov)
# ---- right panel: how the border meets a gate, and three border styles
LW = 900
out = Image.new('RGBA', (base.width + LW, base.height), (248, 246, 240, 255)); out.paste(composed, (0, 0))
g = ImageDraw.Draw(out); x = base.width + 24; y = 20
g.text((x, y), 'Village border and torii gates (plan)', fill=(20, 20, 20, 255), font=FT); y += 40
for t in (f"Irregular closed line, {b['length'] / 1000:.1f} km, always {BD.MARGIN:.0f} m or more outside every house, field and the canal bank.",
          "It meets four torii gates (N, S, E, W) and runs straight and square to the road for 16 m on each side of each gate; between the gates",
          "it wanders (four arcs). The river is the border on the south, so the arch bridge is the south gate. Nothing here is built yet."):
    g.text((x, y), t, fill=(70, 70, 70, 255), font=FS); y += 17
y += 12
g.text((x, y), 'A. Where the border meets a gate (plan view)', fill=(20, 20, 20, 255), font=FB); y += 28
# plan diagram: road runs up the middle, border across, 1 m = 17 px
U = 17.0; cx = x + 330; cy = y + 215
g.rectangle((x, y, x + 660, y + 400), fill=(236, 230, 214, 255), outline=(180, 170, 150, 255))
g.rectangle((cx - 2.5 * U, y, cx + 2.5 * U, y + 400), fill=(190, 160, 120, 255))                       # road 5 m
g.text((cx, y + 380), 'road 5 m', fill=(60, 40, 20, 255), font=FS, anchor='mm')
# border straight 16 m each side: fence line
g.line([(x, cy), (cx - 4.6 * U, cy)], fill=(150, 25, 25, 255), width=6); g.line([(cx + 4.6 * U, cy), (x + 660, cy)], fill=(150, 25, 25, 255), width=6)
for k in range(0, 18):
    for sgn in (-1, 1):
        px = cx + sgn * (5.2 + k * 1.1) * U
        if abs(px - cx) < 328: g.rectangle((px - 2, cy - 7, px + 2, cy + 7), fill=(255, 235, 200, 255))
# gate piers + torii pillars + bar
for sgn in (-1, 1):
    g.rectangle((cx + sgn * 4.6 * U - 8, cy - 11, cx + sgn * 4.6 * U + 8, cy + 11), fill=(120, 120, 115, 255), outline=(40, 40, 40, 255))      # stone pier
    g.ellipse((cx + sgn * 3.3 * U - 9, cy - 9, cx + sgn * 3.3 * U + 9, cy + 9), fill=(215, 35, 35, 255), outline=(255, 255, 255, 255), width=2)  # torii pillar
g.line([(cx - 3.8 * U, cy), (cx + 3.8 * U, cy)], fill=(215, 35, 35, 255), width=5)
for sgn in (-1, 1):                                                                                        # stone lanterns on the village side
    g.rectangle((cx + sgn * 3.3 * U - 6, cy - 3.6 * U - 6, cx + sgn * 3.3 * U + 6, cy - 3.6 * U + 6), fill=(190, 190, 185, 255), outline=(40, 40, 40, 255))
g.rectangle((cx - 9.5 * U, cy - 7.5 * U, cx - 5.2 * U, cy - 3.5 * U), fill=(160, 120, 80, 255), outline=(60, 40, 20, 255))                     # keeper's hut
g.text((cx - 7.35 * U, cy - 5.5 * U), 'hut', fill=(255, 255, 255, 255), font=FS, anchor='mm')
for sgn in (-1, 1): g.line([(cx + sgn * 5.0 * U, cy + 3.2 * U), (cx + sgn * 10 * U, cy + 3.2 * U)], fill=(60, 130, 190, 255), width=4)  # ditch outside
g.rectangle((cx - 5.0 * U, cy + 2.6 * U, cx + 5.0 * U, cy + 3.8 * U), fill=(150, 110, 60, 255), outline=(60, 40, 20, 255))                    # plank bridge over the ditch
g.text((cx, cy + 3.2 * U), 'plank bridge', fill=(255, 255, 255, 255), font=FS, anchor='mm')
g.text((x + 10, y + 12), 'OUTSIDE', fill=(90, 90, 90, 255), font=FS); g.text((x + 10, y + 388), 'VILLAGE', fill=(90, 90, 90, 255), font=FS)
g.text((x + 10, y + 12), '', font=FS)
g.text((cx + 5.6 * U, cy - 1.5 * U), 'stone pier', fill=(40, 40, 40, 255), font=FS, anchor='lm')
g.text((cx + 3.5 * U, cy - 3.0 * U), 'torii 6.6 m wide', fill=(160, 20, 20, 255), font=FS, anchor='lm')
g.text((cx + 6 * U, cy + 0.9 * U * 0), '', font=FS)
g.text((x + 14, cy - 18), 'border runs straight 16 m ->', fill=(150, 25, 25, 255), font=FS)
y += 416
g.text((x, y), 'B. Three ways to build the border (side views)', fill=(20, 20, 20, 255), font=FB); y += 26
def card(ox, oy, title, kind):
    g.rectangle((ox, oy, ox + 280, oy + 190), fill=(236, 240, 246, 255), outline=(180, 185, 195, 255))
    g.rectangle((ox, oy + 125, ox + 280, oy + 190), fill=(150, 120, 80, 255))
    g.text((ox + 140, oy + 14), title, fill=(20, 20, 20, 255), font=F, anchor='mm')
    if kind == 'A':       # earth bank + ditch + hedge
        g.polygon([(ox + 70, oy + 125), (ox + 100, oy + 85), (ox + 150, oy + 85), (ox + 185, oy + 125)], fill=(125, 95, 60, 255))
        for k in range(5): g.ellipse((ox + 98 + k * 11, oy + 62, ox + 120 + k * 11, oy + 90), fill=(60, 130, 55, 255))
        g.polygon([(ox + 195, oy + 125), (ox + 210, oy + 150), (ox + 245, oy + 150), (ox + 260, oy + 125)], fill=(80, 140, 200, 255))
        g.rectangle((ox + 52, oy + 98, ox + 66, oy + 125), fill=(200, 200, 195, 255), outline=(40, 40, 40, 255))
        g.text((ox + 140, oy + 160), 'bank 1 m + hedge, ditch outside', fill=(255, 255, 255, 255), font=FS, anchor='mm')
        g.text((ox + 140, oy + 177), 'boundary stones every 36 m', fill=(255, 255, 255, 255), font=FS, anchor='mm')
    elif kind == 'B':     # palisade on a stone footing
        g.rectangle((ox + 40, oy + 112, ox + 240, oy + 125), fill=(130, 130, 125, 255), outline=(40, 40, 40, 255))
        for k in range(14): g.rectangle((ox + 46 + k * 14, oy + 50, ox + 55 + k * 14, oy + 112), fill=(125, 85, 45, 255), outline=(60, 40, 20, 255))
        g.rectangle((ox + 40, oy + 62, ox + 240, oy + 68), fill=(90, 60, 30, 255)); g.rectangle((ox + 40, oy + 92, ox + 240, oy + 98), fill=(90, 60, 30, 255))
        g.text((ox + 140, oy + 160), 'board / bamboo palisade 2 m', fill=(255, 255, 255, 255), font=FS, anchor='mm')
        g.text((ox + 140, oy + 177), 'on a stone footing, corner posts', fill=(255, 255, 255, 255), font=FS, anchor='mm')
    else:                 # stones + sacred rope
        for sx in (70, 210):
            g.rectangle((ox + sx, oy + 82, ox + sx + 24, oy + 125), fill=(190, 190, 185, 255), outline=(40, 40, 40, 255))
        g.arc((ox + 82, oy + 70, ox + 222, oy + 120), 0, 180, fill=(235, 220, 170, 255), width=4)
        for k in range(5): g.rectangle((ox + 96 + k * 26, oy + 99 + (8 if k in (0, 4) else 15 if k in (1, 3) else 17) - 8, ox + 100 + k * 26, oy + 112 + (8 if k in (0, 4) else 15 if k in (1, 3) else 17) - 6), fill=(255, 255, 255, 255), outline=(120, 120, 120, 255))
        g.text((ox + 140, oy + 160), 'standing stones + shimenawa rope', fill=(255, 255, 255, 255), font=FS, anchor='mm')
        g.text((ox + 140, oy + 177), 'symbolic, no wall (invisible collision)', fill=(255, 255, 255, 255), font=FS, anchor='mm')
card(x, y, 'A  Bank + ditch + hedge', 'A'); card(x + 300, y, 'B  Palisade fence', 'B'); card(x + 600, y, 'C  Stones + rope', 'C')
y += 206
g.text((x, y), 'Recommendation', fill=(20, 20, 20, 255), font=FB); y += 24
for t in ('Mix them along the line: B (palisade) beside the houses and at the gates, A (bank, ditch, hedge) on the open fields, C on steep or wet ground, and the river',
          'on the south. The gates are the same everywhere: torii + stone piers + lanterns + keeper hut + plank bridge. In the kit I would build: torii (2 sizes), stone pier,',
          'palisade segment / post / corner, boundary stone, shimenawa segment, keeper hut. The bank, ditch and hedge are Landscape splines and vegetation in Unreal.',
          'Side gates (white circles on the map) are small torii or a stone marker with a Jizo statue.'):
    g.text((x, y), t, fill=(60, 60, 60, 255), font=FS); y += 17
out.convert('RGB').save(sys.argv[2], quality=90); print('saved', sys.argv[2], out.size)
