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

## v10 slim (all 8 heroes)
- Armour wall 1 vox (chest/shoulder/glove/leg/belt), boots 2; pin-hole fill limited to the armour's own thickness off the body (no bridging bulk); pauldron height cap removed (1-vox pauldrons follow the shoulder; a cap exposed raw body voxels). Lames/rivets/cops/straps and v8/v9 helms unchanged.

## v11 worn (all 8 heroes)
- Walls back to 2 vox with a raised rolled rim on every piece edge (gold on rare+/legendary, edge steel below, dark on robed) -> pieces read as worn kit with real thickness, not painted skin.
- Legendary filigree speckle only on helms; body pieces carry gold rims.
- Chest covers coat/hips-weighted front cells and overlaps the belt, min half-width 15 cm (Wren tunic bleed).
- Helm mask also hides head/neck/chest/hair-weighted gear above the neck (Rook's beige back gear).

## v12 (all 8 heroes)
- Body pieces: 1-vox walls + rolled rims, wider-spaced lame lips, sparse rivets, no surface speckle on rare+ (clean metal), mail showing around plate couters/poleyns, grooves instead of raised shoulder ridges.
- Helms: great helms get a 2-lame gorget to the collar; bascinets close to the chin with a pig-faced snout visor + breaths over the aventail.
- Chest takes coat-weighted cells on all sides (Wren).

## v13 reshape (all 8 heroes)
- Chest/belt: per-slice ellipse fit (84th pct; robed sash 70th), smoothed along height -> clean cuirass/faulds silhouette instead of mirroring voxel lumps.
- Shoulders/gloves/legs: per-bone tube fit along joint->child-joint axes (pauldron dome cap; robed mantle slim, no dome; robed cuffs and all boots keep the hugging shell).
- Masks hide every body cell inside each fitted envelope (+6 cm limbs, +13 cm and a side half-slab to mid-shin on legs for skirts/coats; torso +7 vox). dress.gd hides a body tri when 2 of 3 verts are masked (no edge fragments).
- Rims = top/bottom band of each fitted piece; lames/rivets/straps/cops/joint mail and v8-v12 helms unchanged.

## v14 (RPG pass)
Stepped overlapping lames (pauldron cascade, fauld, limb lames) with dark riveted lips, mail at elbows/knees, chest emblem+jewel (gold legendary, molten masterwork), wider leg side slab, dagged robed mantles. Tris 3538-7990, lod1<=50%. Shots: /workspace/shots/loot3/fitted_rpg/

## v15 (robes, coats, unique helms)
Per-hero helm silhouettes: darius comb+up-horns, orin plume+wings, rook ram horns, finn spike, elira comb+wings, wren spiked crown, rowan tall hood tip, talia brow diadem. Robed: slim top-of-shoulder mantle, cloak thk 1, sash+tabard to ankle, reduced hood flare. Leg cover slab foot..belt, |x|<0.75; glove mask dil 3. Chain fitted pieces: calm ring rows. Tris 3538-7990, lod1<=50%. Shots /workspace/shots/loot3/fitted_rpg2/

## v16 (leftover polish, soft hold)
Robed: full skirt panel to ankle |x|<0.30 with vertical drape folds, shoulder mantles get a hanging cape curtain on the outer side. Leg greave to 62% shin + coat-weighted shin cells. Shoulder mask dil 3 (coat flaps). Finn: finial spike with collar + knop at helm apex. Tris 3538-7990, lod1<=50%. Shots /workspace/shots/loot3/fitted_rpg3/

## v17 (leftover polish, soft hold)
Grid +35cm headroom (crest/spike stamps were clipped). Finn: thick tapered spike + gold ball finial + jewel knop. Rook: coat wraps shins (no air) -> boots get a synthetic greave core along shin->foot + ankle bridge, grown through the hidden coat; glove mask covers arm-axis coat cuffs. Robed: pelerine = thin conical cape sheet from neck over shoulders (dagged rim), hides T-pose sleeve drapes; skirt panel |x|<0.38. Mask dims changed (z) - always rebuild full heroes. Tris 3538-7990, lod1<=50%. Shots /workspace/shots/loot3/fitted_rpg4/

## v18 (leftover polish, soft hold)
Robed pelerine wider (+9cm) and lower (starts at shoulder joint), slope flare 0.22, slimmer front/back depth (<=15/17cm). T-pose sleeve drapes hidden incl. forearm drapes, down to belt-45cm; skirt panel |x|<0.42. Rook: wider ankle bridge (r 7.5cm), forearm coat-cuff mask r 16cm. Tris 3538-7990, lod1<=50%. Shots /workspace/shots/loot3/fitted_rpg5/

## v19 (leftover polish, soft hold)
Robed pelerine: rounded shoulder (sqrt profile), wider lower flare 0.35, thinner sheet (1.6 cells); hides specks within 1.35x of the sheet; T-pose drape mask widened to the ankle. Rook: boot foot trimmed to the foot (no coat-hem toe), synthetic thigh core so the cuisse meets the fauld; chest env +3. Sheets via tools/godot/r_sheets.py. Tris 3538-7990, lod1<=50%. Shots /workspace/shots/loot3/fitted_rpg6/

## v20 (leftover polish, soft hold)
Rook boot: close(2)+opening (smooth, no 1-voxel strays), rim band only at boot top, no rolled edge blotches, mask dil 3. Chest: hide non-arm body cells at the chest sides under the arms. Robed: cape speck-hide zone 1.6x (+6 above, -3 below), cape 2cm narrower and flare 0.28; skirt panel |x|<0.46. Tris 3538-7990, lod1<=50%. Shots /workspace/shots/loot3/fitted_rpg7/

## v21 (leftover polish, soft hold)
Rook: ground coat hem skinned to the foot (cells up to 40cm from the foot joint) hidden via the boot mask; under-arm upperArm/shoulder-weighted cells near the torso below shoulder-8cm hidden by the chest mask. Robed: speck-hide zone 1.9x, drape mask 4cm further in. Tris 3538-7990, lod1<=50%. Shots /workspace/shots/loot3/fitted_rpg8/

## v22 (leftover polish, soft hold)
Chest armour grows over the under-arm gap (CSIDE cells become plate); Rook chest envelope pc95. Rook ground-hem mask to foot+18cm, dil 2. Robed: hand-skinned bits >11cm from the hand hidden. Diagnostic: Rook body under the chest piece is a wide coat outside the chest env; Talia specks are her fur/feather spikes. Tris 3538-7990, lod1<=50%. Shots /workspace/shots/loot3/fitted_rpg9/
