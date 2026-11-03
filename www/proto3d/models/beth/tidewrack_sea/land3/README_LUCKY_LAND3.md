# Land pass 3 (Beth) - supersedes land2. Boss review first; nothing to main/live. None of your files edited.

## Islands (`tidewrack_sea/land3/`) - drop-in exactly like land1/land2 (same file names, see ../land1/README_LUCKY_LAND1.md)
- **Ash landmarks:** 406 spaced landmarks (>= 26 m apart, off paths/docks/props): lava spires (2-4 jagged cones 5-14 m, ember tips),
  boulder clusters (3-5 rocks, 2-5 m), basalt column stacks (3-9 m). Each has a 4 m collider core in its chunk `_col`.
  Small filler cut back (cinders/stones/ash grass) so **Ash scatter High went down 561k -> 449k tris** (lod1 19%).
- **Ash ground** brighter basalt + pale ash dunes so the detail reads under your ACES env. **Material update for ash terrain:**
  `lift 0.1, ambient 1.25, spec 0.075` (replaces land2's 0.045/1.0):
```gdscript
	if n.contains("_tile_") or n == "arch_islands" or (n.contains("_isl_") and not n.ends_with("_glow") and not n.ends_with("_port")):
		var t := _sh("stage1/shaders/vc_terrain.gdshader"); t.set_shader_parameter("region", ["arch_", "coast_", "frost_", "ash_"].find(n.substr(0, n.find("_") + 1)))
		if n.begins_with("ash_"): t.set_shader_parameter("lift", 0.1); t.set_shader_parameter("ambient", 1.25); t.set_shader_parameter("spec", 0.075)
		if not high(): t.set_shader_parameter("detail", 0.5)
		return t
```
- **Frost snow:** off-white blue-grey base (0.5/0.555/0.65 linear), blue hollows + blue shaded slopes, long wind-drift bands,
  sastrugi ridges, sparse sparkle; snow self-light cut to 20%. Measured on screen ~211-236 instead of clipped 255 (render env now
  matches main.gd `_env()`: ACES, white 6, contrast 1.08, saturation 1.12). Renders are on the Compatibility fallback (no Vulkan on the
  box); Mobile usually shows ~5-10% darker, which is the side we want - please confirm on the S26.

## Mainland (`terrain_pass/mainland_land3/`)
- `ground5.gdshader` = ground4 + **meadow variety** (heather tint, buttercup and clover drifts, mossy hollows, bleached bents, r 240-820 m)
  and the scorch moved in to 165-245 m from `volc_c` (dry grass out to ~340 m). Same uniforms as ground2: in `_terrain()` load it instead of ground2.
- **Green-over-scorch fix:**
  - `far_grass.gdshader` (my terrain_fix2 file): drop-in over `res://terrain_fix2/grass/far_grass.gdshader` - collapses clumps inside the
    scorch, dries them toward the edge, adds lush/seed-head tint variety. No code change.
  - `terrain_flowers.gdshader` (my file): drop-in over `res://terrain_flowers/terrain_flowers.gdshader` - no flowers on the scorch.
  - Near grass is your `scripts/grass.gdshader`, so it needs **1 code line**: in `_grass()` change
    `load("res://scripts/grass.gdshader")` -> `load("res://terrain_pass/grass_land3.gdshader")` (copy `grass_land3.gdshader` there). Same uniforms + `volc_c`, `dry_col`.
  - Not covered: the trees/bushes of `terrain_scatter.scn` near the volcano are still green (only a few now that the scorch is tighter).
- Optional mountain hunk from land2 README still applies (the after shots use it).
