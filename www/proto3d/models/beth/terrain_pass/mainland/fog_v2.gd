class_name FogV2
## Terrain pass fix 3 (Beth): soft layered fog that fades with distance.
## Two layers in one Godot exponential fog: a thin distance haze (aerial perspective carries the far blue) plus a low
## valley mist via height fog (denser below fog_height, thinning above). Colour = horizon pulled slightly toward a
## cool blue-grey so it never turns a white sheet. Call apply() from main._env() and at the end of main._set_time().
const DENSITY := 0.00042        # was 0.0011
const AERIAL := 0.78            # was 0.5: distance fades into the sky colour (natural haze) instead of flat fog colour
const SKY_AFFECT := 0.12        # was 0.25: keeps the sky gradient/horizon silhouette
const MIST_TOP := 2.0          # m: valley mist layer top (town ground 0, hills 10-40, peaks 150-300)
const MIST_DENSITY := 0.012     # height falloff: mist thick in the lowlands/valleys, gone over ridges
static func apply(env: Environment, horizon: Color, night := 0.0) -> void:
	env.fog_enabled = true
	env.fog_mode = Environment.FOG_MODE_EXPONENTIAL
	env.fog_density = DENSITY * lerpf(1.0, 0.7, night)
	env.fog_aerial_perspective = AERIAL
	env.fog_sky_affect = SKY_AFFECT
	env.fog_height = MIST_TOP
	env.fog_height_density = MIST_DENSITY
	env.fog_light_color = horizon.lerp(Color(0.62, 0.70, 0.80), 0.35)   # cooler + a touch darker than the horizon
	env.fog_light_energy = 1.0
## Flight / high cameras (main._alt_fog): keep the existing thinning, but scale from these values:
##   env.fog_density = DENSITY * lerpf(1.0, 0.03, k); env.fog_height_density = MIST_DENSITY * lerpf(1.0, 0.2, k)
