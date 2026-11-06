# Mainland mountain — remaining piece, not applied

Read-only check of `origin/main:scripts/main.gd` (2026-11-06): `_height_raw` still has the needle term

`h += mr * (60.0 + (40.0 + 230.0 * rg * rg) * (0.3 + 0.7 * massif) + 45.0 * rg2 * rg2 * mr)`.

That file is not on `beth-world-art`. Applying the gully changes height for r ≳ 800 m and therefore collision. It was not applied, and there is no mainland render. Do not treat the mainland mountains as finished.

Fix 2 (`../mainland/fix02_main_gd.patch`) is already the smooth knee and the cut from a 45 m fine spike to 14 m. What land2 still asked for, and what is still missing, is the gully term. It only runs where `mr > 0` (r ≳ 800 m). After fix 2, the mountain line would become:

```gdscript
var rgs := smoothstep(0.0, 1.0, rg); rgs = rgs * rgs * (0.55 + 0.45 * rgs)
var gl := absf(noise.get_noise_2d(x * 3.6 - 120.0, z * 3.6 + 640.0))
h += mr * (60.0 + (40.0 + 215.0 * rgs) * (0.3 + 0.7 * massif) + 14.0 * rg2 * rg2 * mr) - mr * 18.0 * (1.0 - smoothstep(0.0, 0.18, gl)) * smoothstep(0.2, 0.6, rgs)
```

That last subtraction is the part not in fix 2. It digs gullies down the fall line. It changes height, so it changes collision. After it, rebake `terrain_n.png` and reseat range scatter. Town, farm and the volcano pad (r < ~800 m) are outside `mr`.
