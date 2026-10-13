"""Build the Edo kit texture sets.

    python -I tools/kit/make_textures.py <repo_root> <out_dir>      (needs bpy for the .exr normal maps)

Writes <out_dir>/T_Edo_<Name>/{BaseColor.jpg, Normal_DX.jpg, ORM.jpg} (ORM: R=AO, G=Roughness, B=Metallic).
Photo sets come from the CC0 downloads in the repo root (Poly Haven zips, ambientCG Moss001); Kawara, Stone,
Paper and Ceramic are generated procedurally. All sets tile seamlessly. Downloads are only read as image data.
"""
import sys, os, io, glob, zipfile
import numpy as np
from PIL import Image, ImageFilter

Image.MAX_IMAGE_PIXELS = None
ROOT, OUT = sys.argv[-2], sys.argv[-1]
LUM = np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
rng = np.random.default_rng(1820)
WANT = [w for w in os.environ.get('KIT_SETS', '').split(',') if w]
want = lambda n: not WANT or n in WANT


# ---------------------------------------------------------------- io helpers
def load_any(data, name):
    if name.lower().endswith('.exr'):
        import bpy
        tmp = os.path.join(OUT, '_tmp.exr'); open(tmp, 'wb').write(data)
        im = bpy.data.images.load(tmp); im.colorspace_settings.name = 'Non-Color'
        w, h = im.size; a = np.empty(w * h * 4, dtype=np.float32); im.pixels.foreach_get(a)
        a = a.reshape(h, w, 4)[::-1, :, :3].copy()
        bpy.data.images.remove(im); os.remove(tmp)
        return np.clip(a, 0, 1)
    im = Image.open(io.BytesIO(data)); im.load()
    if im.mode in ('I;16', 'I', 'I;16B'):
        return np.asarray(im, dtype=np.float32)[..., None].repeat(3, -1) / 65535.0
    return np.asarray(im.convert('RGB'), dtype=np.float32) / 255.0

def polyhaven(name):
    if WANT and name not in NEEDS: return dict(color=np.zeros((4,4,3),np.float32), normal_gl=np.zeros((4,4,3),np.float32), rough=np.zeros((4,4),np.float32), height=np.zeros((4,4),np.float32))
    zf = zipfile.ZipFile(os.path.join(ROOT, f'{name}_4k.blend.zip'))
    def g(key):
        f = next(i for i in zf.namelist() if f'_{key}_4k' in i)
        return load_any(zf.read(f), f)
    return dict(color=g('diff'), normal_gl=g('nor_gl'), rough=g('rough')[..., 0], height=g('disp')[..., 0])

def save_set(name, color, normal_dx, rough, ao, metal=None):
    if not want(name): return
    d = os.path.join(OUT, f'T_Edo_{name}'); os.makedirs(d, exist_ok=True)
    def s8(a, p):
        a = (np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8)
        Image.fromarray(a, 'RGB' if a.ndim == 3 else 'L').save(p, quality=95 if 'Normal' in p else 93, subsampling=0 if 'Normal' in p else 2)
    s8(color, f'{d}/BaseColor.jpg'); s8(normal_dx, f'{d}/Normal_DX.jpg')
    m = np.zeros_like(rough) if metal is None else metal
    s8(np.stack([ao, rough, m], -1), f'{d}/ORM.jpg')
    print(f'T_Edo_{name}: {color.shape[1]}x{color.shape[0]}  color mean {color.mean():.3f}  rough {rough.mean():.2f}  ao {ao.mean():.2f}', flush=True)


# ---------------------------------------------------------------- generic image ops (all wrap = tile safe)
def blur(a, r):
    """Periodic Gaussian blur (sigma r px) via FFT, so tiles stay seamless."""
    n0, n1 = a.shape
    fy = np.fft.fftfreq(n0)[:, None]; fx = np.fft.rfftfreq(n1)[None, :]
    g = np.exp(-2 * (np.pi ** 2) * (r ** 2) * (fx ** 2 + fy ** 2))
    return np.fft.irfft2(np.fft.rfft2(a) * g, s=(n0, n1)).astype(np.float32)

