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

## v2 - joint gaps (tools/knight_rig/gaps.py -> stage3)
- Fragment fix: small pieces (<120 verts) bound to upperArm/shoulder that touch big torso plates are re-bound rigidly to the bone of the plate they touch (male 74, female 49 pieces).
- Lame overlap: every core plate grown ~5 mm about its own centroid (rigid rest-pose scale, cap 4%) so neighbours overlap.
- Cloth underlayer (material `gambeson`, dark, double-sided, untextured): 14 tubes - neck, waist, shoulders, elbows, wrists, hips, knees, ankles - fitted per sector inside the plate shells and LBS-blended between the two bones (wrist also uses foreArm_twist). Rest-hidden by ray test from 36 view dirs; verts still visible through source-mesh openings are collapsed to the axis.
- Plates stay 100% rigid (edge stretch max <0.1%). Underlayer stretch reported separately in knight_*_stretch.json (under_*).
- Gap check (gapcheck.py, 3 views x all poses): joint-region pixels showing background or back-faces; before/after in knight_*_gapcheck_*.json and gap_summary.json.
- lod1: plates snapped to one bone, underlayer keeps its blend.
- Not solved: plate-plate interpenetration in deep poses (rigid plates cannot slide), tabard/tasset chains need runtime spring motion.
