# Stage 5 - island interiors behind the 13 landings
- 5a: read tw_sea.gd (Lucky's loader): region dirs auto-load every `{pre}*.glb` (+_lod1 on Low, `_col` -> trimesh StaticBody, `_glow` -> glow_vc).
  Plan: per landing `{pre}isl_<id>.glb/_lod1/_col/_glow` overlay patch (base terrain sampled from stage1/2/4 tiles, +0.08 m, cut around existing props, pier-head area kept at base height).
- 5b: builder + render5 working on Lantern Rock (paths <=31 deg, rim tucked under base, window-edge fade, slope softening). Render shadows off (PSSM acne, render-only).
- 5c: bridges for islet landings (frostreach 58 m, beached_wreck 39 m, ember_wreck 16 m), directional-grade router, bench-fill paths, POIs only on ground reachable at <=35 deg. All 13 built.
- 5d: renders checked by eye, smalls + README_LUCKY done.
