# Stage 3 progress
- 3a. Cave mouths: deeper dark overhangs on Echo Grotto + Smugglers Throat (brow, overhang slab, dark underside, black opening fill, dripstone fringe). Done, checked by eye.
- 3a. Sea stacks: natural_stack() (tiered, leaning, darker, strata, wet notch, lichen/guano cap) replaces the pale cones in A + B; map islets in B are now low, rounded, dark rock. Done, checked.

## 3b — cave interiors + Sunken Ward (done)
- Fixed negative seed in ruined_house; houses moved to block centres so the 50 m streets are clear.
- Shaders: glow_vc, cave_water, cave_portal, kelp_sway, light_shaft (fog_disabled — fog made additive cones white), surface_under, seabed_caustics.
- render_stage3.gd: 4 shots/cave + 6 underwater, High+Low (36). Checked by eye; caves needed far more ambient/omni + cull off.
- Before/after: renders/small/S3_before_after_cave_mouths.jpg, S3_before_after_sea_stacks.jpg.
