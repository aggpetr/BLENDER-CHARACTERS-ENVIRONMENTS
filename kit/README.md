# Edo house kit (work in progress: stage 2 prototype)

## Use it in Blender (5.2)

1. Open `kit/Edo_Kit.blend`. The textures must be in `kit/textures/` next to it (see "Textures" below).
2. Select any mesh object (an empty mesh is fine), add a **Geometry Nodes** modifier and pick **GN_EdoKitHouse**.
3. Set **Ground** to the terrain object the house stands on, then the house parameters:

| Input | Meaning |
|---|---|
| Ground | Terrain object. Floor = highest ground under the post grid + 1.30 m; stilts, footings, steps, fence and props follow it |
| Bays X / Bays Y | Size in bays (1 bay = 1.82 m). Bays Y up to 6 |
| Floors | 1 or 2 (2 builds the upper walls; the pent roof comes in a later stage) |
| Roof | 0 none, 1 tile hip, 3 tile hip (2 thatch: later stage, uses tiles for now) |
| Engawa | Veranda with railing and steps on the front (-Y) side |
| Fence | 0 none, 1 board fence (2 stone wall: later stage) |
| Props | Amount of barrels, jars, rice bales and firewood along the back and sides |
| Seed | Picks the wall layout, footing stones and props |
| Realize | Output real geometry instead of instances (needed to export one merged mesh) |

The object's origin is the centre of the house footprint; the front (door, engawa) faces -Y.
To use the kit in another .blend, append the node group `GN_EdoKitHouse` (its `KIT_*` collections come with it).

## Unreal Engine

- `kit/export/modules/KIT_*/SM_Edo_*.fbx`: one mesh per module, origin at the module's pivot, metric scale, smoothing groups and tangents.
  Import with "Build Nanite" on; materials are named `M_Edo_*`.
- `kit/export/SM_Edo_House_dwellA_4x3_test.fbx`: one merged dwellA house for a quick look.
- Textures: `T_Edo_<Set>/BaseColor` (sRGB), `Normal_DX` (DirectX, Unreal's convention, no flip needed), `ORM` (R = AO, G = Roughness, B = Metallic; set sRGB off).
- Placement data for rebuilding the village from modules (the manifest) and an import helper come in a later stage.

## Rebuild from scratch

```
python -I tools/kit/make_textures.py <repo_root> kit/textures     # needs bpy 5.2 (pip install bpy==5.2.2)
python -I tools/kit/build_kit.py kit/Edo_Kit.blend
python -I tools/kit/export_fbx.py kit/Edo_Kit.blend kit/export
```

## Module conventions

- Metres, Z up. Wall-like modules face their exterior toward local -Y.
- Origin on the floor top of the storey a module belongs to (footings, fence and props: on the ground).
- Bay modules are centred on their bay; roof modules come per depth (`_D1` to `_D6` = short side in bays).
- Collection children are named so that alphabetical order is the variant index the geometry nodes use.
