# Tidewrack Sea art (Beth)
- stage1/: the Archipelago (region A), Brinecrown Coil, and ship upgrades.
- stage2/: the Saltglass Coast (region B) and the Sunken Ward dive spot.
- map/: the v4 world map and its generator.

The land-mask .npz is not committed because of its size (35 MB). To rebuild it, run map/draw_combined_v4.py.
The build scripts in stage*/tools expect /workspace/godot-art paths, so adjust ROOT if you rebuild somewhere else.
