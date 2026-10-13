"""Geometry-nodes groups for the town: GN_EdoKitField (crop rows / paddy on a patch) and GN_EdoKitEmbank (stone-lined canal).

    gn_town.build_field()              -> GN_EdoKitField    (modifier on a mesh object placed at the field centre)
    gn_town.build_embank(gaps)         -> GN_EdoKitEmbank   (modifier on a curve object: the canal centre line)
Both follow the terrain through the Ground input like GN_EdoKitHouse.
"""
import bpy, math
from gn_house import GB

PI = math.pi


def _ground(g, G):
    oi = g.node('GeometryNodeObjectInfo', transform_space='RELATIVE'); g.L.new(G('Ground'), g.I(oi, 'Object'))
    ground = g.O(oi, 'Geometry')

    def gz():
        x, y, _ = g.pos()
        rc = g.node('GeometryNodeRaycast'); g.L.new(ground, g.I(rc, 'Target Geometry'))
        g.put(rc, 'Source Position', g.vec(x, y, 2000.0)); g.put(rc, 'Ray Direction', g.vec(0.0, 0.0, -1.0)); g.put(rc, 'Ray Length', 5000.0)
        s = g.node('ShaderNodeSeparateXYZ'); g.L.new(g.O(rc, 'Hit Position'), s.inputs[0])
        return g.sw('FLOAT', g.O(rc, 'Is Hit'), 0.0, s.outputs['Z'])
    return gz


def _inst(g, points, coll, index, rot_z, scale=None, selection=None):
    n = g.node('GeometryNodeInstanceOnPoints')
    g.L.new(points, g.I(n, 'Points')); g.L.new(g.coll(coll), g.I(n, 'Instance'))
    g.put(n, 'Pick Instance', True); g.put(n, 'Instance Index', index)
    e = g.node('FunctionNodeEulerToRotation'); g.put(e, 'Euler', g.vec(0.0, 0.0, rot_z)); g.L.new(e.outputs[0], g.I(n, 'Rotation'))
    if scale is not None: g.put(n, 'Scale', scale)
    if selection is not None: g.put(n, 'Selection', selection)
    return n.outputs[0]


def _new_group(name, geometry_in=True):
    old = bpy.data.node_groups.get(name)
    if old: bpy.data.node_groups.remove(old)
    t = bpy.data.node_groups.new(name, 'GeometryNodeTree'); t.is_modifier = True
    if geometry_in: t.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    return t


