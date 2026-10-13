"""Category props: small yard modules that give each house type its own character.

Origin: centre of the footprint on the ground (z = 0), front of the module = local -Y, metric.
One collection per category (KIT_Cat<Name>); the geometry nodes pick the module by its alphabetical index.
Weapon smith: swords and axes only.
"""
import math
from mathutils import Vector, Matrix
from kit_lib import MB

PI = math.pi


def _shift(mb, start, dx=0.0, dy=0.0, dz=0.0):
    for v in list(mb.bm.verts)[start:]:
        v.co.x += dx; v.co.y += dy; v.co.z += dz


def _n(mb):
    return len(mb.bm.verts)


def _tilt(mb, start, ang, axis='X', pivot=(0, 0, 0)):
    M = Matrix.Translation(pivot) @ Matrix.Rotation(ang, 4, axis) @ Matrix.Translation(-Vector(pivot))
    for v in list(mb.bm.verts)[start:]:
        v.co = M @ v.co


def _turn(mb, start, ang, pivot=(0, 0, 0)):
    _tilt(mb, start, ang, 'Z', pivot)


def _legs(mb, x0, x1, y0, y1, top, mat='Timber', t=0.035):
    for x in (x0 + t, x1 - t):
        for y in (y0 + t, y1 - t):
            mb.box((x - t, y - t, 0.0), (x + t, y + t, top), mat, grain=2, skip=('-z',))


def _bowl(mb, x, y, z, r=0.10, mat='Ceramic'):
    s = _n(mb)
    k = r / 0.10
    mb.lathe([(0.04 * k, 0.0), (0.07 * k, 0.012 * k), (0.10 * k, 0.07 * k), (0.10 * k, 0.078 * k), (0.092 * k, 0.078 * k), (0.062 * k, 0.025 * k), (0.0, 0.02 * k)],
             10, mat, cap_top=False)
    _shift(mb, s, x, y, z)


def _jar(mb, x, y, z, k=0.5):
    s = _n(mb)
    prof = [(0.15, 0.0), (0.25, 0.10), (0.30, 0.30), (0.28, 0.50), (0.19, 0.61), (0.175, 0.65), (0.20, 0.68)]
    mb.lathe([(r * k, h * k) for r, h in prof], 10, 'Ceramic', cap_top=False)
    mb.lathe([(0.215 * k, 0.675 * k), (0.215 * k, 0.705 * k)], 10, 'Planks', cap_top=True, smooth=False)
    _shift(mb, s, x, y, z)


def _bale(mb, x, y, z, along='x'):
    s = _n(mb)
    prof = [(0.10, -0.38), (0.19, -0.36), (0.22, -0.30), (0.225, 0.0), (0.22, 0.30), (0.19, 0.36), (0.10, 0.38)]
    mb.lathe([(r, a) for r, a in prof], 10, 'Thatch', axis='x', cap_top=True, cap_bottom=True)
    for xx in (-0.22, 0.0, 0.22):
        mb.lathe([(0.228, xx - 0.02), (0.234, xx), (0.228, xx + 0.02)], 10, 'Thatch', axis='x', cap_top=False)
    if along == 'y':
        _turn(mb, s, PI / 2)
    _shift(mb, s, x, y, z + 0.225)


def _bundle(mb, x, y, z, h=0.34, r=0.07, mat='Thatch'):
    s = _n(mb)
    mb.lathe([(0.012, 0.0), (r * 0.7, 0.05 * h / 0.34), (r, 0.12 * h / 0.34), (r * 0.8, 0.26 * h / 0.34), (0.015, h)], 6, mat, cap_top=False, smooth=False)
    _shift(mb, s, x, y, z - h)


# ======================================================================= restaurant
def rst_dining_set():
    mb = MB('SM_Edo_Rst_DiningSet')                    # low table with two benches, bowls and a teapot
    mb.box((-0.72, -0.36, 0.62), (0.72, 0.36, 0.68), 'Planks', grain=0)
    _legs(mb, -0.72, 0.72, -0.36, 0.36, 0.62)
    mb.box((-0.62, -0.30, 0.46), (0.62, 0.30, 0.49), 'Timber', grain=0)
    for sy in (-1, 1):
        y = 0.58 * sy
        mb.box((-0.72, y - 0.15, 0.40), (0.72, y + 0.15, 0.44), 'Planks', grain=0)
        _legs(mb, -0.72, 0.72, y - 0.15, y + 0.15, 0.40, t=0.03)
    for x, y in ((-0.45, -0.17), (-0.15, 0.17), (0.25, -0.17), (0.5, 0.17)):
        _bowl(mb, x, y, 0.68)
    s = _n(mb)
    mb.lathe([(0.0, 0.0), (0.075, 0.0), (0.10, 0.07), (0.09, 0.14), (0.05, 0.16), (0.0, 0.17)], 10, 'Ceramic', cap_top=False)
    _shift(mb, s, 0.0, 0.0, 0.68)
    return mb


def rst_furnace():
    mb = MB('SM_Edo_Rst_Furnace')                      # kamado: clay stove with a rice pot, wooden lid and chimney
    mb.box((-0.46, -0.40, 0.0), (0.46, 0.40, 0.62), 'Plaster', skip=('-z',))
    mb.box((-0.16, -0.405, 0.12), (0.16, -0.30, 0.42), 'Iron')                    # fire mouth
    mb.box((-0.18, -0.41, 0.10), (0.18, -0.39, 0.12), 'StoneWall')
    s = _n(mb)
    mb.lathe([(0.0, 0.62), (0.27, 0.62), (0.34, 0.68), (0.34, 0.76), (0.29, 0.80), (0.26, 0.80), (0.26, 0.64)], 14, 'Iron', cap_top=False)
    mb.lathe([(0.37, 0.80), (0.35, 0.83), (0.20, 0.96), (0.03, 1.02), (0.0, 1.06)], 14, 'Planks', cap_top=False)
    _shift(mb, s, -0.08, 0.0, 0.0)
    mb.box((0.18, 0.12, 0.62), (0.40, 0.36, 1.95), 'Plaster', skip=('-z',))        # chimney
    mb.box((0.15, 0.09, 1.95), (0.43, 0.39, 2.02), 'StoneWall')
    s = _n(mb)
    mb.lathe([(0.0, 0.0), (0.08, 0.0), (0.075, 0.18)], 8, 'Timber', cap_top=True)   # fire poker stand: stack of kindling
    _shift(mb, s, 0.0, -0.60, 0.0)
    for i in range(5):
        mb.box((-0.12 + i * 0.05, -0.74, 0.0), (-0.08 + i * 0.05, -0.46, 0.035), 'Timber', grain=1, skip=('-z',))
    return mb