def periodic_noise(n, beta=2.0, aniso=(1.0, 1.0), seed=0, lo=0.0):
    """Tileable fractal noise in [0,1] via FFT filtering (1/f^beta spectrum)."""
    r = np.random.default_rng(seed)
    w = r.standard_normal((n, n)).astype(np.float32)
    fy = np.fft.fftfreq(n)[:, None] * aniso[1]; fx = np.fft.rfftfreq(n)[None, :] * aniso[0]
    f = np.sqrt(fx ** 2 + fy ** 2); f[0, 0] = 1
    filt = 1.0 / (f ** beta); filt[0, 0] = 0
    if lo: filt *= (f > lo)
    a = np.fft.irfft2(np.fft.rfft2(w) * filt, s=(n, n)).astype(np.float32)
    a = (a - a.mean()) / (a.std() + 1e-6)
    return np.clip(0.5 + a * 0.18, 0, 1)

def normal_from_height(h_m, texel_m, strength=1.0):
    """h_m: height in metres, texel_m: metres per pixel. Returns DirectX-encoded normal (green = -Y)."""
    dx = (np.roll(h_m, -1, 1) - np.roll(h_m, 1, 1)) / (2 * texel_m) * strength
    dr = (np.roll(h_m, -1, 0) - np.roll(h_m, 1, 0)) / (2 * texel_m) * strength   # +row = down the image
    n = np.stack([-dx, -dr, np.ones_like(dx)], -1)                                  # DirectX: green follows +row
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    return n * 0.5 + 0.5

def ao_from_height(h, radius_px=(6, 30), k=4.0):
    ao = np.zeros_like(h)
    for r, w in zip(radius_px, (0.5, 0.5)):
        ao += w * np.clip((blur(h, r) - h) * k, 0, 1)
    return 1.0 - np.clip(ao, 0, 0.85)

def tint(c, rgb, gain=1.0):
    return np.clip(c * np.array(rgb, dtype=np.float32) * gain, 0, 1)

def desat(c, amount):
    l = (c @ LUM)[..., None]
    return l + (c - l) * (1 - amount)

def gl_to_dx(n):
    n = n.copy(); n[..., 1] = 1.0 - n[..., 1]; return n


N2 = 2048; px2 = 1.0 / N2; N3 = 1024; px3 = 0.5 / N3
os.makedirs(OUT, exist_ok=True)
SRC = {'Timber': 'rough_wood', 'Planks': 'dark_wooden_planks', 'Plaster': 'white_stucco', 'Thatch': 'reed_roof_03', 'StoneWall': 'stacked_stone_wall', 'Kawara': 'roof_tiles'}
NEEDS = {SRC[w] for w in WANT if w in SRC}

# ---------------------------------------------------------------- photo-based sets
if want('Timber'):
    s = polyhaven('rough_wood')                        # structural timber: weathered wood stained dark brown
    c = desat(s['color'], 0.6)
    c = tint(c, (0.78, 0.58, 0.42), 0.82)
    save_set('Timber', c, gl_to_dx(s['normal_gl']), np.clip(s['rough'] * 0.9 + 0.05, 0, 1), ao_from_height(s['height']))
if want('Planks'):

    s = polyhaven('dark_wooden_planks')                # boards: wainscot, doors, decks, fences
    save_set('Planks', tint(s['color'], (1.0, 0.93, 0.86), 0.95), gl_to_dx(s['normal_gl']), s['rough'], ao_from_height(s['height']))
if want('Plaster'):

    s = polyhaven('white_stucco')                      # lime plaster, warm
    c = tint(s['color'], (1.0, 0.95, 0.85), 0.97)
    grime = periodic_noise(4096, 1.7, seed=3)
    c = c * (1.0 - 0.05 * np.clip((grime - 0.5) * 3, 0, 1))[..., None]
    save_set('Plaster', c, gl_to_dx(s['normal_gl']), np.clip(s['rough'], 0.6, 1), ao_from_height(s['height']))
