# Varnethryl character model correction audit

**Lore correction:** Sslythar is a **basilisk**, like Balthrix, **not a dragon**. The uploaded asset's source filename contains the word `dragon`; that is a filename and does not change Sslythar's species. His intended motion is ground-based head-to-tail serpentine slithering and turning, not flapping/flying. Keep him **hidden from gameplay, character selection, enemies, companions, saved slots, and debug shortcuts** until rigged, animated, and explicitly approved. Preserve stable character IDs.

## New user-supplied GLB candidates (October 21, 2026)

| Supplied file | Varnethryl character | Rig audit | Next action |
| --- | --- | --- | --- |
| `hydra 3d model_Clone1(1).glb` | **Hydrella** | Static mesh: 0 skins, 0 bones, 0 clips | Rig separate heads, necks and torso; animate idle, movement and attacks |
| `fantasy centaur 3d model_Clone1(1).glb` | **Briar** | Static mesh: 0 skins, 0 bones, 0 clips | Rig horse legs and humanoid body together; animate quadrupedal walk/trot/run, attacks |
| `fantasy ogre 3d model_Clone1(1).glb` | **Unassigned** | Static mesh: 0 skins, 0 bones, 0 clips | Do not misassign to another character without approval |
| `dragon 3d model (1)(1).glb` | **Sslythar, BASILISK** | 1 skin, 22 joints, no clips; head and tail joints exist | Evaluate basilisk silhouette and make authentic ground slither; no dragon/flight logic; remain hidden |
| `wizard owl 3d model (1).glb` | **Wren** | 1 skin, 65 joints, no clips | Inspect wing weight painting; retarget/create animations before replacing functioning Wren NEW |

**Important:** These five files were supplied in chat, but are **not part of the committed game assets**. Do not claim they are installed or silently substitute an unanimated model for the functioning one. Use the exact source files when they can be added to the repository. Preserve existing working versions for comparison/rollback.

## Original 20 playable heroes

Canonical slot order below must not change, since saves refer to these IDs. Source assets live at `www/proto3d/models/<id>.glb`; variants in `models-new`, `models-placeholder` and procedurally generated characters are separate.

| # | ID | Hero | Original GLB |
| -: | --- | --- | --- |
| 1 | `aldric` | Sir Aldric | `models/aldric.glb` |
| 2 | `darius` | Darius Umbral | `models/darius.glb` |
| 3 | `selene` | Selene Frostveil | `models/selene.glb` |
| 4 | `elira` | Lady Elira | `models/elira.glb` |
| 5 | `orin` | Orin Ashlance | `models/orin.glb` |
| 6 | `seraphine` | Dame Seraphine | `models/seraphine.glb` |
| 7 | `talia` | Talia Stormcall | `models/talia.glb` |
| 8 | `finn` | Finn Valecourt | `models/finn.glb` |
| 9 | `brynn` | Brynn Cogwright | `models/brynn.glb` |
| 10 | `mirelle` | Mirelle Thornroot | `models/mirelle.glb` |
| 11 | `nyx` | Nyx Varrin | `models/nyx.glb` |
| 12 | `vesper` | Vesper Crowe | `models/vesper.glb` |
| 13 | `thorne` | Brother Thorne | `models/thorne.glb` |
| 14 | `rook` | Rook Wildbane | `models/rook.glb` |
| 15 | `asha` | Asha Ironfist | `models/asha.glb` |
| 16 | `rowan` | Rowan Firebrand | `models/rowan.glb` |
| 17 | `kael` | Kael Runebinder | `models/kael.glb` |
| 18 | `cedric` | Cedric Vale | `models/cedric.glb` |
| 19 | `morwen` | Morwen Blackveil | `models/morwen.glb` |
| 20 | `garruk` | Garruk Stonefist | `models/garruk.glb` |

All twenty original files currently exist, **but presence does not establish correct appearance, class, equipment or movement**. Review **one character at a time** against the established portrait, outfit, weapon, role and lore height. Record status as `unreviewed` until visual approval; do not blindly overwrite the original models or alter saved slot order.

## Safe correction workflow

1. Run `tools/audit_original_20.py` on the repository to identify rig/clip gaps in the originals.
2. For each hero, compare the exact original portrait with the *loaded game model* (not just a generic viewer render); verify identity, costume, weapons and recognizable silhouette.
3. If replacement model is supplied, stage as a **named candidate**, audit GLB joint weights and animation clips, then retarget/create gait and combat, test mobile rendering and get approval.
4. Promote candidate without changing `GLB_IDS` or global slot ordering. Keep the previous binary and one signed Android build for rollback.
5. Never make Sslythar visible while his basilisk slither is in private development.