def rst_stall():
    mb = MB('SM_Edo_Rst_Stall')                        # food stall: counter, stove pot, bowls, awning
    mb.box((-0.85, -0.42, 0.0), (0.85, 0.42, 0.86), 'Planks', grain=2, skip=('-z',))
    mb.box((-0.90, -0.46, 0.86), (0.90, 0.46, 0.91), 'Timber', grain=0)
    for x in (-0.85, 0.85):
        for y in (-0.42, 0.42):
            mb.box((x - 0.04, y - 0.04, 0.91), (x + 0.04, y + 0.04, 2.05), 'Timber', grain=2)
    mb.box((-0.92, -0.50, 2.05), (0.92, 0.50, 2.09), 'Timber', grain=0)
    M = Matrix.Translation((0.0, -0.05, 2.09)) @ Matrix.Rotation(-0.30, 4, 'X')
    mb.box((-0.95, -0.45, 0.0), (0.95, 0.45, 0.012), 'ClothRed', M=M, grain=0)
    s = _n(mb)
    mb.lathe([(0.0, 0.0), (0.20, 0.0), (0.24, 0.06), (0.24, 0.16), (0.20, 0.20), (0.0, 0.20)], 12, 'Iron', cap_top=False)
    _shift(mb, s, -0.40, 0.0, 0.91)
    for x in (0.05, 0.25, 0.45, 0.65):
        _bowl(mb, x, -0.1 if x < 0.3 else 0.1, 0.91)
    return mb


