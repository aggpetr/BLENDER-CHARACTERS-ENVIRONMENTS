# Edo village house kit: analysis (stage 1)

Source: `Feudal_Japan4 - Copy.blend` (Blender 5.2.2, opened headless with `bpy` 5.2.2).
Target: Unreal Engine 5.8, PC (from `Target_Engine_UnrealEngine5.8_PC.txt`).
Nothing in the .blend was modified. Scripts are in `scripts/`, raw data in `data/`.

## 1. What the scene contains

| Item | Count |
|---|---|
| Objects | 265 (131 mesh, 13 curve, 120 light, 1 camera) |
| Houses (`GN_EdoHouse` modifier) | 94 |
| Road/water ribbons (`GN_EdoRibbon`) | 13 |
| Village generator (`GN_EdoVillage`) | 1 |
| Node groups | 37 (`GN_EdoHouse` alone has 599 nodes, 36 sub-groups) |
| Materials | 17 |
| Images | 0 real (only Render Result / Viewer Node) |
| UV maps on any house | **none** |
| Embedded scripts | `edo_village_tools.py` (42 KB, builds the village/cluster solver node trees), `edo_lights_sync.py` (turns lantern marker points into 120 point lights) |

Collections: Town 51 houses, Farms 21, Kit 16, Mountain 5, Generator 1.

## 2. The house generator (`GN_EdoHouse`)

33 inputs. The ones that shape a house:

| Group | Input | Range | Used values in village |
|---|---|---|---|
| Size | Bays X / Bays Y | 1-14 / 1-16 | X: 2,3,4,5,6,7,9. Y: 2,3,4,6 |
| Size | Floors | 1-5 | 1 or 2 |
| Size | Bay Scale | 0.6-2.0 | always 1.0 |
| Size | Raise (stilt height) | 0-5 | 1.12 (93 of 94) |
| Style | Roof | 0-3 | 1 (30), 2 (27), 3 (37) |
| Style | Shopfront | bool | 21 houses |
| Style | Seed | 0-100000 | 93 distinct values |
| Details | Engawa / Balcony / Lanterns / Gate | bool | 40 / 16 / 29 / 2 |
| Details | Fence | 0-2 | 0 (50), 1 (42), 2 (2) |
| Weathering | Wear | 0-1 | 1.0 (93 of 94) |
| Weathering | Props | 0-1 | 1.0 (69), 0.2 (14), 0.3 (8), 0.6 (3) |
| | Roof Detail | 0.1-1 | 0.2 (93 of 94) |

The "Cluster (set by village)" inputs (offset, angle, keepouts, ...) are all at defaults on the house objects. They are driven by the village and compound node groups, not by the house modifiers.

### The 94 houses are only 17 designs

Each archetype name maps to exactly one structural parameter set; the Seed is the only per-house difference inside an archetype.

| Archetype | n | Bays | Floors | Roof | Extras | Fence | Median tris | Median size (m, WxDxH) |
|---|---|---|---|---|---|---|---|---|
| kura (storehouse) | 14 | 2x2 | 2 | 3 | | 0 | 12,446 | 6.5 x 6.3 x 9.3 |
| shopA | 13 | 3x3 | 1 | 1 | Shopfront, Lanterns | 0 | 15,002 | 9.1 x 9.1 x 6.6 |
| dwellA | 11 | 4x3 | 1 | 1 | Engawa | 1 | 23,712 | 12.0 x 11.9 x 6.9 |
| farmhouse | 9 | 5x3 | 1 | 2 | Engawa | 1 | 19,462 | 11.6 x 13.9 x 9.3 |
| dwellB | 9 | 4x3 | 2 | 3 | Balcony | 1 | 29,112 | 11.9 x 12.0 x 10.4 |
| barn | 8 | 3x4 | 1 | 2 | | 0 | 8,026 | 10.2 x 8.9 x 8.8 |
| dwellC | 7 | 3x3 | 1 | 3 | Engawa | 1 | 20,318 | 10.3 x 11.5 x 7.2 |
| hutB | 3 | 4x3 | 1 | 2 | Engawa, Lanterns | 1 | 17,012 | 11.5 x 12.1 x 9.3 |
| restA | 3 | 5x4 | 1 | 1 | Shopfront, Engawa, Lanterns | 0 | 24,464 | 13.2 x 12.4 x 7.4 |
| shopB | 3 | 3x4 | 2 | 3 | Shopfront, Balcony, Lanterns | 0 | 24,312 | 10.6 x 10.3 x 9.8 |
| tea | 3 | 3x3 | 1 | 2 | Engawa, Lanterns | 0 | 9,926 | 9.5 x 10.2 x 8.8 |
| hutA | 2 | 3x3 | 1 | 2 | Engawa | 1 | 13,434 | 10.9 x 10.9 x 9.3 |
| hutC | 2 | 3x2 | 1 | 2 | | 0 | 5,658 | 7.7 x 7.4 x 8.1 |
| inn | 2 | 9x6 | 2 | 1 | Engawa, Balcony, Lanterns, Gate | 2 | 81,050 | 21.6 x 18.3 x 11.7 |
| restB | 2 | 6x4 | 2 | 3 | Shopfront, Balcony, Lanterns | 0 | 37,806 | 13.0 x 12.9 x 10.2 |
| row (rowhouse) | 2 | 7x2 | 1 | 3 | | 0 | 19,509 | 11.8 x 11.8 x 6.4 |
| (EdoHouse_01, generator test) | 1 | 4x3 | 2 | 1 | | 1 | 20,032 | 12.0 x 11.1 x 10.3 |

