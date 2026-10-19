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
  // game-ui 2390da3 explicit pip/phoenix/wren/owner entries folded into HERO_HEIGHTS below (same heights; full per-hero set + scaled speed/camera/radius)
  'o:vaelthryx': { height: 3.59, radius: 1.0, speed: 1.1, step: 0.7, reach: 1.4, camDist: 1.5, camHeight: 1.4, camMin: 0.45, camMax: 1.7 },                  // blocky builder (authored 5.1 world units)
  /* ---- test-bundle-1019 (Beth). Boss-approved heights only: everyone 1.905 m, Titan 11.4, frost trolls 5.7, Vaelthryx 19.05, giants 20/40/60x.
     Bundle GLBs are size-baked; where the baked height differs from the approved one, `native` = baked height and the model is scaled at load to the approved height (listed in the v1.1.14 report). ---- */
  'n:vaelthryx_new7': { height: 10 * HERO_M, radius: 5.2, speed: 1.5, step: 3.0, reach: 4.8, camDist: 5.0, camHeight: 4.8, camMin: 0.6, camMax: 1.7 },   // baked 19.05 m = approved, no rescale
  'n:ssylthar_coil': { height: HERO_M, native: 2.044 },   // night3/ssylthar_coil.glb baked 2.044 m -> approved 1.905 m
  'n:hydrella_coil': { height: HERO_M, native: 1.928 },   // night3/hydrella_coil.glb baked 1.928 m -> approved 1.905 m
  'n:titan_giant_20x': { height: 38.1, radius: 10.6, speed: 1.6, step: 7.0, reach: 10.0, camDist: 8, camHeight: 8, camMin: 0.6, camMax: 1.7 },   // giant test spawn (night3/titan_giant_20x.glb), owner-only
  'n:titan_giant_40x': { height: 76.2, radius: 21.2, speed: 1.6, step: 14.0, reach: 20, camDist: 8, camHeight: 8, camMin: 0.6, camMax: 1.7 },   // giant test spawn (night3/titan_giant_40x.glb), owner-only
  'n:titan_giant_60x': { height: 114.3, radius: 31.8, speed: 1.6, step: 21.0, reach: 20, camDist: 8, camHeight: 8, camMin: 0.6, camMax: 1.7 },   // giant test spawn (night3/titan_giant_60x.glb), owner-only
};

/* v1.1.15 REAL HERO HEIGHTS (boss approved Beth's suggested table, 9:15 AM Oct 19). Owner stays HERO_M (1.905), Vaelthryx 10x, Titan 11.4, trolls 5.7.
   Source: MANIFEST.md baked heights for the core New models (pip/phoenix/wren/ember/thrain/garruk/darius/zephyr), HEIGHTS.md lore/invented heights for everyone else.
   Every variant of a hero (blocky, refined, New, armor2) is shown at that hero's height. NATIVE = measured idle height of each size-baked GLB (scaled at load to the hero height). */
export const HERO_HEIGHTS = Object.freeze({"pip": 0.52, "phoenix": 0.756, "wren": 1.35, "ember": 1.296, "thrain": 1.477, "garruk": 2.02, "darius": 1.9, "zephyr": 1.899, "aldric": 1.88, "seraphine": 1.778, "finn": 1.753, "orin": 1.829, "rook": 1.905, "elira": 1.727, "mirelle": 1.676, "rowan": 1.854, "kael": 1.803, "brynn": 1.626, "morwen": 1.753, "nyx": 1.702, "vesper": 1.778, "thorne": 1.854, "cedric": 1.829, "talia": 1.778, "selene": 1.753, "asha": 1.803, "lunara": 1.78, "marella": 1.83, "mortimer": 1.98, "coral": 1.15, "snowy": 1.1, "player": 1.0, "pikachu": 1.0, "cinder": 0.45});
export const NATIVE_H = Object.freeze({"aldric_armor2": 1.914, "orin_armor2": 1.84, "finn_armor2": 1.736, "seraphine_armor2": 1.77, "garruk_armor2": 2.02, "rook_armor2": 1.95, "elira_armor2": 1.699, "brynn_armor2": 1.592, "cedric_armor2": 2.017, "asha_armor2": 1.71, "kael_armor2": 1.805, "mirelle_armor2": 1.652, "morwen_armor2": 1.736, "nyx_armor2": 1.667, "rowan_armor2": 1.877, "selene_armor2": 1.946, "talia_armor2": 1.772, "thorne_armor2": 1.877, "vesper_armor2": 1.768, "darius_armor2": 1.9, "mortimer_new": 1.903, "lunara_new": 1.902, "marella_new": 1.977, "coral_new": 1.881, "cinder_new": 1.216, "snowy_new4": 1.514, "player_pikachu": 1.902, "asha_new3": 1.708, "garruk_new4": 1.9, "phoenix_new3": 0.756, "wren_new3": 1.35, "ember_new3": 1.296, "thrain_new4": 1.477, "garruk_new5": 2.02, "pip_new2": 0.52, "darius_new6": 1.9, "zephyr_new2": 1.899});
export const heroBase = (id) => { const b = String(id || '').replace(/^[a-z]:/, '').split('_')[0]; return b === 'owner' ? null : b; };
export const heroHeight = (id) => { const b = heroBase(id); return b && HERO_HEIGHTS[b] ? HERO_HEIGHTS[b] : null; };
/* gameplay scaled to height: collision radius and reach linear (reach floored), speed ~ sqrt(height) (walking-pace physics, clamped so tiny heroes keep up),
   collision radius never above the base 0.53 m (tall heroes up to ~2.1 m keep the base body width so every door still fits), step never below the hero's 0.35 m (tiny heroes still climb town stairs), camera distance/height eased so small heroes stay framed */
