# Hooded male zombie: game asset handoff (offline repair v2, 2026-11-09)

The baseline is unchanged and read-only: `/workspace/zombie_repair/final_baseline_v1/` (approved repair_mc.glb/.blend, 96.6k tris, 20 joints). Everything below is a new candidate built on top of it.

## Files
| file | tris | size | notes |
|---|---|---|---|
| final2/hooded_male_full_game.glb | 96,615 | 11.1 MB | Full detail. PNG textures and corrected motion. **Fallback / reference.** |
| final2/hooded_male_mobile.glb | 47,583 | 8.4 MB | Mobile LOD. Same skeleton, animations, and textures. **Above the 45k target, see LOD.** |
| final2/hooded_male_far.glb | 783 | 0.2 MB | Far LOD. Vertex colours, no textures. Secondary. |
| final2/impostor/impostor_card.glb + atlas/front PNG | 2 | small | RGBA impostor. Secondary. |

All 4 pass the Khronos glTF-Validator with 0 errors. The three skinned files each have 1 warning, NODE_SKINNED_MESH_NON_ROOT; the original input has the same warning. The card has 0 warnings. All three skinned GLBs carry byte-identical animation data.

## Materials (game GLBs)
- EXT_texture_webp has been removed. Images are embedded PNG: albedo (sRGB, RGB) and metallicRoughness (linear).
- MR texture: B (metallic) was set to 0 and G (roughness) kept from the source (~0.99). The source B≈181 (metallic ≈0.71) caused the washed-out grey look. metallicFactor is 0, roughnessFactor is 1, and doubleSided is true (thin cloth/tatter shells).
- No normal map. The source has none, and a high→low bake was tried and rejected: thin double shells and fragmented UVs produced black inverted blotches.

## Skeleton (actual data)
There are 20 skin joints, in order:
hips, spine, chest, neck, head, **cloak_back**, shoulder_L, upperArm_L, foreArm_L, hand_L, shoulder_R, upperArm_R, foreArm_R, hand_R, thigh_L, shin_L, foot_L, thigh_R, shin_R, foot_R

- The 19 original bones are all of the above except `cloak_back`. `cloak_back` is new: it is a child of chest and drives the back cloak.
- The earlier "21" count was the node count of the input: 19 joints + `geometry_0` mesh node + `fit` armature root. Output nodes: 22.

Hierarchy:
```
fit (armature root)
├─ geometry_0 (skinned mesh)
├─ hips ─ spine ─ chest ─┬─ neck ─ head
│                        └─ cloak_back
├─ shoulder_L ─ upperArm_L ─ foreArm_L ─ hand_L
├─ shoulder_R ─ upperArm_R ─ foreArm_R ─ hand_R
├─ thigh_L ─ shin_L ─ foot_L
└─ thigh_R ─ shin_R ─ foot_R
```
- Shoulders and thighs are root-level siblings of hips, not children, as in the source. A retarget must not assume hips→thigh or chest→shoulder parenting.
- Bone names are not Godot/Mixamo/Unity-humanoid standard. Retargeting needs an explicit bone map. I have not verified Godot import.
- Character faces glTF +Z. 24 fps. All animations are in place (no root motion).

## Animations (glTF names, durations)
| clip | frames | s | loop | suggested root speed |
|---|---|---|---|---|
| attack2 | 0–25 | 1.0417 | no | – |
| death | 0–38 | 1.5833 | no | – |
| hit | 0–9 | 0.375 | no | – |
| idle | 0–60 | 2.5 | yes | – |
| run | 0–22 | 0.9167 | yes | ~2.0 m/s |
| walk | 0–32 | 1.3333 | yes | ~0.91 m/s |

Every clip has 60 channels (20 joints × T/R/S), including identity cloak_back keys in the clips that don't use it. For idle, run, and walk, the first and last frames are identical (seamless loops).

