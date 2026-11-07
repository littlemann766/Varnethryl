# Test 54 art candidate — checked against the tag, not applied

Target is the immutable tag `godot-test-54` at `33ec05515fa2907c1d6958e39e884eed92955776` in `https://github.com/littlemann766/Varnethryl`. That SHA is also `refs/heads/main` at the time of the fetch. `refs/heads/godot-voxel` still does not exist. Nothing here was pushed to the tag or to `main`.

The tag tree is a Godot project, not a release-only APK. `project.godot` is present (`config/features` is `4.7` and `Mobile`, `config/version` is `1.9.3`, `config/test_build` is `33`). `run/main_scene` is `res://main.tscn`. Tidewrack is loaded by `tidewrack/tw_sea.gd`.

## What the tag actually binds

`TidewrackSea._mat_for` (`tidewrack/tw_sea.gd` lines 77–92) does **not** use `vc_terrain.gdshader`. There is no such shader anywhere under the tag's `tidewrack/`.

- Fog, storm, glow, lava, and steam return their own shaders.
- Every visual whose name starts with `ash_` then gets a `StandardMaterial3D` (vertex color, roughness 0.9, metallic specular 0.15).
- Everything else, including archipelago and frost terrain, returns `res://tidewrack/stage1/shaders/vc_lit.tres`, a `StandardMaterial3D` with `vertex_color_use_as_albedo` and roughness 0.9.

The test 49 `_mat_for` snippet that assumed `vc_terrain` was already wired is wrong for this tag. Do not paste that older block.

`_build_region` sets `material_override = _mat_for(b)` on each visual glb. Names ending in `_col` are turned into trimesh static bodies and are not drawn. `_files` loads every `arch_` / `coast_` / `frost_` / `ash_` glb in the stage mesh folder except `_lod1` (low tier swaps to `_lod1` inside `_path` when `tier < 2` and the lod file exists).

`project.godot` sets `renderer/rendering_method="mobile"` and `renderer/rendering_method.mobile="mobile"`. The Android preset (`export_presets.cfg`, package `com.varnethryl.godottest`, arm64, versionName `1.9.3`) does not override the renderer. This is not the Compatibility GLES renderer.

There is no `hero_cut` reference in the tag. The land4 shader declares `global uniform vec4 hero_cut` and only cuts when `hero_cut.w > 0.5`. Left unset, that stays off.

## Art files (unchanged, commit 4f8c97f8)

Shader: `www/proto3d/models/beth/tidewrack_sea/land4/shaders/vc_terrain.gdshader`
Copy to `res://tidewrack/stage1/shaders/vc_terrain.gdshader`.

Fifteen jpgs in `land4/textures/`, copy to `res://tidewrack/land4/textures/`. Uniforms are `grass|earth|sand|rock|snow` plus `_col` / `_nrm` / `_rgh`. Sources, CC0 ambientCG: Grass004, Ground048, Ground054, Rock023, Snow001. See `textures/TEXTURES.md`.

Load them the way the stills did: `Image.load_from_file`, `generate_mipmaps`, `ImageTexture`. Do not rely on the importer's sRGB flag.

Terrain glbs to copy onto the same `res://tidewrack/` relative path. 78 files. These are the high mesh and its `_lod1` only. No `_col`, no `land_scatter`, no ports, no glow.

The 13 `*_isl_*` meshes are not inside the tile meshes (sampled: Gullhaven is not in `arch_islands`, Frostreach is not in a frost tile). The tag's `arch_islands.glb` does cover the Gullhaven area with the old surface. Replacing `arch_islands.glb` without also adding `arch_isl_gullhaven.glb` (and the other `*_isl_*` files) leaves a hole. Adding them does not stack a second copy of the same triangles.

