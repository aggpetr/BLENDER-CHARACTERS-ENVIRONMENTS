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
| Category | Props for the type of house (see below): 0 none, 1 restaurant, 2 weapon smith, 3 tea house, 4 shop, 5 storehouse, 6 farm, 7 inn, 8 clinic / hospital, 9 home |
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

### Props per house type (`Category`)

Every category has its own collection of small modules (`KIT_Cat*`, 31 meshes, 90 to 3,100 triangles each) that the node group
places in the yard, relative to the house footprint and on the terrain:

| Category | Props |
|---|---|
| 1 Restaurant | dining sets (low table, two benches, bowls, teapot), kamado furnaces with rice pot and chimney, food stall (only with a fenced yard) |
| 2 Weapon smith | forge with hood and bellows, anvil on a log stump with hammer, grindstone with water trough, quench tub, katana display rack (sheathed swords and one bare blade), axe rack (felling axes, hatchets). Swords and axes only |
| 3 Tea house | red parasol over a bench, low tea table with stools and cups, kettle stove with cup shelf |
| 4 Shop | market stand with indigo awning and baskets, open goods shelf (cloth, jars, bowls), crates with sack and barrel |
| 5 Storehouse (kura) | pyramid of rice bales on a pallet, hand cart with a load, row of storage jars |
| 6 Farm | rice drying rack (hazakake), haystack, tool rack (hoe, rake, scythe), water trough |
| 7 Inn | horse hitching rail, palanquin (kago), goemon bath (iron tub on a clay stove) |
| 8 Clinic / hospital | herb drying rack, yagen herb grinder, stretcher with futon, decoction stove with medicine pot and jars, raised herb bed |
| 9 Home | laundry pole, stone water basin, small garden (pine, rocks) |

`install_kit.py` sets the category on the kit twins of your town houses by matching their parameters to the 17 designs
(`kit/archetypes.json`), and the district planner sets it per slot. Set `CATEGORY_PROPS = False` at the top of
`install_kit.py` (and `village_build.py`) if you do not want the extra props on your town houses. The props are normal kit
modules (iron, leaf and red cloth are three more texture sets: `T_Edo_Iron`, `T_Edo_Leaf`, `T_Edo_ClothRed`).

### The plaza district (`GN_EdoKitVillage`)

A round plaza (radius 20 m, centred at x -48, y -122) with a well, stone lanterns, benches and a notice board; one very big
hall (13 x 8 bays, two storeys, stone compound wall and gate) on the east side facing the plaza on the axis of the west entrance;
shops, tea houses and restaurants around the plaza; a second ring of dwellings, farmhouses, huts, weapon smiths and a clinic; a small
hamlet along the north street; and in the north-west a hospital compound: a wide, low main building (16 x 6 bays, one storey,
board-fence court with gate, herb racks, stretchers, decoction stoves) with a ward on each side, reached by its own street.
Streets: ring street, outer ring street, the west street (continues your `RD_VillageRoad`), north-west and south-west streets
(continue `RD_Lane1`/`RD_Lane2`), the trail to the mountain hub (joins `PATH_hub_p2`), the north street, the hospital street, and
four streets leaving the outer ring towards the surroundings (east, south, west-north-west, south-west).
The houses are nested `GN_EdoKitHouse` nodes inside the group (open `GN_EdoKitVillage`: every house is a labelled group node
whose Bays/Floors/Roof/... you can change); the plaza radius is a modifier input. Move the object `EdoKitVillage_01` to move
the whole district. The layout comes from `tools/kit/district.py` (`python tools/kit/plot_plan.py out.png` draws the plan).

### Town extension (streets, houses, farms, fields, canal banks, bridges, props)

`install_kit.py` also builds the town extension (set `TOWN_EXTENSION = False` at the top to skip it). It is planned by
`tools/kit/town.py` from `kit/village/town_context.json` (roads, streams, fields, props and bridges extracted from your village
file by `tools/kit/extract_context.py`) and written to `kit/village/town_layout.json`. `python tools/kit/plot_town.py out.png` draws it.

