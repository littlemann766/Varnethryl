# Six-character reskin to skin cards (2026-10-25 ET, boss-approved)
garruk, rook, talia, cedric, morwen, nyx. Texture-only: only the base-colour image in each GLB was replaced
(mesh, skin weights, skeleton, animations, ORM, scale, triangle counts untouched; LOD textures are the new base resized 1024/512 like the originals).
Method: per-triangle bone-region map rasterised into UV space (label.py) + HSV recolour rules per character (recolor.py), injected with glb.py/build.py.
- rook: cloak -> forest green, legs brown leather. talia: teal robe, white/silver highlights. cedric: crimson cape, royal-blue tunic.
- morwen: purple robes/hood. nyx: red accents (cape lining/sash). garruk: source already bare-chested fur barbarian; only warmed skin/red.
Not done: Garruk geometry (not needed), Cedric lute (no finger/hand rigid prop added), Rook wolf (separate companion).
Palms-up diagnosis: see palms.jpg; 21-bone rigs have near-T rest arms with world-aligned joint frames; run clip rotates upperArm/foreArm about X, which on an outstretched arm is a twist -> palms roll up. Clip/rest mismatch (Lucian retarget or arms-down rebind).
