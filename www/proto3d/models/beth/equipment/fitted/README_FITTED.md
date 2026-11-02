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

## v3 (Darius only): fixes for the open issues on the pilot
1. **Triangle budget.** The high-poly fitted shell is decimated to 3.5–8k tris per piece (helm 8000, chest 6988, shoulders 5000, belt 4495, legs 4480, cloak 3995, boots 4000, gloves 3500). lod1 is 45% of High.
   - Colour is now a baked albedo texture embedded in the glb, not vertex colour: 512 px for helm, chest and cloak, 256 px for the rest. The bake is Cycles, emission, selected-to-active.
   - Keep `vertex_color_use_as_albedo` and `vertex_color_is_srgb = true`. With no COLOR_0 the vertex colour is white, so the baked texture shows. `dress.gd mat_fix` copies `albedo_texture` across.
2. **Helm and cloak are fitted, skinned pieces.**
   - Helm: a great helm fitted per height to Darius's head and beard.
     - Every tier: 3 cm wall, recessed black eye slits.
     - Common and up: a bright lip round the slits and a raised visor plate. Rare and up: breaths, a gold cross and a brow band.
     - Epic and up: horns. Legendary and up: crest. Masterwork: dark horns and molten veins.
   - Cloak: built from the cape bones plus the cape cloth near the top (cape-weight ≥ 0.15). It floats 3–4 cm off the back so it clears the back plate.
3. **Gaps closed.** A couter on the gloves (upper arm from t > 0.66) overlaps the rerebrace, and a poleyn on the legs (shin to t < 0.24) overlaps the 3 cm greave. There's a morphological close plus a 5-pass smooth, with leather straps on the backs of the arms and thighs, and the rivets and lames kept.
4. **Tabard.** The belt now has faulds down to 17 cm below the belt plus a front tasset. The body mask also hides the tabard strip between the thighs.
5. **Dark rod.** It was the baked sword on hand_R. The pieces are now fitted to, and rendered on, Lucky's weaponless rig `voxel/darius_voxel_noweapon.glb` (weaponless-rigs @ af4e553, read-only copy). Set `job.rig` to it. The skeleton is identical.

## v4 (Darius): helm and cloak polish
- **Helm:** the per-height ellipse is now fitted to the skull only (head/jaw/eye-weighted cells) at the 93rd percentile with no air gap, and it keeps straight cheeks below the skull. It is noticeably slimmer and shorter from behind. The beard and hair sit under the helm and are hidden by the helm mask. Eye slits and all tier details are kept. Each rarity is about 8000 tris, with lod1 at 45%.
- **Cloak:** a mantle and collar run from the cape top up to the neck and out to the shoulder edge, behind the body only. The trim is now just a gold hem. No plate or purple shows where it meets the pauldrons in walk or attack. About 4000 tris, lod1 at 45%.

## v5: all 8 heroes
Fitted sets now exist for darius (plate, on the weaponless rig), orin (plate), rook (scale), finn and elira (chain), wren (leather), and rowan and talia (cloth, robed).
- Every piece uses the proficient family from MAPPING and comes in all 6 rarities.
- Robed casters keep their robe: no chest or leg pieces, a cowl with an open face (no visor or horns), a thin mantle, cuff-only gloves, and a sash belt.
- Chain, scale and leather pieces get the family surface (`armor3d.skin`).
- The front direction is now taken from the feet, because most rigs have no eye or jaw bones.
- Small loose bits are dropped from every piece except the helm.
- The cloak is limited to the back half, and its shell is closed, which fixed the light speck on Darius's back.
Each hero folder has its own `<hero>_body_mask.json` and `<hero>_<fam>_tris.json`.

## v7 (all heroes)
- Helm centred on the modelled head's own cells on rigs without jaw bones (Rook/Talia head bones sit 15-19 cm behind the face); ellipse fit at 100th pct; mask hides every body cell inside the helm envelope -> no faces under helms/hoods.
- Robed (Rowan/Talia): no close(), no shoulder ridges/flare/spikes -> slimmer mantles.
- Non-robed legs: mask hides skirt/tabard flaps the rigs weight to thigh/shin (>11.5 cm off the bone) that swung loose in attack1.
- Thin pieces subdivided before decimate -> every High piece >= 3538 tris; lod1 = 45%.

## v8 rebuild (all heroes) — replaces the v7 "barrel" helms
- Helms: skull-fitted egg/dome profile (front/back radii fitted separately, crown leans back), wall allowed over body cells (no holes), body masked inside.
  - plate/leather: great helm to the chin, recessed eye slit, raised brow band, face keel, breaths, riveted rim.
  - chain/scale: pointed bascinet + flared mail aventail to the shoulders.
  - cloth: open cowl with oval face opening, black shadow, pointed back.
  - rare+: comb crest (taller per tier); epic+: horns; legendary gold trim; masterwork blackened + molten.
- Armour: shoulder wall 2 vox; overlapping lame lips with domed rivets (plate/scale/leather; pauldrons/sabatons on all), couters/poleyns over elbow/knee, raised leather buckle straps. Robed sets keep no chest/leg plate.

## v9 (orin, rook, finn, elira, wren, rowan, talia; Darius kept at approved v8)
- Aventail (Finn/Elira/Rook): riveted-ring mail pattern, gold lower edge on legendary, molten glints on masterwork.
- Helm mask reaches 9 vox out and 8 vox under the rim on armoured heroes (Wren's blue collar/specks hidden).
- Very wide heads (Rook) fit at the 84th percentile -> snug helm.
- Pauldrons capped at +4.5 cm over the shoulder joint (not Darius/Wren).
- Robed: no filigree, gold only on the hem -> clean mantles.
