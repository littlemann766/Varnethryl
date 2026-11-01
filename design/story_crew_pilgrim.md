# Varnethryl main story: "The Owner's Crew & the Ashen Pilgrim"

Design only. No game changes. Points of interest come from godot-voxel `tidewrack/stage5_manifest.json`.

## Story
A fallen holy knight, the Ashen Pilgrim (`holyknight_villain`), wants the Ashen Titan free. The fire-vents that keep the Titan asleep were sealed long ago by a captain's crew, and only those crew members know how the seals work. So the knight is hunting them down one by one to force them to open the vents. The Owner inherits the dead captain's galleon and chart, and has to reach each crew member before the knight does. Every recruit gives the ship an ability that opens the next stretch of sea, and tells the Owner where the knight will strike next. Some you save in time. At other stops he has already been and gone, and the vent is open. The ash keeps getting heavier. It ends at the volcano rim: you defeat the knight, the Titan rises, and the whole crew fights it.

## Main beats
1. **Gullhaven:** The knight raids the Founders' Stone and leaves the harbourmaster hurt. The Harbourmaster's Cache holds the captain's chart and the crew list. Pip joins. First name on the list: the lighthouse keeper.
2. **Lantern Rock (night sail):** The knight got there first, and the Old Lantern is smashed. Wren hid in the Keeper's Hut. Relight the lantern and Wren joins (unlocks **night sailing**). Wren: "He's after the diver next."
3. **Saltglass Landing:** The Singing Shards are cracked and his men are searching. Find Brynn at the Glass-diver's Chest and she joins (unlocks **cave diving**). From the Saltglass Lookout you spot the knight's ship entering Glasswyrm Cavern.
4. **Glasswyrm Cavern (cave):** His abandoned camp has a burnt order: "Frost Gate next, then the shipwright." Rowan is a prisoner in Echo Grotto.
5. **Echo Grotto (cave):** Rescue Rowan. He joins and ice-proofs the hull (unlocks **ice waters**).
6. **Frozen Wreck:** Frost trolls have Garruk cornered at the Frozen Camp. Beat them and he joins. Garruk says the knight is heading for the Frostreach Waystone.
7. **Frostreach:** Too late: the Frozen Waystone is already open (first vent; the ash gets heavier everywhere). In Rimehollow Ice Cave, the captain's Iced Chest holds a storm sail (unlocks **storm sailing**).
8. **Smugglers' Throat (storm sail):** Nyx sold the knight passage south. Win her over and she joins. She tells you where he's going: Ember Wreck, to meet Darius.
9. **Ember Wreck (mid-story fight):** At the Cinder Camp you fight the knight for the first time. He gets away towards the ash isles, but Darius is saved and joins. The Scorched Chest holds **heat plating** (unlocks **ash waters**).
10. **Vent Harbour:** Second vent: minions pour from the Ventmouth. Clear them, close the Ember Shrine and read the knight's diary in the Ash-buried Chest. Last crew member: Selene, at Saltwatch Keep.
11. **Saltwatch Keep (sail back north):** The knight's wolves are attacking the Outer Wall. Defend it and Selene joins. On Beached Wreck, the Captain's Last Log gives the volcano landing.
12. **Gullhaven, then the volcano:** The crew gathers at the Founders' Stone as ash falls on the town. At the rim you defeat the knight, the existing TitanQuest intro plays, and the Titan fight follows with crew heroes fighting alongside.

**Coverage:** 9 landings, 3 sea caves and 3 wrecks, with repeat stops at Gullhaven and the north.

## Side quests
- **Crew Bonds:** a personal errand for each recruit, for example Wren at Aurora Arch's Starwatcher's Stone, Darius at Obsidian Arch's Glassfire Shrine and Brynn at Hot Spring Grotto's Bathers' Shrine. Reward: companion upgrades.
- **Rowan's Salvage:** Rowan wants parts from Saltglass's Clifftop Cache and Coil Isle's Drowned Offering. Reward: a faster hull.
- **Serpent of Coil Isle:** Serpent Shrine plus Coil Bones (stone troll). Reward: a figurehead.

## What's new it needs
- **Code:**
  - A `quests.json` file plus a `QuestManager` autoload, with saving.
  - Dialogue boxes and points of interest you can interact with.
  - A crew roster tied into party.gd (crew show on deck and join fights).
  - Ship abilities that gate travel: night, caves, ice, storm, ash.
  - Vent states that thicken the ash, and islands that change as the story moves forward.
- **NPCs:** the heroes standing on their islands, plus a harbourmaster and smugglers (recolored guards).
- **Enemies on islands:**
  - Knight's men (recolored guards) at Saltglass Landing.
  - Frost trolls at Frozen Wreck.
  - The knight fight at Ember Wreck.
  - Minions at Vent Harbour.
  - Wolves at Saltwatch Keep.
  - Stone troll (side quest) at Coil Isle.
- **Items:** chart and crew list, storm sail, heat plating, diary, captain's log.
- **Cutscenes:** the knight escaping at Ember Wreck, and the knight's defeat at the rim leading into the Titan intro.
- **Check with Beth or the boss:** which hero gets which role.
