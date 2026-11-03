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