def build_field():
    t = _new_group('GN_EdoKitField')
    it = t.interface

    def sock(name, typ, default, lo=None, hi=None, desc=''):
        s = it.new_socket(name, in_out='INPUT', socket_type=typ)
        s.default_value = default
        if lo is not None: s.min_value = lo
        if hi is not None: s.max_value = hi
        s.description = desc
    sock('Ground', 'NodeSocketObject', None, desc='Terrain the field lies on')
    sock('Size X', 'NodeSocketFloat', 30.0, 2.0, 400.0, 'Field size along X (rows run along X), centred on the object')
    sock('Size Y', 'NodeSocketFloat', 20.0, 2.0, 400.0, 'Field size along Y')
    sock('Crop', 'NodeSocketInt', 0, 0, 2, '0 vegetables on ridges, 1 barley / grain on ridges, 2 rice paddy with bunds')
    sock('Seed', 'NodeSocketInt', 0, 0, 100000)
    sock('Realize', 'NodeSocketBool', False, desc='Output real geometry instead of instances')
    it.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    g = GB(t); gi = g.node('NodeGroupInput'); go = g.node('NodeGroupOutput'); G = lambda n: g.O(gi, n)
    gz = _ground(g, G)
    sx, sy, seed = G('Size X'), G('Size Y'), G('Seed')
    empty = g.node('GeometryNodeJoinGeometry').outputs[0]

    def rows(spacing_x, spacing_y):
        vx = g.toint(g.m('DIVIDE', sx, spacing_x), 'FLOOR'); vy = g.toint(g.m('DIVIDE', sy, spacing_y), 'FLOOR')
        return g.grid(vx, vy, g.mul(g.sub(vx, 1), spacing_x), g.mul(g.sub(vy, 1), spacing_y))

    def jitter(pts, a, k):
        jx = g.rnd('FLOAT', -a, a, seed, k); jy = g.rnd('FLOAT', -a, a, seed, k + 1)
        return g.set_pos(pts, offset=g.vec(jx, jy, 0.0))

    def on_ground(pts, dz=0.0):
        return g.set_pos(pts, offset=g.vec(0.0, 0.0, g.add(gz(), dz) if dz else gz()))

    def planted(points, coll, count, dz, keep, k):
        yaw = g.rnd('FLOAT', 0.0, 2 * PI, seed, k)
        sc = g.rnd('FLOAT', 0.85, 1.25, seed, k + 1)
        scale = g.vec(sc, sc, g.mul(sc, g.rnd('FLOAT', 0.9, 1.1, seed, k + 2)))
        idx = g.toint(g.rnd('FLOAT', 0.0, count - 0.001, seed, k + 3), 'FLOOR')
        sel = g.rnd('BOOLEAN', keep, None, seed, k + 4)
        return _inst(g, on_ground(jitter(points, 0.05, k + 5), dz), coll, idx, yaw, scale, sel)

    ridges = _inst(g, on_ground(rows(2.0, 1.0)), 'KIT_CropRidge', g.toint(0.0), 0.0)
    veg = g.join(ridges, planted(rows(0.5, 1.0), 'KIT_CropVeg', 3, 0.19, 0.92, 10))
    grain = g.join(ridges, planted(rows(0.42, 1.0), 'KIT_CropGrain', 2, 0.19, 0.95, 20))
    rice = planted(rows(0.36, 0.36), 'KIT_CropRice', 2, 0.0, 0.97, 30)
    nbx = g.toint(g.m('DIVIDE', sx, 2.0), 'FLOOR'); nby = g.toint(g.m('DIVIDE', sy, 2.0), 'FLOOR')
    hx, hy = g.mul(sx, 0.5), g.mul(sy, 0.5)
    bunds = g.join(
        _inst(g, on_ground(g.line(nbx, g.vec(g.add(g.mul(hx, -1), 1.0), g.mul(hy, -1), 0.0), g.vec(2.0, 0.0, 0.0))), 'KIT_PaddyBund', g.toint(0.0), 0.0),
        _inst(g, on_ground(g.line(nbx, g.vec(g.add(g.mul(hx, -1), 1.0), hy, 0.0), g.vec(2.0, 0.0, 0.0))), 'KIT_PaddyBund', g.toint(0.0), 0.0),
        _inst(g, on_ground(g.line(nby, g.vec(g.mul(hx, -1), g.add(g.mul(hy, -1), 1.0), 0.0), g.vec(0.0, 2.0, 0.0))), 'KIT_PaddyBund', g.toint(0.0), PI / 2),
        _inst(g, on_ground(g.line(nby, g.vec(hx, g.add(g.mul(hy, -1), 1.0), 0.0), g.vec(0.0, 2.0, 0.0))), 'KIT_PaddyBund', g.toint(0.0), PI / 2))
    paddy = g.join(rice, bunds)
    out = g.sw('GEOMETRY', g.cmp('GREATER_THAN', G('Crop'), 1.5), g.sw('GEOMETRY', g.cmp('EQUAL', G('Crop'), 1.0, 0.1), veg, grain), paddy)
    rz = g.node('GeometryNodeRealizeInstances'); g.L.new(out, g.I(rz, 'Geometry'))
    g.L.new(g.sw('GEOMETRY', G('Realize'), out, rz.outputs[0]), g.I(go, 'Geometry'))
    return t


