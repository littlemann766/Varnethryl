# Knight rig (ref armor, fully rigged)
Source: boss ref_armor.glb (3,757 loose parts), split at centroid x<5 (fixes stray male wing tip in female file).
Skeleton: 78 bones on hero (Darius) names - hips/spine/chest/neck/head, clavicles, arms + upperArm/foreArm twist, fingers,
legs + thigh/shin twist, feet/toes, secondary chains wing_L/R_01-04, tabard_F_01-03, tabard_B_01-03.
Binding policy: every part 100% rigid to one bone; joint-spanning / long chain parts are edge-split into rigid slices. 0 blended.
- male: 1512 rigid, 705 chain-rigid, 53 split, 0 blended (2270)  | female: 1189 / 253 / 45 / 0 (1487)
Stretch (all hero anims + extreme poses): male edge max 0.09% p95 0.004%; female edge max 0.028% p95 0.0036%; area <=2.1% (sub-mm2 float noise). No tri >10%.
Runtime notes: foreArm_twist should follow 50% of hand roll (CopyTransformModifier3D or bake). Tabard/wing chains are not driven by hero anims - add SpringBone/secondary motion.
Retarget is rotation-only (loc/scale only on hips/root). Texture kept as albedo; keep vertex_color_is_srgb in import.
lod1: ~45% tris, each vertex snapped to a single bone.

## v3 - faithful rework (v2 underlayer/plate scaling REVERTED)
Mesh = boss original geometry, untouched (rest renders vs his GLB: PSNR 31-47 dB, see lookmatch.json). Full PBR kept: base, ORM, normal at 2048 JPEG.
Pipeline: parts.py -> rig.py -> bind3.py (NORT=1) -> opt.py -> export3.py.
- Joint-spanning (connective) parts: not cut; smoothstep weight band (6-12 cm, tabard 8, wing 5) across the label boundary; non-adjacent mislabels folded to the majority bone.
- Plates: 100% rigid. Helper bones: pauldron_L/R (45% upperArm), elbow_L/R (50% foreArm), knee_L/R (50% shin), tasset_L/R (85% thigh). Tabard_F/B_01-02 driven by both thighs (X only).
- opt.py: each rigid part re-homed (hierarchy distance <=2) to the bone that best keeps rest contacts across 42-54 animation frames.
- All clips baked with the helpers/twist into the GLB (plain bone tracks). No corrective shape keys.
- Result vs e0fbc6c: see gap_summary_v3.json. Plates rigid (<0.1% edge), seam bands stretch a lot (see stretch json). Gaps/clipping NOT solved: the source mesh has no geometry under the plates.

## v4 - joint rim extensions (tools/knight_rig/extend.py, EXTL=0.07, after opt.py -> stage4)
Open boundary rims of rigid joint plates (pauldron/shoulder/arm/elbow/hand/neck/torso/hips/tasset/thigh/knee/shin/foot; helm excluded) facing a joint within 14 cm are extruded up to 7 cm along the surface, as separate rigid strips on the plate's own bone with UVs mirrored back into the plate's own UV island (his texels, no smear) and their own verts (original normals untouched).
Each strip is kept only if it is hidden at rest from 90 view directions (sampled along its length); otherwise shrunk, then dropped. Result: rest look unchanged, but only a few hundred rims qualify (male 345 edges, female 195), so the gain is small. See summary_v4.json.

## v5 - joint limits on the baked clips (tools/knight_rig/limits.py + limit_actions.py, stage4 -> stage5)
Mesh/texture unchanged (rest identical to v4). Every clip's bone rotations are soft-limited: angle' = L*tanh(angle/L), L per bone (deg): upperArm 26, foreArm 45, hand 32, shoulder 7, pauldron 18, thigh 30, shin 48, foot 22, toe 18, neck 20, head 26, wing 12, tabard 14; spine2/upperChest folded into chest (rigid cuirass, L 14). Hips untouched.
Godot: if you play other clips, clamp with the same limits (SkeletonModifier3D / retarget step). Big swings (attack overhead, run stride) are visibly toned down.

## v6 - bigger moves (limits.py LIMSET=6, limit_actions.py -> stage6, then midrig.py)
Mesh/texture unchanged. Soft knee limit per bone: full clip motion up to K=0.75*L, then eased (tanh) toward L.
L (deg): upperArm 170, foreArm 115, hand 50, shoulder 30, pauldron 60, thigh 85, shin 120, foot 50, toe 20, torso(folded spine) 35, neck 25, head 30, wing 28, tabard 28, hips 180 (free).
Seam smear: the blended connective pieces (male 43, female 39) are now 100% rigid on mid_<bone> helpers that copy 50% of the child joint's rotation -> zero texture stretch everywhere (0 blended tris); costs some extra clipping. Helpers are baked into the clips.

