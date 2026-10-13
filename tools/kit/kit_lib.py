"""Shared constants, mesh builder and materials for the Edo house kit (Blender 5.2, bpy)."""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix

# ---------------------------------------------------------------- dimensions (measured from the original GN_EdoHouse)
B = 1.82                 # one bay (1 ken) as used by the original generator
STOREY = 3.14            # floor to floor
FLOOR_ABOVE_GROUND = 1.30  # floor top above the highest ground point under the post grid
KETA_TOP = 2.956         # top of the wall's top beam above the floor
EAVE_Z = 2.78            # roof eave (mid-span, below the tile ends) above the floor of the top storey
ROOF_O = 1.21            # eave overhang measured from the wall centre line
PITCH = 0.533            # ridge rise / horizontal run (2.10 m over 3.94 m in the original 4x3 house)
ROOF_P = 1.25            # roof profile exponent (concave, steeper toward the ridge)
CORNER_RISE = 0.24       # upturn of the eaves at the corners
RIB = B / 7              # tile rib spacing: 7 ribs per bay = 0.26 m
RIB_A = 0.032            # tile rib amplitude
MAX_DEPTH = 8            # roof modules exist for short sides of 1..8 bays

# texture world size (metres per texture repeat) and which image direction the wood/plank grain runs in
TEXSIZE = {'Timber': 2.0, 'Planks': 2.0, 'Plaster': 2.0, 'Kawara': B, 'Stone': 1.0, 'Paper': 1.0,
           'Ceramic': 0.5, 'Thatch': 2.0, 'StoneWall': 2.0, 'Cloth': 1.0, 'Lantern': 0.5}
GRAIN_IMG = {'Timber': 'v', 'Planks': 'u', 'Thatch': 'v'}


