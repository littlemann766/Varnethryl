# Optional original creator scenery models

This folder holds **seven textured static GLBs** placed in designated Varnethryl areas. The models are referenced by `scenery-map-data.js` and streamed only when the player approaches.

Upload these unmodified files here:

| Filename | Area |
|---|---|
| `volcano.glb` | Ashen Titan volcano outskirts |
| `lava-rock.glb` | Ashen Titan lava region |
| `sailing-ship.glb` | Volcanic harbor water |
| `castle-props.glb` | Castle Keep courtyard |
| `medieval-weapon.glb` | Blacksmith display |
| `ice-cavern.glb` | Frost realm rocky side cavern |
| `ice-crystals.glb` | Frost realm crystal clusters |

Original uploads were audited: each of these seven has UV coordinates and an embedded texture, and is a static mesh without animation clips.

The original 3D buildings, terrain, water, boss models, combat and collision remain as fallback; missing scenic assets do not crash gameplay. The dragon and fantasy warriors were deliberately not inserted as moving characters because they contain no animation clips. The armor/equipment models are deferred as requested.

Do not rename the files. After adding GLBs to this directory, run the browser terrain and Android QA checks on the branch before release.
