# Owner run rework (2026-10-25)
Replaces the `Running` clip in `varnethryl-owner-test/owner-animated.glb` (the rig the game actually loads for `n:owner`)
with a procedural "warrior king" sprint built by `gen.js` (params in `P`), and sets `SPEEDS['n:owner'].run = 6.08`
(native m/s of the new clip = game run speed 9.67 world / mscale 1.592) so it plays at 1.0x with planted feet.

Old problem: the old clip covers ~4.7 native m/s but was profiled as 2.28, so at run speed it was clamped to 2.4x
(455 steps/min shuffle) and feet skated ~5-5.7 native m/s.

Regenerate: `npm i puppeteer-core` here, `node serve.mjs &` (paths in serve.mjs), `node export.mjs` -> newrun.json,
`python3 splice.py <orig.glb> <out.glb>`; videos: `node render.mjs old <timeScale> 6.08 out.mp4 [glbUrl]`; slide: `node slide.mjs old 1 6.08 [glbUrl]`.

## Walk (v1.5.34)
`Walking` clip is now also procedural (`PW` in gen.js): heel-strike/toe-roll IK walk, 2.0 native m/s, 140 steps/min,
upright chest. Owner walk-mode travel speed is scaled by OWNER_WALK_MUL (2.0/3.04) because the generic walk speed is a jog
for him. Walk<->run blend is phase-synced (`userData.phaseSync`). `node export.mjs walk` -> newwalk.json; splice.py writes both clips.

## v2 (1.5.35, boss 9:40 AM)
Running = the ORIGINAL Mixamo run clip, resampled so phase 0 = left touchdown (exportold.mjs) for the synced blend; SPEEDS run 4.63 (measured) so it plays 1.31x at run speed. Walking = procedural walk. `python3 splice.py orig.glb out.glb oldrun_shift.json=Running newwalk.json=Walking`
