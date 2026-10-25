# Frost trolls re-rig (Beth's clean meshes, fitted 31-bone skeleton, A-pose, weapon socket)
Files: frosttroll_a(.glb|_lod1), frosttroll_b(.glb|_lod1). 5.715 m, feet at origin, facing same as Mossgut.
Socket: node `weapon_R` (child of bone hand_R), weapon mesh already under it (A stone club, B ice mace). Swap meshes by replacing the socket child (grip origin, +Y shaft).
Clips (both): idle walk run attack1 attack2 attack3 hit death skill. B no longer has `windup` (play_attack falls back fine).
Hit frames = BOSS_PATTERNS tele:
- A Krag (heavy club): attack1 winterhammer 1.1 s, attack2 glacierbreaker 1.5 s, attack3 brotherswrath 1.3 s (low ring sweep).
- B Mog (stiff, snappy mace): attack1 frostcrash 1.1 s, attack2 avalanche lance 1.6 s, attack3 brothersvengeance 1.2 s.
Weapons: held head-up at rest (handle in fist, like Beth's contact sheet); on hit frames the wrist cocks forward and the head lands on the floor.
Weapon head lowest point at the hit frame (m, negative = digs slightly into the floor on impact): A attack1 -0.12, attack2 -0.30, attack3 +0.27 (low sweep); B attack1 -0.34, attack2 +0.14 (thrust), attack3 +0.01.
Zero torso penetration on all clips.
