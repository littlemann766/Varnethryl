# Stage 5 - island interiors behind the 13 landings
- 5a: read tw_sea.gd (Lucky's loader): region dirs auto-load every `{pre}*.glb` (+_lod1 on Low, `_col` -> trimesh StaticBody, `_glow` -> glow_vc).
  Plan: per landing `{pre}isl_<id>.glb/_lod1/_col/_glow` overlay patch (base terrain sampled from stage1/2/4 tiles, +0.08 m, cut around existing props, pier-head area kept at base height).
- 5b: builder + render5 working on Lantern Rock (paths <=31 deg, rim tucked under base, window-edge fade, slope softening). Render shadows off (PSSM acne, render-only).
- 5c: bridges for islet landings (frostreach 58 m, beached_wreck 39 m, ember_wreck 16 m), directional-grade router, bench-fill paths, POIs only on ground reachable at <=35 deg. All 13 built.
- 5d: renders checked by eye, smalls + README_LUCKY done.
- 5e: committed 014f54f to beth-world-art (fresh sparse clone in /tmp - /workspace/beth-world's git dir is gone with vgpt-cmp); /tmp cleaned.
- 6a: Saltglass switchback stair (5 flights 19.6 deg, rise 35.7 m, stone slabs + rails + pillars, in _col) + 2 plateau POIs; routes exported to manifest.
- 6a done (walk-verified): Saltglass stair 5 flights 19.6 deg, landings span both flights (rail on outer side only), top walk flat then eases onto plateau, foot dips under the shelf. Walk test: stair up PASS, stair down PASS. Top POIs: Saltglass Lookout, Clifftop Cache.
- 6b done: lane check - no stage 1-4 route/lane crosses Frostreach (nearest Rimefang Narrows 309 m), Beached Wreck (no lane) or Ember Wreck (Cinder Gate 631 m) causeways -> no arch needed, causeways stay low. Caveat: gap under Frostreach deck is technically sailable (>=8 m water) but no route uses it.
- 6c in progress (walk test, capsule = Lucky's ashore physics): builder fixes so far - route y from final mesh, bench fill no longer cuts trenches, patch rides >=0.08 m above the game's coarse terrain collider (bulge-sampled), full-res patch collider, edges fade onto the game collider, holes only for standing props (flush decals re-laid on the patch), final re-route on the finished surface >=4 m inside the rim, causeway approach ramps, terrain kept out of stair headroom.
  Run 5: gullhaven 5/5, frozen_wreck 4/4, others partial; ~45/71 legs pass. Lucky's own pier boards on 7 steep landings (31-49 deg) fail by design of the board (not stage 5).
