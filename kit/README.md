# Edo house kit

## Use it in Blender (5.2)

1. Open `kit/Edo_Kit.blend`. Its textures are in `kit/textures/` next to it (keep the folder structure).
2. Select any mesh object (an empty mesh is fine), add a **Geometry Nodes** modifier and pick **GN_EdoKitHouse**.
3. Set **Ground** to the terrain object the house stands on, then the house parameters:

| Input | Meaning |
|---|---|
| Ground | Terrain object. Floor = highest ground under the post grid + Raise + 0.18 m (1.30 m by default); stilts, footings, steps, fence and props follow it |
| Bays X / Bays Y | Size in bays (1 bay = 1.82 m). Bays Y up to 6 |
| Floors | 1 or 2 (2 adds the upper storey and the pent roof ring) |
| Roof | 0 none, 1 or 3 tile hip roof, 2 thatched gable roof |
| Engawa | Veranda with railing and steps on the front (-Y) side |
| Balcony | Upper-floor balcony on the front (Floors 2) |
| Shopfront | Noren curtain over the door and a hanging sign |
| Lanterns | Paper lanterns either side of the door (lit) |
| Fence | 0 none, 1 board fence, 2 stone compound wall |
| Gate | Roofed gate in the front opening of the fence |
| Raise | Stilt height (default 1.12 as in the original) |
| Props | Amount of barrels, jars, rice bales and firewood along the back and sides |
| Seed | Picks the wall layout, footing stones and props |
| Realize | Output real geometry instead of instances (needed to export one merged mesh) |

The object's origin is the centre of the house footprint; the front (door, engawa) faces -Y.
To use the kit in another .blend, append the node group `GN_EdoKitHouse` (its `KIT_*` collections come with it).

## Install everything in your village .blend (Blender)

1. Pull the repo branch; keep the `kit/` folder together (the `.blend` finds `kit/textures/` next to it).
2. Open your village `.blend`. In the Text Editor open `tools/kit/install_kit.py`, set `KIT_PATH` at the top to the
   full path of `kit/Edo_Kit.blend`, and click Run Script. It is safe to run again later: each run replaces the previous
   kit install.

It (1) refreshes the kit data, (2) makes a kit twin `<name>_KIT` of every generated house in the collection `KIT_Village` and
hides the original, (3) creates the new plaza district `EdoKitVillage_01`, (4) creates the district streets as curves with your
own `GN_EdoRibbon` group, joined to the existing town streets and the mountain trail, (5) hides the old compound village
`EdoVillage_01` and its lights and adds point lights for the new lanterns (collection `EDO_KitLights`).

### The plaza district (`GN_EdoKitVillage`)

A round plaza (radius 20 m, centred at x -48, y -122) with a well, stone lanterns, benches and a notice board; one very big
hall (13 x 8 bays, two storeys, stone compound wall and gate) on the east side facing the plaza on the axis of the west entrance;
shops, tea houses and restaurants around the plaza; a second ring of dwellings, farmhouses and huts; a small hamlet along the
north street. Streets: ring street, outer ring street, the west street (continues your `RD_VillageRoad`), north-west and
south-west streets (continue `RD_Lane1`/`RD_Lane2`), the trail to the mountain hub (joins `PATH_hub_p2`), the north street.
The houses are nested `GN_EdoKitHouse` nodes inside the group (open `GN_EdoKitVillage`: every house is a labelled group node
whose Bays/Floors/Roof/... you can change); the plaza radius is a modifier input. Move the object `EdoKitVillage_01` to move
the whole district. The layout comes from `tools/kit/district.py` (`python tools/kit/plot_plan.py out.png` draws the plan).

## Rebuild your village with the kit (Blender), manifest only

Open your village .blend, open `tools/kit/village_build.py` in Blender's Text Editor, set `KIT_PATH` at the top to
`kit/Edo_Kit.blend`, and run it. Every `GN_EdoHouse` house gets a kit twin in the collection `KIT_Village` with the same
transform, terrain and parameters; the originals are hidden, not deleted.

## Unreal Engine

- `kit/export/modules/KIT_*/SM_Edo_*.fbx`: one mesh per module with its `UCX_` collision, origin at the module's pivot,
  metric scale, smoothing groups and tangents. Import with "Build Nanite" on; material slots are named `M_Edo_*`.
- `kit/export/SM_Edo_House_dwellA_4x3_test.fbx`: one merged dwellA house for a quick look.
- Textures: `T_Edo_<Set>/BaseColor` (sRGB), `Normal_DX` (DirectX, Unreal's convention, no flip needed), `ORM` (R = AO, G = Roughness, B = Metallic; sRGB off).
- `tools/kit/unreal_import.py` (run in the Unreal editor, **untested**): imports textures and meshes, builds a master material
  (with the moss blend) and instances, imports the plaza and street meshes of the district
  (`kit/export/district/`, world space, placed at the origin), and can place houses from `kit/village/village_manifest.json`
  (the 94 town houses plus the 37 district entries `DISTRICT_*`) with lantern lights. Set `KIT_DIR`, then the flags at the top
  (`HOUSES = ['DISTRICT_*']` places only the new district). Bring the terrain over from Blender with the same world origin.
- To refresh the manifest and the district ground after changing the village in Blender: run `tools/kit/village_build.py`
  (manifest) and `tools/kit/export_district_ground.py` (plaza and streets) in your village file.

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
