# Ashen Titan — VOLCANO boss (11x Owner, 20.955 m) — branch-only, untested in game

All files: `/workspace/rigged/volcano/`. Nothing is on main. Viewer: `/workspace/VARNETHRYL-VOLCANO-TITAN-VIEWER.html` (its `step()`/`fire()` code is a working reference implementation of everything below).

| file | what |
|---|---|
| ashentitan_volcano_11x.glb | 1.84 MB, 69-joint rig, WebP 1024, metalness 0, height 20.955 m (idle bbox top, measured in three.js) |
| ashentitan_volcano_11x.json | footsteps, shake, attack events, projectile list, leash |
| volcanic_boulder.glb (980 tris, r≈1 m) · lava_blob.glb (500, r≈0.6 m) · ember_rock_small.glb (320, r≈0.35 m) · impact_crater.glb (960, r=1 m decal mesh) | projectiles/decal, vertex-coloured (painted lava, **no emissive**), metalness 0 |
| make_clips.mjs, build_giant.mjs, finalize.mjs, props.mjs, viewer/ | rebuild scripts (run in that order; props independent) |

## Size is BAKED — do not rescale
Root joint scale = 1.83817 (vertices/IBMs untouched, same method as night3 giants). Load at scale 1. Do NOT run it through charscale / boss multipliers or scale the scene node. Set `frustumCulled=false` (or compute skinned bounds).

## Clips (seconds already retimed for size)
idle 4.07 (loop) · walk 2.29 (loop, in place, move at 5.47 m/s) · run 1.21 (loop, 12.41 m/s) · attack 2.20 · attack2 1.95 · hit 0.49 · death 2.39 ·
**windup 2.71** (telegraph: pose reached ~0.81 s, then trembling hold) · **eruption_slam 2.96** · **boulder_hurl 3.61** · **magma_sweep 2.68** · **volcano_roar 4.34**.
Everything except idle/walk/run: `LoopOnce` + `clampWhenFinished=true` (holds last frame). Cross-fade 0.25 s.
Suggested sequences (`attackSequenceSuggestion`): windup 1.2 s → eruption_slam; windup 0.8 s → boulder_hurl; windup 1.5 s → volcano_roar; magma_sweep on its own. Cooldowns 9 / 6 / 5 / 22 s.
Walk/run feet locked with 2-bone IK (slip ≤2 cm); the five new attacks keep both feet planted exactly at idle stance.

## Event loop
Per titan keep `lastT`; each frame, for every event in `attackEvents` with `clip === current` fire it when `lastT < e.t <= action.time`. Footsteps (`clips.<c>.footsteps`) use the same rule as GIANT.md (night3) with `suggestedShake` (radius 63 m, full 10 m). The slam fists, rock rip and roar are in footsteps too, so they shake the camera.

### Positions
All `offset` / `center` / `pos` are **model space metres** (+Z = titan forward, +X = his left). World = rotate by titan yaw + titan position. `spawn.bone` = live bone (`hand_R`) — prefer reading the bone's world position at fire time; the offset is the same point baked from the clip as fallback.

### spawn_projectile
`count` copies of `projectile` (scale `projectileScale`). Patterns:
- `ring`: yaw_i = i/count·360° (+ jitter); landing distance random in `landRadius` from spawn point.
- `cone_forward`: yaw = `aimYawDeg` ± `spread`/2 (0 = forward, + = his left); landing distance in `landRadius`.
- `target:'player'` (boulder_hurl release): land at player position ± spread/2; flight time = clamp(dist/40, flightSec).
- `rain_zone` (volcano_roar): pick landing point uniformly in the leash circle (TITAN_CENTER, r 122), with `biasToPlayer` chance of a point within 10 m of the player; start `startHeight` m above it with small drift.

**Ballistic arc** (one formula for all): pick landing point L and flight time T (for ring/cone: T = 2·v·sin(angle)/9.81 with v from `speed`, angle from `launchAngleDeg`). Velocity `v0 = (L - S)/T - 0.5·g·T` with g = (0,-9.81,0); integrate `p += v·dt, v.y -= 9.81·dt`, or evaluate p(t)=S+v0·t+0.5·g·t². Use `heightAt(x,z)` for L.y. Spin the mesh for flavour.

**Ground warning circle**: spawn the moment the projectile launches at L, radius `impactRadius`, fill growing 0→1 over the flight time (red ring); AoE events show a yellow circle for `telegraphSec` during the windup. Because L is decided at launch, the circle is exact.

**Impact**: at t = T: damage everyone within `impactRadius` of L = `damageMult` × the titan's base attack (designer tunes base); `lava_blob` with `dot` leaves a lava pool (`poolRadius`, `dps` × base per s for `sec`). Spawn `impact_crater.glb` scaled to impactRadius at L (fade after ~6 s), a flash, dust, and camera shake falloff ~60 m. boulder_hurl has `splinters`: 8 ember_rock_small in a 4–12 m ring, 0.9 s flights.

### aoe
Instant circle at `center`, `radius`, `damageMult`, optional `knockback` (m/s outward). `rip_up_rock`: attach a volcanic_boulder (scale 2.5) to `hand_R` until the `release` event.

## Leash (stays in the volcano)
Source of truth: `www/proto3d/bossregions.js` → `TITAN_CENTER = {x:405, z:-402, radius:122}` (vgpt-cmp @ a8aa181; I did not edit it). Also `LAVA_POOLS`, `lavaAmount()`, and townlands.js `townElevation()` (massif d<148, crater d<36).
Rule: clamp the titan's center to ≤ 107 m from TITAN_CENTER (radius-15 so his 20 m body stays inside the rim). If the player is > 162 m away he stops chasing, walks back toward center and keeps boulder_hurl'ing while the player is inside `maxRange` (110 m). Projectiles may land up to ~30 m outside the rim. He never leaves the zone. Snap feet to `heightAt(x,z)`.

## Budget
1 skinned mesh, 1 material, 24.5k tris. Pool projectiles (≤ ~60 alive during volcano_roar); they share 4 tiny vertex-coloured materials, so instancing is easy.
