# Beth round 3: notes for Lucky (Godot target)
Branch beth-world-art. No Lucky code files or zone files were edited.

## Contents
- **16 more building exteriors** in models/beth/buildings: guildhall, library, townhall, mage, treasury, crypt, market, apothecary, bakery, inn, smithy, training, keep (corner towers, crenellated flat roof, banners), temple (columned portico), observatory (round with dome) and colosseum (arched ring).
  - Footprints and door positions come from bldview measurements (audit/r3/bld_before.json and bld_spec.json). The door is on local +z at x=0, 3.7 × 3.3 m.
  - All are ≤8k tris, with 2 meshes per building (walls and roof) on one shared 1024 atlas. Tris are in NUMBERS.md.
- **Emissive night windows (newly allowed).** Every building GLB now carries `emissiveTexture` = buildings/atlas/emissive.png. It is a mask that is black everywhere except the window and lantern-glass panes, with emissiveFactor 1.
  - To get a night glow, scale `emission_energy_multiplier` with time of day (0 by day, about 1–2 at night). It is free: no extra draw calls and one extra texture fetch.
  - On the Low tier, set the energy to 0 or disable emission.
  - The round-2 buildings were rebuilt with the same mask.
- **Road, wall and town dressing** in models/beth/dressing, all on the building atlas: curb_2m, cobble_edge_2m, lantern_post, wall_lantern, signpost, milestone, well, market stalls (red/blue/green), banner poles (blue/red), wall_cap_4m, rubble, bench, flower_planter.
  - Placements: PLACEMENT_dressing_town.json (560 items: street edges, plaza curb, stalls, benches, banners, wells, wall lanterns, rubble) and PLACEMENT_dressing_roads.json (143: milestones, signposts, rubble, road decals).
  - Merge them per chunk (beth-zones.js `placeDressing` does this in three.js; in Godot use a MultiMesh per file, or merge per chunk with SurfaceTool).
- **Decals** in models/beth/decals: a separate 512 alpha-cut atlas with moss, cracks, dirt, grime, soot, leaves and puddle, as 2-tri quads. PLACEMENT_decals.json has 314 items on wall feet, streets and building fronts.
  - In Godot, set the material to alpha scissor 0.5, depth-draw opaque, with a render priority or a small offset. Real Decal nodes would cost more.
- **Terrain and mountain pieces** in models/beth/terrain: mountain_peak_snow, mountain_peak_bare, volcano_cone_flank, cliff_ridge_60m, scree_slope, grass_mound, rock_arch.
  - Each has _lod1, and the big ones have _lod2 too: High = base, Medium = lod1, Low = lod2/lod1. Use Godot visibility ranges or the auto-LOD.
- **Volcano titan files** (ashentitan_volcano_11x, projectiles, VOLCANO_TITAN.md) are in models/beth/volcano.

## Godot import check
- I worked in a copy of godot-proto at /tmp/gp3, with /workspace/godot-proto untouched. Godot 4.7.2 Mobile on llvmpipe.
- 38/38 GLBs imported and instanced cleanly: 16 buildings, 15 dressing, 7 terrain, plus the decals.
- Shots are in audit/r3/godot/ and contact_godot_r3.png, covering day, night (emissive windows) and decals.
- The harness is audit/r3/godot/lineup.gd/.tscn.
- **Important:** Godot's glTF importer does NOT enable vertex colours. All Beth tints (slate-blue roofs, banner colours, stall fruit, rock shading) live in COLOR_0. Set `vertex_color_use_as_albedo = true` on imported materials. lineup.gd `_vc()` does it at runtime; a post-import script or material override is better. Without it, banners come out white and rocks look washed out.

## Known flaws
- I didn't measure in game (in Godot or three.js) the before/after draw calls with the dressing placed, nor retake the bad round-2 three.js shots. The direction moved to Godot and three.js preview work was dropped. NUMBERS.md has the asset numbers and an estimate.
- The new exteriors have more tris than the old ext+roof for most buildings (for example apothecary 3.1k→6.3k and inn 4.6k→7.9k) but far fewer meshes (≈25–50 → 2). The keep, temple, mage and observatory went down.
- The exteriors are generic: a parametric house shell with style options. Unique features of the old models (towers on the mage academy, the library's details, the colosseum's interior seating) are NOT reproduced. The keep, temple, observatory and colosseum got bespoke but simple shapes.
- Fountain, port warehouse/dock, gatehouse body and town walls have no new exterior. Wall caps were built but not placed, because the existing parapet already occupies the wall top.
- The dressing pieces are below the 300-tri prop floor on purpose: they are batch pieces.
- Terrain pieces are icosphere blobs: they read as chunky low-poly rocks, and the snow cap is weak. They have no placement yet.
- The street-edge placement assumes the three.js street widths (N-S 8.5 m, E-W 6.8 m, plaza r 36.4 m) and flat town ground at y=0. Recheck it against the Godot town layout.
