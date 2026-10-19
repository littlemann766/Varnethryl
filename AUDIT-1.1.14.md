# Varnethryl v1.1.14 — conservative save and display patch

Changes:
- Preserve saved hero index `0` (Sir Aldric) in 3D startup instead of replacing it with index `1` (Darius).
- On page hide/background, mark and flush the current position even if the polling interval did not notice a final small move.
- Keep the saver dirty when a storage write fails so a later flush may retry.
- Align the project version, service-worker cache, 3D asset cache, and 3D display at 1.1.14.
- Add regression tests for hero 0, shutdown flush code, and failed-write retry.

Out of scope: no changes to 3D models, skeletons, clips, character animations, combat, world physics, or save-data schema.

Risks: local storage can remain unavailable (retry occurs on a later flush/mark). A real-device test remains necessary. Export in-game saves before updating.

Run: `node tools/save3d_test.mjs` and the existing JS test scripts.
