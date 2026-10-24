# Beth world-art kit (for Lucky) — branch `beth-world-art` off a8aa181

**Nothing here is wired into the game. Nothing is pushed.** I only added new files; I didn't touch any file on your no-edit list.
The preview screenshots came from a throwaway local patch that is *not committed*. It's saved as diffs in `audit/` so you can see exactly what I ran.

## What's here
- `atlas/atlas.webp` (116 KB) + `atlas/atlas.png` fallback: ONE shared 1024² atlas (4×4 tiles of 256: bark, leaf card, pine card, grass card, flower card, rock, wood, iron, snow, ice, basalt, lava crust, cloth, cobble, oak and pine impostors). Each GLB references it externally (EXT_texture_webp with a png fallback), so the atlas downloads once.
- 76 GLBs, each **one mesh, one primitive, one material** (`beth_kit_atlas`: Standard, metalness 0, roughness 0.85, alphaTest 0.5, double-sided, COLOR_0 tint). Y-up, metres, origin at the base centre. List in `kit_index.json` (file, tris, height, width).
  - `trees/` oak a/b/autumn/yellow/red, apple_blossom, birch, pine a/b, pine_snow, dead. Each comes in full, `_lod1` and `_bb` (4-tri crossed billboard) versions.
  - `veg/` bush a/b, grass a/dry, flowers white/yellow/purple/red/blue (6–88 tris).
  - `rocks/` rock_small, rock_mossy, boulder, rock_slab, standing_stone, cliff_a/b (720).
  - `props/` fence_2m, crate, barrel, cart, lamp_post (the lantern is pale cloth with no emissive).
  - `frost/`, `volcano/` (lava cracks are painted into the albedo, no emissive), `port/` (dock_10m, ship_cog), `hobcamp/`, `ruins/` (wall, arch with a 1.6 × 3.4 m opening, path_stones).
  - `clusters/` 11 merged sets for empty land: grove, pine stand, meadow, outcrop a/b, ruins, roadside, frost, volcano, hob camp, port dock (180–2.5k tris).
- `PLACEMENT.json`: 70 cluster placements between zones, generated with your own `possible()`/`clear()` rules from townlands.js. y = `townElevation(x,z)-0.05`. Also has the rule-based replacements and the unplaced zone kits.
- `../../beth-kit.js` (new file): loads the kit with top-level await and exports `KIT.geo/material/Acc/forVariant/placement`. Rewrite or drop it as you like.
- `kit-viewer.html?cat=trees&lod=1`: contact-sheet viewer.
- Generator: `tools/beth/{atlas,kit,assets,build}.py` (numpy + PIL). Run `python3 tools/beth/build.py www/proto3d/models/beth`.

## How to wire it (proposal, your call)
1. `audit/proposed-townlands.diff` (30 lines):
   - `put()` asks `KIT.forVariant()` first and accumulates into kit chunks that keep uv. It falls back to makeVariant when the kit is missing.
   - Tree billboards go into a `far` layer of 128 m chunks.
   - The clusters from PLACEMENT.json go into the same chunk batches, so they add no draw calls. Outcrops, ruins and volcano clusters get one circle collider.
   - The cull keeps near detail to 90 m (grass and flowers to 60 m) and shows the billboards from 55 to 170 m.
2. `audit/preview-only-main.diff`: the tree block after `window.__treeCount` swaps 3 instanced cone meshes for 1 merged kit mesh. The `__P`/`__PV_HOOK` lines in it are only for my screenshots, so drop them.

## Not my files, but the biggest wins for the 300-call target (see audit/PROFILE.md)
- Ladders: each of the 59 ladders makes its own 3 InstancedMeshes. One shared InstancedMesh per part (rails, rungs, anchors) for all ladders would recover most of what they cost now: hiding every ladder removed 21 calls in town and 61 at outskirts_east.
- Building merged chunks are about 180 calls in town. Fewer material classes per zone (the atlas approach) is the lever.
