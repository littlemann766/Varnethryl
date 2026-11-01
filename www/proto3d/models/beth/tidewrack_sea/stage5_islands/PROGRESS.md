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
- 6c status at pause (run 5, ../walk_test_run5.json; harness tools/walk5.gd + dbg.py, run in a /tmp project with the region _col copies):
  all pass: gullhaven 5/5, frozen_wreck 4/4 | partial: lantern 4/5, vent 3/5, saltwatch 3/4, coil 3/4, aurora 2/4, hot_spring 3/5, obsidian 3/4, frostreach 4/7 (both causeway legs pass)
  failing: saltglass 2/9 (stair up/down pass; lower-shelf POI routes: final re-route can't leave the pier zone -> falls back to old route, snags at (-2134,21,-75)),
  beached_wreck 1/6 and ember_wreck 0/6 (same pier-zone disconnect + causeway ends: walker falls off the deck side near the end / approach ramp).
  Next: fix okw connectivity at the pier zone, widen causeway ends (flared approach, rails start after the ramp), then re-run remaining snags one island at a time.
- 6d: causeway ends opened (no rail on first/last span) + routes stay on the deck (no over-water corridor). Frostreach now 6/6 incl. both causeway legs.
  Tried and rolled back (made other islands worse, kept in /tmp only): bench cutting, wider path corridor, adaptive bank ramps, second Saltglass pier stair (bottom landed mid-slope).
  Final table in walk_test_final.json: 34/55 legs pass (pier boards excluded).
- 6e: Saltglass stair before/after renders (renders/small/saltglass_stair_before_after_A/B.jpg, checked by eye) + README Stage 6 section.

## 7 — built structures for the last gaps (walk test 34/55 -> 53/57)
- 7a (0e9d16a): Saltglass pier stair. A 6-flight tower stands in the water beside the pier head and climbs from 20.5 m to 68.7 m at 21.9 deg. Its top walk runs onto the lower shelf, and the POI routes follow the deck chain. Saltglass went from 4/10 to 9/10.
- 7b (6c28e67): bank stairs where causeways meet steep banks. Beached Wreck's far end gets 2 flights (1.2 -> 33.1 m). Ember Wreck gets one at each end (2.0 -> 12.3 m and 2.0 -> 8.0 m). Open causeway ends get 7 m wide approach ramps. Beached went from 0/5 to 5/5 and Ember from 0/5 to 2/5.
- 7c (fc581e3): the five snags. Coil Bones' spine is trimmed to fit inside its pad. POI centre props are off the walk graph, so routes end at the pad edge. No scatter rocks or plants within 3 m of a route. Aurora, Coil, Hot Spring, Saltwatch and Vent all pass.
- Still failing: Ember Vent and Scorched Chest (a steep terrain lip at 496,30,2268), Frozen Camp (a lip at -245,6,-2598) and Glass-diver's Chest (drops through at -2152,105,58).
- 9 (stage 9): Saltglass dock lift (88.3 m, 6 m/s) + locked shortcut ramp tower (10 x 17.5 deg) + 80.7 m skybridge to the plateau; gate/lever + flags (saltglass_shortcut_open, saltglass_lift_unlocked) as props/*.tscn. Walk test 66/66 (57 old + 9 new). Renders saltglass_lift_shortcut_before_after_A/B/C.jpg.
