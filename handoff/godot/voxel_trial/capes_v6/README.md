# capes_v6 (test 32), from capes_v5
- Run: removed the shin pop (60°→35°/frame max) and capped arm abduction (57-88°→25-30°). Hands are kept off the thighs with forearm bend. Walk and run plant feet have a lateral lock (drift is about 0).
- New clips jump, jump_start, jump_loop, jump_land, swim_tread and swim_stroke for Owner, Selene and Darius (Quaternius UAL1, CC0). The hand offset is fixed, and the feet are locked where they are on the ground.
- Selene death: right-leg kick and snap at frames 41-44 bridged (98°→29°).
- Villain death: wrist clamped from 169° to 60°. Twist is kept at ±60° on all clips.
- metrics/: <name>_before.json and _after.json (meas32), check1 arm-leg and cape, mfix logs.
- Clip 'jump_loop' renamed to 'jump_hang', because Godot strips a _loop suffix and it collided with 'jump'. Godot 4.7.2 import of all 55 test-32 files (Beth's glb_sealed_v3, capes_v6, Titan v2, trolls v8): 0 errors, chk.gd RESULT PASS (godot_chk_t32.txt).
