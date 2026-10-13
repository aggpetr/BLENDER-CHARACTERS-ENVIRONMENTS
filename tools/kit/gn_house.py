"""Builds the GN_EdoKitHouse geometry-nodes group: a house assembled from the kit modules.

Inputs: Ground (object the house stands on), Bays X/Y, Floors, Roof, Engawa, Fence, Props, Seed, Realize.
Same layout rules as the original generator where measured: 1.82 m bays centred on the object origin, floor 1.30 m
above the highest ground point under the post grid, footings and stilts on the terrain, roof on the top storey.
"""
import bpy, math
from kit_lib import B, STOREY, FLOOR_ABOVE_GROUND, MAX_DEPTH

PI = math.pi


def _ok(s):
    return getattr(s, 'enabled', True) and not getattr(s, 'is_unavailable', False)


class GB:
    def __init__(self, tree):
        self.t = tree; self.N = tree.nodes; self.L = tree.links; self._x = 0

    def node(self, idn, **props):
        n = self.N.new(idn)
        for k, v in props.items():
            setattr(n, k, v)
        n.location = (self._x * 40 % 4000, -(self._x // 100) * 300); self._x += 1
        return n

    @staticmethod
    def I(n, key):
        ins = [s for s in n.inputs if _ok(s)]
        return ins[key] if isinstance(key, int) else next(s for s in ins if s.name == key)

    @staticmethod
    def O(n, key=0):
        outs = [s for s in n.outputs if _ok(s)]
        return outs[key] if isinstance(key, int) else next(s for s in outs if s.name == key)

    def put(self, n, key, val):
        s = self.I(n, key)
        if isinstance(val, bpy.types.NodeSocket):
            self.L.new(val, s)
        elif val is not None:
            s.default_value = val

    # ---- math
    def m(self, op, a, b=0.0, c=0.0):
        n = self.node('ShaderNodeMath', operation=op)
        n_in = len([x for x in n.inputs if _ok(x)])
        self.put(n, 0, a)
        if n_in > 1: self.put(n, 1, b)
        if n_in > 2: self.put(n, 2, c)
        return n.outputs[0]

    def add(self, a, b): return self.m('ADD', a, b)
    def sub(self, a, b): return self.m('SUBTRACT', a, b)
    def mul(self, a, b): return self.m('MULTIPLY', a, b)

    def toint(self, a, mode='ROUND'):
        n = self.node('FunctionNodeFloatToInt', rounding_mode=mode); self.put(n, 0, a); return n.outputs[0]

    def cmp(self, op, a, b, eps=0.001):
        n = self.node('FunctionNodeCompare', data_type='FLOAT', operation=op)
        self.put(n, 'A', a); self.put(n, 'B', b)
        if op in ('EQUAL', 'NOT_EQUAL'):
            self.put(n, 'Epsilon', eps)
        return self.O(n, 'Result')

    def sw(self, typ, cond, f, t):
        n = self.node('GeometryNodeSwitch', input_type=typ)
        self.put(n, 'Switch', cond); self.put(n, 'False', f); self.put(n, 'True', t)
        return self.O(n, 'Output')

    def vec(self, x=0.0, y=0.0, z=0.0):
        n = self.node('ShaderNodeCombineXYZ')
        self.put(n, 'X', x); self.put(n, 'Y', y); self.put(n, 'Z', z)
        return n.outputs[0]

    def pos(self):
        n = self.node('ShaderNodeSeparateXYZ'); self.L.new(self.node('GeometryNodeInputPosition').outputs[0], n.inputs[0])
        return n.outputs['X'], n.outputs['Y'], n.outputs['Z']

    def index(self):
        return self.node('GeometryNodeInputIndex').outputs[0]

    def rnd(self, typ, a, b, seed, seed_add=0):
        n = self.node('FunctionNodeRandomValue', data_type=typ)
        if typ == 'BOOLEAN':
            self.put(n, 'Probability', a)
        else:
            self.put(n, 'Min', a); self.put(n, 'Max', b)
        self.put(n, 'ID', self.index())
        self.put(n, 'Seed', self.add(seed, seed_add) if seed_add else seed)
        return self.O(n, 'Value')

    # ---- geometry
    def line(self, count, start, offset):
        n = self.node('GeometryNodeMeshLine', mode='OFFSET')
        self.put(n, 'Count', count); self.put(n, 'Start Location', start); self.put(n, 'Offset', offset)
        p = self.node('GeometryNodeMeshToPoints'); self.L.new(n.outputs[0], self.I(p, 'Mesh'))
        return p.outputs[0]

    def grid(self, vx, vy, sx, sy):
        n = self.node('GeometryNodeMeshGrid')
        self.put(n, 'Size X', sx); self.put(n, 'Size Y', sy); self.put(n, 'Vertices X', vx); self.put(n, 'Vertices Y', vy)
        p = self.node('GeometryNodeMeshToPoints'); self.L.new(n.outputs[0], self.I(p, 'Mesh'))
        return p.outputs[0]

    def point(self, position):
        n = self.node('GeometryNodePoints'); self.put(n, 'Count', 1); self.put(n, 'Position', position)
        return n.outputs[0]

    def set_pos(self, geo, position=None, offset=None, selection=None):
        n = self.node('GeometryNodeSetPosition')
        self.L.new(geo, self.I(n, 'Geometry'))
        if position is not None: self.put(n, 'Position', position)
        if offset is not None: self.put(n, 'Offset', offset)
        if selection is not None: self.put(n, 'Selection', selection)
        return n.outputs[0]

    def set_z(self, geo, z):
        x, y, _ = self.pos()
        return self.set_pos(geo, position=self.vec(x, y, z))

    def delete(self, geo, sel):
        n = self.node('GeometryNodeDeleteGeometry', domain='POINT')
        self.L.new(geo, self.I(n, 'Geometry')); self.put(n, 'Selection', sel)
        return n.outputs[0]

    def stat_max(self, geo, field):
        n = self.node('GeometryNodeAttributeStatistic', data_type='FLOAT', domain='POINT')
        self.L.new(geo, self.I(n, 'Geometry')); self.put(n, 'Attribute', field)
        return self.O(n, 'Max')

    def coll(self, name):
        n = self.node('GeometryNodeCollectionInfo', transform_space='ORIGINAL')
        self.I(n, 'Collection').default_value = bpy.data.collections[name]
        self.put(n, 'Separate Children', True); self.put(n, 'Reset Children', True)
        return n.outputs[0]

    def inst(self, points, collection, index=0, rot_z=0.0, selection=None, instance_geo=None):
        n = self.node('GeometryNodeInstanceOnPoints')
        self.L.new(points, self.I(n, 'Points'))
        self.L.new(instance_geo if instance_geo is not None else self.coll(collection), self.I(n, 'Instance'))
        self.put(n, 'Pick Instance', True); self.put(n, 'Instance Index', index)
        e = self.node('FunctionNodeEulerToRotation'); self.put(e, 'Euler', self.vec(0.0, 0.0, rot_z))
        self.L.new(e.outputs[0], self.I(n, 'Rotation'))
        if selection is not None: self.put(n, 'Selection', selection)
        return n.outputs[0]

    def join(self, *geos):
        n = self.node('GeometryNodeJoinGeometry')
        for g in geos:
            self.L.new(g, n.inputs[0])
        return n.outputs[0]

    def transform_rot(self, geo, angle):
        n = self.node('GeometryNodeTransform'); self.L.new(geo, self.I(n, 'Geometry'))
        e = self.node('FunctionNodeEulerToRotation'); self.put(e, 'Euler', self.vec(0.0, 0.0, angle))
        self.L.new(e.outputs[0], self.I(n, 'Rotation'))
        return n.outputs[0]


def build():
    old = bpy.data.node_groups.get('GN_EdoKitHouse')
    if old: bpy.data.node_groups.remove(old)
    t = bpy.data.node_groups.new('GN_EdoKitHouse', 'GeometryNodeTree')
    t.is_modifier = True
    it = t.interface
    it.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    def sock(name, typ, default, lo=None, hi=None, desc=''):
        s = it.new_socket(name, in_out='INPUT', socket_type=typ)
        if default is not None: s.default_value = default
        if lo is not None: s.min_value = lo
        if hi is not None: s.max_value = hi
        s.description = desc
        return s
    sock('Ground', 'NodeSocketObject', None, desc='Terrain the house stands on (floor = highest ground under the posts + 1.30 m)')
    sock('Bays X', 'NodeSocketInt', 4, 1, 9, 'Bays along X (1 bay = 1.82 m)')
    sock('Bays Y', 'NodeSocketInt', 3, 1, MAX_DEPTH, 'Bays along Y')
    sock('Floors', 'NodeSocketInt', 1, 1, 2, 'Storeys (2 adds the pent roof ring between the floors)')
    sock('Roof', 'NodeSocketInt', 1, 0, 3, '0 none, 1 tile hip, 2 thatched gable, 3 tile hip')
    sock('Engawa', 'NodeSocketBool', False, desc='Veranda with railing and steps on the front (-Y) side')
    sock('Balcony', 'NodeSocketBool', False, desc='Upper-floor balcony on the front (needs Floors 2)')
    sock('Shopfront', 'NodeSocketBool', False, desc='Noren curtain over the door and a hanging sign')
    sock('Lanterns', 'NodeSocketBool', False, desc='Paper lanterns either side of the door')
    sock('Fence', 'NodeSocketInt', 0, 0, 2, '0 none, 1 board fence, 2 stone compound wall')
    sock('Gate', 'NodeSocketBool', False, desc='Roofed gate in the front opening of the fence')
    sock('Props', 'NodeSocketFloat', 0.6, 0.0, 1.0, 'Amount of yard props along the back and sides')
    sock('Seed', 'NodeSocketInt', 0, 0, 100000, 'Variant seed (wall layout, footing stones, props)')
    sock('Realize', 'NodeSocketBool', False, desc='Output real geometry instead of instances (for export as one mesh)')
    it.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')

    g = GB(t)
    gi = g.node('NodeGroupInput'); go = g.node('NodeGroupOutput')
    G = lambda name: g.O(gi, name)
    nx, ny, floors, seed = G('Bays X'), G('Bays Y'), G('Floors'), G('Seed')
    W = g.mul(nx, B); D = g.mul(ny, B)
    hW = g.mul(W, 0.5); hD = g.mul(D, 0.5)
    empty = g.node('GeometryNodeJoinGeometry').outputs[0]
    fx0 = g.add(g.mul(hW, -1), B / 2); fy = g.mul(hD, -1)

    # ground
    oi = g.node('GeometryNodeObjectInfo', transform_space='RELATIVE'); g.L.new(G('Ground'), g.I(oi, 'Object'))
    ground = g.O(oi, 'Geometry')

    def gz(dx=0.0, dy=0.0):
        """ground height under the current point (field), optionally sampled at an offset."""
        x, y, _ = g.pos()
        rc = g.node('GeometryNodeRaycast')
        g.L.new(ground, g.I(rc, 'Target Geometry'))
        g.put(rc, 'Source Position', g.vec(g.add(x, dx), g.add(y, dy), 2000.0))
        g.put(rc, 'Ray Direction', g.vec(0.0, 0.0, -1.0)); g.put(rc, 'Ray Length', 5000.0)
        return g.sw('FLOAT', g.O(rc, 'Is Hit'), 0.0, _hitz(g, rc))

    def _hitz(g_, rc):
        s = g_.node('ShaderNodeSeparateXYZ'); g_.L.new(g_.O(rc, 'Hit Position'), s.inputs[0]); return s.outputs['Z']

    def stilt_index(top_z, ground_z):
        need = g.sub(g.sub(top_z, ground_z), 0.12)
        return g.toint(g.add(g.cmp('GREATER_THAN', need, 1.25), g.cmp('GREATER_THAN', need, 2.55)), 'FLOOR')

    parts = []

    # ---------------------------------------------------------- foundation and floor
    gp = g.grid(g.add(nx, 1), g.add(ny, 1), W, D)
    F = g.add(g.stat_max(gp, gz()), FLOOR_ABOVE_GROUND)
    parts.append(g.inst(g.set_z(gp, gz()), 'KIT_Footing', g.rnd('INT', 0, 2, seed, 3), g.rnd('FLOAT', 0.0, 2 * PI, seed, 4)))
    parts.append(g.inst(g.set_z(gp, F), 'KIT_Stilt', stilt_index(g.sub(F, 0.25), gz())))
    parts.append(g.inst(g.set_z(gp, F), 'KIT_PostStorey'))
    parts.append(g.inst(g.set_z(g.grid(nx, g.add(ny, 1), g.sub(W, B), D), F), 'KIT_FloorBeam'))
    parts.append(g.inst(g.set_z(g.grid(g.add(nx, 1), ny, W, g.sub(D, B)), F), 'KIT_FloorBeam', 0, PI / 2))
    parts.append(g.inst(g.set_z(g.grid(nx, ny, g.sub(W, B), g.sub(D, B)), F), 'KIT_FloorDeck'))

    # ---------------------------------------------------------- walls (storey 1, and storey 2 when Floors = 2)
    kdoor = g.toint(g.mul(nx, 0.5), 'FLOOR')
    engawa = G('Engawa')
    variants = {'A': 0, 'B': 1, 'C': 2, 'D': 3, 'E': 4}

    def walls(zf, storey):
        k = g.index()
        r = lambda add: g.rnd('FLOAT', 0.0, 1.0, seed, add + storey * 101)
        if storey == 0:
            front_other = g.sw('INT', engawa, g.sw('INT', g.cmp('LESS_THAN', r(11), 0.6), variants['A'], variants['B']), variants['D'])
            front = g.sw('INT', g.cmp('EQUAL', k, kdoor), front_other, variants['C'])
        else:
            front = g.sw('INT', g.cmp('LESS_THAN', r(11), 0.7), variants['A'], variants['B'])
        side = lambda add: g.sw('INT', g.cmp('LESS_THAN', r(add), 0.25),
                                g.sw('INT', g.cmp('LESS_THAN', r(add), 0.85), variants['E'], variants['A']), variants['B'])
        back_win = g.m('FLOORED_MODULO', seed, nx)
        back = g.sw('INT', g.cmp('EQUAL', k, back_win), g.sw('INT', g.cmp('LESS_THAN', r(31), 0.75), variants['E'], variants['A']), variants['B'])
        out = [
            g.inst(g.line(nx, g.vec(g.add(g.mul(hW, -1), B / 2), g.mul(hD, -1), zf), g.vec(B, 0, 0)), 'KIT_Wall', front, 0.0),
            g.inst(g.line(ny, g.vec(hW, g.add(g.mul(hD, -1), B / 2), zf), g.vec(0, B, 0)), 'KIT_Wall', side(21), PI / 2),
            g.inst(g.line(nx, g.vec(g.sub(hW, B / 2), hD, zf), g.vec(-B, 0, 0)), 'KIT_Wall', back, PI),
            g.inst(g.line(ny, g.vec(g.mul(hW, -1), g.sub(hD, B / 2), zf), g.vec(0, -B, 0)), 'KIT_Wall', side(41), -PI / 2),
        ]
        return g.join(*out)

    parts.append(walls(F, 0))
    F2 = g.add(F, STOREY)
    xd = g.add(g.mul(hW, -1), g.mul(g.add(kdoor, 0.5), B))

    def perim(zf):
        return [(g.line(nx, g.vec(fx0, fy, zf), g.vec(B, 0, 0)), 0.0),
                (g.line(ny, g.vec(hW, g.add(fy, B / 2), zf), g.vec(0, B, 0)), PI / 2),
                (g.line(nx, g.vec(g.sub(hW, B / 2), hD, zf), g.vec(-B, 0, 0)), PI),
                (g.line(ny, g.vec(g.mul(hW, -1), g.sub(hD, B / 2), zf), g.vec(0, -B, 0)), -PI / 2)]
    pent = [g.inst(pts, 'KIT_PentSide', 0, r) for pts, r in perim(F)]
    for sx, sy, r in ((-1, -1, 0.0), (1, -1, PI / 2), (1, 1, PI), (-1, 1, -PI / 2)):
        pent.append(g.inst(g.point(g.vec(g.mul(hW, sx), g.mul(hD, sy), F)), 'KIT_PentCorner', 0, r))
    bpts = g.line(nx, g.vec(fx0, fy, F2), g.vec(B, 0, 0))
    balc = g.join(g.inst(bpts, 'KIT_EngawaDeck'), g.inst(bpts, 'KIT_Railing', 0),
                  g.inst(g.line(2, g.vec(g.mul(hW, -1), fy, F2), g.vec(W, 0, 0)), 'KIT_RailingEnd'),
                  g.inst(g.point(g.vec(hW, fy, F2)), 'KIT_RailPost'),
                  g.inst(g.line(g.add(nx, 1), g.vec(g.mul(hW, -1), fy, F2), g.vec(B, 0, 0)), 'KIT_BalconyBracket'))
    upper = g.join(walls(F2, 1),
                   g.inst(g.set_z(gp, F2), 'KIT_PostStorey'),
                   g.inst(g.set_z(g.grid(nx, g.add(ny, 1), g.sub(W, B), D), F2), 'KIT_FloorBeam'),
                   g.inst(g.set_z(g.grid(g.add(nx, 1), ny, W, g.sub(D, B)), F2), 'KIT_FloorBeam', 0, PI / 2),
                   *pent, g.sw('GEOMETRY', G('Balcony'), empty, balc))
    parts.append(g.sw('GEOMETRY', g.cmp('GREATER_THAN', floors, 1.5), empty, upper))

    # ---------------------------------------------------------- shopfront and lanterns (front, storey 1)
    shop = g.join(g.inst(g.point(g.vec(xd, fy, F)), 'KIT_Noren'), g.inst(g.point(g.vec(g.sub(hW, 0.30), fy, F)), 'KIT_ShopSign'))
    parts.append(g.sw('GEOMETRY', G('Shopfront'), empty, shop))
    parts.append(g.sw('GEOMETRY', G('Lanterns'), empty, g.inst(g.line(2, g.vec(g.sub(xd, 0.84), fy, F), g.vec(1.68, 0, 0)), 'KIT_Lantern')))

    # ---------------------------------------------------------- roof: tile hip (1, 3) or thatched gable (2)
    ns = g.m('MINIMUM', nx, ny); nl = g.m('MAXIMUM', nx, ny)
    Lh = g.mul(nl, B / 2); Ds2 = g.mul(ns, B / 2)
    mid = g.sub(nl, ns)
    zR = g.add(F, g.mul(g.sub(floors, 1), STOREY))
    di = g.toint(g.sub(g.m('MINIMUM', ns, MAX_DEPTH), 1))
    rotz = g.mul(g.cmp('GREATER_THAN', ny, nx), PI / 2)
    no_mid = g.cmp('LESS_THAN', mid, 0.5)
    end_geo = g.sw('GEOMETRY', no_mid, g.coll('KIT_RoofEnd'), g.coll('KIT_RoofEndApex'))
    two_ends = lambda: g.line(2, g.vec(g.mul(Lh, -1), 0.0, zR), g.vec(g.mul(Lh, 2), 0.0, 0.0))
    ends = g.inst(two_ends(), None, di, g.mul(g.index(), PI), instance_geo=end_geo)
    mids = g.inst(g.line(g.toint(mid), g.vec(g.add(g.mul(Lh, -1), Ds2), 0.0, zR), g.vec(B, 0, 0)), 'KIT_RoofMid', di)
    apex = g.sw('GEOMETRY', no_mid, empty, g.inst(g.point(g.vec(0.0, 0.0, zR)), 'KIT_RoofApex', di))
    tile_roof = g.transform_rot(g.join(ends, mids, apex), rotz)
    th = g.join(g.inst(two_ends(), 'KIT_ThatchEnd', di, g.mul(g.index(), PI)),
                g.inst(g.line(g.toint(nl), g.vec(g.mul(Lh, -1), 0.0, zR), g.vec(B, 0, 0)), 'KIT_ThatchMid', di))
    thatch_roof = g.transform_rot(th, rotz)
    roof = g.sw('GEOMETRY', g.cmp('EQUAL', G('Roof'), 2.0, 0.1), tile_roof, thatch_roof)
    parts.append(g.sw('GEOMETRY', g.cmp('GREATER_THAN', G('Roof'), 0.5), empty, roof))

    # ---------------------------------------------------------- engawa, railing, steps (front side)
    EDGE = -1.03
    deck_pts = g.line(nx, g.vec(fx0, fy, F), g.vec(B, 0, 0))
    eng = [g.inst(deck_pts, 'KIT_EngawaDeck'),
           g.inst(deck_pts, 'KIT_Railing', g.toint(g.cmp('EQUAL', g.index(), kdoor))),
           g.inst(g.line(2, g.vec(g.mul(hW, -1), fy, F), g.vec(W, 0, 0)), 'KIT_RailingEnd'),
           g.inst(g.point(g.vec(hW, fy, F)), 'KIT_RailPost')]
    epts = g.line(g.add(nx, 1), g.vec(g.mul(hW, -1), fy, 0.0), g.vec(B, 0, 0))
    eoff = EDGE + 0.06
    eng.append(g.inst(g.set_pos(g.set_z(epts, gz(0.0, eoff)), offset=g.vec(0.0, eoff, 0.0)), 'KIT_Footing', g.rnd('INT', 0, 2, seed, 5), g.rnd('FLOAT', 0.0, 2 * PI, seed, 6)))
    eng.append(g.inst(g.set_z(epts, F), 'KIT_EngawaPost', stilt_index(g.sub(F, 0.37), gz(0.0, eoff))))
    land = g.point(g.vec(xd, g.add(fy, EDGE - 1.2), 0.0))
    gl = g.stat_max(land, gz())
    nsteps = g.m('MINIMUM', g.m('MAXIMUM', g.toint(g.m('DIVIDE', g.sub(g.sub(F, 0.15), gl), 0.19)), 2), 14)
    eng.append(g.inst(g.point(g.vec(xd, fy, F)), 'KIT_Steps', g.toint(g.sub(nsteps, 2))))
    parts.append(g.sw('GEOMETRY', engawa, empty, g.join(*eng)))

    # ---------------------------------------------------------- fence 1 (boards) or 2 (stone compound wall), gate
    yf = g.sub(fy, 2 * B); yb = g.add(hD, B); xl = g.sub(g.mul(hW, -1), B); xr = g.add(hW, B)
    on_ground = lambda pts: g.set_z(pts, gz())
    def seg_lines():
        return [(g.delete(g.line(g.add(nx, 2), g.vec(g.add(xl, B / 2), yf, 0.0), g.vec(B, 0, 0)), g.cmp('EQUAL', g.index(), g.add(kdoor, 1))), 0.0),
                (g.line(g.add(nx, 2), g.vec(g.sub(xr, B / 2), yb, 0.0), g.vec(-B, 0, 0)), PI),
                (g.line(g.add(ny, 3), g.vec(xl, g.sub(yb, B / 2), 0.0), g.vec(0, -B, 0)), -PI / 2),
                (g.line(g.add(ny, 3), g.vec(xr, g.add(yf, B / 2), 0.0), g.vec(0, B, 0)), PI / 2)]
    def post_lines():
        return [g.line(g.add(nx, 3), g.vec(xl, yf, 0.0), g.vec(B, 0, 0)), g.line(g.add(nx, 3), g.vec(xl, yb, 0.0), g.vec(B, 0, 0)),
                g.line(g.add(ny, 2), g.vec(xl, g.add(yf, B), 0.0), g.vec(0, B, 0)), g.line(g.add(ny, 2), g.vec(xr, g.add(yf, B), 0.0), g.vec(0, B, 0))]
    def fence_of(seg, post):
        return g.join(*[g.inst(on_ground(l), seg, 0, r) for l, r in seg_lines()], *[g.inst(on_ground(l), post) for l in post_lines()])
    fence = g.sw('GEOMETRY', g.cmp('GREATER_THAN', G('Fence'), 1.5), fence_of('KIT_FenceSeg', 'KIT_FencePost'), fence_of('KIT_Wall2Seg', 'KIT_Wall2Pier'))
    gate = g.sw('GEOMETRY', G('Gate'), empty, g.inst(on_ground(g.point(g.vec(xd, yf, 0.0))), 'KIT_Gate'))
    parts.append(g.sw('GEOMETRY', g.cmp('GREATER_THAN', G('Fence'), 0.5), empty, g.join(fence, gate)))

    # ---------------------------------------------------------- yard props along the back and the sides
    step = 0.8; off = 0.65
    nb = g.toint(g.m('DIVIDE', g.sub(W, 0.6), step), 'FLOOR'); nsd = g.toint(g.m('DIVIDE', g.sub(D, 0.6), step), 'FLOOR')
    cand = g.join(g.line(nb, g.vec(g.add(g.mul(hW, -1), 0.4), g.add(hD, off), 0.0), g.vec(step, 0, 0)),
                  g.line(nsd, g.vec(g.sub(g.mul(hW, -1), off), g.add(g.mul(hD, -1), 0.4), 0.0), g.vec(0, step, 0)),
                  g.line(nsd, g.vec(g.add(hW, off), g.add(g.mul(hD, -1), 0.4), 0.0), g.vec(0, step, 0)))
    keep = g.rnd('BOOLEAN', g.mul(G('Props'), 0.45), None, seed, 77)
    nk = g.node('FunctionNodeBooleanMath', operation='NOT'); g.put(nk, 0, keep)
    cand = g.delete(cand, nk.outputs[0])
    jit = g.vec(g.rnd('FLOAT', -0.12, 0.12, seed, 78), g.rnd('FLOAT', -0.12, 0.12, seed, 79), 0.0)
    cand = g.set_z(g.set_pos(cand, offset=jit), gz())
    parts.append(g.inst(cand, 'KIT_Props', g.rnd('INT', 0, 3, seed, 80), g.rnd('FLOAT', 0.0, 2 * PI, seed, 81)))

    # ---------------------------------------------------------- output
    allg = g.join(*parts)
    rz = g.node('GeometryNodeRealizeInstances'); g.L.new(allg, g.I(rz, 'Geometry'))
    g.L.new(g.sw('GEOMETRY', G('Realize'), allg, rz.outputs[0]), g.I(go, 'Geometry'))
    return t
