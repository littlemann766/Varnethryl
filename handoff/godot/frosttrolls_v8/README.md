# Frost trolls v8 (test 32): attack wrist twist
Source: the game's godot-voxel/characters/frosttroll_{a,b}_lod1.glb (54e17f1). The only change is hand_R in attack1/2/3, where the hand rotation relative to the rest pose is clamped to 45° or less (it was 80° on A and 100° on B), using slerp toward the rest pose (tools/voxel_v3/t32/wclamp.py).
The weapon is parented to the weapon_R bone under the hand, so it stays in the grip; only the wrist snap is smaller. Arm-leg (check1): 0 before and 0 after on attack1-3. The other clips are unchanged.
The offset was not constant: q_*.json shows a mean offset of 23-44° with p90 motion of 41-77°, so this is a swing, not a fixed retarget offset.
