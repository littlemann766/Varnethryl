# World-boss Ashen Titan clips v1 (2026-10-25, 2:30 PM ET)
Files: ashentitan_worldboss.glb / _lod1.glb = the same Titan rig and mesh with ALL earlier clips plus the wb_* clips below (follows specs/worldboss_titan.md).
Scale: confirmed ~114 m tall. The native model is ~20.95 units tall -> node scale ~5.44. Every clip is scale-independent (root motion and poses are in model units), so a scale change only changes the metres below.
Root motion: wb_walk / wb_run move the 'root' bone forward (-Z in Godot, the facing direction). Use root motion (AnimationTree root_motion_track = root) so the planted feet do not slide. At 114 m: wb_walk 2.96 m/s (spec 3 m/s), wb_run 8.1 m/s.
Times are seconds from clip start. Hold / loop clips loop seamlessly and can be cut on any frame (interrupt).

| clip | len | events (s) |
|---|---|---|
| wb_idle | 6.0 loop | slow breathing |
| wb_walk | 10.0 loop | footstep L 0.0, R 5.0 (10 s cycle, ~15 m steps at 114 m) |
| wb_run | 5.6 loop | footstep L 0.0, R 2.8 |
| wb_turn_L / wb_turn_R | 6.233 | 90 deg in place, yaw ramp avg ~16 deg/s (peak ~24); footsteps L/R alternate at 2.375, 3.625, 5.0, 6.125 (turn_L starts with L) |
| wb_stomp (arrive) | 4.4 | R foot lifts 0.9-2.0, STOMP 2.4 (shake 120 m, decal, dust) |
| wb_ritual_fissure_in | 2.5 | anticipation dip 0-0.8, enters the HOLD at 2.5 |
| wb_ritual_fissure_loop | 4.0 loop | hold (fists high, hands glow) - play for the 12 s wind-up |
| wb_ritual_fissure_release | 3.6 | GROUND SLAM 0.9 (fists on the ground) -> spawn fissures |
| wb_ritual_meteor_in / _loop / _release | 2.5 / 4.0 / 3.6 | right arm to the sky; release CALL 0.6 (meteors), arm sweeps down by 1.4 |
| wb_ritual_lavawave_in / _loop / _release | 2.5 / 4.0 / 3.6 | crouched scoop; release heave 0.9, FLING 1.3 -> ring spawns |
| wb_stagger | 2.5 | interrupt reaction, recoil peak 0.25-0.6, stumbles back, ends in the stagger pose |
| wb_stagger_loop | 4.0 loop | dazed hold for the rest of the 8 s stagger, then blend to wb_idle |
| wb_knockdown | 4.0 | drops to knees, body hits the ground 2.4 (shake) |
| wb_down_loop | 4.0 loop | knocked-down hold (20 s) |
| wb_getup | 4.5 | rise |
| wb_swat_forearm_L / _R | 3.4 | telegraph raise 0-1.2, SWAT HIT 1.6 (front arc near the ground), recover to 3.4 |
| wb_swat_knee | 4.4 | knee reaction = the stomp: lift 0.9-2.0, STOMP 2.4 (15 m) |
| wb_swat_back | 3.4 | hunch 0-1.2, shudder 1.2-2.4 (peak 1.5) knocks climbers off (also use for chest) |
| grow | 5.4 | brace 1.0, root scale 1 -> 1.6 (2.0) -> 2.4 (3.0) -> 3.0 (4.2), holds x3 at the end. After it, set the node scale x3 and play clips normally |

Machine-readable events: worldboss_events.json ({"events": footsteps per clip, "contact": hit times}).

## Weak-point bones (attach Beth's crystals as BoneAttachment3D)
- forearm L / R: foreArm_L / foreArm_R (mid-bone)
- knee L / R: shin_L / shin_R (bone head = knee)
- chest (front plate, +Z): bone `chest`, back plates (-Z): bone `upperChest` - use Beth's attach_points.json offsets, which match this (my v1 note had the two swapped)

## Server / sync sketch (for Lucian)
- Server-authoritative WorldBoss state: hp, max_hp, weak_points[6]{hp, broken_until}, waypoint index, phase (moving/arrive/idle/ritual/stagger/knockdown/cooldown), ritual id plus start time, cooldown_until, pressure 0-3, respawn_at (kill + 2 h), contribution map (player -> damage).
- Broadcast 5 Hz: position, yaw, phase, anim clip plus clip start server-time, hp, weak-point flags. Clients interpolate the position (100-200 ms buffer) and seek the clip to (now - clip_start), so everyone sees the same frame.
- Damage: clients send hits (target part + amount); the server validates range and part, applies x0.1 body, x1 weak point (x2 staggered, x3 knockdown), checks the interrupt threshold 8% x sqrt(n)/2 (min 4%) during a ritual, and fires the stagger/knockdown events.
- Events are pushed as one-shots with server time: footstep(pos, foot), stomp, ritual_start/3s_warning/release, swat(limb), weak_point_broken/regrow, adds spawn. Clients play the shake/decal/dust.
- Footprint decals: spawned client-side from the footstep events at the foot bone position, ~25 m, fade at 120 s. The server does not track them.
- Distance-scaled shake: amp = base x clamp(1 - (d - 120)/(250 - 120), 0, 1) for stomps (full inside 120 m, 0 at 250 m); walking footsteps use ~0.3x base and a 60/150 m falloff.
- Respawn: the server persists respawn_at; on boot it restores state, and the timer survives restarts.

## v2 (2026-10-25 3:30 PM ET): knee fix
All wb_* clips and grow: the knees now bend forward (toward the toes) on every frame. A per-frame check puts the knee in front of the hip-ankle line on all 25 wb clips. Root motion: Lucky strips it, so wb_walk/wb_run play in place, and the planted feet only hold still if the node moves at 2.96 m/s (walk) / 8.1 m/s (run) at 114 m.

## v4b (2026-10-25, 6:20 PM ET): back to the original fists (the boss's call); knee fixes kept
The open-hands notes below were reverted. The fists come from 75c0682. The extra finger chains are not weighted. The wb_stagger_hold rename stays.

## v4 (reverted hands; 2026-10-25, 5:45 PM ET): open hands, finger chains, knee follow-ups
- Beth's open hands are merged in (her apply.py/integ2.py). Each finger now has its own chain: index/middle/ring/pinky/thumb 1-3 _L/_R, parented to hand_*, with joints at the sculpt knuckles. fingers_L/R is still there but nothing is weighted to it.
- Finger poses are keyed in every clip. Fists: attack1-3, eruption_slam, magma_sweep, windup, wb_ritual_fissure*, wb_stomp, wb_swat_*. Half-curled grip: boulder_hurl. Open palms: everything else (idle/walk/run, intro, death, hit, grow, lavawave/meteor rituals, knockdown/down/getup, stagger).
- Rename: wb_stagger_loop -> wb_stagger_hold. Godot's importer strips the "_loop" suffix, so the old name collided with wb_stagger and one clip was lost.
- Knees: wb_idle both knees >= 7.5%. Pool attacks: the knee bend now follows the swing.
