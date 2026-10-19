/* CENTRAL CHARACTER SCALE CONFIG (plain data, no THREE/DOM). ONE place for real-size play. Read by main.js (render/physics/speed), combat (reach), fight.js, camrig.js (camera) and Lucky's buildings/stairs/doors.
   Models are authored in metres and their scale is BAKED (never rescaled here). `height` is the true model height in METRES (hero = 1.905 m); world units = metres * WORLD_PER_M(HS) (0.947 * HS = 1.4205 at HS 1.5).
   Heights are NOT yet confirmed by the boss: edit the numbers below only. Anything missing falls back to DEFAULT (the 1.905 m hero).
   Format:  CHARS[id] = { height, radius, speed, step, reach, camDist, camHeight, camMin, camMax }   (all optional; metres unless noted)
     height    model height in metres (info + doors/stairs fit tests)       radius   body collision radius in metres (player collision)
     speed     movement speed multiplier vs the hero (capped by SPEED_CAP)   step     max step-up height in metres (stairs/curbs)
     reach     melee/AoE range multiplier for combat skills                  camDist/camHeight  third-person distance / height multipliers (x the hero's camera)
     camMin/camMax  zoom clamp for this character (zoom pref units, hero 0.4..1.7)
   Lookup key = the dropdown model id (e.g. 'n:ashentitan_new'). */
