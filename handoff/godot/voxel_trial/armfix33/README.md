# armfix33 (test 33): arms clipping through legs
Tool: tools/capes/armfix33.py. Per frame, the upper arm is turned outward about the shoulder (front axis) by the smallest angle that clears the legs (cap 40°, fly clips 60°), smoothed over ±4 frames and baked. Only the upperArm rotation changes; the wrist fix and other bones are kept.
Measure = arm cubes (18 mm cells) inside leg cells, worst side, every frame. Per-clip before/after in *.armfix.json.
- on_capefix32/: on Beth's cape_fix32/glb (+robes Wren). These lack the test-32 clips (jump/swim, run fix).
- on_sealed_v3/: same fix on glb_sealed_v3 (test 32 motion incl. jump/swim), no Beth cape fix.
Godot 4.7.2 headless import: 0 errors, chk.gd PASS (godot_chk_t33.txt).
