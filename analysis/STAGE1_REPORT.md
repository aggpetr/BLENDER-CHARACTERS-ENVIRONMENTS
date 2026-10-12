# Stage 1 report (mechanical setup)

## 1. Placements: houses stay where they are
All 94 houses (`data/placements.json`) were checked in the source .blend:
- no parenting, no animation, no delta transforms
- location z = 0 for every house; only x and y differ
- rotation only about Z, in steps of 90 degrees (-90, 0, 90, 180)
- scale = 1 everywhere

The kit manifest will reuse exactly these x, y and rotation values, so each rebuilt house sits where the original is.

## 2. Ground adaptation (important for the new geometry nodes)
`GN_EdoHouse` reads the terrain through its `Ground` input (72 houses use `EDO_Ground_Town`, 16 `EDO_Ground_KitFlat`,
5 the mountain pads `MT_pad1..5`, 1 `EDO_TestGround_Large`). Measured on `TWN_10_dwellA`:
- raising the object by 3 m moves the evaluated mesh down by 3 m in local space (the house stays at the same world height);
- switching Ground to `EDO_Ground_KitFlat` changes the mesh extent (local z min -1.8 -> -0.36, max 5.14 -> 6.34): floor level and stilt length follow the terrain.

Consequence: the kit foundation needs a variable-length stilt post, and `GN_EdoKitHouse` must sample the same Ground object to set floor level and post length, otherwise houses would not meet the terrain where they did.

## 3. Roof values (confirmed from renders, `roof_values_sheet.png`)
| Roof | Result |
|---|---|
| 0 | No roof (open timber frame, interior beams and partitions visible) |
| 1 | Tile hip roof |
| 2 | Thatched gable roof with ridge log and crossed finials |
| 3 | Tile hip roof, nearly identical to 1 (appears to differ only in the ridge cap) |

Every two-floor house gets a pent tier between the floors, whatever the roof style (including thatch).

## 4. Textures (`tools/prepare_textures.py`, output not committed)
Reads the 7 Poly Haven zips and the loose ambientCG Moss001 files and writes, per set: BaseColor, Normal_DX (green flipped from the
OpenGL normals for Unreal), Roughness, Height, AO (derived from the height map, tile-safe; Moss001 uses its own AO) and a packed ORM
(R=AO, G=Roughness, B=0). `roof_tiles` is recoloured to dark grey and `stacked_stone_wall` desaturated. Ran on all 8 sets, all 4096x4096;
average normal z between 0.84 and 0.99. The prepared set is about 745 MB, so it is generated on demand rather than committed
(`texture_prep_check.png` shows a sample).
Notes: `reed_roof_03` has a non-seamless ridge band along its top edge (to be used as trim); `grey_roof_01` is a flat shingle pattern and
is kept as a colour and weathering reference; Moss001 licence still to be confirmed on its page.
