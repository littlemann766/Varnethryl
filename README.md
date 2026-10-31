# Varnethryl

Varnethryl is now a **Godot 4.7 game** (Mobile renderer). The Godot project lives at the repo root (`project.godot`, `main.tscn`).

- `multiplayer/` – the live Node multiplayer/auth server (Railway deploys from here; unchanged). The Godot client talks to it from `net/Net.gd`.
- Snapshot of Godot test build godot-test-33 (local commit 1b7e415).
- The old web game was removed; the full pre-Godot main is preserved on branch `backup-main-before-godot`.

Test APKs are published as GitHub prereleases (`godot-test-N`). Build/ outputs, `.godot/` cache and keystores are not committed.