## Motion changes vs baseline
- **run:** the original had swapped stance/swing and ~0.4 m tucked "flight", so it floated. I re-synthesised the legs with 2-bone IK:
  - stride 0.6 m, 7-frame stance, hips lowered to 0.886 m (rest 0.98) so the leg is ≤97% extended, 5 cm bob.
  - Toe-pivot push-off; swing lift 0.30.
  - Stance foot speed is about 2.0 m/s (std 0.13), with short natural 2–3-frame airborne phases. Feet are not snapped every frame.
  - Shoulders are re-attached to the chest.
  - cloak_back counter-rotates at −0.8 × chest pitch (chest pitch 6–24°). This removes the cloak smear seen from the back.
- **walk:** treadmill foot-lock at a constant 0.91 m/s through detected contacts, smoothstep-blended through swing with 2.5 cm clearance. Max hip drop 3.9 cm. Max foot correction 13/16 cm.
- **idle, hit, attack2:** feet planted at their median position during contact; hip drop ≤3.9 cm; soles at z=0. No IK clamping in any clip.
- **death:** NOT foot-locked. Locking shifted the body 0.4–0.7 m, so the baseline death is kept.
- A baseline bug, documented honestly: in repair_mc the planned 32° cloak_back death fold was never keyed (Blender 'REPLACE' key option). The death cloak tuck there comes from the weights alone. That is unchanged here.

## Mobile LOD
- Built from the full-detail game GLB with meshoptimizer 1.3 simplifyWithAttributes:
  - 1 cm absolute error.
  - Face/head (head/neck weight >0.5, upper region) and hands vertex-locked.
  - Attribute weights: UV 0.5, normals 0.
- Normals, UVs, and skin weights are carried over from the source vertices. Welded duplicates are identical, and coincident seam separation is ~4e-7 m.
- Deviation from full: p99 5.9–7.1 mm, max 29 mm.
- No faces were deleted, and nothing was removed by game metric. Small islands and crossing-joint faces are kept.
- **Result: 47,583 tris, ABOVE the 35–45k target.** The UV seams/borders set a floor of about 46k at acceptable quality. These variants got into the band but were rejected for visible damage:
  - mobile_a (44.8k): back-cloak cracks/shards.
  - gltfpack (43.7k): shards.
  - mobile_c: spiky fingers.
- I kept the larger mesh rather than trade appearance for the count.

## Far LOD / impostor (secondary)
- **Far:** 783 tris, area-weighted vertex colours, untextured. At ~100 px tall it reads as the character, but it is thinner and darker than the full model and the head is crude.
- **Impostor:**
  - 8 yaw views, rendered at 45° steps: 1024 atlas and 512×1024 front RGBA (edge-bled).
  - Card: 1.0687×2.1374 m quad, KHR_materials_unlit, alpha MASK 0.5.
  - Source pose is idle frame 0 from the pre-foot-lock export, so the feet differ by at most a few cm.

## Visual review (renders from the reimported final exports; neutral light, materials as exported)
| clip | verdict | remarks |
|---|---|---|
| run | PASS | Grounded crouched zombie run with short flights. Front and side are coherent across the loop boundary. |
| walk | PASS | Feet planted, loop seamless. |
| idle | PASS | Stable, feet planted. |
| hit | PASS (with caveat) | Starts and holds an arms-out/head-back pose. Needs crossfade in-engine. |
| attack2 | PASS (with caveat) | Starts and ends arms-out. Needs a blend from idle. |
| death | PASS (with caveat) | Arms-out start. Backward fall to the ground. Not foot-locked. |
| mobile vs full | PASS at gameplay distance | Full-body frames of all clips match. The face is identical (locked). At a 1 m back close-up the hood edge and upper-cloak tatters are more jagged/faceted, with a few small dark slits; it is most visible in run. The chest cloth near the hands is slightly faceted. No shards or texture damage. |
| far / impostor | usable, secondary | See above. |

No slabs, tears, or giant stretch were seen in the reviewed frames. Max per-edge stretch p99 is 1.5–2.6× (run highest), at the knee/hip creases.

## Not tested
- Godot import or AnimationTree retargeting.
- Any phone or GPU performance.
- In-engine blending, root motion, or physics.
- Every frame of every clip was not individually inspected. I reviewed 66 sampled columns, including all loop start/end frames.
- The impostor/far LOD was not tested in a real LOD switch.
