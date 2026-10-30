# Ship upgrades: spec for Lucky's code (Stage 1)
Your galleon (ship_tidewrack_sailing_ship*.glb, 30 m) and skiff (ship_boat_sail*.glb, 7 m) are never edited.
Each tier is one add-on mesh, parented to the ship root with an identity transform (same origin, bow +Z, waterline y 0):
meshes/upg_galleon_t1..t3.glb and meshes/upg_skiff_t1..t3.glb, each with a _lod1 at 45% tris.
It costs +1 draw call per ship. Only the current tier is shown (never stacked), and its shadows are off.

## Tiers (what you see)
| Tier | Name | Sails | Rigging | Hull trim | Figurehead | Wind charm |
|---|---|---|---|---|---|---|
| T0 | Base | your model's own | your model | none | none | none |
| T1 | Patched Canvas | cream course + topsail per mast, a bit larger than base | 2 shrouds a side + forestay | copper gunwale rail | carved post | small pale-glass charm at the stern |
| T2 | Gullwing Rig | white with red stripes, bigger, + jib | 3 shrouds a side | brass rail + waterline band | white gull, wings spread | brighter teal charm, 3 vanes |
| T3 | Stormsilk | deep-blue silk with gold stripes, biggest, + jib, spanker, bowsprit | 4 shrouds a side | gold rail + waterline band | gold tide-warden with a glowing lantern orb | glowing cyan charm, 4 vanes |

## Speeds (proposal)
A typical Stage 1 crossing is about 2.4 km (for example, the Tidewrack bay mouth to Gullhaven).

| | T0 | T1 | T2 | T3 |
|---|---|---|---|---|
| Galleon top speed (m/s) | 13 | 16 | 20 | 26 |
| Time for 2.4 km | ~3.1 min | ~2.5 min | 2.0 min | ~1.5 min |
| Galleon accel (m/s2) / turn (deg/s) | 1.2 / 14 | 1.5 / 16 | 1.9 / 18 | 2.4 / 20 |
| Skiff top speed (m/s) | 9 | 11 | 13.5 | 17 |
| Skiff accel / turn | 2.0 / 40 | 2.4 / 44 | 2.9 / 48 | 3.5 / 52 |

- The skiff stays slower than the galleon on purpose. It is for caves, shallows and the Wreck Reef.
- Wind: speed = top * lerp(0.55, 1.15, a), where a = clamp(dot(heading, wind_dir) * 0.5 + 0.5, 0, 1), using the per-region wind.
- Shallows: within 25 m of land (from shaders/arch_shore_dist.png), the galleon is capped at 40% speed.
- Wind charm "gust" (button):
  - T1: +15% for 6 s, 40 s cooldown.
  - T2: +20% for 7 s, 35 s cooldown.
  - T3: +30% for 8 s, 30 s cooldown.
  - The charm brightens while a gust is active.

## Unlock and cost (suggestion)
| Tier | Unlock | Cost |
|---|---|---|
| T1 | Gullhaven shipwright, first voyage | 400 gold + 10 Driftwood |
| T2 | after Brinecrown Coil | 1500 gold + 6 Coil Scales + 4 Saltglass |
| T3 | after the Glasswyrm (Stage 3) | 4000 gold + Stormsilk Bolt (Sunken Ward) + 3 Glasswyrm Shards |

The galleon and skiff are upgraded separately.

## Fast travel (idea): Harbour Charts
- When you first dock at a port, it's added to a chart table on the galleon deck. The ports are Tidewrack pier and Gullhaven, then later Saltglass Landing, Frostreach Ice Dock and Vent Harbour.
- Picking a port plays a 3-4 s "sails filling" fade, loads that region, and places the ship at the port's anchor (for Gullhaven, props.gullhaven.anchor in meshes/stage1_manifest.json).
- It is blocked in boss fights, and to ports in locked regions.
- It's free at T2+, with a small fee at T0/T1. That keeps early sailing meaningful.

## Code needed (Lucky)
1. Save fields: galleon_tier and skiff_tier (0-3), plus a discovered_ports list.
2. On a tier change, free the old add-on node, then instance upg_<ship>_t<n>(.glb or _lod1.glb, matching the ship's LOD) under the ship root, with shadows off.
3. A stats table (top speed, accel, turn, gust) read by the sailing controller.
4. Shipwright UI at Gullhaven: preview, cost, confirm.
5. The gust button, its cooldown, and the charm glow.
6. The Harbour Charts menu, plus fade, teleport and region load.

## Honest limits
- Your ship models are each one merged mesh with their sails baked in. So the tier sails are overlays, slightly forward of and larger than the originals.
  This is fine on the skiff and the galleon's fore and aft masts. Since the 2026-10-30 polish, all 3 galleon masts are covered.
- A true swap needs a sail-less hull copy, with the sail faces cut out into a new file and the originals kept. That is a small follow-up.
- The T1 figurehead reads like a log from the side, and the skiff trim line is a little wavy. These are for a polish pass.
