"""Prepare the downloaded CC0 texture sets for the Edo kit.

Run with bpy (needed only to read the .exr normal maps):
    python -I tools/prepare_textures.py <repo_root> <output_dir>

For every <set>_4k.blend.zip in repo_root (Poly Haven) plus the loose Moss001 maps (ambientCG) it writes, into
<output_dir>/<set>/ : BaseColor.png, Normal_DX.png (OpenGL -> DirectX, for Unreal), Roughness.png, Height.png,
AO.png (derived from the height map, tile-safe) and ORM.png (R=AO, G=Roughness, B=Metallic=0).
The tile roof is recoloured to the village's dark grey and the stone is desaturated toward grey.
Inputs are untrusted downloads: they are only read as image data.
"""
import sys, os, io, zipfile, glob
import numpy as np
from PIL import Image, ImageFilter
import bpy

Image.MAX_IMAGE_PIXELS = None
root, out = sys.argv[-2], sys.argv[-1]

def load_any(data, name):
    if name.lower().endswith('.exr'):
        tmp = os.path.join(out, '_tmp.exr'); open(tmp, 'wb').write(data)
        im = bpy.data.images.load(tmp); im.colorspace_settings.name = 'Non-Color'
        w, h = im.size; a = np.empty(w * h * 4, dtype=np.float32); im.pixels.foreach_get(a)
        a = a.reshape(h, w, 4)[::-1, :, :3]            # Blender stores bottom-up
        bpy.data.images.remove(im); os.remove(tmp)
        return np.clip(a, 0, 1)
    im = Image.open(io.BytesIO(data)); im.load()
    if im.mode in ('I;16', 'I'):
        return np.asarray(im, dtype=np.float32)[..., None].repeat(3, -1) / 65535.0
    return np.asarray(im.convert('RGB'), dtype=np.float32) / 255.0

def save8(a, path, mode='RGB'):
    a = np.clip(a, 0, 1); a = (a * 255 + 0.5).astype(np.uint8)
    Image.fromarray(a if mode == 'RGB' else a[..., 0], mode).save(path, optimize=False)

def ao_from_height(h):
    """Cavity-style AO from a tiling height map (wraps at the edges so tiles stay seamless)."""
    pad = 160
    hp = np.pad(h, pad, mode='wrap')
    img = Image.fromarray((np.clip(hp, 0, 1) * 255).astype(np.uint8), 'L')
    ao = np.zeros_like(hp)
    for radius, weight in ((6, 0.5), (30, 0.5)):
        blur = np.asarray(img.filter(ImageFilter.GaussianBlur(radius)), dtype=np.float32) / 255.0
        ao += weight * np.clip((blur - hp / 1.0) * 4.0, 0, 1)
    ao = 1.0 - np.clip(ao, 0, 0.85)
    return ao[pad:-pad, pad:-pad]

def recolor_tile(c):
    lum = c @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
    lo, hi = np.percentile(lum, (1, 99)); n = np.clip((lum - lo) / (hi - lo + 1e-6), 0, 1)
    v = 0.06 + 0.26 * n                                   # dark kawara range
    return v[..., None] * np.array([0.92, 0.97, 1.0], dtype=np.float32)

def desaturate(c, amount):
    lum = (c @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32))[..., None]
    return lum + (c - lum) * (1 - amount)

def write_set(name, color, normal_gl, rough, height, ao=None, normal_is_dx=False):
    d = os.path.join(out, name); os.makedirs(d, exist_ok=True)
    if name == 'roof_tiles': color = recolor_tile(color)
    if name == 'stacked_stone_wall': color = desaturate(color, 0.75) * 0.9
    n = normal_gl.copy()
    if not normal_is_dx: n[..., 1] = 1.0 - n[..., 1]      # flip green: OpenGL -> DirectX
    h = height[..., 0]
    a = ao[..., 0] if ao is not None else ao_from_height(h)
    r = rough[..., 0]
    save8(color, f'{d}/BaseColor.png'); save8(n, f'{d}/Normal_DX.png'); save8(r[..., None].repeat(3, -1), f'{d}/Roughness.png')
    save8(h[..., None].repeat(3, -1), f'{d}/Height.png'); save8(a[..., None].repeat(3, -1), f'{d}/AO.png')
    orm = np.stack([a, r, np.zeros_like(r)], -1); save8(orm, f'{d}/ORM.png')
    nz = n[..., 2].mean()
    print(f'{name}: {color.shape[1]}x{color.shape[0]}  normal-z mean {nz:.2f}  AO mean {a.mean():.2f}  rough mean {r.mean():.2f}', flush=True)

os.makedirs(out, exist_ok=True)
for z in sorted(glob.glob(os.path.join(root, '*_4k.blend.zip'))):
    name = os.path.basename(z).replace('_4k.blend.zip', ''); zf = zipfile.ZipFile(z)
    pick = lambda key: next(i for i in zf.namelist() if f'_{key}_4k' in i)
    g = lambda key: load_any(zf.read(pick(key)), pick(key))
    write_set(name, g('diff'), g('nor_gl'), g('rough'), g('disp'))

m = lambda suffix: os.path.join(root, f'Moss001_4K-JPG_{suffix}.jpg')
ld = lambda suffix: load_any(open(m(suffix), 'rb').read(), m(suffix))
write_set('moss001', ld('Color'), ld('NormalDX'), ld('Roughness'), ld('Displacement'), ao=ld('AmbientOcclusion'), normal_is_dx=True)
print('done')