def build_embank(gaps=()):
    """gaps: list of (lo, hi) ranges along Y where no bank is built (bridges)."""
    t = _new_group('GN_EdoKitEmbank')
    it = t.interface

    def sock(name, typ, default, lo=None, hi=None, desc=''):
        s = it.new_socket(name, in_out='INPUT', socket_type=typ)
        s.default_value = default
        if lo is not None: s.min_value = lo
        if hi is not None: s.max_value = hi
        s.description = desc
    sock('Ground', 'NodeSocketObject', None, desc='Terrain')
    sock('Half Width', 'NodeSocketFloat', 1.15, 0.5, 6.0, 'Distance of the stone curb from the canal centre line')
    sock('Rocks', 'NodeSocketFloat', 0.35, 0.0, 1.0, 'Share of the 2 m sections that get a boulder at the outer edge')
    sock('Seed', 'NodeSocketInt', 0, 0, 100000)
    sock('Realize', 'NodeSocketBool', False, desc='Output real geometry instead of instances')
    it.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    g = GB(t); gi = g.node('NodeGroupInput'); go = g.node('NodeGroupOutput'); G = lambda n: g.O(gi, n)
    gz = _ground(g, G); seed = G('Seed')
    rs = g.node('GeometryNodeResampleCurve'); rs.inputs['Mode'].default_value = 'Length'; g.L.new(g.O(gi, 'Geometry'), g.I(rs, 'Curve')); g.put(rs, 'Length', 2.0)
    cp = g.node('GeometryNodeCurveToPoints', mode='EVALUATED'); g.L.new(rs.outputs[0], g.I(cp, 'Curve'))
    pts = cp.outputs['Points']; tang = cp.outputs['Tangent']
    ts = g.node('ShaderNodeSeparateXYZ'); g.L.new(tang, ts.inputs[0])
    tx, ty = ts.outputs['X'], ts.outputs['Y']
    yaw = g.m('ARCTAN2', ty, tx)
    sidex, sidey = g.mul(ty, -1.0), tx                                  # unit vector to the left of the flow direction
    px, py, _ = g.pos()
    in_gap = None
    for lo, hi in gaps:
        a = g.node('FunctionNodeBooleanMath', operation='AND'); g.L.new(g.cmp('GREATER_THAN', py, lo), a.inputs[0]); g.L.new(g.cmp('LESS_THAN', py, hi), a.inputs[1])
        if in_gap is None: in_gap = a.outputs[0]
        else:
            o = g.node('FunctionNodeBooleanMath', operation='OR'); g.L.new(in_gap, o.inputs[0]); g.L.new(a.outputs[0], o.inputs[1]); in_gap = o.outputs[0]
    base = g.delete(pts, in_gap) if in_gap is not None else pts

    def at(d):
        """points shifted sideways by d (a field or float) and set on the ground"""
        off = g.set_pos(base, offset=g.vec(g.mul(sidex, d), g.mul(sidey, d), 0.0))
        return g.set_pos(off, offset=g.vec(0.0, 0.0, gz()))

    def side_of(sgn):
        hw = G('Half Width')
        flip = PI if sgn < 0 else 0.0
        yaw_s = g.add(yaw, flip) if flip else yaw
        s = float(sgn)
        curb = _inst(g, at(g.mul(hw, s)), 'KIT_EmbankCurb', g.toint(0.0), yaw_s)
        k = g.rnd('INT', 0, 3, seed, 7 if sgn > 0 else 17)
        turn = g.mul(g.toint(g.rnd('FLOAT', 0.0, 3.999, seed, 8 if sgn > 0 else 18), 'FLOOR'), PI / 2)
        cob1 = _inst(g, at(g.mul(g.add(hw, 1.35), s)), 'KIT_EmbankCobble', g.toint(0.0), g.add(yaw_s, turn))
        cob2 = _inst(g, at(g.mul(g.add(hw, 3.35), s)), 'KIT_EmbankCobble', g.toint(0.0), g.add(yaw_s, turn))
        edge = g.mul(g.add(hw, g.rnd('FLOAT', 4.9, 5.7, seed, 9 if sgn > 0 else 19)), s)
        off = g.set_pos(base, offset=g.vec(g.mul(sidex, edge), g.mul(sidey, edge), 0.0))
        rp = g.set_pos(off, offset=g.vec(0.0, 0.0, gz()))
        rk = _inst(g, rp, 'KIT_EmbankRock', g.toint(g.rnd('FLOAT', 0.0, 2.999, seed, 10 if sgn > 0 else 20), 'FLOOR'),
                   g.rnd('FLOAT', 0.0, 2 * PI, seed, 11 if sgn > 0 else 21),
                   scale=(lambda r: g.vec(r, r, r))(g.rnd('FLOAT', 0.8, 1.7, seed, 12 if sgn > 0 else 22)),
                   selection=g.rnd('BOOLEAN', G('Rocks'), None, seed, 13 if sgn > 0 else 23))
        return g.join(curb, cob1, cob2, rk)
    both = g.join(side_of(1), side_of(-1))
    rz = g.node('GeometryNodeRealizeInstances'); g.L.new(both, g.I(rz, 'Geometry'))
    g.L.new(g.sw('GEOMETRY', G('Realize'), both, rz.outputs[0]), g.I(go, 'Geometry'))
    return t


