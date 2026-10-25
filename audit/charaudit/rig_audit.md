# Rig audit: all characters, creatures and companions in the Godot build (2026-10-25 ET)

Source: godot-proto/characters/*_lod1.glb (read-only; same as godot-art/characters) + godot-proto/enemies/models/*.glb. Nothing modified.
Metrics (rig_measure.py / rig_twist.py, bpy 5.2): **rest arm** = angle of shoulder→hand joint from straight down (0 = arms down, 90 = T-pose). **ident** = share of skin joints whose glTF rest rotation is identity. **run rot / twist** = max upper/forearm rotation over the run clip and the part of it about the arm's own axis (twist = palm roll). Contact sheet: rig_contact.jpg (run at 30%, red = problem rig).

| model | bones | ident | rest arm° | run arm° | run rot° | run twist° | verdict |
|---|---|---|---|---|---|---|---|
| aldric | 21 | 0.95 | 67 | 69 | 31 | 29 | **PROBLEM: near-T/A rest + X-axis clip = palms roll up, arms stuck out** |
| asha | 78 | 0.99 | 26 | 50 | 104 | 48 | OK swing; noticeable twist, check hands |
| ashentitan | 69 | 0.99 | 9 | 32 | 82 | 13 | OK |
| ashentitan_volcano | 69 | 0.99 | 9 | 33 | 80 | 13 | OK |
| brynn | 21 | 0.95 | 67 | 69 | 31 | 29 | **PROBLEM: near-T/A rest + X-axis clip = palms roll up, arms stuck out** |
| cedric | 21 | 0.95 | 67 | 69 | 31 | 29 | **PROBLEM: near-T/A rest + X-axis clip = palms roll up, arms stuck out** |
| darius | 82 | 0.99 | 12 | 16 | 125 | 64 | OK swing; noticeable twist, check hands |
| elira | 21 | 0.95 | 13 | 25 | 31 | 29 | arms down, but clip is ~94% twist: stiff arms (no swing), forearm roll; minor |
| finn | 21 | 0.95 | 16 | 27 | 31 | 29 | arms down, but clip is ~94% twist: stiff arms (no swing), forearm roll; minor |
| frosttroll_a | 69 | 0.29 | 18 | 40 | 56 | 39 | OK |
| frosttroll_b | 69 | 0.99 | 34 | 35 | 53 | 25 | OK |
| garruk | 78 | 0.99 | 17 | 66 | 105 | 49 | OK swing; noticeable twist, check hands |
| kael | 21 | 0.95 | 67 | 69 | 31 | 29 | **PROBLEM: near-T/A rest + X-axis clip = palms roll up, arms stuck out** |
| mirelle | 21 | 0.95 | 67 | 69 | 31 | 29 | **PROBLEM: near-T/A rest + X-axis clip = palms roll up, arms stuck out** |
| morwen | 21 | 0.95 | 67 | 69 | 31 | 29 | **PROBLEM: near-T/A rest + X-axis clip = palms roll up, arms stuck out** |
| nyx | 21 | 0.95 | 67 | 69 | 31 | 29 | **PROBLEM: near-T/A rest + X-axis clip = palms roll up, arms stuck out** |
| orin | 21 | 0.95 | 40 | 45 | 31 | 24 | **PROBLEM: near-T/A rest + X-axis clip = palms roll up, arms stuck out** |
| owner | 86 | 0.97 | 17 | 15 | 111 | 27 | OK |
| phoenix | 60 | 0.98 | None | None |  |  | non-humanoid (no arms); not audited for palms |
| pip | 59 | 0.98 | None | None |  |  | non-humanoid (no arms); not audited for palms |
| rook | 21 | 0.95 | 43 | 47 | 31 | 22 | **PROBLEM: near-T/A rest + X-axis clip = palms roll up, arms stuck out** |
| rowan | 21 | 0.95 | 13 | 25 | 31 | 29 | arms down, but clip is ~94% twist: stiff arms (no swing), forearm roll; minor |
| selene | 27 | 0.96 | 4 | 14 | 126 | 44 | OK |
| seraphine | 21 | 0.95 | 67 | 69 | 31 | 29 | **PROBLEM: near-T/A rest + X-axis clip = palms roll up, arms stuck out** |
| stonetroll | 21 | 0.95 | 90 | 91 | 31 | 31 | **PROBLEM: near-T/A rest + X-axis clip = palms roll up, arms stuck out** |
| talia | 21 | 0.95 | 25 | 33 | 31 | 16 | arms down, but clip is ~94% twist: stiff arms (no swing), forearm roll; minor |
| thorne | 21 | 0.95 | 52 | 55 | 31 | 25 | **PROBLEM: near-T/A rest + X-axis clip = palms roll up, arms stuck out** |
| vesper | 21 | 0.95 | 79 | 80 | 31 | 31 | **PROBLEM: near-T/A rest + X-axis clip = palms roll up, arms stuck out** |
| wolf | 21 | 0.0 | None | None |  |  | non-humanoid (no arms); not audited for palms |
| wren | 81 | 0.96 | 32 | 37 | 45 | 11 | OK |
| ember_rock_small | 0 |  | None | None |  |  | static mesh, no rig |
| impact_crater | 0 |  | None | None |  |  | static mesh, no rig |
| lava_blob | 0 |  | None | None |  |  | static mesh, no rig |
| volcanic_boulder | 0 |  | None | None |  |  | static mesh, no rig |

## Problem rigs (21-bone, identity orientations, rest arm ≥ 40°)
aldric, brynn, cedric, kael, mirelle, morwen, nyx, seraphine (67°), vesper (79°), stonetroll/Mossgut (90°, full T), thorne (52°), orin (45°), rook (43°).
In all 21-bone rigs the run clip rotates the arms only ~31°, and ~29° of that is twist about the arm itself: on an outstretched arm a world-X rotation is a roll, so palms flip up and the arm never swings forward/back. Mid-run arm angle barely moves from rest (67→69°).
Secondary (21-bone, arms already down: elira, finn, rowan, talia): same clip, so arms swing stiffly with forearm roll. Talia's figure reads arms-out on the sheet despite a 25° skeleton because her robe sleeves flare.
Not affected: the 59–86 bone rigs (asha, darius, garruk, owner, selene, wren, ashentitan x2, frosttroll a/b) get real 50–125° swings. frosttroll_a has only 29% identity orientations but rotates sensibly. wolf/phoenix/pip are quadruped/flyer rigs with no humanoid arms. The 4 enemies/models GLBs are static (no skin).

## Would re-posing the skins arms-down fix it without touching clips?
**Likely yes for run/walk/idle, about 80% confidence; attacks need a check.** The clips key local rotations about world X on identity-rest bones. If the bind pose is changed so the upper arm hangs down (move the foreArm/hand joint translations to point down, keep the joint rotations at identity, re-bake the mesh into that pose with the current weights and rewrite the inverse bind matrices), the same world-X rotation becomes a forward/back pendulum swing, which is the intended run motion, and the palm roll disappears. No keyframes change.
Risks: (1) attack clips authored against T-pose arms would aim ~60° lower (overhead swings become chest-height); check attack1-3 visually per hero. (2) Shoulder/armpit weights were painted for T-pose, so a 60–90° drop may crease or collapse cloaks and sleeves. Stonetroll (90°) is the worst case. (3) Swing amplitude is only ~30°, still modest but natural-looking. (4) Any Godot-side IK or attachment offsets on hand_R (weapons) would need their rest offset re-checked.
Recommended: prototype on one copy in /tmp (kael or aldric) and render run plus attack1-3 before doing all 13. The alternative is a Lucian-side retarget of the clips to the real rest (no skin change).