function heroProfile(h) { const s = h / HERO_M, q = Math.sqrt(s); return { height: h, radius: +Math.min(0.53, Math.max(0.18, 0.53 * s)).toFixed(3), speed: +Math.min(1.1, Math.max(0.78, q)).toFixed(3), step: +Math.max(0.35, 0.35 * s).toFixed(3), reach: +Math.min(1.15, Math.max(0.6, s)).toFixed(3), camDist: +(0.4 + 0.6 * s).toFixed(3), camHeight: +(0.35 + 0.65 * s).toFixed(3), camMin: 0.4, camMax: 1.7 }; }
/* config for an id: explicit CHARS entry, else the real-height hero profile (+ native for size-baked GLBs) */
function charOf(id) { const c = CHARS[id]; if (c) return c; const h = heroHeight(id); if (!h) return null; const k = String(id).replace(/^[a-z]:/, ''), nat = /^n:/.test(id) ? NATIVE_H[k] : 0; const pr = heroProfile(h); if (nat && Math.abs(nat - h) > 0.004) pr.native = nat; return pr; }
const clampN = (v, lo, hi, d) => { v = +v; return Number.isFinite(v) ? Math.max(lo, Math.min(hi, v)) : d; };
/* profile in METRES with every field filled + clamped (safe even if the config is edited badly) */
/* load-time model scale for models whose authored size differs from the config height (1 = use the normal fit) */
export const loadScale = (id) => { const c = charOf(id); return c && c.native > 0 ? clampN(c.height, 0.3, HEIGHT_MAX, DEFAULT.height) / c.native : 1; };
export function profileFor(id) {
  const c = Object.assign({}, DEFAULT, charOf(id) || {});
  return { id: id || '', height: clampN(c.height, 0.3, HEIGHT_MAX, DEFAULT.height), radius: clampN(c.radius, 0.1, 20, DEFAULT.radius), speed: clampN(c.speed, 0.3, SPEED_CAP, 1), step: clampN(c.step, 0.05, 8, DEFAULT.step), reach: clampN(c.reach, 0.5, 8, 1),
    camDist: clampN(c.camDist, 0.5, 8, 1), camHeight: clampN(c.camHeight, 0.5, 8, 1), camMin: clampN(c.camMin, 0.2, 1.7, 0.4), camMax: clampN(c.camMax, 0.4, 2.5, 1.7), scale: clampN(c.height, 0.3, HEIGHT_MAX, DEFAULT.height) / HERO_M, custom: !!charOf(id) };
}
/* same profile in WORLD units (height/radius/step) for the engine */
export function worldProfile(id, HS = 1.5) { const p = profileFor(id), k = WORLD_PER_M(HS); return Object.assign({}, p, { heightW: p.height * k, radiusW: Math.min(p.radius, COLLIDE_RADIUS_CAP) * k, stepW: p.step * k }); }
/* does a character of this id fit through a door of this height/width (metres)? Lucky: giants may stand outside / enter without fitting (giant-mode fallback). */
export function fitsDoor(id, doorH, doorW) { const p = profileFor(id); return p.height <= doorH && p.radius * 2 <= doorW; }
export const isGiant = (id) => profileFor(id).height > HERO_M * 2;
