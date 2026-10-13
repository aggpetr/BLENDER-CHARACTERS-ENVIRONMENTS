# Edo house kit: status report

All 17 original house designs now build from kit modules with the new geometry nodes `GN_EdoKitHouse`, and the whole
village (94 houses) has been rebuilt in place from the kit. Stage 2 details (dwellA prototype) are in `STAGE2_REPORT.md`.

## Contents

| Item | Where |
|---|---|
| Kit scene: 86 modules in `KIT_*` collections, 12 materials, `GN_EdoKitHouse`, test houses, all 17 house types (`ARCH_*`) | `kit/Edo_Kit.blend` |
| Textures: 12 sets, 4K (Cloth 2K, Paper/Stone 2K, Ceramic/Lantern 1K), BaseColor + Normal_DX + ORM, JPG | `kit/textures/` |
| One FBX per module with `UCX_` convex collision (82 of 86 modules; cloth, lanterns, sign and brackets have none) | `kit/export/modules/` |
| Merged dwellA test house | `kit/export/SM_Edo_House_dwellA_4x3_test.fbx` |
| Village manifest: 94 houses, their parameters, 17,561 module instances (world transforms), 58 lantern light positions | `kit/village/village_manifest.json` |
| Floor height check, original vs kit, all 94 houses | `kit/village/village_floor_check.json` |
| Renders | `kit/previews/` |
| Unreal Engine import helper (untested) | `tools/kit/unreal_import.py` |
| Rebuild the village in your own .blend | `tools/kit/village_build.py` |

## Modules

Foundation (footing stones x3, stilts x3 lengths), floor beam, floor deck, storey post, 5 wall bays (plaster, lattice window,
sliding door, shoji, plain plaster), tile hip roof (end / apex end / mid / finial, for short sides of 1-6 bays), pent roof (side,
corner), thatched gable roof (end with gable wall, ridge log and crossed finials / mid, depths 1-6), engawa deck and posts,
railing (bay, open, end, post), steps (2-14 risers), balcony bracket, board fence (segment, post), stone compound wall
(segment, pier), roofed gate, noren, shop sign, lantern, props (rice bale, barrel, firewood, jar).

## GN_EdoKitHouse inputs

Ground, Bays X (1-9), Bays Y (1-6), Floors (1-2), Roof (0 none, 1/3 tile hip, 2 thatch), Engawa, Balcony, Shopfront,
Lanterns, Fence (0/1 boards/2 stone wall), Gate, Props, Raise, Seed, Realize.

## Checks

- **Same place as the original:** every one of the 94 kit houses uses its original object transform, terrain object and seed.
  Floor height differs from the original by at most 1.5 cm (mean 0.8 cm).
- Terrain: floor = highest ground under the post grid + Raise + 0.18 m (the original rule); stilts, footings, engawa posts,
  steps (riser count), fence and wall segments and props follow the terrain.
- FBX round trip (re-import in Blender): triangle counts, dimensions, scale 1.0, UVs and material slots preserved.

## Triangles per house (kit, whole house incl. fence and props)

| Design | Count in village | Triangles |
|---|---|---|
| hutC | 2 | 5.4-5.6K |
| barn | 8 | 6.8-8.6K |
| tea | 3 | 9.6-10.7K |
| kura | 14 | 11.5-13.1K |
| hutA | 2 | 12.8-13.2K |
| shopA | 13 | 13.2-14.9K |
| hutB | 3 | 15.7-16.0K |
| farmhouse | 9 | 16.9-18.1K |
| dwellC | 7 | 18.7-20.1K |
| row | 2 | 19.2-19.8K |
| dwellA | 11 | 21.4-23.4K |
| restA | 3 | 23.3-25.4K |
| shopB | 3 | 23.2-25.0K |
| dwellB | 9 | 26.3-29.1K |
| restB | 2 | 33.7-35.6K |
| inn | 2 | 69.7-71.8K (roof 22K, 40 stone wall segments) |

Whole village: 1.74 million triangles from 86 reusable meshes (original: 1.84 million unique triangles, no UVs).

## Not verified here (no Unreal in this environment)

- The Unreal import script, material graph, Nanite build, collision behaviour, performance.
- Appearance under Unreal lighting. The renders are Blender Cycles.

## Known limits

- Upper-storey windows use the same wall modules as the ground floor; there are no interiors (doors and windows are closed).
- Moss and plaster grime are material effects (in Blender and in the Unreal master material), not baked into the textures.
- The fence plot is whole bays (1 bay at the sides and back, 2 at the front), slightly different from the original plot size.

## Plaza district (replaces the old compound village)

