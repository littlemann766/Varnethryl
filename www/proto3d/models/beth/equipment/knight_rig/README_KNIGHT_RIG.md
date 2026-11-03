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
