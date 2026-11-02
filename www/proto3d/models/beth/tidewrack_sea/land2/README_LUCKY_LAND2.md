# Land pass 2 (Beth) - supersedes land1. Boss review first: nothing to main/live without his yes. None of your files edited.

## Islands (`tidewrack_sea/land2/`) - drop-in exactly like land1 (see ../land1/README_LUCKY_LAND1.md), plus:
- **Frost:** snow albedo/self-light lowered (no blown-out white), wind ripples + blue-shaded slopes; sea cliffs (<14 m up) are no
  longer reshaped or rock-tinted and render as clean glacier ice (vertical blue streaks, no horizontal stripes).
- **Saltglass:** cliff/outcrop displacement halved and low-frequency (no lumpy noise), starts 10 m up; chalky cliffs replaced by
  warm sandstone with soft bedding; salt crust only on ledges.
- **Ash:** basalt-dark base, cooled lava flows, pale ash dunes, sulphur crusts, cinder speckle, sparse glowing ember seams;
  scatter ~6x denser (5.1k instances: lava rocks, sulphur crystals, ash grass, cinders, basalt columns, obsidian, dead trees).
  **Material change vs land1:** for ash terrain use `lift 0.045, ambient 1.0` (land1 said 0.14/1.2 - that washed the new detail out):
```gdscript
	if n.contains("_tile_") or n == "arch_islands" or (n.contains("_isl_") and not n.ends_with("_glow") and not n.ends_with("_port")):
		var t := _sh("stage1/shaders/vc_terrain.gdshader"); t.set_shader_parameter("region", ["arch_", "coast_", "frost_", "ash_"].find(n.substr(0, n.find("_") + 1)))
		if n.begins_with("ash_"): t.set_shader_parameter("lift", 0.045); t.set_shader_parameter("ambient", 1.0); t.set_shader_parameter("spec", 0.075)
		if not high(): t.set_shader_parameter("detail", 0.5)
		return t
```
- **Grass:** two rotated high-frequency blade layers inside 38 m of the camera (no grid pattern), dark gaps between blades.
- Small no-collider scatter (tufts, stones, cinders) may now sit beside paths; trees/boulders with colliders still keep 4.5 m off routes.
- Tris: terrain as land1 except Saltglass/Frost slightly lower; scatter High A 159k, B 236k, frost 405k, ash 561k per region in 26-69 chunks (lod1 ~20%).

## Mainland (`terrain_pass/mainland_land2/ground4.gdshader`) - needs 1-3 code lines (main.gd), your call
1. **Shader (art, drop-in, same uniforms as ground2):** copy to `res://terrain_fix2/ground/ground4.gdshader` and in `_terrain()` change
   `load("res://terrain_fix2/ground/ground2.gdshader")` -> `ground4.gdshader`. Adds crisp near grass blades, scree band at the foot
   of the range, eroded rock (gullies down the fall line, lichen), softer blue-shaded snow, scorched ash + cinders + faint ember
   glow around the volcano (blends out through dry grass by ~430 m from `volc_c`).
2. **Mountain shape (code, optional):** in `_height_raw`, replace the `h += mr * (...)` line with:
```gdscript
		var rgs := smoothstep(0.0, 1.0, rg); rgs = rgs * rgs * (0.55 + 0.45 * rgs)
		var gl := absf(noise.get_noise_2d(x * 3.6 - 120.0, z * 3.6 + 640.0))   # erosion gullies
		h += mr * (60.0 + (40.0 + 215.0 * rgs) * (0.3 + 0.7 * massif) + 14.0 * rg2 * rg2 * mr) - mr * 18.0 * (1.0 - smoothstep(0.0, 0.18, gl)) * smoothstep(0.2, 0.6, rgs)
```
   Only affects r >~ 800 m (the range). Afterwards re-bake `terrain_n.png` (terrain_pass/mainland/tools/bake_n.gd) and re-run reseat.gd for scatter in the range.
3. **Known gap (code):** the grass blade meshes / far grass still draw green blades over the new scorched ground near the volcano.
   Thin them with a mask (e.g. skip instances within ~300 m of VOLC) or tint by distance - needs a change in your grass code.
Tested in a /tmp copy of test 49 via `--tfshots` (+5 views: volcano_near, mtn_north, mtn_east, foothills_w). Renders came out on the
GL Compatibility fallback (no Vulkan in the headless box), so check colours on the S26 Mobile renderer.
