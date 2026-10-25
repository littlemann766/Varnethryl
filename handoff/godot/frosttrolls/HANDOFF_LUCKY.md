# Frost trolls re-rig (Beth's clean meshes, fitted 31-bone skeleton, A-pose, weapon socket)
Files: frosttroll_a(.glb|_lod1), frosttroll_b(.glb|_lod1). 5.715 m, feet at origin, facing same as Mossgut.
Socket: node `weapon_R` (child of bone hand_R), weapon mesh already under it (A stone club, B ice mace). Swap meshes by replacing the socket child (grip origin, +Y shaft).
Clips (both): idle walk run attack1 attack2 attack3 hit death skill. B no longer has `windup` (play_attack falls back fine).
Hit frames = BOSS_PATTERNS tele:
- A Krag (heavy club): attack1 winterhammer 1.1 s, attack2 glacierbreaker 1.5 s, attack3 brotherswrath 1.3 s (low ring sweep).
- B Mog (stiff, snappy mace): attack1 frostcrash 1.1 s, attack2 avalanche lance 1.6 s, attack3 brothersvengeance 1.2 s.
Weapons: held head-up at rest (handle in fist, like Beth's contact sheet); on hit frames the wrist cocks forward and the head lands on the floor.
Weapon head lowest point at the hit frame (m, negative = digs slightly into the floor): A attack1 +0.39, attack2 +0.43, attack3 +0.09; B attack1 -0.38, attack2 +0.09 (thrust), attack3 -0.21.
Zero torso penetration on all clips.

## v3 deformation fix (12:25 note: troll A skin stretch)
- Troll A's hands/fingers were fused to the thigh/belly shell; they are now split from it (geometry cut along the hand/body contact; A 208/110 edges hi/lod1, B 43/28), and A's hand joints were refit to the real hands (in front of the groin).
- Small loose pieces (claws/shards/plates < 0.6 m) are rigid, 100% on their dominant bone; body weights smoothed (14 passes) within each partition; shoulder carries 30% of arm raise; wrist cock reduced 130 -> 100 deg, crouches reduced, overhead windups capped at 150 deg.
- Elongation per edge, 99th percentile worst frame: A lod1 idle 4.5%, walk 7%, run 12%, attacks 19-27%; B lod1 idle 4%, walk 4%, attacks 10-12% (old A: 115-430%). Max single-edge outliers remain on a few tiny edges.
- Weapons: Beth's 12:23 polished club/mace.

## Troll A v4 (2026-10-25 1:20 PM ET) - rebuilt from the ORIGINAL model
- Source: varn-core 9e6ad07:www/proto3d/models-new/frosttroll_a.glb (Body mesh only; stray Icosphere + old Darius_Rig removed, scaled to 5.715 m, feet at origin). Not Beth's cleaned mesh.
- Fresh fitted 31-bone skeleton (joints_a_orig.json), club on weapon_R, same clips (idle walk run attack1 attack2 attack3 hit death skill).
- attack1: club head in front on the floor at 1.1 s (no longer out sideways). Head min z: a1 0.02, a2 -0.16, a3 0.03 m.
- lod1 = same body mesh (the original has no lod1) with the lod1 club.

## Troll B v4 (2026-10-25 1:45 PM ET) - rebuilt from the ORIGINAL troll model
- Source: varn-core ae85eee:www/proto3d/models-new/frosttroll_b.glb ("corrected, animated Frost Troll B"). The 9e6ad07 frosttroll_b.glb is a frost SERPENT (removed in 58bfdc1), so not used.
- Prep: Body mesh only (Icosphere + old rig removed), 5.715 m, feet at origin. Hand/body fused edges split (--cut). Fresh fitted skeleton (joints_b_orig.json), mace on weapon_R, same clips; attack2 hit 1.6 s.
- lod1 = same body mesh (no original lod1) with the lod1 mace.

## Trolls v5 grips (2026-10-25 2:30 PM ET)
- Beth's thick-grip weapons (club ~0.31 m, mace ~0.27 m grip, origin = grip centre, +Y up, scale 1.0) on weapon_R.
- weapon_R now seated at the palm centre; fingers_R keyed curled around the handle in every clip (B also got finger weights).
- Hit frames checked in Godot 4 headless (weapon lowest point): A attack1 1.1 s 0.16 m, attack2 1.5 s -0.17, attack3 1.3 s -0.18; B attack1 1.1 s -0.52, attack2 1.6 s -0.10, attack3 1.3 s -0.60.

## v6 (2026-10-25, 4:50 PM ET): Beth's socket and grip numbers, v7 weapons
- v7 club and mace (hero-motion/weapons) on weapon_R.
- B: weapon_R (child of hand_R) translation (-0.0863, -0.0086, -0.0964), rotation wxyz (0.1792, 0.146, -0.9578, -0.1707), Beth's measurement as given. Fingers unchanged.
- A: fingers_R grip pose keyed (constant) in every clip, 90 deg about the bone's local -Z axis, local quat wxyz (0.7071, 0, 0, -0.7071). Fingers clear a 0.30 m cylinder centred 0.15 m off the palm (finger median 0.295 m, min 0.182 m from its axis). A's socket is unchanged and waiting for Beth to re-measure.