if want('Thatch'):

    s = polyhaven('reed_roof_03')                      # thatch: only the straw area below the ridge band, stretched to full height
    def straw(a):
        lo = a[1400:]
        if lo.ndim == 2:
            return np.asarray(Image.fromarray(lo, 'F').resize((4096, 4096), Image.BICUBIC), dtype=np.float32)
        return np.stack([np.asarray(Image.fromarray(np.ascontiguousarray(lo[..., k]), 'F').resize((4096, 4096), Image.BICUBIC), dtype=np.float32) for k in range(3)], -1)
    save_set('Thatch', straw(s['color']), gl_to_dx(straw(s['normal_gl'])), straw(s['rough']), ao_from_height(straw(s['height'])))
if want('StoneWall'):

    s = polyhaven('stacked_stone_wall')                # dry stone walls (later stages)
    save_set('StoneWall', desat(s['color'], 0.7) * 0.92, gl_to_dx(s['normal_gl']), s['rough'], ao_from_height(s['height']))
if want('Moss'):

    mp = lambda k: os.path.join(ROOT, f'Moss001_4K-JPG_{k}.jpg')
    ml = lambda k: load_any(open(mp(k), 'rb').read(), mp(k))
    save_set('Moss', ml('Color'), ml('NormalDX'), ml('Roughness')[..., 0], ml('AmbientOcclusion')[..., 0])

# ---------------------------------------------------------------- Kawara (procedural, matched to the roof geometry)
if want('Kawara'):
    # Texture = 7 ribs x 7 courses = 1.82 m x 1.82 m (one bay). U=0 is a rib crest (geometry crest), image top = ridge side.
    N = 4096; CELLS = 7; TEX_M = 1.82; px_m = TEX_M / N
    yy, xx = np.mgrid[0:N, 0:N].astype(np.float32)
    u = xx / N * CELLS; v = yy / N * CELLS
    ci = np.floor(u).astype(np.int32) % CELLS; cj = np.floor(v).astype(np.int32) % CELLS
    fu = u - np.floor(u); fv = v - np.floor(v)                 # fv: 0 at the top of a tile (under the course above), 1 at its exposed lower edge
    r_val = rng.normal(0, 1, (CELLS, CELLS)).astype(np.float32)[cj, ci]
    r_tilt = rng.normal(0, 1, (CELLS, CELLS)).astype(np.float32)[cj, ci]
    r_rgh = rng.normal(0, 1, (CELLS, CELLS)).astype(np.float32)[cj, ci]
    r_tint = rng.normal(0, 1, (CELLS, CELLS, 3)).astype(np.float32)[cj, ci]
    ss = lambda a, b, x: np.clip((x - a) / (b - a), 0, 1) ** 2 * (3 - 2 * np.clip((x - a) / (b - a), 0, 1))
    fine = periodic_noise(N, 1.4, seed=11); mid = periodic_noise(N, 2.0, seed=12)
    h = 0.2 + 0.8 * ss(0.0, 0.93, fv)                           # each tile rises toward its exposed lower edge
    h *= 1.0 - 0.9 * ss(0.94, 1.0, fv)                          # rounded drop onto the next course
    lip = np.exp(-((fu - 0.47) / 0.018) ** 2)                   # side overlap of the S-tile, in the trough
    h += 0.12 * lip + 0.04 * r_tilt * (fu - 0.5) + 0.05 * (fine - 0.5) + 0.04 * (mid - 0.5)
    h_m = h * 0.016                                             # ~16 mm course step
    nrm = normal_from_height(h_m, px_m, 1.0)
    ao = (0.5 + 0.5 * ss(0.0, 0.10, fv)) * (1 - 0.35 * np.exp(-((fu - 0.505) / 0.012) ** 2))
    ao = np.clip(ao * (0.9 + 0.1 * ao_from_height(h)), 0, 1)
    src = polyhaven('roof_tiles')['color']                      # photo grain from the real tile scan (high-pass only)
    lum = src @ LUM; grain = lum - blur(lum, 1.6); grain = np.clip(grain / (grain.std() * 4 + 1e-6), -0.5, 0.5)
    streak = periodic_noise(N, 2.4, aniso=(1.0, 0.18), seed=21)  # vertical water streaks / grime
    grime = np.clip((streak - 0.5) * 2.2, 0, 1)
    base = np.array([0.295, 0.298, 0.305], dtype=np.float32)   # ibushi (smoked) grey, sRGB, near neutral
    col = base * (1 + 0.09 * r_val)[..., None] * (1 + 0.025 * r_tint)
    col = col * (1 + 0.10 * ss(0.86, 0.94, fv) * (1 - ss(0.94, 1.0, fv)))[..., None]   # worn lower edge
    col = col * (1 + 0.22 * grain + 0.06 * (fine - 0.5))[..., None] * (1 - 0.28 * grime)[..., None] * (0.55 + 0.45 * ao)[..., None]
    rough = np.clip(0.60 + 0.07 * r_rgh + 0.25 * grime + 0.12 * (1 - ao) + 0.05 * (fine - 0.5), 0.25, 0.95)
    save_set('Kawara', np.clip(col, 0, 1), nrm, rough, ao)
    del xx, yy, u, v, fu, fv, h, h_m, nrm, src, lum, grain, streak

