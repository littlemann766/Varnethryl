# Incoming enemy artwork

Drop finished enemy / boss art here (png, jpg or webp, any size, plain or busy background; one full-body figure per image).

Name each file after the enemy, lower-case with dashes, e.g. `wild-wolf.png`, `ashen-titan.png`.
Known enemies: wild-wolf, forest-raider, vine-wraith, ash-skeleton, rune-sentinel, frost-hound, ice-wraith, glacier-brute, ashen-titan.

Then run from the repo root:

    pip install rembg onnxruntime scipy pillow numpy
    python3 tools/ingest_enemy_art.py            # all new images
    python3 tools/ingest_enemy_art.py --height 70 wild-wolf.png   # override in-world height

The script cuts the figure out (rembg), cleans the edge, scales it onto a 256x256 canvas with a shared baseline,
writes `assets/enemies/<name>.png`, records its in-world height in `assets/enemies/manifest.json`,
and moves the original into `enemies-incoming/processed/`. The game picks the art up by enemy name
automatically (falls back to the old blob if no art exists). Bump the cache version in `sw.js` when shipping.
