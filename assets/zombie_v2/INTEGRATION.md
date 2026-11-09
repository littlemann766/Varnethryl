# Wiring the v2 villager

No gameplay script was changed. The horde still spawns the placeholder until someone points it at this scene.

## Files

- `assets/zombie_v2/zombie_villager.glb` — skinned villager, 13,596 tris, kael clips.
- `assets/zombie_v2/zombie_far.glb` — 402-tri idle pose for a far crowd. Not skinned.
- `assets/zombie_v2/skin_*.png`, `cloth_*.png` — the 2048 maps. The same images are embedded in the villager glb.

The glTF nodes face the same way as `voxel/kael_voxel.glb`. `CharacterRig` already turns humanoid visuals 180° on Y because the game looks down -Z. Use that, or the same turn you use for Kael. Do not also rotate the mesh inside the glb.

Collision stays `HordeZombie.BODY_R = 0.46`. This mesh was not used to change the capsule.

## Clips

`idle`, `walk`, `run`, `attack1`, `attack2`, `attack3`, `hit`, `death`. `attack` is not a separate clip; use `attack1`. There is no `bite` or `bite_windup`.

`idle` is the kael idle. It leans and drops the arms. It is not a new hunched override.

## Swap

When a horde actor is allowed to change, instance `zombie_villager.glb` the same way `CharacterRig` instances `kael_voxel.glb`: one `AnimationPlayer`, the skeleton above, no extra scale. The far mesh is a `MeshInstance3D` or a `MultiMesh` of `zombie_far.glb`, not the skinned villager.

v1 under `assets/zombie/` is the previous procedural pass. Leave it in place until a swap is deliberate.
