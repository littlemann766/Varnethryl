# Tidewrack Sea Stage 4 — Region C (the Straits) + polish (Beth)

## 4a map fields
- frost/ash signed fields regenerated from map/draw_combined_v4.py (same seeds), saved to ocean_stage4/map/straits_fields.npz (map file untouched).

## 4b region C built (iterating)
- C-N Frost Strait: ice-shelf terrain (cliffs w/ buttresses, crevasse + strata colours, shelf near harbour), Rimefang Narrows (gorge carved through the shelf; min 57 m, mean 195 m),
  floes (520), 3 iceberg variants x12 drifting instances, icicle fringes + 9 frozen falls, Frostreach Ice Dock, Rimefang Maw (cleft carved), Frozen Wreck, Aurora Arch.
- C-S Ash Strait: basalt terrain + ridged Cinderreach volcano w/ crater lake, Cinder Gate (lava spit added to the map field; min 106 m), lava seams (3 shore contours + 9 rivulets),
  34 vents + steam plumes, Vent Harbour, Obsidian Arch, Ember Wreck, Hot-spring Grotto. Fog v2 border per region with frost/ash tints.
- Render pass 1: cliffs too tall/smooth, arch edge-on, ash too brown, steam too thin -> fixed in pass 2/3.

## 4c
- Fixed ash white-foam water: test copy had a stale shore_dist png (old rect); also shore_dist now baked from terrain height; ash sky horizon darkened; Low water `rough` uniform (ash 0.45).
- Final renders checked by eye (24 shots), smalls + contact sheets + polish before/after in renders/small.
- 4d: committed 1764517, pushed to beth-world-art; /tmp test dirs deleted.
- 4e: Echo spike root cause = old shot camera inside north-bank cliff (fixed with clear_dist); ash Low water own shader (cool, less specular); stage1 Low shader reverted to original.