# ---------------------------------------------------------------- Footing stone (granite boulder, 2K, 1 m)
if want('Stone'):
    N2 = 2048; px2 = 1.0 / N2
    big = periodic_noise(N2, 2.6, seed=31); med = periodic_noise(N2, 1.9, seed=32); fin = periodic_noise(N2, 1.1, seed=33)
    spk = periodic_noise(N2, 0.6, seed=34)
    hgt = 0.6 * big + 0.3 * med + 0.1 * fin
    col = np.array([0.46, 0.45, 0.42], dtype=np.float32) * (0.86 + 0.22 * med + 0.08 * big)[..., None]
    col = col * (1 - 0.55 * (spk > 0.74))[..., None] + 0.16 * (spk < 0.24)[..., None] + 0.05 * (fin - 0.5)[..., None]
    lichen = np.clip((periodic_noise(N2, 2.3, seed=35) - 0.62) * 4, 0, 1)[..., None]
    col = col * (1 - lichen * 0.5) + lichen * 0.5 * np.array([0.47, 0.48, 0.30], dtype=np.float32)
    save_set('Stone', np.clip(col, 0, 1), normal_from_height(hgt * 0.02, px2), np.clip(0.72 + 0.15 * (med - 0.5) + 0.1 * lichen[..., 0], 0, 1), ao_from_height(hgt))

# ---------------------------------------------------------------- Shoji paper (washi, 2K, 1 m)
if want('Paper'):
    fib = np.zeros((N2, N2), np.float32)
    for k, (ax, ay) in enumerate([(1, 0.08), (0.08, 1), (1, 0.3), (0.3, 1)]):
        fib += periodic_noise(N2, 0.9, aniso=(ax, ay), seed=40 + k)
    fib = (fib - fib.min()) / (fib.max() - fib.min())
    yel = periodic_noise(N2, 2.5, seed=45)
    col = np.array([0.91, 0.89, 0.82], dtype=np.float32) * (0.94 + 0.08 * fib)[..., None]
    col = col * (1 - 0.03 * np.clip((yel - 0.5) * 3, 0, 1))[..., None] * np.array([1.0, 0.99, 0.95], dtype=np.float32)
    save_set('Paper', np.clip(col, 0, 1), normal_from_height(fib * 0.0004, px2), np.full((N2, N2), 0.86, np.float32), np.ones((N2, N2), np.float32))

# ---------------------------------------------------------------- Glazed ceramic (jars, 1K, 0.5 m)
if want('Ceramic'):
    N3 = 1024; px3 = 0.5 / N3
    drip = periodic_noise(N3, 2.0, aniso=(1.0, 0.25), seed=51); spot = periodic_noise(N3, 1.2, seed=52)
    col = np.array([0.23, 0.14, 0.085], dtype=np.float32) * (0.8 + 0.45 * drip)[..., None]
    col = col + 0.05 * (spot > 0.75)[..., None]
    save_set('Ceramic', np.clip(col, 0, 1), normal_from_height(drip * 0.0015, px3), np.clip(0.28 + 0.2 * (spot - 0.5), 0.1, 0.6), np.ones((N3, N3), np.float32))
