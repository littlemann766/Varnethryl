# Fitted armour (v2 pilot): Darius, plate, all 6 rarities. Awaiting boss approval before roll-out.

These pieces are built from Darius's own rest-pose body mesh (`vmain/voxel/darius_voxel.glb`).
- That file was only read; Lucian's rig and skeleton are not modified.
- The body is voxelised at 1 cm. Each slot's region is picked by dominant bone plus a few geometric limits.
- The shell is the region offset outward by 2 voxels (2 cm). Pauldrons are 3 cm, or 4 cm at legendary and above.
- The shell is smoothed (`bl.smooth_plate`) and keeps the rarity details: trim edges, rivets, lames, chest keel (rare and up), filigree (legendary and up), pauldron flange (legendary and up), molten veins and spikes (masterwork) and battle wear.
- Skin weights come from the 6 nearest body vertices of that slot's bones (top 4, normalised), so each piece deforms with the body as a skinned mesh.

## Files
- `<hero>_<family>_<rarity>_<piece>.glb` and `_lod1.glb` are skinned meshes. Each one also contains a copy of the hero armature.
  - Pieces: chest, belt, shoulder_L/R, glove_L/R, leg_L/R, boot_L/R.
- `<hero>_body_mask.json` holds one cell list per piece (1 cm grid, rest pose).
  - Hide a body triangle when all 3 of its vertices fall in an equipped piece's cells.

Godot reference: `tools/godot/dress.gd` → `attach_fitted()` and `hide_mask()`.
- `attach_fitted()` rebinds the skin by bone name onto the live hero Skeleton3D.
- `hide_mask()` applies the body mask.

The helmet (great helm) and the cloak still use the v1 meshes.

Cost: about 15–60k tris per piece at lod0 (the chest is the heaviest). It still needs decimation before mobile; see `darius_plate_tris.json`.