| Part | What it is |
|---|---|
| Streets | 11 more streets (`KITROAD_T_*`, built with your `GN_EdoRibbon`): west outer street, north link, field ring, hospital link, two southern lanes, east link, a link joining the south-west street to `RD_Lane2`, and three streets from the district towards the mountain trail: `EAST_TRAIL` (joins `PATH_p2_p3`), `NE_ROAD` (joins `PATH_p3_p4`) and `SE_ROAD`. Streets east of x = 62 follow the full `EDO_Terrain` |
| Houses | `EdoKitTown_01` (node group `GN_EdoKitTown`) and `EdoKitTownOuter_01` (`GN_EdoKitTownOuter`, houses beyond x = 62 on the full terrain; one labelled `GN_EdoKitHouse` node per house): 91 houses in your marked areas and along the new streets (the outer streets are lined with farmhouses, huts, barns and kuras wherever the ground is not steeper than about 3.6 m across the plot), plus barns, kuras, huts, dwellings, 2 weapon smiths, all with their category props |
| Fields | `EdoKitField_*` (node group `GN_EdoKitField`: Size X / Size Y / Crop 0 vegetables, 1 barley, 2 rice paddy with bunds). 6 farmland patches and 7 paddies from your `LD_Field*` / `LD_Paddy*` meshes (their crop meshes are hidden, soil and water stay). About 47,000 crop instances from 7 crop modules (cabbage x2, daikon, barley x2, rice x2), ridges and bunds |
| Canal bank | `KITEMBANK_Canal` (node group `GN_EdoKitEmbank`) along the vertical canal at x = -178: ashlar curb on both banks, 2 x 2 m cobblestone tiles (individual stones) 4 m wide on each side, scattered boulders; no bank where the bridges are |
| Bridges | `BR_*` replaced by kit bridges (`BR_*_KIT`): 2 timber bridges (4.0 and 6.4 m wide, stone abutments, beams, planks, balustrade with onion caps) and the stone arch bridge (18 m, cobbled deck, parapets). Originals are hidden, not deleted |
| Border | `EdoKitBorder_01` (`GN_EdoKitBorder`): standing stones with a sacred rope around the village, torii gates north / west / south, open gaps where trails cross, the river as the south border (widened to 12 m). `VILLAGE_BORDER = False` in `install_kit.py` skips it |
| Props | your 12 `PR_*` props replaced by kit modules (well, notice board, stall, bench, stone lantern); originals hidden |

Unreal: the manifest has `TOWN_*`, `BRIDGE_*` and `PROP_*` entries; fields and canal bank are in `kit/village/fields_manifest.json`
(per module: `[x, y, z, yaw, sx, sy, sz]`) and are placed as hierarchical instanced meshes with `PLACE_FIELDS = True` in
`tools/kit/unreal_import.py` (untested).

## Rebuild your village with the kit (Blender), manifest only

Open your village .blend, open `tools/kit/village_build.py` in Blender's Text Editor, set `KIT_PATH` at the top to
`kit/Edo_Kit.blend`, and run it. Every `GN_EdoHouse` house gets a kit twin in the collection `KIT_Village` with the same
transform, terrain and parameters; the originals are hidden, not deleted.

## Unreal Engine

**Full guide: `docs/Edo_Village_Unreal_Guide.md` (and `.pdf`)**: terrain, import, lights, World Partition, instancing, collision, navigation, terrain blending.
Extra tools: `export_heightmap.py` (Landscape heightmap, `kit/export/terrain/`), `cluster_lights.py` (30 real lights instead of 108, `kit/village/lights_clustered.json`),
`md_to_pdf.py`. Planned additions (not built): `kit/previews/village_additions_plan.jpg`, data in `tools/kit/additions.py`.

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