# ======================================================================= weapon smith (swords and axes)
def smi_forge():
    mb = MB('SM_Edo_Smi_Forge')                        # forge hearth with hood chimney and bellows
    mb.box((-0.65, -0.50, 0.0), (0.65, 0.50, 0.78), 'StoneWall', skip=('-z',))
    mb.box((-0.50, -0.38, 0.78), (0.50, 0.38, 0.84), 'Iron')
    s = _n(mb)
    for i in range(7):                                  # glowing charcoal lumps
        a = i * 0.9
        mb.lathe([(0.0, 0.0), (0.07, 0.0), (0.06, 0.07), (0.0, 0.08)], 5, 'Stone', cap_top=False, smooth=False, phase=a)
        _shift(mb, _n(mb) - 5 * 4, -0.36 + (i % 4) * 0.24, -0.18 + (i // 4) * 0.34, 0.84)
    mb.lathe([(0.62, 1.55), (0.58, 1.8), (0.36, 2.2), (0.20, 2.7), (0.17, 3.1)], 4, 'Plaster', cap_top=False, phase=PI / 4, smooth=False, want='radial')
    _shift(mb, _n(mb) - 5 * 4, 0.0, 0.18, 0.0)
    for x in (-0.58, 0.58):
        mb.box((x - 0.045, 0.40, 0.0), (x + 0.045, 0.50, 1.55), 'Timber', grain=2)
    mb.box((-0.66, -0.50, 1.52), (0.66, -0.40, 1.60), 'Timber', grain=0)
    mb.box((0.62, -0.20, 0.30), (1.22, 0.20, 0.62), 'Planks', grain=0)             # bellows (fuigo)
    mb.box((0.62, -0.18, 0.62), (1.22, 0.18, 0.66), 'Cloth', grain=0)
    s = _n(mb)
    mb.lathe([(0.03, -0.62), (0.03, 0.0)], 6, 'Iron', axis='x', cap_top=True)
    _shift(mb, s, 0.0, 0.0, 0.45)
    mb.box((1.20, -0.03, 0.40), (1.55, 0.03, 0.46), 'Timber', grain=0)
    mb.box((0.0, -0.46, 0.55), (0.45, -0.40, 0.58), 'Iron')                         # tongs hung at the front
    return mb


def smi_anvil():
    mb = MB('SM_Edo_Smi_Anvil')                        # anvil on a log stump, hammer and tongs beside
    mb.lathe([(0.27, 0.0), (0.30, 0.04), (0.28, 0.25), (0.26, 0.50), (0.0, 0.50)], 10, 'Timber', cap_top=False, smooth=True)
    mb.box((-0.13, -0.11, 0.50), (0.13, 0.11, 0.58), 'Iron')
    mb.box((-0.09, -0.07, 0.58), (0.09, 0.07, 0.68), 'Iron')
    mb.box((-0.30, -0.10, 0.68), (0.30, 0.10, 0.76), 'Iron')
    s = _n(mb)
    mb.lathe([(0.075, 0.0), (0.05, 0.12), (0.02, 0.24), (0.0, 0.30)], 8, 'Iron', axis='x', cap_top=False, phase=PI / 8)
    _shift(mb, s, 0.30, 0.0, 0.715)
    mb.box((-0.45, 0.30, 0.0), (-0.25, 0.46, 0.14), 'Timber', grain=0, skip=('-z',))  # water pail stool
    mb.box((-0.43, 0.32, 0.14), (-0.27, 0.44, 0.17), 'Iron')
    mb.box((0.28, -0.52, 0.0), (0.36, -0.36, 0.05), 'Iron')                       # hammer on the ground
    mb.box((0.15, -0.46, 0.0), (0.38, -0.42, 0.04), 'Timber')
    mb.box((0.30, -0.54, 0.0), (0.42, -0.34, 0.09), 'Iron')
    return mb


def smi_grindstone():
    mb = MB('SM_Edo_Smi_Grindstone')                   # wet grindstone for sharpening blades
    mb.box((-0.35, -0.30, 0.0), (0.35, 0.30, 0.20), 'Planks', skip=('-z',))      # water trough
    mb.box((-0.30, -0.25, 0.20), (0.30, 0.25, 0.22), 'Iron')
    for x in (-0.33, 0.33):
        mb.box((x - 0.04, -0.04, 0.20), (x + 0.04, 0.04, 0.72), 'Timber', grain=2)
    s = _n(mb)
    mb.lathe([(0.0, -0.055), (0.34, -0.055), (0.35, 0.0), (0.34, 0.055), (0.0, 0.055)], 18, 'Stone', axis='x', cap_top=False)
    _shift(mb, s, 0.0, 0.0, 0.52)
    s = _n(mb)
    mb.lathe([(0.02, -0.36), (0.02, 0.50)], 6, 'Iron', axis='x', cap_top=True, cap_bottom=True)
    _shift(mb, s, 0.0, 0.0, 0.52)
    mb.box((0.50, -0.02, 0.40), (0.56, 0.02, 0.52), 'Timber')                    # crank
    mb.box((0.50, -0.05, 0.38), (0.54, 0.05, 0.42), 'Timber')
    mb.box((-0.12, -0.50, 0.0), (0.12, -0.34, 0.07), 'StoneWall', skip=('-z',))   # whetstone on the ground
    return mb


def smi_quench_tub():
    mb = MB('SM_Edo_Smi_QuenchTub')                    # water tub for quenching blades, with a bucket ladle
    prof = [(0.38, 0.0), (0.42, 0.18), (0.44, 0.36), (0.42, 0.54), (0.38, 0.70)]
    mb.lathe(prof, 14, 'Planks', cap_top=False)
    mb.lathe([(0.37, 0.69), (0.37, 0.15), (0.0, 0.15)], 14, 'Planks', cap_top=False, want='inward')
    mb.lathe([(0.37, 0.58), (0.0, 0.58)], 14, 'Iron', cap_top=False, want=(0, 0, 1))
    for z in (0.10, 0.50):
        r = 0.425 if z < 0.3 else 0.43
        mb.lathe([(r, z), (r + 0.02, z + 0.025), (r, z + 0.05)], 14, 'Iron', cap_top=False)
    mb.box((0.46, -0.02, 0.36), (1.0, 0.02, 0.40), 'Timber', M=Matrix.Translation((0, 0, 0)), grain=0)
    s = _n(mb)
    mb.lathe([(0.0, 0.0), (0.07, 0.0), (0.085, 0.10), (0.085, 0.11)], 8, 'Planks', cap_top=False)
    _shift(mb, s, 1.0, 0.0, 0.34)
    return mb


def smi_sword_rack():
    mb = MB('SM_Edo_Smi_SwordRack')                    # katana display rack: three sheathed swords, one bare blade
    for x in (-0.55, 0.55):
        mb.box((x - 0.04, -0.04, 0.0), (x + 0.04, 0.04, 1.55), 'Timber', grain=2, skip=('-z',))
        mb.box((x - 0.06, -0.14, 0.0), (x + 0.06, 0.14, 0.05), 'Timber', grain=1)
    mb.box((-0.60, 0.04, 0.40), (0.60, 0.07, 1.50), 'Planks', grain=2)
    for i, z in enumerate((0.55, 0.92, 1.28)):
        for x in (-0.40, 0.40):
            mb.box((x - 0.03, -0.08, z - 0.03), (x + 0.03, 0.04, z + 0.03), 'Timber', grain=1)
        s = _n(mb)
        if i < 2:
            mb.box((-0.50, -0.06, z + 0.03), (0.32, -0.02, z + 0.08), 'Iron', grain=0)      # sheathed (black lacquer)
            mb.box((0.38, -0.06, z + 0.03), (0.64, -0.02, z + 0.075), 'Cloth', grain=0)    # wrapped grip
            tsuba = _n(mb)
            mb.lathe([(0.0, 0.32), (0.055, 0.32), (0.055, 0.34), (0.0, 0.34)], 10, 'Iron', axis='x', cap_top=False)
            _shift(mb, tsuba, 0.0, -0.04, z + 0.055)
        else:
            mb.box((-0.50, -0.05, z + 0.03), (0.34, -0.03, z + 0.075), 'Iron', grain=0)     # bare blade
            mb.box((0.34, -0.06, z + 0.03), (0.40, -0.02, z + 0.09), 'Iron')
            mb.box((0.40, -0.06, z + 0.03), (0.66, -0.02, z + 0.075), 'Cloth', grain=0)
    return mb


def smi_axe_rack():
    mb = MB('SM_Edo_Smi_AxeRack')                      # wall rack with felling axes and hatchets
    for x in (-0.62, 0.62):
        mb.box((x - 0.045, -0.04, 0.0), (x + 0.045, 0.04, 1.80), 'Timber', grain=2, skip=('-z',))
    mb.box((-0.66, 0.04, 0.55), (0.66, 0.08, 1.70), 'Planks', grain=2)
    mb.box((-0.66, -0.02, 0.50), (0.66, 0.06, 0.58), 'Timber', grain=0)
    mb.box((-0.66, -0.02, 1.70), (0.66, 0.06, 1.78), 'Timber', grain=0)
    for k, x in enumerate((-0.42, -0.14, 0.14, 0.42)):
        big = k % 2 == 0
        top = 1.62 if big else 1.50
        low = 0.75 if big else 0.85
        mb.box((x - 0.018, -0.07, low), (x + 0.018, -0.03, top), 'Timber', grain=2)
        hz = top - 0.22 if big else top - 0.16
        # head: eye block + flared blade (wedge made from stacked boxes)
        mb.box((x - 0.035, -0.095, hz), (x + 0.035, 0.0, hz + (0.13 if big else 0.10)), 'Iron')
        for j in range(4):
            f = j / 3.0
            w = 0.045 + 0.09 * f * (1.4 if big else 1.0)
            mb.box((x - 0.012, -0.09, hz + 0.01 + 0.03 * j - 0.04 * f), (x + 0.012, -0.045, hz + 0.05 + 0.03 * j + 0.04 * f), 'Iron', M=Matrix.Translation((w, 0, 0)))
    return mb


# ======================================================================= tea house
def tea_parasol():
    mb = MB('SM_Edo_Tea_Parasol')                      # nogasa: big red parasol over a bench
    mb.box((-0.80, -0.55, 0.40), (0.80, -0.15, 0.45), 'Planks', grain=0)
    mb.box((-0.80, -0.55, 0.455), (0.80, -0.15, 0.47), 'ClothRed', grain=0)
    _legs(mb, -0.80, 0.80, -0.55, -0.15, 0.40, t=0.03)
    s = _n(mb)
    mb.lathe([(0.34, 0.0), (0.38, 0.12), (0.30, 0.20)], 10, 'StoneWall', cap_top=True)   # base stone
    _shift(mb, s, 0.0, 0.25, 0.0)
    s = _n(mb)
    mb.lathe([(0.03, 0.1), (0.03, 2.35)], 8, 'Timber', cap_top=True)
    _shift(mb, s, 0.0, 0.25, 0.0)
    s = _n(mb)
    mb.lathe([(1.20, 1.95), (1.05, 2.12), (0.70, 2.30), (0.30, 2.42), (0.05, 2.47)], 16, 'ClothRed', cap_top=False, smooth=True, want='radial')
    mb.lathe([(1.20, 1.95), (1.14, 1.93), (0.50, 2.15), (0.05, 2.35)], 16, 'ClothRed', cap_top=False, smooth=True, want='inward')
    _shift(mb, s, 0.0, 0.25, 0.0)
    return mb


def tea_table():
    mb = MB('SM_Edo_Tea_Table')                        # low tea table, two stools, cups and a tray
    mb.box((-0.50, -0.30, 0.34), (0.50, 0.30, 0.39), 'Planks', grain=0)
    _legs(mb, -0.50, 0.50, -0.30, 0.30, 0.34, t=0.03)
    for x in (-0.28, 0.28):
        for y in (-0.52, 0.52):
            mb.lathe([(0.17, 0.0), (0.19, 0.02), (0.19, 0.30), (0.17, 0.32), (0.0, 0.32)], 10, 'Planks', cap_top=False)
            _shift(mb, _n(mb) - 5 * 10, x, y, 0.0)
    mb.box((-0.25, -0.15, 0.39), (0.05, 0.10, 0.415), 'Timber', grain=0)
    for x, y in ((-0.18, -0.05), (-0.05, 0.03), (0.28, -0.12)):
        _bowl(mb, x, y, 0.415, r=0.055)
    return mb


def tea_kettle_stove():
    mb = MB('SM_Edo_Tea_KettleStove')                  # clay stove with an iron kettle and a cup shelf
    mb.box((-0.30, -0.30, 0.0), (0.30, 0.30, 0.46), 'Plaster', skip=('-z',))
    mb.box((-0.12, -0.305, 0.08), (0.12, -0.28, 0.28), 'Iron')
    s = _n(mb)
    mb.lathe([(0.0, 0.0), (0.15, 0.0), (0.19, 0.07), (0.185, 0.16), (0.12, 0.22), (0.07, 0.24), (0.0, 0.245)], 12, 'Iron', cap_top=False)
    mb.box((0.16, -0.015, 0.14), (0.31, 0.015, 0.17), 'Iron')
    _shift(mb, s, 0.0, 0.0, 0.46)
    mb.box((-0.55, 0.20, 0.0), (-0.38, 0.38, 0.25), 'Planks', grain=2, skip=('-z',))
    for z in (0.62, 1.00):
        mb.box((0.38, 0.15, z), (0.95, 0.35, z + 0.03), 'Planks', grain=0)
    for x in (0.40, 0.93):
        mb.box((x - 0.02, 0.15, 0.62), (x + 0.02, 0.35, 1.03), 'Timber', grain=2)
    for x in (0.52, 0.66, 0.80):
        _bowl(mb, x, 0.25, 1.03, r=0.05)
    mb.box((0.40, 0.33, 0.0), (0.93, 0.38, 1.10), 'Planks', grain=2)
    return mb


# ======================================================================= shop
def shop_stand():
    mb = MB('SM_Edo_Shop_Stand')                       # market stand: counter, baskets of goods, indigo awning
    mb.box((-0.80, -0.38, 0.0), (0.80, 0.38, 0.80), 'Planks', grain=2, skip=('-z',))
    mb.box((-0.85, -0.42, 0.80), (0.85, 0.42, 0.85), 'Timber', grain=0)
    for x in (-0.82, 0.82):
        for y in (-0.40, 0.40):
            mb.box((x - 0.035, y - 0.035, 0.85), (x + 0.035, y + 0.035, 2.05), 'Timber', grain=2)
    M = Matrix.Translation((0.0, -0.02, 2.05)) @ Matrix.Rotation(-0.28, 4, 'X')
    mb.box((-0.92, -0.46, 0.0), (0.92, 0.46, 0.012), 'Cloth', M=M, grain=0)
    for x in (-0.55, -0.10, 0.35):
        s = _n(mb)
        mb.lathe([(0.17, 0.0), (0.20, 0.06), (0.22, 0.14), (0.20, 0.15), (0.0, 0.15)], 10, 'Thatch', cap_top=False)
        mb.lathe([(0.19, 0.12), (0.15, 0.22), (0.07, 0.27), (0.0, 0.28)], 8, 'Ceramic', cap_top=False)
        _shift(mb, s, x, 0.0, 0.85)
    _jar(mb, 0.65, 0.0, 0.85, k=0.5)
    return mb


def shop_goods_shelf():
    mb = MB('SM_Edo_Shop_GoodsShelf')                  # open shelf with folded cloth, boxes and jars
    for x in (-0.70, 0.70):
        mb.box((x - 0.035, -0.20, 0.0), (x + 0.035, 0.20, 1.70), 'Timber', grain=2, skip=('-z',))
    for z in (0.05, 0.55, 1.05, 1.55):
        mb.box((-0.72, -0.21, z), (0.72, 0.21, z + 0.035), 'Planks', grain=0)
    mb.box((-0.70, 0.19, 0.05), (0.70, 0.22, 1.60), 'Planks', grain=2)
    for i in range(4):                                  # folded cloth on the third shelf
        mb.box((-0.62 + i * 0.30, -0.14, 1.085), (-0.40 + i * 0.30, 0.14, 1.085 + 0.05 * (1 + i % 2)), 'Cloth' if i % 2 else 'ClothRed', grain=0)
    for x in (0.0, 0.30):
        mb.box((x - 0.12, -0.12, 1.085), (x + 0.12, 0.12, 1.23), 'Planks', grain=0)
    for x in (-0.50, -0.15, 0.20, 0.52):
        _jar(mb, x, 0.0, 0.585, k=0.38)
    for x in (-0.55, -0.2, 0.15, 0.50):
        _bowl(mb, x, 0.0, 0.085, r=0.09)
    return mb


def shop_crates():
    mb = MB('SM_Edo_Shop_Crates')                      # stacked crates, a sack and a barrel
    for (x, y, z, w) in ((-0.35, 0.0, 0.0, 0.60), (0.30, 0.02, 0.0, 0.60), (-0.05, 0.0, 0.40, 0.56)):
        mb.box((x - w / 2, y - 0.30, z), (x + w / 2, y + 0.30, z + 0.40), 'Planks', grain=0, skip=('-z',))
        for dz in (0.08, 0.20, 0.32):
            mb.box((x - w / 2 - 0.01, y - 0.31, z + dz), (x + w / 2 + 0.01, y + 0.31, z + dz + 0.03), 'Timber', grain=0)
    s = _n(mb)
    mb.lathe([(0.0, 0.0), (0.20, 0.0), (0.26, 0.15), (0.24, 0.40), (0.14, 0.55), (0.06, 0.58), (0.0, 0.56)], 10, 'Thatch', cap_top=False)
    _shift(mb, s, 0.75, 0.15, 0.0)
    s = _n(mb)
    mb.lathe([(0.245, 0.0), (0.27, 0.18), (0.278, 0.36), (0.27, 0.54), (0.245, 0.72)], 12, 'Planks', cap_top=True)
    _shift(mb, s, -0.80, 0.10, 0.0)
    return mb


# ======================================================================= storehouse (kura)
def sto_bale_stack():
    mb = MB('SM_Edo_Sto_BaleStack')                    # pyramid of rice bales on a pallet
    mb.box((-0.55, -0.50, 0.0), (0.55, 0.50, 0.08), 'Planks', grain=0)
    z0 = 0.08
    for row, n in enumerate((3, 2, 1)):
        for i in range(n):
            x = (i - (n - 1) / 2.0) * 0.50
            _bale(mb, x, -0.22, z0 + row * 0.42, 'x')
            _bale(mb, x, 0.22, z0 + row * 0.42, 'x')
    return mb


def sto_handcart():
    mb = MB('SM_Edo_Sto_Handcart')                     # two-wheeled hand cart with a load of bales
    mb.box((-0.55, -0.45, 0.36), (0.55, 0.50, 0.42), 'Planks', grain=1)
    for x in (-0.55, 0.55):
        mb.box((x - 0.03, -0.45, 0.42), (x + 0.03, 0.50, 0.50), 'Timber', grain=1)
    for x in (-0.45, 0.45):
        mb.box((x - 0.03, -1.35, 0.44), (x + 0.03, -0.45, 0.50), 'Timber', grain=1)
    mb.box((-0.48, -1.38, 0.43), (0.48, -1.32, 0.51), 'Timber', grain=0)
    for x in (-0.64, 0.64):
        s = _n(mb)
        mb.lathe([(0.0, -0.035), (0.34, -0.035), (0.36, 0.0), (0.34, 0.035), (0.0, 0.035)], 14, 'Timber', axis='x', cap_top=False)
        mb.lathe([(0.06, -0.06), (0.06, 0.06)], 8, 'Iron', axis='x', cap_top=True, cap_bottom=True)
        _shift(mb, s, x, 0.0, 0.36)
    mb.box((-0.62, -0.03, 0.34), (0.62, 0.03, 0.38), 'Iron')
    _bale(mb, -0.25, 0.0, 0.42, 'y'); _bale(mb, 0.25, 0.0, 0.42, 'y'); _bale(mb, 0.0, 0.0, 0.85, 'y')
    return mb


def sto_jar_row():
    mb = MB('SM_Edo_Sto_JarRow')                       # large storage jars and a barrel on a pallet
    mb.box((-0.95, -0.40, 0.0), (0.95, 0.40, 0.07), 'Planks', grain=0)
    for x in (-0.60, 0.0, 0.60):
        _jar(mb, x, 0.0, 0.07, k=0.95)
    s = _n(mb)
    mb.lathe([(0.245, 0.0), (0.27, 0.18), (0.278, 0.36), (0.27, 0.54), (0.245, 0.72)], 12, 'Planks', cap_top=True)
    _shift(mb, s, 0.0, 0.0, 0.0)
    _shift(mb, s, 1.25, 0.0, 0.0)
    return mb


# ======================================================================= farm
def farm_hay_stack():
    mb = MB('SM_Edo_Farm_HayStack')                    # haystack around a pole
    mb.lathe([(0.95, 0.0), (1.05, 0.30), (1.00, 0.80), (0.82, 1.35), (0.55, 1.85), (0.25, 2.25), (0.0, 2.45)], 14, 'Thatch', cap_top=False, cap_bottom=True)
    mb.lathe([(0.03, 2.30), (0.03, 2.95)], 6, 'Timber', cap_top=True)
    mb.lathe([(0.98, 0.02), (1.08, 0.32)], 14, 'Thatch', cap_top=False)
    return mb


def farm_tool_rack():
    mb = MB('SM_Edo_Farm_ToolRack')                    # hoe, rake and sickle leaning on a frame
    for x in (-0.55, 0.55):
        mb.box((x - 0.04, -0.04, 0.0), (x + 0.04, 0.04, 1.30), 'Timber', grain=2, skip=('-z',))
    mb.box((-0.60, -0.04, 1.22), (0.60, 0.04, 1.30), 'Timber', grain=0)
    mb.box((-0.60, -0.04, 0.60), (0.60, 0.04, 0.66), 'Timber', grain=0)
    for k, x in enumerate((-0.35, 0.0, 0.35)):
        s = _n(mb)
        mb.box((x - 0.015, -0.015, 0.0), (x + 0.015, 0.015, 1.65), 'Timber', grain=2, skip=('-z',))
        if k == 0:
            mb.box((x - 0.02, -0.12, 1.55), (x + 0.02, 0.02, 1.65), 'Iron')            # hoe blade
            mb.box((x - 0.07, -0.20, 1.52), (x + 0.07, -0.12, 1.62), 'Iron')
        elif k == 1:
            mb.box((x - 0.20, -0.02, 1.58), (x + 0.20, 0.02, 1.64), 'Timber')          # rake head
            for j in range(6):
                mb.box((x - 0.19 + j * 0.076, -0.01, 1.42), (x - 0.17 + j * 0.076, 0.01, 1.58), 'Iron')
        else:
            mb.box((x - 0.015, -0.015, 1.60), (x + 0.015, 0.03, 1.66), 'Iron')         # scythe
            mb.box((x - 0.30, -0.01, 1.64), (x + 0.015, 0.01, 1.68), 'Iron')
        _tilt(mb, s, 0.12, 'X', pivot=(x, 0.0, 0.0))
        _shift(mb, s, 0.0, 0.0, 0.0)
    return mb


def farm_drying_rack():
    mb = MB('SM_Edo_Farm_DryingRack')                  # hazakake: rice drying rack with hung bundles
    L = 3.0
    for x in (-L / 2, -L / 6, L / 6, L / 2):
        mb.box((x - 0.04, -0.04, 0.0), (x + 0.04, 0.04, 2.30), 'Timber', grain=2, skip=('-z',))
    for z in (0.95, 1.30, 1.65, 2.00):
        mb.box((-L / 2 - 0.1, -0.03, z), (L / 2 + 0.1, 0.03, z + 0.06), 'Timber', grain=0)
        for i in range(12):
            _bundle(mb, -L / 2 + 0.15 + i * (L - 0.3) / 11, 0.0, z, h=0.30, r=0.065)
    return mb


def farm_trough():
    mb = MB('SM_Edo_Farm_Trough')                      # wooden water trough on legs
    mb.box((-0.80, -0.28, 0.20), (0.80, 0.28, 0.26), 'Planks', grain=0)
    for y in (-0.28, 0.25):
        mb.box((-0.80, y, 0.26), (0.80, y + 0.03, 0.62), 'Planks', grain=0)
    for x in (-0.80, 0.77):
        mb.box((x, -0.28, 0.26), (x + 0.03, 0.28, 0.62), 'Planks', grain=1)
    for x in (-0.65, 0.65):
        mb.box((x - 0.05, -0.30, 0.0), (x + 0.05, 0.30, 0.22), 'Timber', grain=2, skip=('-z',))
    mb.box((-0.77, -0.25, 0.52), (0.77, 0.25, 0.525), 'Cloth', grain=0)               # water surface (dark)
    return mb


# ======================================================================= inn
def inn_hitching_post():
    mb = MB('SM_Edo_Inn_HitchingPost')                 # stone-footed hitching rail for horses, with a rope
    for x in (-0.9, 0.9):
        mb.box((x - 0.07, -0.07, 0.0), (x + 0.07, 0.07, 1.25), 'Timber', grain=2, skip=('-z',))
        mb.box((x - 0.14, -0.14, 0.0), (x + 0.14, 0.14, 0.14), 'StoneWall')
    mb.box((-0.95, -0.04, 1.00), (0.95, 0.04, 1.08), 'Timber', grain=0)
    mb.box((-0.95, -0.04, 0.60), (0.95, 0.04, 0.66), 'Timber', grain=0)
    for z in (0.95, 0.88, 0.86):
        pass
    mb.lathe([(0.015, -0.55), (0.015, 0.55)], 6, 'Thatch', axis='x', cap_top=True, cap_bottom=True)
    _shift(mb, _n(mb) - 12, 0.0, 0.0, 0.84)
    mb.box((-0.4, -0.55, 0.0), (0.4, -0.15, 0.12), 'StoneWall', skip=('-z',))          # stepping stone
    return mb


def inn_kago():
    mb = MB('SM_Edo_Inn_Kago')                         # palanquin (kago) resting on two stands
    for y in (-0.55, 0.55):
        mb.box((-0.30, y - 0.04, 0.0), (0.30, y + 0.04, 0.38), 'Timber', grain=0, skip=('-z',))
        mb.box((-0.30, y - 0.05, 0.36), (0.30, y + 0.05, 0.40), 'Timber', grain=0)
    mb.box((-0.025, -1.45, 0.94), (0.025, 1.45, 0.99), 'Timber', grain=1)             # carrying pole
    mb.box((-0.38, -0.40, 0.40), (0.38, 0.40, 0.50), 'Planks', grain=1)
    for sx in (-1, 1):
        for sy in (-1, 1):
            mb.box((sx * 0.38 - 0.02, sy * 0.40 - 0.02, 0.50), (sx * 0.38 + 0.02, sy * 0.40 + 0.02, 1.05), 'Timber', grain=2)
    mb.box((-0.40, -0.42, 1.05), (0.40, 0.42, 1.09), 'Timber', grain=0)
    mb.box((-0.36, -0.38, 0.50), (0.36, 0.38, 0.56), 'Planks', grain=0)
    mb.box((-0.36, -0.40, 0.56), (0.36, -0.37, 1.02), 'Paper')                       # front screen
    mb.box((0.36, -0.38, 0.56), (0.39, 0.38, 1.02), 'Paper')
    mb.box((-0.39, -0.38, 0.56), (-0.36, 0.38, 1.02), 'Paper')
    mb.box((-0.36, 0.37, 0.56), (0.36, 0.40, 1.02), 'Paper')
    mb.box((-0.42, -0.44, 1.09), (0.42, 0.44, 1.14), 'Thatch', grain=0)
    for sx in (-1, 1):
        mb.box((sx * 0.30 - 0.02, -0.55, 0.78), (sx * 0.30 + 0.02, 0.55, 0.82), 'Timber', grain=1)
    return mb


def inn_bath_tub():
    mb = MB('SM_Edo_Inn_BathTub')                      # goemon-buro: iron bath on a clay stove with a floating lid
    mb.box((-0.50, -0.50, 0.0), (0.50, 0.50, 0.40), 'Plaster', skip=('-z',))
    mb.box((-0.17, -0.505, 0.06), (0.17, -0.45, 0.26), 'Iron')
    s = _n(mb)
    mb.lathe([(0.0, 0.0), (0.46, 0.0), (0.52, 0.12), (0.55, 0.40), (0.56, 0.70), (0.54, 0.74), (0.50, 0.72), (0.47, 0.40), (0.0, 0.38)], 16, 'Iron', cap_top=False)
    mb.lathe([(0.0, 0.64), (0.42, 0.64), (0.43, 0.67), (0.0, 0.67)], 16, 'Planks', cap_top=False)
    _shift(mb, s, 0.0, 0.0, 0.40)
    mb.box((0.45, 0.25, 0.0), (0.95, 0.55, 0.20), 'Planks', grain=0, skip=('-z',))          # step
    mb.box((-0.60, 0.50, 0.0), (-0.40, 0.70, 0.14), 'Timber', skip=('-z',))
    return mb


# ======================================================================= clinic / hospital
def cln_herb_rack():
    mb = MB('SM_Edo_Cln_HerbRack')                     # drying frame for medicinal herbs with hung bundles and trays
    for x in (-1.0, 1.0):
        mb.box((x - 0.04, -0.20, 0.0), (x + 0.04, 0.20, 2.05), 'Timber', grain=2, skip=('-z',))
    for z in (1.15, 1.60, 2.00):
        mb.box((-1.04, -0.03, z), (1.04, 0.03, z + 0.05), 'Timber', grain=0)
        for i in range(9):
            _bundle(mb, -0.85 + i * 0.2125, 0.0, z, h=0.34, r=0.055, mat='Leaf' if i % 3 else 'Thatch')
    for y in (-0.14, 0.14):
        mb.box((-1.0, y - 0.02, 0.50), (1.0, y + 0.02, 0.55), 'Timber', grain=0)
    mb.box((-0.90, -0.14, 0.55), (0.0, 0.14, 0.60), 'Planks', grain=0)                # drying tray
    mb.box((0.10, -0.14, 0.55), (0.90, 0.14, 0.60), 'Planks', grain=0)
    mb.box((-0.88, -0.12, 0.60), (-0.02, 0.12, 0.64), 'Leaf')
    return mb


def cln_yagen():
    mb = MB('SM_Edo_Cln_Yagen')                        # yagen: iron herb-grinding wheel in a boat trough on a bench
    mb.box((-0.60, -0.30, 0.0), (0.60, 0.30, 0.50), 'Planks', grain=0, skip=('-z',))
    mb.box((-0.64, -0.34, 0.50), (0.64, 0.34, 0.55), 'Timber', grain=0)
    rings = []
    for x in (-0.50, -0.30, 0.0, 0.30, 0.50):
        w = 0.09 + 0.08 * (1 - abs(x) / 0.5)
        rings.append([(x, -w, 0.60), (x, -w * 0.5, 0.55), (x, w * 0.5, 0.55), (x, w, 0.60)])
    mb.loft(rings, 'Iron', want_out=lambda m: Vector((0, m.y, m.z - 0.70)), smooth=False)
    inner = [[(x, y * 0.82, z - 0.012 if z > 0.56 else z + 0.02) for x, y, z in r] for r in rings]
    mb.loft(inner, 'Iron', want_out=lambda m: Vector((0, -m.y, 0.70 - m.z)), smooth=False)
    s = _n(mb)
    mb.lathe([(0.0, -0.012), (0.17, -0.012), (0.19, 0.0), (0.17, 0.012), (0.0, 0.012)], 18, 'Iron', axis='y', cap_top=False)
    _shift(mb, s, 0.0, 0.0, 0.76)
    s = _n(mb)
    mb.lathe([(0.015, -0.30), (0.015, 0.30)], 6, 'Iron', axis='y', cap_top=True, cap_bottom=True)
    _shift(mb, s, 0.0, 0.0, 0.76)
    for y in (-0.30, 0.30):
        mb.box((-0.02, y - 0.02, 0.60), (0.02, y + 0.02, 0.80), 'Timber', grain=2)
        mb.box((-0.045, y - 0.03, 0.80), (0.045, y + 0.03, 0.88), 'Timber')
    for x in (-0.50, 0.50):
        mb.box((x - 0.02, -0.30, 0.55), (x + 0.02, -0.28, 0.62), 'Iron')
    return mb


def cln_stretcher():
    mb = MB('SM_Edo_Cln_Stretcher')                    # stretcher (tanka) with a blue futon, resting on two stands
    for y in (-0.80, 0.80):
        mb.box((-0.38, y - 0.05, 0.0), (0.38, y + 0.05, 0.34), 'Timber', grain=0, skip=('-z',))
    for x in (-0.33, 0.33):
        mb.box((x - 0.025, -1.25, 0.34), (x + 0.025, 1.25, 0.39), 'Timber', grain=1)
    for y in (-1.0, 1.0):
        mb.box((-0.33, y - 0.02, 0.34), (0.33, y + 0.02, 0.38), 'Timber', grain=0)
    mb.box((-0.33, -0.95, 0.38), (0.33, 0.95, 0.40), 'Planks', grain=1)
    mb.box((-0.30, -0.90, 0.40), (0.30, 0.60, 0.47), 'Cloth', grain=1)
    mb.box((-0.18, 0.62, 0.40), (0.18, 0.88, 0.52), 'Paper')                         # pillow
    return mb


def cln_decoction():
    mb = MB('SM_Edo_Cln_Decoction')                    # clay stove with a simmering medicine pot, ladle and herb jars
    mb.box((-0.34, -0.34, 0.0), (0.34, 0.34, 0.52), 'Plaster', skip=('-z',))
    mb.box((-0.12, -0.345, 0.08), (0.12, -0.32, 0.30), 'Iron')
    s = _n(mb)
    mb.lathe([(0.0, 0.0), (0.16, 0.0), (0.22, 0.08), (0.24, 0.20), (0.20, 0.32), (0.15, 0.35), (0.12, 0.34)], 12, 'Ceramic', cap_top=False)
    mb.lathe([(0.17, 0.35), (0.08, 0.40), (0.0, 0.42)], 12, 'Planks', cap_top=False)
    _shift(mb, s, 0.0, 0.0, 0.52)
    mb.box((0.22, -0.01, 0.80), (0.60, 0.01, 0.84), 'Timber')
    for i, x in enumerate((0.55, 0.78, 1.01)):
        _jar(mb, x, 0.05, 0.0, k=0.45 + 0.05 * i)
    mb.box((0.45, -0.20, 0.0), (1.12, 0.30, 0.0 + 0.02), 'Planks', grain=0)
    return mb


def cln_herb_bed():
    mb = MB('SM_Edo_Cln_HerbBed')                      # raised herb bed with shrubs
    mb.box((-1.05, -0.45, 0.0), (1.05, 0.45, 0.30), 'Planks', grain=0, skip=('-z',))
    mb.box((-0.98, -0.38, 0.28), (0.98, 0.38, 0.31), 'Stone')                           # soil
    for i, x in enumerate((-0.75, -0.38, 0.0, 0.38, 0.75)):
        for y in (-0.15, 0.17):
            r = 0.17 + 0.03 * ((i + (y > 0)) % 2)
            s = _n(mb)
            mb.lathe([(0.02, 0.0), (r * 0.8, 0.08), (r, 0.18), (r * 0.7, 0.30), (0.04, 0.36)], 8, 'Leaf', cap_top=False, smooth=True)
            _shift(mb, s, x + 0.07 * (y > 0), y, 0.31)
    return mb


# ======================================================================= dwelling
def home_laundry():
    mb = MB('SM_Edo_Home_Laundry')                     # laundry pole with hanging cloths
    for x in (-1.1, 1.1):
        mb.box((x - 0.04, -0.04, 0.0), (x + 0.04, 0.04, 1.95), 'Timber', grain=2, skip=('-z',))
        mb.box((x - 0.12, -0.12, 0.0), (x + 0.12, 0.12, 0.10), 'StoneWall')
    mb.box((-1.15, -0.025, 1.82), (1.15, 0.025, 1.87), 'Timber', grain=0)
    for x0, x1, h, m in ((-0.95, -0.45, 1.00, 'Cloth'), (-0.35, 0.15, 0.80, 'ClothRed'), (0.30, 0.85, 1.15, 'Cloth')):
        mb.box((x0, -0.012, 1.82 - h), (x1, 0.012, 1.82), m, grain=2)
    return mb


def home_stone_basin():
    mb = MB('SM_Edo_Home_StoneBasin')                  # tsukubai: stone water basin with a bamboo spout and gravel ring
    mb.lathe([(0.45, 0.0), (0.45, 0.04)], 16, 'Stone', cap_top=False)
    mb.lathe([(0.45, 0.04), (0.0, 0.04)], 16, 'Stone', cap_top=False, want=(0, 0, 1))
    mb.lathe([(0.28, 0.04), (0.30, 0.20), (0.24, 0.40), (0.20, 0.42)], 12, 'StoneWall', cap_top=False)
    mb.lathe([(0.20, 0.42), (0.17, 0.38), (0.0, 0.36)], 12, 'StoneWall', cap_top=False, want=(0, 0, 1))
    s = _n(mb)
    mb.lathe([(0.035, 0.0), (0.035, 0.50)], 6, 'Timber', axis='x', cap_top=True, cap_bottom=True)
    _shift(mb, s, -0.30, 0.0, 0.50)
    mb.box((-0.35, -0.03, 0.0), (-0.29, 0.03, 0.50), 'Timber', grain=2)
    return mb


def home_garden():
    mb = MB('SM_Edo_Home_Garden')                      # small garden: a pine-like tree, rocks and a stone lantern base
    mb.lathe([(0.06, 0.0), (0.05, 0.8), (0.04, 1.3)], 7, 'Timber', cap_top=True)
    for z, r, h in ((0.65, 0.55, 0.30), (1.00, 0.45, 0.28), (1.32, 0.32, 0.30)):
        s = _n(mb)
        mb.lathe([(0.04, 0.0), (r, 0.04), (r * 0.9, 0.12), (r * 0.5, h), (0.0, h + 0.04)], 9, 'Leaf', cap_top=False, smooth=True)
        _shift(mb, s, 0.05 * math.sin(z * 9), 0.05 * math.cos(z * 9), z)
    for x, y, r, h in ((0.75, 0.15, 0.22, 0.20), (0.95, -0.12, 0.15, 0.14), (-0.70, 0.05, 0.20, 0.18)):
        s = _n(mb)
        mb.lathe([(0.0, 0.0), (r, 0.0), (r * 1.1, h * 0.5), (r * 0.7, h), (0.0, h * 1.05)], 8, 'StoneWall', cap_top=False, smooth=False)
        _shift(mb, s, x, y, 0.0)
    mb.lathe([(0.0, 0.0), (0.0, 0.0)], 4, 'Stone', cap_top=False)
    return mb


# ======================================================================= registry
def build_cat():
    return {
        'KIT_CatRestaurant': [rst_dining_set(), rst_furnace(), rst_stall()],
        'KIT_CatSmith': [smi_anvil(), smi_axe_rack(), smi_forge(), smi_grindstone(), smi_quench_tub(), smi_sword_rack()],
        'KIT_CatTea': [tea_kettle_stove(), tea_parasol(), tea_table()],
        'KIT_CatShop': [shop_crates(), shop_goods_shelf(), shop_stand()],
        'KIT_CatStore': [sto_bale_stack(), sto_handcart(), sto_jar_row()],
        'KIT_CatFarm': [farm_drying_rack(), farm_hay_stack(), farm_tool_rack(), farm_trough()],
        'KIT_CatInn': [inn_bath_tub(), inn_hitching_post(), inn_kago()],
        'KIT_CatClinic': [cln_decoction(), cln_herb_bed(), cln_herb_rack(), cln_stretcher(), cln_yagen()],
        'KIT_CatHome': [home_garden(), home_laundry(), home_stone_basin()],
    }


# category id -> (collection, [(module name, x anchor, dx, y anchor, dy, rot, side_only)])
#   x anchor: L (-half width), R (+half width), C (centre), D (door x); y anchor: F (front wall), B (back wall), M (middle)
#   rot: 0 = module front to -Y (the street), pi = to the back, -pi/2 = to -X, pi/2 = to +X
CATS = {
    1: ('KIT_CatRestaurant', 'Rst_DiningSet Rst_Furnace Rst_Stall'),
    2: ('KIT_CatSmith', 'Smi_Anvil Smi_AxeRack Smi_Forge Smi_Grindstone Smi_QuenchTub Smi_SwordRack'),
    3: ('KIT_CatTea', 'Tea_KettleStove Tea_Parasol Tea_Table'),
    4: ('KIT_CatShop', 'Shop_Crates Shop_GoodsShelf Shop_Stand'),
    5: ('KIT_CatStore', 'Sto_BaleStack Sto_Handcart Sto_JarRow'),
    6: ('KIT_CatFarm', 'Farm_DryingRack Farm_HayStack Farm_ToolRack Farm_Trough'),
    7: ('KIT_CatInn', 'Inn_BathTub Inn_HitchingPost Inn_Kago'),
    8: ('KIT_CatClinic', 'Cln_Decoction Cln_HerbBed Cln_HerbRack Cln_Stretcher Cln_Yagen'),
    9: ('KIT_CatHome', 'Home_Garden Home_Laundry Home_StoneBasin'),
}
NAMES = {1: 'restaurant', 2: 'weapon smith', 3: 'tea house', 4: 'shop', 5: 'storehouse', 6: 'farm', 7: 'inn', 8: 'clinic / hospital', 9: 'home'}

FRONT, BACK = -1.75, 1.05        # distance from the front wall (outwards) / from the back wall
PLACE = {
    1: [('Rst_DiningSet', 'L', 1.40, 'F', FRONT - 0.2, 0.0, 0), ('Rst_DiningSet', 'R', -1.40, 'F', FRONT - 0.2, 0.0, 0),
        ('Rst_Furnace', 'L', 1.1, 'B', BACK, PI, 0), ('Rst_Furnace', 'R', -1.1, 'B', BACK, PI, 0), ('Rst_Stall', 'L', -1.15, 'M', 0.0, -PI / 2, 1)],
    2: [('Smi_SwordRack', 'D', -1.45, 'F', FRONT + 0.35, 0.0, 0), ('Smi_AxeRack', 'D', 1.45, 'F', FRONT + 0.35, 0.0, 0),
        ('Smi_Forge', 'L', 1.0, 'F', FRONT - 0.8, 0.0, 0), ('Smi_Anvil', 'L', 2.6, 'F', FRONT - 0.8, 0.0, 0),
        ('Smi_Grindstone', 'R', -1.0, 'F', FRONT - 0.8, 0.0, 0), ('Smi_QuenchTub', 'R', -2.4, 'F', FRONT - 0.8, 0.0, 0)],
    3: [('Tea_Parasol', 'R', -1.4, 'F', FRONT + 0.1, 0.0, 0), ('Tea_Table', 'L', 1.1, 'F', FRONT, 0.0, 0), ('Tea_KettleStove', 'C', 0.0, 'B', BACK, PI, 0)],
    4: [('Shop_Stand', 'L', 1.15, 'F', FRONT + 0.1, 0.0, 0), ('Shop_GoodsShelf', 'R', -1.05, 'F', FRONT + 1.25, 0.0, 0),
        ('Shop_Crates', 'C', 0.0, 'B', BACK, PI, 0)],
    5: [('Sto_BaleStack', 'L', 0.3, 'F', FRONT, 0.0, 0), ('Sto_Handcart', 'R', -0.3, 'F', FRONT - 0.2, PI, 0), ('Sto_JarRow', 'C', 0.0, 'B', BACK, PI, 0)],
    6: [('Farm_ToolRack', 'L', 1.0, 'F', FRONT + 0.2, 0.0, 0), ('Farm_Trough', 'R', -1.0, 'F', FRONT + 0.1, 0.0, 0),
        ('Farm_DryingRack', 'C', 0.0, 'B', BACK + 0.2, PI, 0), ('Farm_HayStack', 'R', 1.5, 'M', 0.0, 0.0, 1)],
    7: [('Inn_HitchingPost', 'L', 1.9, 'F', FRONT - 0.3, 0.0, 0), ('Inn_Kago', 'R', -2.0, 'F', FRONT - 0.5, PI / 2, 0),
        ('Inn_BathTub', 'R', -1.4, 'B', BACK + 0.2, PI, 0)],
    8: [('Cln_HerbRack', 'L', 1.5, 'F', FRONT + 0.1, 0.0, 0), ('Cln_Yagen', 'R', -1.3, 'F', FRONT, 0.0, 0), ('Cln_Stretcher', 'R', -2.6, 'F', FRONT - 0.2, PI / 2, 0),
        ('Cln_Decoction', 'L', 1.2, 'B', BACK, PI, 0), ('Cln_HerbBed', 'R', -1.6, 'B', BACK + 0.2, PI, 0)],
    9: [('Home_StoneBasin', 'L', 0.9, 'F', FRONT + 0.4, 0.0, 0), ('Home_Garden', 'R', -1.0, 'F', FRONT + 0.3, 0.0, 0), ('Home_Laundry', 'C', 0.0, 'B', BACK, PI, 0)],
}
