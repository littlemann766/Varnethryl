# Beth round 2: notes for Lucky
Branch beth-world-art has been rebased onto 25f4fdc. The round-1 commit 38a2604 is now 0fc1b19 with the same content. None of Lucky's code files and none of the zone files are edited in this commit.

## What's new
- **Zone kits** (models/beth/{frost,volcano,port,hobcamp}/). Placement is in models/beth/PLACEMENT_{frost_town,frost_realm,volcano,port,hobcamps}.json, in world coords except frost_realm and port, which are relative to the realm centre and PORT_CENTER. `y:null` means snap to the ground.
  - Frost: frozen_pond (1200 tris), snow_drift_a/b (240), ice_spire (160), plus the round-1 ice and snow rocks and snowy pines.
  - Volcano: ash_tree (60), steam_vent (480, geometry only), basalt_boulder (80), plus basalt_columns and lavacrust_rock.
  - Port: pier_post (56), crate_stack (180), net_rack (828), ship_galleon (2984), ship_sloop (2280). The ships use the buildSailingShip frame (deck y≈1.64, bow +z), so animateMooredShip still works when they are parented to the existing ship group.
  - Hob camps: hob_tent2 and hob_tent2_red (84), hob_totem (232), hob_banner (14), hob_rack (62), plus the round-1 firepit and palisade. The layout copies hobcamps.js, with the open approach kept.
- **beth-zones.js**: `loadZonePlacement(zone)`, `placeZone(items,{heightAt,chunk,origin})` (one merged mesh per chunk on the shared atlas) and `kitMesh(file)`.
- **Building exteriors** (models/beth/buildings/bld_*.glb with a separate 1024 atlas and buildings_index.json).
  - Each file has a `walls` node and a `roof` node. The windmill also has a `blades` node that rotates about local Z.
  - They are in metres and built from the bldkit footprint and door data measured in audit/r2/bld_before.json. The door stays at local +z, x=0, ≥3.7×3.3 m.
  - Tris: house1 5362, house2 5972, house3 5238, house4 5982, farmhouse 7724, thieves 6760, barn 3570, stables 6868, windmill 2676, lighthouse 3644, gate_tower 1340. All are under 8k.
  - Integration: add the GLB at the building root with scale 1/K. Remove the textured G.ext meshes and the G.roof/G.frame/G.walls children, and put the `roof` node into G.roof so it hides when the player is inside. Set userData.merged so chunkStatics folds it in.
  - Meshes per building go from 12–28 ext meshes plus 2–16 roof meshes down to 2 (3 for the windmill).
- **Round-1 fixes**:
  - Leaf cards on the trees now use a smaller, alpha-cut leaf tile, so their shadows are cut out and not square.
  - oak and apple 138 tris, birch 98, boulder 80 (lighter).
  - Billboards are 3 crossed planes with spherical normals.
  - New oak_yellow and oak_red.

## How to preview
`git apply audit/proposed-townlands.diff audit/r2/preview-only-r2.diff` (throwaway; the second patch includes the round-1 main.js preview). Add `?nobeth` to compare.

## Proposals (not applied)
audit/r2/preview-only-r2.diff is the full integration reference: building swap, zones, harbor ships, hob-camp replacement and frost realm. Port its blocks into townlands.js (volcano and port), hobcamps.js, port-ships.js and frostreach.js where they belong.

## Known flaws
- Frost and volcano draw calls are not clearly below the old ones (see INGAME_NUMBERS.md). The square-grid chunk merge suits large spread-out rings badly.
- Windows are painted amber with no emissive, so night lighting is lost. The lighthouse loses its glow.
- The old houses were already detailed. The new shells look comparable rather than clearly better, and the roofs on the brown or red barn and stables changed hue.
- The house3/house4 front and lighthouse shots have the camera clipped inside a neighbour or blocked by a rock. The 3/4 shots are fine.
- The frost-realm shots come out almost black because of the realm's lighting at that camera, so they show little.
