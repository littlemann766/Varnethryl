# Varnethryl — Approved Model Keep Register

This is the roster/skin decision log for the Varnethryl 3D game. **Do not delete any old GLB, move an existing character slot, or overwrite saves just to hide a skin.** The existing 20 hero slot indices remain unchanged. Proposed art variants can stay on disk while hidden in the chooser.

## Owner and hero decisions
- **Owner:** new appearance is preferred; locked 1.905 m (6 ft 3 in). Existing in-repository `models-new/owner.glb` remains as the gameplay fallback. A different newly requested Owner mesh **still needs its actual file and a validated complex combat rig** before replacing it. Required: deformable spine/chest, clavicles, shoulders, upper/lower arms, hands and finger chains; legs, feet/toes, neck/head; right-handed lightsaber grip socket; idle, walk, run, turn, dodge, jump, 3-hit saber combo, special skills, ultimate, hit, death. Test skin weights, GLB animations, weapon alignment and collision before activating.
- **Sir Aldric:** keep Old and Blocky.
- **Asha Ironfist:** keep Old and New.
- **Garruk Stonefist:** keep Old and New 5.
- **Darius Umbral:** Blocky only in the visible selector; retain other files for rollback.
- **Lady Elira:** Blocky only in the visible selector; retain old assets for rollback.
- **Remaining heroes:** preserve their current variants until a specific newer-skin decision is confirmed; never silently delete them.
- **Luna:** white puppy. Playful, energetic puppy movement, bouncing and following.
- **Peaches:** two brown puppy skin choices (A/B). Keep **both** for side-by-side comparison, with the same playful puppy behavior.

## Character lore-height reference

The Owner is exactly **1.905 m**. Each hero has one central body-height target; hair, weapons, wings and tall helmets are excluded. Existing written lore overrides a proposed number, but proportions are never stretched on one axis.

| Hero | Feet/inches | Metres |
|---|---|---|
| Sir Aldric | 6′2″ | 1.8796 |
| Darius Umbral | 6′2″ | 1.8796 |
| Selene Frostveil | 5′9″ | 1.7526 |
| Lady Elira | 5′8″ | 1.7272 |
| Orin Ashlance | 6′0″ | 1.8288 |
| Dame Seraphine | 5′10″ | 1.7780 |
| Talia Stormcall | 5′10″ | 1.7780 |
| Finn Valecourt | 5′9″ | 1.7526 |
| Brynn Cogwright | 5′4″ | 1.6256 |
| Mirelle Thornroot | 5′6″ | 1.6764 |
| Nyx Varrin | 5′7″ | 1.7018 |
| Vesper Crowe | 5′10″ | 1.7780 |
| Brother Thorne | 6′1″ | 1.8542 |
| Rook Wildbane | 6′3″ | 1.9050 |
| Asha Ironfist | 5′11″ | 1.8034 |
| Rowan Firebrand | 6′1″ | 1.8542 |
| Kael Runebinder | 5′11″ | 1.8034 |
| Cedric Vale | 6′0″ | 1.8288 |
| Morwen Blackveil | 5′9″ | 1.7526 |
| Garruk Stonefist | 6′10″ | 2.0828 |

**Bosses using existing GitHub GLBs:** Frost Troll A and B exactly **5.715 m** each (3× Owner); Ashen Titan available in 6×, 20×, **40× active lava encounter**, and 60×; Balthrix available in 6× roam and 50× model-viewer comparison.

## Uploaded source GLBs pending optimized GitHub import

The following uploaded GLBs were found in the conversation, **not yet copied into the game repository**. Keep originals untouched and do not assign hero identities or guessed lore heights from ambiguous filenames. Before importing, optimize textures/meshes, check rights and rig integrity, ensure less than GitHub's single-file upload limit, and test phone frame rate:

- fiery phoenix 3d model (1)(1).glb
- Meshy_AI_A_massive_frost_troll_1019010515_texture.glb (**a second upload with (1) is a duplicate**)
- fantasy centaur 3d model.glb
- fantasy ogre 3d model.glb
- barbarian warrior 3d model(1).glb
- vampire character 3d model.glb
- mermaid 3d model.glb
- lava+golem+3d+model.glb
- griffin 3d model.glb
- fantasy queen 3d model.glb
- fantasy character 3d model.glb
- dragon head 3d model.glb
- fantasy mermaid 3d model.glb
- cute polar bear 3d model.glb
- fantasy armored dwarf 3d model.glb
- wizard owl 3d model.glb
- dragon 3d model.glb
- fantasy warrior 3d model.glb
- hydra 3d model.glb
- ice queen character 3d model.glb
- Meshy_AI_A_female_pink_nosed_p_1020013823_texture.glb
- Meshy_AI_A_cute_furry_dog_name_1020013002_texture.glb
- Meshy_AI_A_cute_furry_dog_name_1020012439_texture.glb
- Meshy_AI_Talia_is_a_graceful_t_1020014611_texture.glb (**153 MB source; must be compressed before a normal GitHub upload**)

The three puppy GLBs need visual matching to **Luna**, **Peaches A**, and **Peaches B** before file aliases are approved. More uploaded source models may exist in earlier conversations and should be inventoried, but this register never treats a name or screenshot as proof a playable model was deployed.

## Integration safety
1. Preserve current names, slot order, save format and last working models.
2. Measure each imported model foot-to-head (or species-equivalent anatomical height) and uniformly scale to lore in `www/proto3d/charscale.js`.
3. Add collision, camera, attack reach and root-motion animation using that one profile.
4. Test all GLBs, texture budgets, skeleton and attack clips on Android; use a fallback on failure.
5. Do not call an uploaded asset **integrated** until the GLB is in the GitHub repo, selectable in game, and has passed actual browser/Android tests.