def build_border():
    """GN_EdoKitBorder: modifier on a points mesh. Per point attributes: kind (0 stone, 1 rope, 2 torii, 3 pier, 4 stone lantern, 5 Jizo),
    yaw (radians) and sx (rope length / 6 m). Instances stand on the Ground object."""
    t = _new_group('GN_EdoKitBorder')
    it = t.interface
    s = it.new_socket('Ground', in_out='INPUT', socket_type='NodeSocketObject'); s.description = 'Terrain the border stands on'
    s = it.new_socket('Realize', in_out='INPUT', socket_type='NodeSocketBool'); s.default_value = False
    it.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    g = GB(t); gi = g.node('NodeGroupInput'); go = g.node('NodeGroupOutput'); G = lambda n: g.O(gi, n)
    gz = _ground(g, G)

    def named(name, typ):
        n = g.node('GeometryNodeInputNamedAttribute', data_type=typ); g.put(n, 'Name', name); return g.O(n, 'Attribute')
    kind = named('kind', 'INT'); yaw = named('yaw', 'FLOAT'); sx = named('sx', 'FLOAT')
    pts = g.set_z(g.O(gi, 'Geometry'), gz())
    sel = lambda k: g.cmp('EQUAL', kind, float(k), 0.1)
    stone_i = g.toint(g.rnd('FLOAT', 0.0, 2.999, 5), 'FLOOR'); stone_s = g.rnd('FLOAT', 0.85, 1.25, 6)
    parts = [
        _inst(g, pts, 'KIT_BorderStone', stone_i, g.rnd('FLOAT', 0.0, 2 * PI, 7), scale=g.vec(stone_s, stone_s, stone_s), selection=sel(0)),
        _inst(g, pts, 'KIT_BorderRope', g.toint(0.0), yaw, scale=g.vec(sx, 1.0, 1.0), selection=sel(1)),
        _inst(g, pts, 'KIT_Torii', g.toint(0.0), yaw, selection=sel(2)),
        _inst(g, pts, 'KIT_ToriiPier', g.toint(0.0), yaw, selection=sel(3)),
        _inst(g, pts, 'KIT_Toro', g.toint(0.0), yaw, selection=sel(4)),
        _inst(g, pts, 'KIT_Jizo', g.toint(0.0), yaw, selection=sel(5)),
    ]
    allg = g.join(*parts)
    rz = g.node('GeometryNodeRealizeInstances'); g.L.new(allg, g.I(rz, 'Geometry'))
    g.L.new(g.sw('GEOMETRY', G('Realize'), allg, rz.outputs[0]), g.I(go, 'Geometry'))
    return t