## Review reseat (not a v6 approval)
v6 is what the boss has seen. It is not approved. Mesh, UVs, normals, and the three 2048 JPEGs are unchanged. `tools/knight_rig/reseat_mid.py` only rewrites rigid joint indices.

What the numbers in `summary_v6.json` are: `gapcheck.py` renders 360×480 orthographic views (yaws 25/205/90) with a green background, white front faces, red backfaces. `gap_pct` = 100 × (hole pixels + red backface pixels inside a 14 px radius of the projected joint) / joint-region pixels. `vis_pct` in the summary is that figure averaged over the animation samples (male 10.71, female 7.90). `pen_mean` is the mean count of sampled rigid vertices whose inter-part penetration grew by more than 3 mm versus rest (nearest other-part triangle within 15 mm). v6 deep-pose clipping is higher than v5 (male 189.4 vs 132.0, female 142.7 vs 85.1) because the motion limits were opened and the seam pieces take half the child rotation. Those gapcheck totals were not re-run here: the stage blends are not in the repo, and the shipped GLB clips do not contain the motion (every clip is two identical keys; non-root rotation delta is 0). `/workspace/uploads/ref_male.glb`, `ref_female.glb`, and `/workspace/shots/knight_v6/` were not on this machine.

Reseat rule: a connected island on a limb `mid_*` bone (not wing, tabard, or `mid_chest`) moves entirely onto the parent plate or the child plate when its vertices are at least 4 mm closer to that plate at rest. Wings and the tabard stay on their half-turn helpers. Rest pixels match the previous GLB (male max channel delta 0, female 1). The first posed checks used the extreme poses in `val.py`. Those are not the hero clips. `review_on_hero/` copied local quaternions and is not a valid fit when the rest offsets differ. The later check is `review_bind_fit/`.

## Bind-aware fit on the heroes (review only)

`tools/knight_rig/review_bind_fit.py` is not autoloaded. Hero GLBs stay on their source branches. The armor is not scaled and the plates are not reshaped.

These GLBs give every bone the same node orientation. The limb direction is the child offset, not the joint quaternion. Copying that quaternion keeps each skeleton on its own rest offset, so Talia's arm and the armor's arm do not land in the same place. The review now copies the clip rotation, then aims the long limb bones (upper arm, forearm, hand, thigh, shin, foot) so the armor's own bone length points along the hero's posed limb. The rotation is about the joint. Shoulder and spine stay on the copied rotation, because aiming those short bones swings the arm off the body. After that, limb directions match within 0.03°.

Each hero is one mesh. Cape and coat-bone vertices are hidden on a review copy only (Darius 12,072, Talia 41,300, Rook 12,808). The coat, robe, skirt, and shoulder shell are weighted to chest, hips, upperChest, and shoulder. Hiding those would remove the torso, so they stay. The yellow tabard on Darius is part of that body mesh.

Rest hips already match on Darius. Talia's hips sit 7.9 cm deeper and 2.6 cm lower; Rook's sit 15.4 cm deeper and 3.4 cm higher. The review translates the armor onto the hero hips and does not scale it. Median distance from limb vertices to the armor surface: Darius 2.1–2.6 cm, Talia about 6 cm, Rook 5–7 cm. Share of limb vertices more than 4 cm out: Darius 18–30%, Talia about 62%, Rook 56–67%.

Darius idle, run, and attack now wear the armor in the same pose as the body. His coat still stands outside the plates. Talia's gauntlet follows her forearm; her robe is larger than the female armor and is not a separate garment. Rook's torso and robe are wider than the male armor, which sits inside him. There is still no jump clip in these hero files.

## Outfit split and per-character fit (review only)

Approved as a review of the shared sculpt, not a gameplay change. `tools/knight_rig/fit_heroes.py` reads the source GLBs and writes derived files under `fitted_heroes/`. The shared knight GLBs and the hero sources are not edited. Process, roster, and counts: `fitted_heroes/PROCESS.md` and `fitted_heroes/coverage.json`.

The 22 playable heroes are aldric, asha, brynn, cedric, darius, elira, finn, garruk, kael, mirelle, morwen, nyx, orin, owner, rook, rowan, selene, seraphine, talia, thorne, vesper, and wren. This pass fits Darius (male, weaponless rig), Talia (female), and Rook (taller male). The other 19 are listed and not fitted. None of the 22 voxel files has a jump clip.

Head, hair, face, and the fist stay. Coat, robe, skirt, sleeves, and cape move to `<id>_outfit.glb`. Torso and limbs have no source skin under the clothes, so `<id>_body.glb` adds a rigid underlayer on those bones. Equipped is keep + underlayer + a sized copy of the shared armor. Unequipped is keep + outfit, which puts the cape back. The size is baked into the armor rest pose (one scale per torso, arm, and leg). It is not animated, so the plates do not stretch in a clip. The review still aims the long bones around the joint.