# ---------------------------------------------------------------- Noren cloth (indigo cotton, 2K, 1 m)
if want('Cloth'):
    yy2, xx2 = np.mgrid[0:N2, 0:N2].astype(np.float32)
    weave = 0.5 + 0.25 * np.sin(xx2 * 2 * np.pi / 4.0) * np.sin(yy2 * 2 * np.pi / 4.0)
    fade = periodic_noise(N2, 2.4, seed=61)
    col = np.array([0.10, 0.16, 0.31], dtype=np.float32) * (0.9 + 0.2 * weave)[..., None]
    col = col + (np.clip((fade - 0.55) * 2, 0, 1) * 0.08)[..., None] * np.array([1.0, 1.1, 1.3], dtype=np.float32)
    save_set('Cloth', np.clip(col, 0, 1), normal_from_height(weave * 0.0003, px2), np.full((N2, N2), 0.88, np.float32), 0.92 + 0.08 * weave)
# ---------------------------------------------------------------- Lantern paper (1K, 0.5 m): washi with bamboo rings
if want('Lantern'):
    yy3 = np.mgrid[0:N3, 0:N3][0].astype(np.float32)
    ring = np.abs(((yy3 / N3 * 0.5) / 0.03) % 1.0 - 0.5) < 0.06
    pap = periodic_noise(N3, 1.0, seed=71)
    col = np.array([0.95, 0.86, 0.66], dtype=np.float32) * (0.95 + 0.08 * pap)[..., None]
    col = col * (1 - 0.35 * ring)[..., None]
    save_set('Lantern', np.clip(col, 0, 1), normal_from_height(ring.astype(np.float32) * 0.0008, px3), np.full((N3, N3), 0.8, np.float32), np.ones((N3, N3), np.float32))
# ---------------------------------------------------------------- Iron (forged, slightly rusty, 1K, 0.5 m): ORM blue = metallic
if want('Iron'):
    n1 = periodic_noise(N3, 1.6, seed=81); n2 = periodic_noise(N3, 2.4, seed=82); hm = periodic_noise(N3, 1.0, seed=83)
    rust = np.clip((n2 - 0.58) * 4.0, 0, 1)
    col = np.array([0.17, 0.17, 0.18], dtype=np.float32) * (0.75 + 0.5 * n1)[..., None]
    col = col * (1 - rust)[..., None] + np.array([0.33, 0.15, 0.07], dtype=np.float32) * (0.7 + 0.6 * n1)[..., None] * rust[..., None]
    save_set('Iron', np.clip(col, 0, 1), normal_from_height(hm * 0.0006, px3), np.clip(0.42 + 0.35 * rust + 0.15 * (n1 - 0.5), 0.2, 0.95),
             np.clip(1.0 - 0.3 * rust, 0, 1).astype(np.float32), metal=np.clip(0.95 - 0.7 * rust, 0, 1).astype(np.float32))
# ---------------------------------------------------------------- Leaf (shrubs, pine needles, 1K, 0.5 m)
if want('Leaf'):
    l1 = periodic_noise(N3, 1.2, seed=91); l2 = periodic_noise(N3, 2.0, seed=92); l3 = periodic_noise(N3, 0.8, seed=93)
    col = np.array([0.14, 0.34, 0.075], dtype=np.float32) * (0.7 + 0.8 * l1)[..., None]
    col = col + (np.clip((l2 - 0.6) * 3, 0, 1) * 0.05)[..., None] * np.array([1.0, 0.9, 0.2], dtype=np.float32)
    save_set('Leaf', np.clip(col, 0, 1), normal_from_height(l3 * 0.004, px3), np.clip(0.6 + 0.2 * l1, 0.3, 0.9), np.clip(0.5 + 0.5 * l1, 0, 1).astype(np.float32))