```
stage1/meshes/arch_isl_coil_isle.glb
stage1/meshes/arch_isl_coil_isle_lod1.glb
stage1/meshes/arch_isl_gullhaven.glb
stage1/meshes/arch_isl_gullhaven_lod1.glb
stage1/meshes/arch_isl_lantern_rock.glb
stage1/meshes/arch_isl_lantern_rock_lod1.glb
stage1/meshes/arch_isl_saltwatch_keep.glb
stage1/meshes/arch_isl_saltwatch_keep_lod1.glb
stage1/meshes/arch_islands.glb
stage1/meshes/arch_islands_lod1.glb
stage2/meshes/coast_isl_beached_wreck.glb
stage2/meshes/coast_isl_beached_wreck_lod1.glb
stage2/meshes/coast_isl_saltglass.glb
stage2/meshes/coast_isl_saltglass_lod1.glb
stage2/meshes/coast_tile_x0z0.glb
stage2/meshes/coast_tile_x0z0_lod1.glb
stage2/meshes/coast_tile_x0z1.glb
stage2/meshes/coast_tile_x0z1_lod1.glb
stage2/meshes/coast_tile_x0z2.glb
stage2/meshes/coast_tile_x0z2_lod1.glb
stage2/meshes/coast_tile_x0z3.glb
stage2/meshes/coast_tile_x0z3_lod1.glb
stage2/meshes/coast_tile_x1z0.glb
stage2/meshes/coast_tile_x1z0_lod1.glb
stage2/meshes/coast_tile_x1z1.glb
stage2/meshes/coast_tile_x1z1_lod1.glb
stage2/meshes/coast_tile_x1z2.glb
stage2/meshes/coast_tile_x1z2_lod1.glb
stage2/meshes/coast_tile_x1z3.glb
stage2/meshes/coast_tile_x1z3_lod1.glb
stage2/meshes/coast_tile_x2z1.glb
stage2/meshes/coast_tile_x2z1_lod1.glb
stage2/meshes/coast_tile_x2z2.glb
stage2/meshes/coast_tile_x2z2_lod1.glb
stage2/meshes/coast_tile_x2z3.glb
stage2/meshes/coast_tile_x2z3_lod1.glb
stage4/meshes/ash_isl_ember_wreck.glb
stage4/meshes/ash_isl_ember_wreck_lod1.glb
stage4/meshes/ash_isl_hot_spring.glb
stage4/meshes/ash_isl_hot_spring_lod1.glb
stage4/meshes/ash_isl_obsidian_arch.glb
stage4/meshes/ash_isl_obsidian_arch_lod1.glb
stage4/meshes/ash_isl_vent.glb
stage4/meshes/ash_isl_vent_lod1.glb
stage4/meshes/ash_tile_x0z0.glb
stage4/meshes/ash_tile_x0z0_lod1.glb
stage4/meshes/ash_tile_x0z1.glb
stage4/meshes/ash_tile_x0z1_lod1.glb
stage4/meshes/ash_tile_x1z0.glb
stage4/meshes/ash_tile_x1z0_lod1.glb
stage4/meshes/ash_tile_x1z1.glb
stage4/meshes/ash_tile_x1z1_lod1.glb
stage4/meshes/ash_tile_x2z0.glb
stage4/meshes/ash_tile_x2z0_lod1.glb
stage4/meshes/ash_tile_x2z1.glb
stage4/meshes/ash_tile_x2z1_lod1.glb
stage4/meshes/frost_isl_aurora_arch.glb
stage4/meshes/frost_isl_aurora_arch_lod1.glb
stage4/meshes/frost_isl_frostreach.glb
stage4/meshes/frost_isl_frostreach_lod1.glb
stage4/meshes/frost_isl_frozen_wreck.glb
stage4/meshes/frost_isl_frozen_wreck_lod1.glb
stage4/meshes/frost_tile_x0z0.glb
stage4/meshes/frost_tile_x0z0_lod1.glb
stage4/meshes/frost_tile_x0z1.glb
stage4/meshes/frost_tile_x0z1_lod1.glb
stage4/meshes/frost_tile_x1z0.glb
stage4/meshes/frost_tile_x1z0_lod1.glb
stage4/meshes/frost_tile_x1z1.glb
stage4/meshes/frost_tile_x1z1_lod1.glb
stage4/meshes/frost_tile_x2z0.glb
stage4/meshes/frost_tile_x2z0_lod1.glb
stage4/meshes/frost_tile_x2z1.glb
stage4/meshes/frost_tile_x2z1_lod1.glb
stage4/meshes/frost_tile_x3z0.glb
stage4/meshes/frost_tile_x3z0_lod1.glb
stage4/meshes/frost_tile_x3z1.glb
stage4/meshes/frost_tile_x3z1_lod1.glb
```

Do not copy `land4/stageN/meshes/*_col.glb` or `*land_scatter*`. The tag's collision glbs stay. Do not copy `equipment/`, armor, or PR27. Do not edit `main.gd`.

## Patch

`tw_sea_land4_test54.patch` applies to `tidewrack/tw_sea.gd` from the tag. Dry-run against that blob succeeded (`patch --dry-run`). It inserts one branch **before** the ash `StandardMaterial3D` return, so ash terrain is not left on the basalt material, and it does not catch lava, steam, glow, ports, or scatter.

Region order is `arch_` 0, `coast_` 1, `frost_` 2, `ash_` 3. Frost's cold snow and blue-grey rock is `region == 2`. Ash terrain uses `lift 0.06`, `ambient 0.45`, `spec 0.12` (the approved stills). Other regions keep the shader defaults (`lift 0.03`, `ambient 0.35`, `spec 0.4`). Low tier sets `detail` to 0.55. That only scales normals. It does not drop samples.

Apply from a checkout of the tag, not from `main` if they ever diverge:

```
git checkout 33ec05515fa2907c1d6958e39e884eed92955776
git apply path/to/tw_sea_land4_test54.patch
```

## Renderer limit

15 `sampler2D` uniforms. The helpers expand to 26 `texture()` reads per fragment: two albedo taps for grass, soil, sand, and snow (8), two albedo taps on each of three rock planes (6), four ground normals plus three rock normals (7), five roughness taps.

The Compatibility renderer's GLES ceiling is 16 textures per shader. This project does not use that renderer. The Mobile renderer is Vulkan. Vulkan's guaranteed `maxPerStageDescriptorSamplers` is 16, and a spatial shader also receives the engine's lighting samplers (shadows, radiance) on top of the 15 uniforms. A device that only exposes the spec minimum can fail to link. A 2026 flagship usually exposes more than 16. That was not measured.

Compile evidence: Godot 4.4.1 GL Compatibility on llvmpipe linked this shader. The tag asks for Godot 4.7 Mobile. Godot 4.7 is not installed here (`/tmp/godot` is 4.4.1). No phone run. If the S26 build shows magenta terrain, the shader failed to link. Remove the `_land4_terrain` branch and the ground returns to `vc_lit.tres` or the ash `StandardMaterial3D`.

## Not in this candidate

Frost cliff outlines are still the mesh from `4f8c97f8`. The normal-slide rounder opened dark gullies and was not kept. The shader does not change the silhouette.

Stills are not a Galaxy S26 capture. The Capacitor workflow in `.github/workflows/build-android.yml` is the web game, not this Godot project.
