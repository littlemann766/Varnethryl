# World-boss Ashen Titan: art kit (Beth, 2026-10-25)
Godot 4.7.2, **Mobile** renderer: every shader here compiled and rendered under Forward Mobile (tested on llvmpipe via xvfb). Titan GLBs are **not** touched. Paths below are `res://` relative to this folder, so fix them up if you move it.

## Scale
World boss = **114 m** → put the Titan node at scale **5.440** (native mesh 20.955 m). Crystals, attach points and climb hulls are children of the skeleton, so they inherit that scale. Don't scale them separately. Ground telegraphs are in world metres (sizes below).

## 1. Weak-point crystals (6)
- Meshes: `wb_crystal_{forearm,knee,core}.glb` + `_lod1` (LOD1 is about 1/6 the tris), and broken versions `wb_crystal_*_broken(.glb/_lod1)` (snapped stumps, dark). `core` is used for both chest and back. +Y points out of the skin, and the origin sits on the skin socket.
- Material: in each crystal, surface 0 = crystal and surface 1 = lava-rock socket (leave its GLB material as is). Set `set_surface_override_material(0, wb_crystal_mat.tres.duplicate())` per crystal (`shaders/wb_crystal.gdshader`, 0 textures).
  - States: **dim idle** `glow=0`, **intact** `glow=1`, **glowing during wind-up** `glow=2` (pulse speeds up). **hit**: set `hit_flash=1` and tween it to 0 over 0.15 s. **broken**: swap the mesh to `_broken` and use `wb_crystal_broken_mat.tres` (`broken=1`, faint embers). **regrow** after 60 s: swap the mesh back and tween `broken` 1 to 0 and `glow` 0 to 1 over 1.5 s.
- Attach: see `attach_points.json` for forearm_L/R (`foreArm_L/R`), knee_L/R (`shin_L/R`), chest (`chest`) and back (`upperChest`). For each point: Skeleton3D → `BoneAttachment3D(bone_name=bone)` → `Node3D` with `Transform3D(Basis(Quaternion(rotation_quat)).scaled(Vector3.ONE*scale), Vector3(offset))` → crystal instance. Offsets are bone-local skeleton units. Put each weak-point hurtbox (sphere r ≈ 0.6 × scale) on the same Node3D.
- LOD: use `visibility_range_end` about 120 m on the high mesh and `visibility_range_begin` 120 m on lod1 (with the Titan at 114 m, players often see them from far off).

## 2. Telegraphs (all unshaded, no textures except the cracks and footprint, no screen reads except the sky tint)
| Ritual / event | Node | Material | Size | Drive |
|---|---|---|---|---|
| Fissure Slam: radial cracks | PlaneMesh 1×1, y+0.05 | `wb_crack_radial_mat.tres` | scale **120** (60 m radius) | `progress` 0→1 over 12 s, `erupt`=1 on complete |
| Fissure Slam: 3 lines | PlaneMesh 1×1 | `wb_crack_fissure_mat.tres` | scale (8, 1, 60), long axis = UV.y from the start point | `progress`, `erupt` |
| Meteor Call: target circles ×12 | PlaneMesh 1×1 | `wb_target_circle_mat.tres` | radius × 2 (e.g. 14 m) | `progress` 0→1 = time to impact (strobes after 0.85) |
| Meteor Call: red sky | ColorRect full-screen in a CanvasLayer under the HUD | `wb_sky_tint_mat.tres` | — | `amount` 0→1 over 1.5 s. `tex/wb_sky_tint_lut.png` (16³ strip) is an alternative for `Environment.adjustment_color_correction` if you'd rather not read the screen |
| Lava Wave: rising ring | CylinderMesh r1 h1, no caps, 48 segs | `wb_lava_ring_mat.tres` | scale (80, wall h ~12, 80) | `rise` 0→1 over 10 s, then tween scale outward |
| Lava Wave: ground warning strip | PlaneMesh / ring strip | `wb_lava_strip_mat.tres` (`ground_mode`) | 80 m ring band | `rise` |
| Wind-up hand / chest glow | QuadMesh 1×1 under BoneAttachment `hand_L/R` or `upperChest` (self-billboards) | `wb_hand_glow_mat.tres` | about 3–4 skeleton units | `charge` 0→1 over the wind-up |
| Stomp footprint | PlaneMesh 1×1, y+0.05, yaw = foot | `wb_footprint_mat.tres` | scale **25** | `heat` 1→0 over 10 s, `fade` 1→0 from 100 to 120 s |
| Stomp dust | `wb_dust_burst.tscn` (CPUParticles3D, 40 quads, one-shot, 30 fps) | — | ring r 8–12.5 m | `restart()` on footfall. Scale the node ×2 for the arrival stomp |
| Cast bar + icons | TextureRect/NinePatchRect | `tex/wb_castbar_frame.png` (9-slice margin 48) + `wb_castbar_fill.png`, `tex/wb_icon_{fissure_slam,meteor_call,lava_wave}.png` (256) | — | — |
Duplicate a material for every instance you drive separately.

## 3. Adds (blockout)
`wb_ash_fiend(.glb/_lod1)` (2.4 m melee, 9.5k / 0.9k tris) and `wb_ember_wisp(.glb/_lod1)` (floating, 1.3 m, emissive core). These are **static and unrigged blockouts**: Lucian needs to rig the fiend, and the wisp can just bob in code. They currently face -Z (rotate 180° if they spawn backwards).

## 4. Climbable hulls
`collision/wb_climb_{spine_back,upper_back,shoulder_L,shoulder_R}.tres` (ConvexPolygonShape3D, 23–34 pts, bone-local). See `climb_hulls.json` for the bones. Use BoneAttachment3D(bone) → AnimatableBody3D (climb layer) → CollisionShape3D. They're built from the rest pose, so they follow the bones. Recheck them after Lucian's hand re-sculpt and re-rig (re-run `tools/compute.gd`).

## Tools
`tools/build_crystals.py`, `build_textures.py`, `build_adds.py` (bpy / PIL), `compute.gd` (attach points + hulls from the Titan GLB), `render.gd` (contact sheet). Shots: `shots/contact_worldboss.jpg`.