class MB:
    """Mesh builder: bmesh + per-corner UVs + named material slots."""

    def __init__(self, name):
        self.name = name
        self.bm = bmesh.new()
        self.uv = self.bm.loops.layers.uv.new('UVMap')
        self.mats = []
        self.rng = random.Random(sum(ord(c) * (i + 1) for i, c in enumerate(name)))

    def mi(self, mat):
        if mat not in self.mats:
            self.mats.append(mat)
        return self.mats.index(mat)

    def face(self, verts, mat, uvs, smooth=False, want=None):
        """verts: BMVerts; uvs: list of (u,v); want: desired normal direction (flips winding if needed)."""
        if want is not None and len(verts) >= 3:
            n = (verts[1].co - verts[0].co).cross(verts[2].co - verts[0].co)
            if n.length < 1e-12 and len(verts) > 3:
                n = (verts[2].co - verts[0].co).cross(verts[3].co - verts[0].co)
            if n.dot(Vector(want)) < 0:
                verts = list(reversed(verts)); uvs = list(reversed(uvs))
        try:
            f = self.bm.faces.new(verts)
        except ValueError:
            return None
        f.material_index = self.mi(mat)
        f.smooth = smooth
        for loop, uv in zip(f.loops, uvs):
            loop[self.uv].uv = uv
        return f

    def v(self, co):
        return self.bm.verts.new(Vector(co))

    # ------------------------------------------------------------ boxes with box-projected, grain-aware UVs
    def box(self, mn, mx, mat, grain=2, M=None, skip=(), uv_off=None):
        """Axis-aligned box in local coords (mn..mx), optionally transformed by matrix M.
        grain: local axis (0,1,2) the wood grain / plank length follows. skip: faces to omit, e.g. ('-z',)."""
        T = TEXSIZE.get(mat, 2.0)
        img = GRAIN_IMG.get(mat)
        off = uv_off if uv_off is not None else (self.rng.random() * 7.0, self.rng.random() * 7.0)
        lc = [Vector((mx[0] if i & 1 else mn[0], mx[1] if i & 2 else mn[1], mx[2] if i & 4 else mn[2])) for i in range(8)]
        M = M or Matrix.Identity(4)
        vs = [self.v(M @ c) for c in lc]
        faces = {'-x': (0, 4, 6, 2), '+x': (1, 3, 7, 5), '-y': (0, 1, 5, 4), '+y': (2, 6, 7, 3), '-z': (0, 2, 3, 1), '+z': (4, 5, 7, 6)}
        rot = M.to_3x3()
        for key, idx in faces.items():
            if key in skip:
                continue
            a = 'xyz'.index(key[1]); sgn = 1 if key[0] == '+' else -1
            p = [i for i in range(3) if i != a]
            uvs = []
            for i in idx:
                c = lc[i]
                if img and grain in p:
                    other = p[0] if p[1] == grain else p[1]
                    uu, vv = (c[other], c[grain]) if img == 'v' else (c[grain], c[other])
                else:
                    uu, vv = c[p[0]], c[p[1]]
                uvs.append((uu / T + off[0], vv / T + off[1]))
            want = rot @ Vector([sgn if i == a else 0 for i in range(3)])
            self.face([vs[i] for i in idx], mat, uvs, want=want)
        return vs

    # ------------------------------------------------------------ lofted strips (rings of points along a path)
    def loft(self, rings, mat, closed=False, smooth=True, u_along=True, cap0=False, cap1=False, want_out=None, uv_scale=None):
        """rings: list of equal-length point lists. Faces join ring i to ring i+1.
        UV: v = distance along the path, u = distance around the ring (both / texture size)."""
        T = uv_scale or TEXSIZE.get(mat, 2.0)
        vs = [[self.v(p) for p in ring] for ring in rings]
        along = [0.0]
        for i in range(1, len(rings)):
            c0 = sum((Vector(p) for p in rings[i - 1]), Vector()) / len(rings[i - 1])
            c1 = sum((Vector(p) for p in rings[i]), Vector()) / len(rings[i])
            along.append(along[-1] + (c1 - c0).length)
        around = [0.0]
        r0 = rings[0]
        for j in range(1, len(r0)):
            around.append(around[-1] + (Vector(r0[j]) - Vector(r0[j - 1])).length)
        n = len(r0); last = n if closed else n - 1
        for i in range(len(rings) - 1):
            for j in range(last):
                j2 = (j + 1) % n
                a, b_, c, d = vs[i][j], vs[i][j2], vs[i + 1][j2], vs[i + 1][j]
                uj2 = around[j2] if j2 else around[-1] + (Vector(r0[0]) - Vector(r0[-1])).length
                uvs = [(around[j] / T, along[i] / T), (uj2 / T, along[i] / T), (uj2 / T, along[i + 1] / T), (around[j] / T, along[i + 1] / T)]
                want = None
                if want_out is not None:
                    mid = (a.co + b_.co + c.co + d.co) / 4
                    want = want_out(mid)
                self.face([a, b_, c, d], mat, uvs, smooth=smooth, want=want)
        for flag, ring, k in ((cap0, vs[0], 0), (cap1, vs[-1], -1)):
            if flag:
                ctr = sum((v.co for v in ring), Vector()) / len(ring)
                nxt = sum((v.co for v in vs[1 if k == 0 else -2]), Vector()) / len(ring)
                want = ctr - nxt
                self.face(list(ring), mat, [((v.co - ctr).x / T, (v.co - ctr).z / T) for v in ring], smooth=False, want=want)
        return vs

    def lathe(self, profile, segs, mat, axis='z', cap_top=True, cap_bottom=False, smooth=True, phase=0.0, uv_scale=None, want=None):
        """profile: list of (radius, height). Revolves around the local axis."""
        T = uv_scale or TEXSIZE.get(mat, 2.0)
        rings = []
        for r, h in profile:
            ring = []
            for k in range(segs):
                a = 2 * math.pi * k / segs + phase
                x, y = r * math.cos(a), r * math.sin(a)
                ring.append((x, y, h) if axis == 'z' else (h, x, y))
            rings.append(ring)
        vs = [[self.v(p) for p in ring] for ring in rings]
        img = GRAIN_IMG.get(mat)
        hs = [0.0]
        for i in range(1, len(profile)):
            hs.append(hs[-1] + math.hypot(profile[i][0] - profile[i - 1][0], profile[i][1] - profile[i - 1][1]))
        for i in range(len(rings) - 1):
            for k in range(segs):
                k2 = (k + 1) % segs
                r_ = max(profile[i][0], profile[i + 1][0])
                u0 = (k / segs) * 2 * math.pi * r_; u1 = ((k + 1) / segs) * 2 * math.pi * r_
                quad = [vs[i][k], vs[i][k2], vs[i + 1][k2], vs[i + 1][k]]
                if img == 'u':
                    uvs = [(hs[i] / T, u0 / T), (hs[i] / T, u1 / T), (hs[i + 1] / T, u1 / T), (hs[i + 1] / T, u0 / T)]
                else:
                    uvs = [(u0 / T, hs[i] / T), (u1 / T, hs[i] / T), (u1 / T, hs[i + 1] / T), (u0 / T, hs[i + 1] / T)]
                mid = sum((v.co for v in quad), Vector()) / 4
                ax = Vector((0, 0, 1)) if axis == 'z' else Vector((1, 0, 0))
                radial = mid - ax * mid.dot(ax)
                if want == 'inward': radial = -radial
                elif want is not None and want != 'radial': radial = Vector(want)
                self.face(quad, mat, uvs, smooth=smooth, want=radial)
        for flag, ring, sgn in ((cap_top, vs[-1], 1), (cap_bottom, vs[0], -1)):
            if flag:
                ax = Vector((0, 0, sgn)) if axis == 'z' else Vector((sgn, 0, 0))
                self.face(list(ring), mat, [((v.co.x if axis == 'z' else v.co.y) / T, (v.co.y if axis == 'z' else v.co.z) / T) for v in ring], want=ax)
        return vs

    def to_object(self, coll, name=None):
        name = name or self.name
        me = bpy.data.meshes.new(name)
        bmesh.ops.remove_doubles(self.bm, verts=self.bm.verts, dist=1e-6)
        self.bm.to_mesh(me)
        self.bm.free()
        for m in self.mats:
            me.materials.append(bpy.data.materials[f'M_Edo_{m}'])
        ob = bpy.data.objects.new(name, me)
        coll.objects.link(ob)
        return ob


