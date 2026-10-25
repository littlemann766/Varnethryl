# Frost trolls re-rig (Beth's clean meshes, fitted 31-bone skeleton, A-pose, weapon socket)
Files: frosttroll_a(.glb|_lod1), frosttroll_b(.glb|_lod1). 5.715 m, feet at origin, facing same as Mossgut.
Socket: node `weapon_R` (child of bone hand_R), weapon mesh already under it (A stone club, B ice mace). Swap meshes by replacing the socket child (grip origin, +Y shaft).
Clips (both): idle walk run attack1 attack2 attack3 hit death skill. B no longer has `windup` (play_attack falls back fine).
Hit frames = BOSS_PATTERNS tele:
- A Krag (heavy club): attack1 winterhammer 1.1 s, attack2 glacierbreaker 1.5 s, attack3 brotherswrath 1.3 s (low ring sweep).
- B Mog (stiff, snappy mace): attack1 frostcrash 1.1 s, attack2 avalanche lance 1.6 s, attack3 brothersvengeance 1.2 s.
Weapon head ~0-0.7 m off the floor on every hit frame; zero torso penetration on all clips.