# ---------------------------------------------------------------- Red cloth (stall awnings, parasol, 2K, 1 m)
if want('ClothRed'):
    yy2, xx2 = np.mgrid[0:N2, 0:N2].astype(np.float32)
    weave = 0.5 + 0.25 * np.sin(xx2 * 2 * np.pi / 4.0) * np.sin(yy2 * 2 * np.pi / 4.0)
    fade = periodic_noise(N2, 2.4, seed=101)
    col = np.array([0.46, 0.065, 0.045], dtype=np.float32) * (0.9 + 0.2 * weave)[..., None]
    col = col + (np.clip((fade - 0.55) * 2, 0, 1) * 0.07)[..., None] * np.array([1.0, 0.7, 0.5], dtype=np.float32)
    save_set('ClothRed', np.clip(col, 0, 1), normal_from_height(weave * 0.0003, px2), np.full((N2, N2), 0.88, np.float32), 0.92 + 0.08 * weave)
# ---------------------------------------------------------------- Soil (field ridges, 1K, 1 m)
if want('Soil'):
    N3 = 1024; px3 = 1.0 / N3
    c1 = periodic_noise(N3, 1.4, seed=111); c2 = periodic_noise(N3, 2.6, seed=112); cl = periodic_noise(N3, 0.9, seed=113)
    col = np.array([0.17, 0.105, 0.065], dtype=np.float32) * (0.7 + 0.7 * c1)[..., None]
    col = col + (np.clip((c2 - 0.6) * 3, 0, 1) * 0.05)[..., None]
    save_set('Soil', np.clip(col, 0, 1), normal_from_height((c1 * 0.7 + cl * 0.3) * 0.02, px3), np.clip(0.9 + 0.08 * (c2 - 0.5), 0.6, 1.0), np.clip(0.55 + 0.45 * c1, 0, 1).astype(np.float32))
# ---------------------------------------------------------------- Grain (ripe barley / rice straw, 1K, 0.5 m)
if want('Grain'):
    N3 = 1024; px3 = 0.5 / N3
    g1 = periodic_noise(N3, 1.2, aniso=(1.0, 0.2), seed=121); g2 = periodic_noise(N3, 2.0, seed=122)
    col = np.array([0.55, 0.42, 0.16], dtype=np.float32) * (0.75 + 0.5 * g1)[..., None]
    col = col + (np.clip((g2 - 0.6) * 3, 0, 1) * 0.06)[..., None] * np.array([1.0, 0.8, 0.3], dtype=np.float32)
    save_set('Grain', np.clip(col, 0, 1), normal_from_height(g1 * 0.002, px3), np.clip(0.62 + 0.2 * g2, 0.3, 0.9), np.clip(0.6 + 0.4 * g1, 0, 1).astype(np.float32))
# ---------------------------------------------------------------- Vermilion lacquer (torii pillars, 1K, 1 m) and black lacquer (kasagi)
if want('Vermilion'):
    N3 = 1024; px3 = 1.0 / N3
    gr = periodic_noise(N3, 1.4, aniso=(0.15, 1.0), seed=131); fd = periodic_noise(N3, 2.2, seed=132)
    col = np.array([0.60, 0.065, 0.035], dtype=np.float32) * (0.9 + 0.22 * gr)[..., None]
    col = col + (np.clip((fd - 0.62) * 3, 0, 1) * 0.07)[..., None] * np.array([1.0, 0.7, 0.4], dtype=np.float32)
    save_set('Vermilion', np.clip(col, 0, 1), normal_from_height(gr * 0.0015, px3), np.clip(0.34 + 0.16 * (fd - 0.5), 0.2, 0.6), np.clip(0.8 + 0.2 * gr, 0, 1).astype(np.float32))
if want('Lacquer'):
    N3 = 1024; px3 = 1.0 / N3
    gr = periodic_noise(N3, 1.4, aniso=(0.15, 1.0), seed=141)
    col = np.array([0.022, 0.021, 0.02], dtype=np.float32) * (0.85 + 0.3 * gr)[..., None]
    save_set('Lacquer', np.clip(col, 0, 1), normal_from_height(gr * 0.001, px3), np.clip(0.24 + 0.1 * (gr - 0.5), 0.12, 0.4), np.ones((N3, N3), np.float32))
print('done')