## 3. Measured module sizes

From a one-parameter-at-a-time sweep on a test house (`scripts/sweep.py`):

- **Bay width: about 1.81 m** (footprint grows 1.81 m per bay in X and Y). That is one Japanese *ken* (1.818 m), so a 1 ken grid is the natural kit module.
- **Floor height: about 3.14 m** per floor.
- A fixed ~2.5 m of eave/overhang is added on top of the bay count, and the Raise input adds stilt height.
- **The Seed jitters the footprint by roughly 0.3 m and the triangle count by about 1,200**, so two houses of the same archetype are not identical. A kit would replace this jitter with fixed, grid-snapped modules.

## 4. Where the triangles go (current procedural geometry)

Delta tris vs a 3x3, 1-floor, Roof 1 base house of 12,528 tris:

| Change | Delta tris |
|---|---|
| **Roof Detail 0.1 / 0.5 / 1.0** (village uses 0.2) | -3,000 / +23,040 / **+104,160** |
| Gate | +15,018 |
| Fence 1 / Fence 2 | +4,824 / +1,564 |
| +1 bay in X or Y | about +1,500 to +1,900 |
| +1 floor | about +3,400 to +4,200 |
| Engawa | +1,428 |
| Props 0.5 / 1.0 | +624 / +1,936 |
| Lanterns | +640 |
| Shopfront | +120 |

Roof tiles are real modeled geometry and Roof Detail is by far the largest cost. Whole village: **1.84 M triangles in 94 houses** (min 5,208, median 18,770, max 81,442).

Unverified in the sweep: Balcony showed no change on a 1-floor house (probably needs 2 floors), and Roof 1 and Roof 3 gave the same triangle count with slightly different dimensions. I have not yet visually confirmed what each Roof value looks like.

## 5. Materials

17 materials, **all procedural, no image textures**. The house materials (Timber, Plaster, Stone, Thatch, Tile) are a Principled BSDF mixed by the mesh `Color` vertex attribute (via Attribute, Separate Color, Math, Mix nodes). Paper, Cloth, Lantern and Sign are flat Principled materials. Because the houses have no UVs, none of this exports to Unreal as-is: the materials and the vertex-color masks both have to be rebuilt as real texture-based PBR with UVs.

House attributes available: `position`, `sharp_face`, `sharp_edge`, `edo_base_z`, `material_index`, `Color`.

## 6. What this means for the kit

- 17 designs is a small set to cover. Most of the 94 houses are repeats of 8 archetypes (kura, shopA, dwellA, farmhouse, dwellB, barn, dwellC plus small groups).
- Grid: 1 ken (1.818 m), 3.14 m floor height.
- No UVs and no textures means texturing, UV layout and baking are the bulk of the new work.
- The current meshes are unoptimized: roofs and detail are real geometry, nothing is shared or instanced.

## 7. Decisions needed before building (asset details)

To be agreed before stage 2:

1. Triangle budget per module, and whether to rely on Nanite for roofs.
2. Texel density, texture resolution, trim sheet vs atlas layout.
3. Module list and split (wall bays, corners, window/door variants, roof sections, eaves, engawa, balcony, gate, fence, props).
4. LOD and collision strategy; lantern light handling.
5. Whether to keep the procedural variation (seed jitter) or fix it.
6. Which house roofs / styles to prioritise for the first prototype.
