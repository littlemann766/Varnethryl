# HUD implementation (branch hud-fullscreen)
Files: `www/hud.js` (DOM overlay, party/quest/minimap/chat/potions), `www/hud.css` (styling + web/land/port layouts), `www/hud-config.js` (logo + painted/parallax background slot), `www/fonts/Cinzel.woff`, `www/assets/hud/*`.
- Layout mode lives on `<html data-hud="web|land|port">` (+ `data-hud-small="1"` on small phones). Sizes scale with `--u` / `--sk`, user HUD size/opacity (Settings > HUD) via `--hs` / `--ho`.
- Adventure screen is edge-to-edge (`body.hud-on`). The top bar and nav tuck away; the HUD menu button (☰) slides them in. Journal = book, Inventory = bag, World map/travel = compass or minimap tap.
- Party list = every party member except the controlled hero; 3 heroes total normally, 4 on the Titan Vault (needs guild party capacity ≥ 4).
- Blue bar = Ultimate "Focus" (charge). Potions (Q/E/R) are new, saved additively in `state.potions`; ~12% drop from enemies, always from a boss.
- Painted art: edit `HUD_CONFIG.background.layers` in `hud-config.js` (preview any time with `?bgdemo=1`).
- Layout editor keys added: hudHero, hudMenu, hudMini, hudQuest, hudChat, hudPotions (plus existing stick/dpad/skill ids).
- Tests: `tools/hud_test.py` (web 1280x720, phone 844x390 / 390x844, small phones), `tools/hud_shots.py`.
