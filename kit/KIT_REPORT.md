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
