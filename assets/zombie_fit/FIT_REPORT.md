# Hooded-male fitted rig — not a pass

One character. Source file `assets/zombie_src/hooded_male/trellis2_raw.glb` was not modified. No faces were deleted. The 6.90 ms headless figure is still invalid.

## What was fitted

A copy of the source was scaled by 1.725 so it stands 1.72 m with the feet on z = 0. Joints were placed from cross-sections of that shell, not from the kael T-pose. Bones point from joint to joint. Kael clips were retargeted as directions and length ratios, and the hips translation was copied, so a walk step, a reach, and a fall are in the file.

At rest, before any clip, evaluated vertices match the scaled mesh. Max gap 1.9e-7 m. Every vertex has a weight sum of 1. At most 2 influences. Nothing is unweighted. Influences blend only when the two bones are parent and child and the vertex is near that joint.

## Hands

Vertices within 8 cm of the left hand joint: 1,078. All of them are on `hand_L` or `foreArm_L`. None on a foot.

Distance from that neighborhood’s centroid to the hand bone:

| Clip | Frame | Gap |
|---|---|---|
| walk | 16 | 0.039 m |
| attack2 | 10 | 0.035 m |
| death | 20 | 0.039 m |

On attack2 the hand bone moves from about (0.34, -0.11, 0.90) at rest to (0.63, -0.20, 1.47). The hand leaves the hip and reaches. It does not follow the foot.

## Edges, then the only topology change

Before any cut, walk frame 16, every edge:

| Edges | Count | p50 | p95 | max |
|---|---|---|---|---|
| All | 189,848 | 1.00 | 1.39 | 163 |
| Same bone, or a parent-child pair | 186,396 | 1.00 | 1.14 | 71 |
| Any other pair | 3,452 | 13.9 | 55 | 163 |

Attack2 and death are the same shape: median 1.0, the non-adjacent set around 15–16 at the median.

Those 3,452 edges are the bridges. 1,259 faces that used them were rebuilt onto coincident copies of the foreign vertex. 944 new vertices. Face count stayed 96,615. UVs were copied. The copies sit on the old points, so the rest pose does not move. Export and reimport: 96,615 faces, rest still reads as the source. The glTF split raised the vertex count to 107,220 on reimport.

A second pass, meant to also rip parent-child faces whose center sits more than 16 cm from the joint, rebuilt the same 1,259 faces and no more. The sheets that remain are islands already on one bone.

## What the frames show

Rest, including after reimport, matches the source: hood, face, strap, belt, hands at the sides, wrapped legs.

Walk frame 16, after the rip: a step, the near arm forward, the head still a head. The cloak comes apart into long strips instead of one rectangle. It does not hang as cloth.

Attack2: one arm reaches, the hand is open. The cloak bursts backward.

Death: the body is horizontal and a leg stays a leg. Large cloak sheets still swing out as slabs.

Joints, drawn on the rest pose: heights land on the arm, the hips, the knees, and the boots. From the side the head joint sits behind the skull, and the ankle joints sit in front of the boots. That is not a finished anatomical fit.

## Blocker

The hand follows the hand. The rest pose survives export. The clips do move the limbs. The success gate still fails because the cloak does not survive the motion.

After the fitted skeleton and the non-adjacent rip, the remaining sheets are single-bone islands. They rotate with the torso. They are not edges between a hand and a foot, so cutting every cross-bone edge would not remove them. Making them bend means cutting those islands into pieces that can hang on different bones. That is a reconstruction of the cloak. It was not done.

Files: `hooded_fit.glb` (before the rip), `hooded_fit_seams.glb` (after), `contact_sheet.png`, `joints_front.png`, `joints_side.png`, `reimport_rest_front.png`, `seam_walk_front.png`, `seam_attack2_front.png`, `seam_death_side.png`.
