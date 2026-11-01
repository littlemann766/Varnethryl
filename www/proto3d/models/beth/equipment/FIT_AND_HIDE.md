# Equipment v1: fit and hide rules (step 3)

Files: `fit/armor_attach.json` (22 playable heroes x 14 parts), `fit/companion_attach.json` (Pip, Phoenix collars), meshes in `meshes/<family>/<family>_<rarity>_<part>.glb` + `_lod1`.

## How parts attach
- Rigid segmented pieces, one BoneAttachment3D per part: helmet→head, chest→chest, shoulder_L/R→upperArm, glove_L/R→foreArm, leg_L/R→thigh, boot_shin_L/R→shin, boot_foot_L/R→foot, belt→hips, cloak→chest.
- Child transform: `Transform3D(Basis(Quaternion(rotation))*Basis.from_scale(scale), position)`. Right-side parts have `mirror_of` = the _L mesh and a negative scale.x (Godot flips culling for mirrored instances).
- Sizes come from each hero's skinned rest-pose vertices (limb core radius per bone, torso band, hips band), so the same mesh fits all 22 heroes.
- Cloak (`binding: skin_to_cape`): place the cloak mesh with the chest transform, then bind it to the hero's OWN cape bones: every cloak vertex copies the bone weights of the nearest hero cape vertex (rest pose); the top 0.18 m fades to the chest bone so the collar stays on the shoulders. The hero's cape is hidden (`hide.cloak`). Reference: `tools/godot/dress.gd skin_cloak()`. Do it once per hero+cloak at equip time (or cache). Zero physics cost: it swings with the existing cape animation.
- Material: vertex colours are linear (glTF COLOR_0). Use `vertex_color_use_as_albedo=true`, `vertex_color_is_srgb=false`; surface 1 (`vox_glow`) is emissive.

## Hide rules (data in `hide` per hero)
Selectors use each vertex's REST model-space position and its dominant bone. Remove the triangles that touch a selected vertex (rebuild the index array once at equip time; restore the original mesh on unequip). Reference implementation: `tools/godot/dress.gd` `hide_verts()`.
- `helmet_full` (plate great helms): head verts above the eye line + anything above the head top (hair, hats).
- `helmet_open` (coif/sallet/hood/circlet): hair crown + anything above the head top; the face stays.
- `boots`: foot verts.  `cloak`: all cape* bone verts.  `baked_weapon`: hand verts outside a keep-sphere around the fist.

## Built-in (baked) weapons — list for Lucian
These rigs have a weapon modelled into the hand mesh, which doubles up with an equipped main_hand/off_hand. The `baked_weapon` hide rule removes it at runtime; Lucian may prefer to split it into its own mesh/bone in the rig:

- **darius**: hand_R
- **orin**: hand_L
- **rook**: hand_R, hand_L
- **finn**: hand_L
- **elira**: hand_L
- **wren**: hand_R, hand_L
- **rowan**: hand_L
- **talia**: hand_R, hand_L

## Fixed old issues
- Doubled built-in weapons: hide rule above + list.
- Pip collar: now on neck1 between spine3 and head, sized from the neck (`fit/companion_attach.json`); was inside the head. Phoenix collar sized to the neck core, not the feathers.
- Frostreach and Vent Harbour stalls: snapped onto the dock decks by raycast vs stage4 collision + harbour meshes (`loot/merchants/PLACEMENT_merchants.json`, `position_v0` keeps the old point). Shot: shots/loot3/fix_stalls_frostreach_vent.png.
- Sslythar stays hidden: no meshes, no attach, items tagged hidden.
