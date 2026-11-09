# Zombie model provenance

The mesh and the textures are original. They were generated procedurally by `assets/zombie/build_zombie.py` (numpy and Pillow only). No concept-sheet pixels, no hero textures, and no downloaded texture packs were sampled into the maps. No paid service was used.

The owner's eight concept images (Nov 8, 2026) were used as style reference only: undead islanders, muted cloth, rot and blood, ragged hems, a hood, a belt and pouch, one pauldron and one kneepad, bare feet on the sailor. The models are not copies of those sheets.

## Skeleton and clips

The rest pose is the project's 21-joint humanoid, copied from `voxel/kael_voxel.glb`. That rest matches `characters/kael_lod1.glb` (same joint names and the same local translations). The clip curves embedded in the zombie GLBs are the curves from `voxel/kael_voxel.glb` for these joints only:

`idle`, `walk`, `run`, `attack1`, `attack2`, `attack3`, `hit`, `death`

`attack` is the same keys as `attack1`, so a rig that looks up `attack` finds a clip.

Those curves are the project's existing humanoid set. The lod1 hero files with the same bone names do not swing the arms (the upper arm stays on the bind pose). The voxel file does. Bone lengths during every embedded clip stay within 1 mm of the bind lengths, measured in Godot on the imported skeleton.

The voxel cape-chain bones (`capeV_*`) and the hero fly clips are not included. Cloth on this mesh is not weighted to that chain.

## What is not in the set

There is no `bite` clip and no `bite_windup` clip on this skeleton, on the horde, or on the hero files that were checked. The attack clips keep the nearest hand about 0.44 m from the head (`attack2`). They are not a bite.
