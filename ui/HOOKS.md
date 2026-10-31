# port-ui hooks (for other branches)
Autoloads added to project.godot: `VPrefs` (core/save/prefs.gd), `VSave` (core/save/save_system.gd), `VUI` (ui/ui_root.gd, CanvasLayer 20).
- Town/render (scripts/main.gd): read `VPrefs.tier()` (0 Low..3 Ultra) and `VPrefs.prefs.shadows`, connect `VPrefs.changed` -> apply_quality(). Then remove the old Quality/Time/Speed/FPS buttons + debug label (they overlap the ☰ Menu/minimap), or move them into Settings › Owner & Dev via `VUI.dev_action`. Call `VUI.set_fps(fps)`. Feed minimap: `VUI.hud.minimap.set_map_texture(tex, Rect2 world XZ)`, `set_player(Vector2(x,z), yaw)`, `set_markers([{pos,color}])`.
- Camera: `VPrefs.prefs.view` third/first, `camMode` follow/free, `lookSens`/`zoomSens`, `zoom`. Freeze look input while `VUI.menu_toggled(true)`.
- Heroes: `VUI.hero_selected(id)` (www/data.js index; `VSave.state.active`/party already updated). Portraits: ui/assets/heroes/<id>.webp.
- Game flow: `VUI.play_solo`, `VUI.multiplayer_requested(world)`, `VUI.returned_to_title`, `VUI.travel_requested("town"|"sail"|"hydra")`.
- Save: set `VUI.get_snapshot = func(): return {x,z,yaw,zone,hero}`; autosave every 5 s, on pause/close, and on return to title. Raw save: `VSave.state` + `VSave.write_state()`; JS-compatible keys (guildbound_rpg_save_v1, p3d, vn.active3d.v1, vn_p3d_prefs_v1). `VSave.import_json(localStorage blob)` for migration.
- Combat: `VUI.combat_toggled(on)`, `VPrefs.prefs.combat`. Owner cheats: `VUI.owner_cheat(key, value)` keys god/fly/noclip/bump/unlimited/nocd/bamboo/speed/remax/titan/panel — only emitted after the owner gate passes; sets save.cheated=true.
- Multiplayer: `VUI.coowner_requested` (CoOwner is server-verified, like coowner-panel.js), quick-menu world list in ui/quick_menu.gd WORLDS.
Tests: `godot --headless res://ui/tests/test_ui.tscn`; screenshots: `ui/tests/shots.tscn -- --world`.
