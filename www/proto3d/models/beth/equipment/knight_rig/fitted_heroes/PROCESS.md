# Separated outfits and per-character knight fit

Review assets only. The game does not load this folder. Source hero GLBs and the shared `knight_male.glb` / `knight_female.glb` are not modified.

## What was approved

Separate baked clothing from the body, and size the shared knight design onto each body. No new coat sculpt. No gameplay hookup.

## Playable roster

Godot's equipment list and `www/proto3d/main.js` `GLB_IDS` name 22 playable heroes: aldric, asha, brynn, cedric, darius, elira, finn, garruk, kael, mirelle, morwen, nyx, orin, owner, rook, rowan, selene, seraphine, talia, thorne, vesper, wren. Pip and Phoenix are companions. This pass fits three body types and leaves 19 listed in `coverage.json`.

None of the 22 voxel GLBs contains a jump clip. `tests/jump_test.gd` is a code test. The knight GLB's `jump_*` channels are two identical keys. Jump was not tested.

## Pilot sources (read only)

| Hero | Source | Armor |
|---|---|---|
| Darius | `origin/weaponless-rigs:voxel/darius_voxel_noweapon.glb` `d3746fc` | shared male |
| Talia | `origin/main:voxel/talia_voxel.glb` `a115562` | shared female |
| Rook | `origin/main:voxel/rook_voxel.glb` `ceef637` | shared male |

Darius on `origin/main` still has the baked sword. The weaponless rig is the body used here.

## Derived files

`tools/knight_rig/fit_heroes.py` writes, per hero:

- `<id>_body.glb` — head, hair, face, and the fist, plus an underlayer for regions the source does not model under the clothes. Same skeleton and clips.
- `<id>_outfit.glb` — every other source vertex (coat, robe, skirt, cape, sleeves), same skeleton and clips.
- `<id>_armor_fit.glb` — a sized rest-pose copy of the shared knight. Textures, materials, and topology are the source sculpt. Plate scale is baked into the rest pose and is not animated, so the plates do not stretch while a clip plays.
- `fit.json` — counts, ratios, and the cape rule.

Keep vertices plus outfit vertices are a partition of the source. Positions, normals, UVs, and weights of those vertices are copied. Showing body-keep and outfit together, with the underlayer hidden, is the unequipped appearance. Hiding the outfit and showing keep + underlayer + fitted armor is the equipped appearance. Putting the outfit back restores the cape, because every cape and coat bone vertex lives in the outfit.

## Where the source has no skin

Head, hair, face, and the fist are real source vertices. Torso, upper arm, forearm, thigh, shin, and foot are the clothing shell on the body bones. There is no second skin mesh under them. `ref_male` and `ref_female` are armor, not bodies. The dark mail liner is a filler so a removed sleeve does not leave a hole. It is not an anatomical reconstruction, and it is not a substitute for a missing skin mesh.

## How the armor is sized

The plates are not edited one bone at a time. That tore the helm, the hips, and the knees into slivers.

The whole sculpt gets one scale about the hips so the head height matches. Each arm then gets one uniform scale and one aim, so the arm plates stay one assembly. Pauldrons stay on the cuirass. Legs that are already within 4% are left. Clip rotations are copied in full. There is no angle limit and no pose-bone scale. A 0.90 clamp was a rest-size floor in an earlier file and was not a limit on the animation. It is gone.

The liner is dark mail, about 2–4 cm in radius, with weights blended along the span. It fills openings. It is not skin.

## Bind-pose audit

`fitted_heroes/bind_audit.json` records the check. For Talia and Rook, with no animation applied:

- `jointMatrix = nodeWorld * inverseBindMatrix`. The inverse-bind matrices are column-major. `JOINTS_0` indexes `skin.joints`, and that list is not `0..n` node ids.
- Max vertex residual of the reconstruction against the authored positions is 2.0e-7 m (Talia) and 3.3e-7 m (Rook). `||jointMatrix - I||` max is under 1e-6.
- The hand joint's node-world origin equals `inv(IBM)` to 0.1 mm.
- Blender, animations off, same camera: the original file and the baked reconstruction differ by 0 pixels.

The 14 cm (Talia) and 34 cm (Rook) hand figures are distances, in that correct bind space, from the hand-joint origin to hand-weighted vertices. They are not a bad matrix. Talia's forearm surface comes within 2.6 cm of the hand joint and meets the hand-weighted surface. Rook's forearm comes within 7.9 cm; the hand-weighted surface meets the forearm surface, and the nearest hand-weighted vertex is 28 cm from the joint. Darius's hand joint is 1.2 cm from his hand surface. The arm-length ratios (Talia 0.64, Rook 0.71 against the knight) are the same measurement on two skeletons that both satisfy `world @ IBM = I`. They are real bone-length differences. They were not re-applied in this audit.

Fists are not translated onto the joint, and hair is not deleted. `<id>_body_equipped.glb` is a copy of `<id>_body.glb`. The attachment coordinate is the bind-space joint origin.

Limb direction during a clip uses the same rest-aware aim as `review_bind_fit.py`: copy the clip's local rotation, then aim the long bones around the joint. Bone lengths stay at the fitted rest.

## Checks

`tools/knight_rig/render_fitted.py` is the only viewer. It is not autoloaded. It renders the untouched source, the keep+outfit composite, and the equipped body on idle, run, and attack, from the front, side, and back, plus helm, hand, elbow, and knee close-ups. There is no separate deep-bend clip; the attack and run frames are the largest forearm and shin bends in those files.

## Not done

The other 19 heroes are inventoried and not fitted. Run `python3 tools/knight_rig/fit_heroes.py` only builds the three pilots; the function `build_one` is the repeatable step once a hero id and male/female set are added to `PILOTS`.
