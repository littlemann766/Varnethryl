# Character audit 2026-10-25 (ET)
Columns: skin card | source front | source back | in-game (godot-proto/characters/<id>_lod1.glb) front | back | run 30% | run 70% | attack1 50%.
Result: all 30 in-game character GLBs match their source GLB (same textures, colours, capes); no tearing in run/attack frames.
Gaps are between source model and skin card (source itself differs) - need a decision: garruk (armoured, card = fur barbarian), rook (grey hood, card = green beastmaster + wolf), talia (grey, card = teal/white), cedric (no bard red/blue, no lute), morwen/nyx (very dark vs purple / red accents).
Motion notes for Lucian: stonetroll, vesper, talia keep arms near T-pose in run/attack.
Owner yellow suit + purple cape IS the source (owner_new5_fight); not a placeholder.