def tri_count(ob):
    me = ob.data
    return sum(len(p.vertices) - 2 for p in me.polygons)


# ---------------------------------------------------------------- materials
def make_materials(tex_rel):
    """tex_rel: path prefix for textures, e.g. '//textures' (relative to the saved kit .blend)."""
    moss = {'Kawara': 0.50, 'Stone': 0.38, 'Timber': 0.10, 'Planks': 0.08, 'Thatch': 0.30, 'StoneWall': 0.40}
    for name in TEXSIZE:
        mat = bpy.data.materials.get(f'M_Edo_{name}') or bpy.data.materials.new(f'M_Edo_{name}')
        mat.use_nodes = True
        nt = mat.node_tree; nt.nodes.clear()
        out = nt.nodes.new('ShaderNodeOutputMaterial'); out.location = (900, 0)
        bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled'); bsdf.location = (600, 0)
        nt.links.new(bsdf.outputs[0], out.inputs['Surface'])
        uvn = nt.nodes.new('ShaderNodeUVMap'); uvn.uv_map = 'UVMap'; uvn.location = (-900, 0)

        def img(kind, cs):
            n = nt.nodes.new('ShaderNodeTexImage')
            path = f'{tex_rel}/T_Edo_{name}/{kind}.jpg'
            im = bpy.data.images.get(f'T_Edo_{name}_{kind}') or bpy.data.images.load(bpy.path.abspath(path), check_existing=True)
            im.name = f'T_Edo_{name}_{kind}'; im.filepath = path
            im.colorspace_settings.name = cs
            n.image = im
            nt.links.new(uvn.outputs['UV'], n.inputs['Vector'])
            return n
        col = img('BaseColor', 'sRGB'); col.location = (-500, 300)
        orm = img('ORM', 'Non-Color'); orm.location = (-500, 0)
        nrm = img('Normal_DX', 'Non-Color'); nrm.location = (-500, -300)
        sep = nt.nodes.new('ShaderNodeSeparateColor'); sep.location = (-200, 0); nt.links.new(orm.outputs['Color'], sep.inputs['Color'])
        # DirectX -> OpenGL for Blender: invert green
        sepn = nt.nodes.new('ShaderNodeSeparateColor'); sepn.location = (-250, -300); nt.links.new(nrm.outputs['Color'], sepn.inputs['Color'])
        inv = nt.nodes.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0; inv.location = (-80, -350)
        nt.links.new(sepn.outputs['Green'], inv.inputs[1])
        comb = nt.nodes.new('ShaderNodeCombineColor'); comb.location = (60, -300)
        nt.links.new(sepn.outputs['Red'], comb.inputs['Red']); nt.links.new(inv.outputs[0], comb.inputs['Green']); nt.links.new(sepn.outputs['Blue'], comb.inputs['Blue'])
        nmap = nt.nodes.new('ShaderNodeNormalMap'); nmap.location = (250, -300); nmap.uv_map = 'UVMap'
        nt.links.new(comb.outputs['Color'], nmap.inputs['Color'])
        nt.links.new(nmap.outputs['Normal'], bsdf.inputs['Normal'])
        # AO darkens the base colour a little (Principled has no AO input)
        aomix = nt.nodes.new('ShaderNodeMix'); aomix.data_type = 'RGBA'; aomix.blend_type = 'MULTIPLY'; aomix.location = (100, 250)
        aomix.inputs['Factor'].default_value = 0.7
        nt.links.new(col.outputs['Color'], aomix.inputs['A']); nt.links.new(sep.outputs['Red'], aomix.inputs['B'])
        base_out = aomix.outputs['Result']; rough_out = sep.outputs['Green']
        if name in moss:
            # moss on up-facing surfaces, broken up by world-space noise (Blender preview; recreate as a world-aligned blend in Unreal)
            mc = img('BaseColor', 'sRGB'); mc.image = bpy.data.images.load(bpy.path.abspath(f'{tex_rel}/T_Edo_Moss/BaseColor.jpg'), check_existing=True)
            mc.image.name = 'T_Edo_Moss_BaseColor'; mc.image.filepath = f'{tex_rel}/T_Edo_Moss/BaseColor.jpg'; mc.location = (-500, 600)
            mapn = nt.nodes.new('ShaderNodeMapping'); mapn.inputs['Scale'].default_value = (1.3, 1.3, 1.3); mapn.location = (-700, 600)
            nt.links.new(uvn.outputs['UV'], mapn.inputs['Vector']); nt.links.new(mapn.outputs['Vector'], mc.inputs['Vector'])
            geo = nt.nodes.new('ShaderNodeNewGeometry'); geo.location = (-900, 900)
            sepz = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(geo.outputs['Normal'], sepz.inputs['Vector']); sepz.location = (-700, 900)
            up = nt.nodes.new('ShaderNodeMapRange'); up.inputs['From Min'].default_value = 0.35; up.inputs['From Max'].default_value = 0.95; up.location = (-500, 900)
            nt.links.new(sepz.outputs['Z'], up.inputs['Value'])
            noise = nt.nodes.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value = 0.55; noise.inputs['Detail'].default_value = 6; noise.location = (-500, 1150)
            nt.links.new(geo.outputs['Position'], noise.inputs['Vector'])
            nmr = nt.nodes.new('ShaderNodeMapRange'); nmr.inputs['From Min'].default_value = 0.52; nmr.inputs['From Max'].default_value = 0.68; nmr.location = (-300, 1150)
            nt.links.new(noise.outputs['Fac'], nmr.inputs['Value'])
            m1 = nt.nodes.new('ShaderNodeMath'); m1.operation = 'MULTIPLY'; m1.location = (-100, 1000)
            nt.links.new(up.outputs['Result'], m1.inputs[0]); nt.links.new(nmr.outputs['Result'], m1.inputs[1])
            m2 = nt.nodes.new('ShaderNodeMath'); m2.operation = 'MULTIPLY'; m2.inputs[1].default_value = moss[name]; m2.location = (60, 1000)
            nt.links.new(m1.outputs[0], m2.inputs[0])
            mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.location = (300, 400)
            nt.links.new(m2.outputs[0], mix.inputs['Factor']); nt.links.new(base_out, mix.inputs['A']); nt.links.new(mc.outputs['Color'], mix.inputs['B'])
            base_out = mix.outputs['Result']
            rmix = nt.nodes.new('ShaderNodeMix'); rmix.data_type = 'FLOAT'; rmix.location = (300, 100)
            rmix.inputs['B'].default_value = 0.9
            nt.links.new(m2.outputs[0], rmix.inputs['Factor']); nt.links.new(rough_out, rmix.inputs['A'])
            rough_out = rmix.outputs['Result']
        if name == 'Plaster':
            # weathering: darker toward the bottom of each wall module, with vertical rain streaks (module-local space)
            oc = nt.nodes.new('ShaderNodeTexCoord'); oc.location = (-900, -700)
            sz = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(oc.outputs['Object'], sz.inputs['Vector'])
            grad = nt.nodes.new('ShaderNodeMapRange'); grad.inputs['From Min'].default_value = 0.0; grad.inputs['From Max'].default_value = 1.4
            grad.inputs['To Min'].default_value = 0.80; grad.inputs['To Max'].default_value = 1.0
            nt.links.new(sz.outputs['Z'], grad.inputs['Value'])
            st = nt.nodes.new('ShaderNodeTexNoise'); st.inputs['Scale'].default_value = 3.0; st.inputs['Detail'].default_value = 4
            stm = nt.nodes.new('ShaderNodeMapping'); stm.inputs['Scale'].default_value = (6.0, 6.0, 0.4)
            nt.links.new(oc.outputs['Object'], stm.inputs['Vector']); nt.links.new(stm.outputs['Vector'], st.inputs['Vector'])
            str_ = nt.nodes.new('ShaderNodeMapRange'); str_.inputs['From Min'].default_value = 0.45; str_.inputs['From Max'].default_value = 0.75
            str_.inputs['To Min'].default_value = 1.0; str_.inputs['To Max'].default_value = 0.88
            nt.links.new(st.outputs['Fac'], str_.inputs['Value'])
            g1 = nt.nodes.new('ShaderNodeMath'); g1.operation = 'MULTIPLY'
            nt.links.new(grad.outputs['Result'], g1.inputs[0]); nt.links.new(str_.outputs['Result'], g1.inputs[1])
            gm = nt.nodes.new('ShaderNodeMix'); gm.data_type = 'RGBA'; gm.blend_type = 'MULTIPLY'; gm.inputs['Factor'].default_value = 1.0
            nt.links.new(base_out, gm.inputs['A']); nt.links.new(g1.outputs[0], gm.inputs['B'])
            base_out = gm.outputs['Result']
        nt.links.new(base_out, bsdf.inputs['Base Color'])
        nt.links.new(rough_out, bsdf.inputs['Roughness'])
        if name == 'Lantern':  # lit paper lantern (Unreal: emissive = BaseColor x strength)
            nt.links.new(base_out, bsdf.inputs['Emission Color'])
            bsdf.inputs['Emission Strength'].default_value = 2.0
        if name == 'Paper':   # a little light through the shoji paper
            bsdf.inputs['Transmission Weight'].default_value = 0.0
            bsdf.inputs['Subsurface Weight'].default_value = 0.15
