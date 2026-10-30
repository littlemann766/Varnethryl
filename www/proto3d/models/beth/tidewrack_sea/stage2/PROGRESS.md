# Stage 2 progress (Saltglass Coast + Sunken Ward)
Made by Beth on 2026-10-30. All test renders were done in /tmp copies, and those copies are deleted afterwards.

| Step | Status |
|---|---|
| Stage 1 polish: galleon upgrade sails now cover all 3 masts; T1 figurehead is now a carved bust with a brass collar; contact sheet re-rendered and checked | done |
| Coast terrain from the v4 mask: cliffs, beaches, inlets, islets; split into 11 tiles + lod1 + collider | done |
| Saltglass Landing cliff port | done |
| Echo Grotto, Glasswyrm Cavern, Smugglers' Throat: cave clefts carved into the cliff + mouths | done |
| Sunken Ward surface ruins + dive raft | done |
| Saltglass crystals, offshore rocks and stacks, beach dressing, beached wreck | done |
| Storm wall + fog bank for region B | done |
| Renders checked by eye, small jpgs in renders/small/ | done |

## Open / next
- Cave interiors (Stage 3), and the Sunken Ward underwater cell (the dive itself).
- Textures and UVs: everything is still vertex colour.
- Smugglers' Throat and Echo Grotto read more like rocky clefts than caves from far away. They need a bigger dark overhang.
- The seam view to the Archipelago is mostly open sea, because the A islands are about 600 m away and in fog.
- Overview cameras are a bit high, so the cliffs read best in the close-ups.
| Storm border v2: layered soft fog + storm sky + choppy dark sea, invisible collider unchanged; checked at sailing height, at a distance and inside the bank | done |

## Stage 4 polish
- Cave overhang + roof slabs replaced by lumpy rock clusters (less boxy). C3 camera moved to open-water approach to avoid the Echo-inlet dark spike artefact (~(-2290,-230), tile x1z1, cause unknown). Re-rendered all shots.
- Echo spikes ROOT CAUSE (stage 4e): not bad mesh data (tile x1z1 checked: no stray verts, sane Y range, no flipped faces). The Echo Grotto mouth faces a ~35 m wide north inlet; the old shot put the camera a fixed 60 m in front of the mouth at y16, i.e. INSIDE the north-bank cliff (terrain ~30 m there). The thin dark "spikes" were cliff triangles clipping the near plane. Fix: render_stage2 `clear_dist()` walks out along the mouth facing using coast_shore_dist.png and stops at the last open-water point; new shot C3b_echo_grotto_mouth_front keeps the original front-of-mouth framing. Game note: don't spawn cameras/skiffs at fixed offsets in front of this mouth.
