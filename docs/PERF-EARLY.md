# PERF-EARLY: early-game lag in Varnethryl 3D (branch perf-early, v0.7.6)

Base: origin/main caa209a (v0.7.5). Method: headless Chromium (swiftshader software GL), CDP CPU throttle 4x/6x, 20 s window, single run per cell (noisy). Script: /workspace/varn/perf_measure.py. Software GL makes frame times GPU-bound and not representative of phones, so the main-thread numbers (first frame, TTI, long tasks, calls) are the ones to trust.

## Before -> after
| viewport | thr | party/npc | first frame ms (b→a) | TTI ms | longtasks sum ms | longest task ms | draw calls | programs | geometries |
|---|---|---|---|---|---|---|---|---|---|
| 412x915 | 4x | on | 6095→5486 | 8084→6993 | 7252→4660 | 4106→2009 | 223→159 | 27→31 | 241→116 |
| 412x915 | 4x | off | 5170→3020 | 6277→3566 | 5705→3430 | 3698→1547 | 125→107 | 25→30 | 144→66 |
| 412x915 | 6x | on | 7441→5295 | 10763→7171 | 9527→6280 | 5339→2233 | 223→159 | 27→31 | 241→116 |
| 412x915 | 6x | off | 8845→5200 | 10502→6366 | 9025→5933 | 6352→2828 | 125→107 | 25→30 | 144→66 |
| 1920x1080 | 4x | on | 6156→4641 | 8654→5624 | 6866→3497 | 4070→1868 | 235→171 | 27→31 | 252→127 |
| 1920x1080 | 4x | off | 7046→4869 | 8075→5635 | 5858→3811 | 4433→2035 | 136→118 | 25→30 | 155→77 |
| 1920x1080 | 6x | on | 9477→4860 | 13005→6189 | 11128→5353 | 6851→2683 | 235→171 | 27→31 | 252→127 |
| 1920x1080 | 6x | off | 7062→4444 | None→5135 | 6728→4410 | 5203→2522 | 136→118 | 25→30 | 155→77 |

Hero-on-screen time (marks, party+NPC on, default): 4x 5.4-5.9 s -> 4.1-4.2 s; 6x 7.2 s -> 5.2 s. All 3 crowd members loaded: 4x 6.1-7.4 s -> 4.6-4.7 s; 6x 8.3-8.6 s -> 5.9-6.3 s.
Draw calls per character (merged GLB): about 33 -> 16-19 (hero 24 -> 15). Visuals compared by screenshot diff: same.

## Causes found and fixed
1. **Biggest**: bldkit.js M() built its material cache key with JSON.stringify(extra); extra contains a Texture, so Texture.toJSON encoded the whole image to a PNG data URL, repeatedly. About 1.1 s unthrottled, a 4-6 s single main-thread task at 4-6x. Key now uses texture uuid / colour hex.
2. Procedural stand-in heroes (Aldric/Darius/Selene canvas textures + goldMask pixel loops, about 1.2 s at 4x) were built every start although GLBs replace them. Now built only for ?procedural or if the GLB fails.
3. GLB downloads now start at the very top of main.js (saved party resolved first, fetch memoised), overlapping the village build.
4. Shader prewarm: after the first frame, character material variants (skinned, vertex colour, map, double sided, alpha test, x-ray ghost, blob) are compiled via compileAsync (when KHR_parallel_shader_compile exists, else compile). GLB wrapping waits for it (2.5 s cap). Programs created after hero arrival: 9 -> 0.
5. mergeRigidParts: materials that differ only by flat colour are merged into shared vertex-coloured MeshStandardMaterials (colour baked into a vertex attribute; roughness/metalness snapped to 0.1 steps; textured ones merge only with same image + uv transform).
6. wrapGLB: removed Box3.setFromObject on skinned meshes (about 100 ms per hero). It returned NaN for merged heroes, so they were never rescaled; behaviour kept (rescale only when nothing was merged).
7. Added startup marks (window.__p3dMarks: mainStart, villageBuilt, firstFrame, hero:<id>, crowd:<id>, prewarmed, renderMs[]).

Not changed: pixel ratio already capped at 1.5 with adaptive scaling; GLB textures are already tiny (128-512 px, 2-54 KB); world generation (about 1.4 s at 4x, buildVillage) is still one synchronous block; spreading it across frames would be the next step.

## Checks
node --check all proto3d js: ok. core_test, save3d_test, bump_test, owner_cheats_test: ALL PASS. Browser: proto3d_test, save3d_browser_test fail exactly the same tests as origin/main (inn door/side wall; 176 baseline; bad p3d fallback). owner_cheats_browser_test: "version label" and "solid building box" fail also on the unmodified build (box returns None there too). bump_browser_test only fails its BASE_CALLS baseline check (env var not set). party_test needs a server on :8099 (not run).

## Risks
- Hero is visible a bit later than the world (waits for prewarm); on devices without parallel compile prewarm is a sync stall, but before the hero shows.
- Roughness/metalness snapping (max 0.05 change) and merged materials: visually identical in screenshots but not bit-exact.
- fix061 expects the procedural Aldric stand-in at start; it no longer exists by default (that test already failed on main).
- Not tested on a real phone/GPU.
