# The Mirrored Flame (Kael Runebinder and Rowan Firebrand)

Branch `quest-kael-rowan` (not on main, no APK). Boss decisions: **magic doubles** (not blood twins), mostly serious tone, **Mirror Warden** villain.

## Premise
Rowan Firebrand (Mage) and Kael Runebinder (Runemaster) look near-identical because a Starforge mirror rune split one hero in two. The Mirror Warden steals identities and wants the rune. Brynn Cogwright guides them.

## How it plays
- Separate **Mirrored Flame card** under the Veyra card on Explore, with its own banner ("New chapter ... tap to read") and journal section. Independent of the Veyra quest. Unlocks after 6 kills (or after Veyra V1, or quest step 2).
- Story panels reuse the Veyra story dialog (`Quest.play`). Choices are saved in `state.mirror.choices`.
- **Mirror Bond** (from M4): while Kael and Rowan are both in the party, attack +8% and defense +5% (Unity ending: +18% / +12%).
- No new party slots and no extra sprites. If a chapter needs both heroes and the party is full, the last non-active other member is swapped out (with a toast); the party never exceeds its cap.

## Chapters
| # | Title | Zone | Objective | Reward |
|---|-------|------|-----------|--------|
| M1 | Two of a Kind | Whispering Wilds | Ember Wisp. Choice: who steps in first (flavour). Recruits Rowan and Kael. | 400 gold, 10 shards |
| M2 | The Wrong Twin | Ashen Ruins | Ruin Sentinel. Must have played as **both** Kael and Rowan (tap portraits). | 800 gold |
| M3 | Borrowed Faces | Tidewrack Coast | Masked Shade, then Tidewrack Mimic. Unlocks the coast on its own. | 1,900 gold |
| M4 | Rune and Flame | Frostbite Pass | Tap **Trade staves**, defeat Frost Wyrm. Gives Mirror Bond, Runeflame Sigil, recruits Brynn, unlocks Dusk Hollow. | 3,000 gold |
| M5 | Which One Is Real? | Dusk Hollow | **Mirror Trial** (3 choice rounds). Each wrong or skipped round adds one Mirror Shade to the Mirror Warden fight (max 3). | 4,500 gold, unlocks Starforge |
| M6 | The Shattered Glass | Starforge Hall (new zone) | Mirror Warden, Unmasked. At 50% a glass shield rises (blocks damage): press **Crack the glass** once as Kael and once as Rowan (switch heroes between presses) to break it. | 8,000 gold |
| M7 | Two Flames | Liongate | Return to the village and choose the ending. | 10,000 gold, title **Mirrorbound**, Brothers' Rune |

### Endings (M7 choice)
- **Unity**: Mirror Bond buff grows to +18% attack / +12% defense; Shared Rune Charm.
- **Own Paths**: Silver Rune Scarf (Kael) and Red Ember Cloak (Rowan) charms; +6% attack when either is the active hero; a thin silver (Kael) or red (Rowan) ring is drawn under them on the map (a canvas mark, not a sprite). Mirror Bond keeps +8% / +5%.
Skipping the final panel picks Unity.

### Zone decision
Chapter 6 uses a new, simple **Starforge Hall** story zone (`starforge`, same look as Dusk Hollow, two filler enemies), unlocked after M5 and listed in Travel only then.

## Technical notes
- Code: `www/mirror.js`; hooks in `www/game.js` (defaults, ensure, atk/def, onDefeat, tick, drawMarks, journal, zone list), `www/data.js` (Starforge zone and enemies), `www/styles.css`, `www/sw.js` (precache), `tools/build_standalone.py`.
- Save: key `guildbound_rpg_save_v1`, still `version:1`. Progress is in `state.mirror` (additive; defaults and sanitising in `Mirror.ensure`, also run on backup import). Veyra's `state.veyra` is untouched.
- Quest enemies carry `mq:true` (no `qid`), so the Veyra quest never counts them. Extra shades carry `mqx` and do not count for progress.
- Test: `tools/mirror_test.py` (Playwright, mobile 390x844). Two full runs (Unity with perfect trial, Own Paths with all-wrong trial). Debug hooks only shorten fights.
- Deferred: painted art for panels, a bespoke animation for the shield and Mirror Trial, standalone `PLAY-VARNETHRYL.html` not rebuilt on this branch.
