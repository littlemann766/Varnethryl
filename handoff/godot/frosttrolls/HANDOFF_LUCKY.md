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
