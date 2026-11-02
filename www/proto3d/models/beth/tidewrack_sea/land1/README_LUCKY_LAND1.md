# Land pass 1 (Beth): Tidewrack island terrain, ground detail, mountains, scatter, border blending
Status: FIRST PASS for boss review. Do NOT merge to main/live until the boss says yes. None of your files were edited.

## What's here (mirrors `res://tidewrack/stageN/meshes/`)
- `stage1|stage2|stage4/meshes/<same name>.glb` + `_lod1.glb`: the terrain meshes (`*_tile_*`, `arch_islands`, `*_isl_<id>`), rebuilt from the
  game's current files (godot-voxel test 49):
  - **Mountains/hills:** steep (>26 deg) elevated faces get red-green midpoint refinement (1-2 levels) and ridged/gully/strata displacement.
    Walkable ground (<24 deg), docks (30 m), POIs (r+8 m), POI routes/paths (4.5 m), causeways, anything within 4 m of a prop,
    tile seams, overhangs/arches, and all island patches (`*_isl_*`) keep their exact shape, so walk paths, colliders and props still match.
  - Smooth NORMALs added; COLOR_0 is ubyte normalized; **COLOR.a = 1 natural ground / 0 placed prop** (used by the shader).
  - Biome colours world-space blended (6 m on island patches, 16 m on tiles) => soft region borders; rock tone pulled onto cliffs.
  - lod1 = your original lod1 geometry with the new colours/mask transferred (<= 50% of the new High everywhere).
- `{pre}land_scatter_cXX_YY.glb` / `_lod1` / `_col`: biome scatter in 256 m chunks. `tw_sea._files()` already loads them (prefix match),
  `_col` becomes trimesh StaticBodies (tree trunks, boulders). Gets vc_flat (ash: lifted basalt) from `_mat_for` as-is.
  A: pine, oak, bush, grass tufts, boulders, stones. B Saltglass: shore pine, scrub, dune grass, salt crystals, pale boulders/stones.
  Frost: snow pines, ice shards, dead trees, snow boulders. Ash: dead trees, basalt columns, obsidian, boulders. Counts: `scatter_stats.json`.
- `shaders/vc_terrain.gdshader`: layered procedural ground (grass blades/tufts/dry & lush patches/dirt, sand ripples + wet shore, snow drifts
  + blue slopes, slope rock with warped strata/cracks/lichen/salt crust/ember seams), noise-warped layer borders, bump relief that fades
  with distance. Same uniforms as vc_flat (`lift`, `ambient`, `spec`) + `region` (0 A, 1 B, 2 frost, 3 ash) + `detail`. Keeps hero_cut + near fade.

## Drop-in (Lucky)
1. Copy `land1/stageN/meshes/*` over `res://tidewrack/stageN/meshes/` (same names; scatter files are new).
2. Copy `shaders/vc_terrain.gdshader` to `res://tidewrack/stage1/shaders/`.
3. `tw_sea.gd _mat_for(n)`, before the `ash_` vc_flat line:
```gdscript
	if n.contains("_tile_") or n == "arch_islands" or (n.contains("_isl_") and not n.ends_with("_glow") and not n.ends_with("_port")):
		var t := _sh("stage1/shaders/vc_terrain.gdshader"); t.set_shader_parameter("region", ["arch_", "coast_", "frost_", "ash_"].find(n.substr(0, n.find("_") + 1)))
		if n.begins_with("ash_"): t.set_shader_parameter("lift", 0.14); t.set_shader_parameter("ambient", 1.2); t.set_shader_parameter("spec", 0.075)
		if not high(): t.set_shader_parameter("detail", 0.5)
		return t
```
4. Add vc_terrain to the shader warm-up.
Tri counts: `terrain_stats_all.json` (High terrain A 251k, B 475k, frost 572k, ash 242k per whole region, streamed + culled per tile;
was 210/237/261/211k). Scatter High A 150k, B 228k, frost 408k, ash 98k per region in 25-68 chunks (lod1 20-24%).

## Not done yet (honest)
- Mainland (main.gd height()/ground3) is not in this pass. Low tier keeps the old lod1 shapes. Not tested inside a full game build yet,
  only in a Mobile-renderer harness (`tools/render.gd`) loading the real region files with the game's materials.
