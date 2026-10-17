# A Light in Dusk Hollow (Varnethryl 0.4.0)

Storyboard quest line for **Count Veyra** and **Mortimer**. Based on the boss's handwritten note and Beth's outline (`QUEST-VEYRA-OUTLINE.txt`). Names and beats are kept; the game systems it plugs into are the existing zones, combat, party and save.

## Premise
Veyra (evil) and Mortimer (good) are twin brothers born minutes apart. Mortimer, the elder, was favored, so Veyra turned cold with jealousy and burned the east wing of the Dusk Court library. Mortimer failed to reach him with words, so he gathers heroes of every crest and a few creatures to bring his brother back. It ends in redemption, not a kill. Tone: sad, warm, gothic, no gore.

## How it plays
- **Story card** on the Explore screen and a purple banner ("New chapter ... tap to read"). Starts after the first 3 kills (letter arrives).
- **Storyboard panels**: illustrated frames with a speaker, text, Next/Skip, and a few choices. Panels can be replayed from the journal.
- **Journal**: Quest journal button now also lists all 7 chapters, recruited heroes, creature allies, keepsakes and the title.
- **Mortimer** walks with the party from V2 on as a guest ally (drawn on the map, no party slot, so every hero still has exactly one sprite). Creatures (Pip, Zephyr, Coral, Snowy) trail the party.
- **Brother's Oath** (from V2): attack up to +25% and defense up to +15%, growing with each recruit and ally.
- Fights spawn as named bosses when you stand in the chapter's zone, tracked in the story card.

## Chapters
| # | Title | Zone | Fights | Recruits / allies | Reward |
|---|-------|------|--------|-------------------|--------|
| V1 | The Letter | Whispering Wilds | Snick the Sneak | Brother Thorne, Pip the Fox | Mortimer's Seal, 400 gold. Playable flashback: pick the book you carry out of the fire (keepsake). |
| V2 | A Shield and a Spear | Whispering Wilds | Grukk the Warlord | Dame Seraphine, Sir Aldric, Zephyr | Lionguard Banner, Brother's Oath, 800 gold |
| V3 | The Trail of the Raven | Ashen Ruins | Fenrik Moonhowl, Lady Noctra | Finn, Vesper, Morwen, Rook (Verdant Fang) | Veyra's Unsent Letter, unlocks Tidewrack Coast |
| V4 | The Singing Tide | Tidewrack Coast (new) | Siren Matron Lyrae, Hydrella | Asha, Coral, Queen Marella (guest) | Tidepearl |
| V5 | The Cold Hearth | Frostbite Pass | Frost Troll Brute, Scorpa, Skarn | Selene, Talia, Snowy | Frostmoon Cloak, Dragon-flight (unlocks Dusk Hollow); Glacia flies you instead of fighting |
| V6 | The Library of Ashes | Dusk Hollow (new) | Thrall Captain, Shadowblade Warden + light 3 candles | Kael, Brynn | Choice: take Veyra's Drawings, or leave them |
| V7 | The Twin Eclipse | Dusk Hollow | Count Veyra (3 phases) | n/a | Moonsilver weapon, Brothers' Sigil, Twin Moons (+8% atk/def), title "Bringer of Dawn" |

### V7 boss fight
1. **Mist**: Veyra cannot be hurt. Light 3 candles (button on the story card).
2. **Solid**: fight him down to 66%.
3. **Bat clones**: two clones appear; defeat them.
4. **Eclipse** at 33%: a shield rises; tap **Dawn Spell** to break it.
5. Finish him. He yields: Mortimer will not strike, the party lowers weapons, you give Veyra a drawing (the first one only changes dialogue), the library rebuilds, the brothers share a candle.

## Endings
- **Redeemed** (took the drawings): Veyra spared and redeemed; rewards above. If you also recruited from all five crests on the first attempt, **Veyra and Mortimer become guest allies** and appear beside the party in the Titan Vault (+10% attack there).
- **"Not yet"** (left the drawings): Veyra retreats into the mist, the quest reopens at V7, the drawings are fetched, and the second attempt always ends redeemed (no guest ally).

## Lore changes (flagged)
Mortimer is now Veyra's elder twin and recruits the party from V2; Veyra is his twin, not just an optional boss, and now gets redeemed. The Frostbite and ruins chapters use existing zones; Tidewrack Coast and Dusk Hollow are new story zones (only visible after unlocking).

## Technical notes
- Code: `www/quest.js`, data hooks in `www/game.js` and zones/enemies in `www/data.js`.
- Save: key `guildbound_rpg_save_v1`, still `version:1`. Progress is in `state.veyra` and is filled in with defaults for old saves (and on backup import).
- Test: `tools/quest_test.py` (Playwright, mobile 390x844). Story panels, travel, candles and the Dawn Spell use real taps; `window.__vn.Quest.debug` only shortens fights.
- Deferred: a real Titan-Vault fight mechanic for the guest allies, painted art for panels (placeholder illustrated frames use emoji over scene gradients), audio for panels.