export const HERO_M = 1.905;
export const HEIGHT_MAX = 120;                              // metres (was 60): the 20x/40x/60x giant titans are 38.1 / 76.2 / 114.3 m
export const WORLD_PER_M = (HS = 1.5) => 0.947 * HS;       // main.js: extra models are authored in metres and drawn at 0.947*HS
export const SPEED_CAP = 1.6;                               // never faster than 1.6x the hero (phone-friendly, keeps the world readable)
export const COLLIDE_RADIUS_CAP = 2.1;                        // metres: the PLAYER collision radius never exceeds this (giants stay able to walk the town; they visually overlap thin buildings = giant mode)
export const DEFAULT = Object.freeze({ height: HERO_M, radius: 0.53, speed: 1, step: 0.35, reach: 1, camDist: 1, camHeight: 1, camMin: 0.4, camMax: 1.7 });
export const CHARS = {
  'n:ashentitan_new': { height: 11.4, radius: 3.2, speed: 1.4, step: 2.0, reach: 3.2, camDist: 3.4, camHeight: 3.2, camMin: 0.55, camMax: 1.6 },          // Beth native 11.4 m (6x hero)
  // Vaelthryx variants are baked at DIFFERENT native sizes (measured in-game): _new6 14.3 m tall (79 m long), _new 2.0 m, _straight_rig 0.65 m. Boss quote ~18.7 m coiled; edit height here once confirmed.
  'n:vaelthryx_new': { height: 2.0, radius: 0.6, speed: 1.0, step: 0.4, reach: 1.1, camDist: 1.05, camHeight: 1.05, camMin: 0.5, camMax: 1.7 },
  'n:vaelthryx_new6': { height: 14.3, radius: 4.0, speed: 1.5, step: 2.6, reach: 4.0, camDist: 3.8, camHeight: 3.7, camMin: 0.6, camMax: 1.7 },
  // PLAYABLE Vaelthryx (boss 1:11 AM): 10x the player. height = 10 * HERO_M (19.05 m), derived from the base constant. `native` = the GLB's authored height (0.65 m); the model is scaled at LOAD by loadScale() = height/native, the file on disk is untouched.
  'n:vaelthryx_straight_rig': { height: 10 * HERO_M, native: 0.65, radius: 5.2, speed: 1.5, step: 3.0, reach: 4.8, camDist: 5.0, camHeight: 4.8, camMin: 0.6, camMax: 1.7 },
  'n:frosttroll_a': { height: 5.7, radius: 1.6, speed: 1.25, step: 1.0, reach: 1.9, camDist: 1.9, camHeight: 1.8, camMin: 0.5, camMax: 1.7 },              // trolls = 3x the hero
  'n:frosttroll_b': { height: 5.715, radius: 1.8, speed: 1.25, step: 1.0, reach: 1.9, camDist: 1.9, camHeight: 1.8, camMin: 0.5, camMax: 1.7 },   // frosttrollB_1 (Beth 1019) baked 5.715 m ~ approved 5.7 m troll
  'o:vaelthryx': { height: 3.59, radius: 1.0, speed: 1.1, step: 0.7, reach: 1.4, camDist: 1.5, camHeight: 1.4, camMin: 0.45, camMax: 1.7 },                  // blocky builder (authored 5.1 world units)
  /* ---- test-bundle-1019 (Beth). Boss-approved heights only: everyone 1.905 m, Titan 11.4, frost trolls 5.7, Vaelthryx 19.05, giants 20/40/60x.
     Bundle GLBs are size-baked; where the baked height differs from the approved one, `native` = baked height and the model is scaled at load to the approved height (listed in the v1.1.14 report). ---- */
  'n:vaelthryx_new7': { height: 10 * HERO_M, radius: 5.2, speed: 1.5, step: 3.0, reach: 4.8, camDist: 5.0, camHeight: 4.8, camMin: 0.6, camMax: 1.7 },   // baked 19.05 m = approved, no rescale
  'n:phoenix_new3': { height: HERO_M, native: 0.756 },   // core/phoenix_new3.glb baked 0.756 m -> approved 1.905 m
  'n:wren_new3': { height: HERO_M, native: 1.35 },   // core/wren_new6_fight.glb baked 1.35 m -> approved 1.905 m
  'n:ember_new3': { height: HERO_M, native: 1.296 },   // core/ember_new4_fight2.glb baked 1.296 m -> approved 1.905 m
  'n:thrain_new4': { height: HERO_M, native: 1.477 },   // core/thrain_new6_fight.glb baked 1.477 m -> approved 1.905 m
  'n:garruk_new5': { height: HERO_M, native: 2.02 },   // core/garruk_new5_arms_fight.glb baked 2.02 m -> approved 1.905 m
  'n:pip_new2': { height: HERO_M, native: 0.52 },   // core/pip_new3_fight.glb baked 0.52 m -> approved 1.905 m
  'n:ssylthar_coil': { height: HERO_M, native: 2.044 },   // night3/ssylthar_coil.glb baked 2.044 m -> approved 1.905 m
  'n:hydrella_coil': { height: HERO_M, native: 1.928 },   // night3/hydrella_coil.glb baked 1.928 m -> approved 1.905 m
  'n:orin_armor2': { height: HERO_M, native: 1.84 },   // night2/orin_armor2.glb baked 1.84 m -> approved 1.905 m
  'n:finn_armor2': { height: HERO_M, native: 1.736 },   // night2/finn_armor2.glb baked 1.736 m -> approved 1.905 m
  'n:seraphine_armor2': { height: HERO_M, native: 1.77 },   // night2/seraphine_armor2.glb baked 1.77 m -> approved 1.905 m
  'n:garruk_armor2': { height: HERO_M, native: 2.02 },   // night2/garruk_armor2.glb baked 2.02 m -> approved 1.905 m
  'n:rook_armor2': { height: HERO_M, native: 1.95 },   // night2/rook_armor2.glb baked 1.95 m -> approved 1.905 m
  'n:elira_armor2': { height: HERO_M, native: 1.699 },   // night2/elira_armor2.glb baked 1.699 m -> approved 1.905 m
  'n:brynn_armor2': { height: HERO_M, native: 1.592 },   // night2/brynn_armor2.glb baked 1.592 m -> approved 1.905 m
  'n:cedric_armor2': { height: HERO_M, native: 2.017 },   // night2/cedric_armor2.glb baked 2.017 m -> approved 1.905 m
  'n:asha_armor2': { height: HERO_M, native: 1.71 },   // night2/asha_armor2.glb baked 1.71 m -> approved 1.905 m
  'n:kael_armor2': { height: HERO_M, native: 1.805 },   // night2/kael_armor2.glb baked 1.805 m -> approved 1.905 m
  'n:mirelle_armor2': { height: HERO_M, native: 1.652 },   // night2/mirelle_armor2.glb baked 1.652 m -> approved 1.905 m
  'n:morwen_armor2': { height: HERO_M, native: 1.736 },   // night2/morwen_armor2.glb baked 1.736 m -> approved 1.905 m
  'n:nyx_armor2': { height: HERO_M, native: 1.667 },   // night2/nyx_armor2.glb baked 1.667 m -> approved 1.905 m
  'n:rowan_armor2': { height: HERO_M, native: 1.877 },   // night2/rowan_armor2.glb baked 1.877 m -> approved 1.905 m
  'n:selene_armor2': { height: HERO_M, native: 1.946 },   // night2/selene_armor2.glb baked 1.946 m -> approved 1.905 m
  'n:talia_armor2': { height: HERO_M, native: 1.772 },   // night2/talia_armor2.glb baked 1.772 m -> approved 1.905 m
  'n:thorne_armor2': { height: HERO_M, native: 1.877 },   // night2/thorne_armor2.glb baked 1.877 m -> approved 1.905 m
  'n:vesper_armor2': { height: HERO_M, native: 1.768 },   // night2/vesper_armor2.glb baked 1.768 m -> approved 1.905 m
  'n:titan_giant_20x': { height: 38.1, radius: 10.6, speed: 1.6, step: 7.0, reach: 10.0, camDist: 8, camHeight: 8, camMin: 0.6, camMax: 1.7 },   // giant test spawn (night3/titan_giant_20x.glb), owner-only
  'n:titan_giant_40x': { height: 76.2, radius: 21.2, speed: 1.6, step: 14.0, reach: 20, camDist: 8, camHeight: 8, camMin: 0.6, camMax: 1.7 },   // giant test spawn (night3/titan_giant_40x.glb), owner-only
  'n:titan_giant_60x': { height: 114.3, radius: 31.8, speed: 1.6, step: 21.0, reach: 20, camDist: 8, camHeight: 8, camMin: 0.6, camMax: 1.7 },   // giant test spawn (night3/titan_giant_60x.glb), owner-only
};
const clampN = (v, lo, hi, d) => { v = +v; return Number.isFinite(v) ? Math.max(lo, Math.min(hi, v)) : d; };
/* profile in METRES with every field filled + clamped (safe even if the config is edited badly) */
/* load-time model scale for models whose authored size differs from the config height (1 = use the normal fit) */
export const loadScale = (id) => { const c = CHARS[id]; return c && c.native > 0 ? clampN(c.height, 0.3, HEIGHT_MAX, DEFAULT.height) / c.native : 1; };
export function profileFor(id) {
  const c = Object.assign({}, DEFAULT, CHARS[id] || {});
  return { id: id || '', height: clampN(c.height, 0.3, HEIGHT_MAX, DEFAULT.height), radius: clampN(c.radius, 0.1, 20, DEFAULT.radius), speed: clampN(c.speed, 0.3, SPEED_CAP, 1), step: clampN(c.step, 0.05, 8, DEFAULT.step), reach: clampN(c.reach, 0.5, 8, 1),
    camDist: clampN(c.camDist, 0.5, 8, 1), camHeight: clampN(c.camHeight, 0.5, 8, 1), camMin: clampN(c.camMin, 0.2, 1.7, 0.4), camMax: clampN(c.camMax, 0.4, 2.5, 1.7), scale: clampN(c.height, 0.3, HEIGHT_MAX, DEFAULT.height) / HERO_M, custom: !!CHARS[id] };
}
/* same profile in WORLD units (height/radius/step) for the engine */
export function worldProfile(id, HS = 1.5) { const p = profileFor(id), k = WORLD_PER_M(HS); return Object.assign({}, p, { heightW: p.height * k, radiusW: Math.min(p.radius, COLLIDE_RADIUS_CAP) * k, stepW: p.step * k }); }
/* does a character of this id fit through a door of this height/width (metres)? Lucky: giants may stand outside / enter without fitting (giant-mode fallback). */
export function fitsDoor(id, doorH, doorW) { const p = profileFor(id); return p.height <= doorH && p.radius * 2 <= doorW; }
export const isGiant = (id) => profileFor(id).height > HERO_M * 2;