`EdoVillage_01` (7 compounds of up to 5 houses, set by hand-entered positions) is replaced by `EdoKitVillage_01`, built by the
node group `GN_EdoKitVillage` from kit houses: 36 houses, the plaza and its furniture, in 7,413 module instances / 664K triangles.
Houses: 1 hall (13 x 8 bays, 2 storeys, roof depth 8), 12 around the plaza, 19 in the outer ring, 4 along the north street.
The layout is planned by `tools/kit/district.py` (no plot overlaps, no plot on a street; checked in code), relative to the plaza
centre, so the district can be moved as one object. Streets are built with the existing `GN_EdoRibbon` group and end exactly at
the end points of the town streets (`RD_VillageRoad`, `RD_Lane1`, `RD_Lane2`) and the trail (`PATH_hub_p2`); ground is flat
(-0.05 m) across the district and all three ground objects agree there, so houses, plaza and streets meet the terrain cleanly.

Added to the kit for this: roof modules for depths 7 and 8, bays up to 16, `Offset`/`Angle` inputs on `GN_EdoKitHouse`, plaza
furniture (stone lantern, well, bench, notice board), 103 FBX files in total, district plaza and street meshes
(`kit/export/district/`), and district entries (`DISTRICT_*`) in the village manifest (131 houses, 24,974 module instances).

## District update: outward streets, hospital, props per house type

- **Streets:** four more streets leave the outer ring (east, south, west-north-west, south-west, 4-5 m wide, ending in open
  terrain where the ground is flat to gently sloped) plus a hospital street. 13 street curves in total.
- **Hospital (north-west, `HOSP`, `HOSP_W`, `HOSP_E`):** main building 16 x 6 bays, one storey, tile hip roof, about 29 m wide and
  about 8 m high, board-fence court with gate; two wards of 7 x 3 bays. The district now has 33 planned slots (the new streets
  and the hospital take the room of three ring houses and part of the north hamlet); manifest: 128 houses, 25,994 module instances.
  The position is the constant `HOSPITAL_C` in `tools/kit/district.py`.
- **Props per house type:** new input `Category` (0-9) on `GN_EdoKitHouse`; 31 modules in 9 collections `KIT_Cat*` (restaurant,
  smith, tea, shop, store, farm, inn, clinic, home), listed in `kit/README.md`. Three new texture sets: `T_Edo_Iron` (1K, metallic),
  `T_Edo_Leaf` (1K), `T_Edo_ClothRed` (2K). The 17 town designs and the new designs smithy, clinic, ward and hospital carry a
  category (`tools/kit/archetypes.py`); `install_kit.py` and `village_build.py` match each town house to its design.
  FBX: 136 files; thin or hanging props (laundry, drying and herb racks, sword and axe racks) have no collision, the parasol has box collision.
- Checks: floor height of all 94 town houses still within 1.5 cm of the originals; install is idempotent.
- Not verified: Unreal import (script untested), the category props on every town house yard (clutter with neighbours possible; set
  `CATEGORY_PROPS = False` to switch off).

## Town extension (streets, farms, fields, canal banks, bridges, props)

- **Answer to "have you made ultra quality versions of the bridges, benches and other existing props?"**: before this update only the plaza
  furniture of the new district existed in the kit (stone lantern, well, bench, notice board, 90 to 700 triangles). Your town still used its
  old low-poly props (bench 36 triangles, well 92, stall 84) and bridges (612 to 792 triangles, untextured boxes), and the fields
  were flat meshes (the paddies 6 triangles). Now: 3 bridges (1,650 to 2,000 triangles each), stall (788), bank curb (308), cobble tile
  (about 1,900), 3 boulders, 7 crop modules (140 to 670), ridge and bund, all with UVs and Nanite-ready; `install_kit.py` swaps your
  `PR_*` and `BR_*` objects for them in the same place.
- **Streets:** 7 new streets from your red lines (20 street curves in total).
- **Houses:** 59 in the blue areas and along the new streets (18 farmhouses, 8 barns, 4 kuras, huts, dwellings, 2 smiths). Planned in code
  (no overlaps with your 94 town houses, the district, streets, fields, canal, bridges or props).
- **Fields:** 13 patches (6 farmland, 7 paddies), about 47,000 crop instances.
- **Canal bank:** about 100 sections per side along the canal, gaps at the 4 bridges.
- Manifest: 205 houses, 36,780 module instances (`kit/village/village_manifest.json`), plus `fields_manifest.json`; 154 FBX files; floor
  height of the 94 original houses still within 1.5 cm.
- New texture sets: `T_Edo_Soil`, `T_Edo_Grain` (1K), brighter `T_Edo_Leaf`.
- Not verified: Unreal import (script untested, including the instanced field placement), performance with about 47,000 crop instances
  in the Blender viewport (they are instances, not geometry), appearance under Unreal lighting.
