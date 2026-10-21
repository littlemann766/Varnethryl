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
// Allows the 50x serpent (95.25 m) and reserved 60x Titan (114.3 m); keeps the per-model scale limits explicit.
export const MAX_HEIGHT_M = 120;
export const WORLD_PER_M = (HS = 1.5) => 0.947 * HS;       // main.js: extra models are authored in metres and drawn at 0.947*HS
export const SPEED_CAP = 1.6;                               // never faster than 1.6x the hero (phone-friendly, keeps the world readable)
export const COLLIDE_RADIUS_CAP = 2.1;                        // metres: the PLAYER collision radius never exceeds this (giants stay able to walk the town; they visually overlap thin buildings = giant mode)
export const DEFAULT = Object.freeze({ height: HERO_M, radius: 0.53, speed: 1, step: 0.35, reach: 1, camDist: 1, camHeight: 1, camMin: 0.4, camMax: 1.7 });
// Approved character heights (feet/inches), measured foot to head, not horns, hair or weapons.
// Prior established lore overrides these proposed heights if the lore changes.
export const HERO_LORE_HEIGHTS=Object.freeze({
  aldric:74,darius:74,selene:69,elira:68,orin:72,seraphine:70,talia:70,
  finn:69,brynn:64,mirelle:66,nyx:67,vesper:70,thorne:73,rook:75,
  asha:71,rowan:73,kael:71,cedric:72,morwen:69,garruk:82
});
export const inchesToMeters=inches=>inches*0.0254;
const HERO_LORE=Object.fromEntries(Object.entries(HERO_LORE_HEIGHTS).map(([name,inches])=>
  [name,{height:inchesToMeters(inches),fitMeasuredHeight:true}]));
export const CHARS = {
  ...HERO_LORE,
  'n:owner': {height:HERO_M,fitMeasuredHeight:true},
  'n:owner_pika1': {height:HERO_M,fitMeasuredHeight:true},
  'n:garruk_new4': {height:inchesToMeters(82),fitMeasuredHeight:true},
  'n:garruk_new5': {height:inchesToMeters(82),fitMeasuredHeight:true},
  'n:darius_new6': {height:inchesToMeters(74),fitMeasuredHeight:true},
  'n:asha_new3': {height:inchesToMeters(71),fitMeasuredHeight:true},
  'n:ashentitan_new': { height: 10 * HERO_M, fitMeasuredHeight: true, radius: 3.2, speed: 0.64, step: 2.0, reach: 3.2, camDist: 3.4, camHeight: 3.2, camMin: 0.55, camMax: 1.6 },          // Main Titan encounter: 10x Owner
  // Extra Titan variants: all share one rigged GLB with uniform lore-height scaling.
  'n:ashentitan_20': { height: 10 * HERO_M, fitMeasuredHeight: true, radius: 5.4, speed: 0.64, step: 3.2, reach: 4.7, camDist: 5.2, camHeight: 5, camMin: .55, camMax: 1.8 },
  'n:ashentitan_60': { height: 60 * HERO_M, fitMeasuredHeight: true, radius: 19, speed: 0.64, step: 8, reach: 8, camDist: 8, camHeight: 8, camMin: .55, camMax: 2.0 },
  // Legacy Titan selector slot retained for old saves; legacy selector uses the current 10x encounter size.
  'n:ashentitan_40': { height: 10 * HERO_M, fitMeasuredHeight: true, radius: 5.4, speed: 0.64, step: 3.2, reach: 4.7, camDist: 5.2, camHeight: 5, camMin: 0.55, camMax: 1.8 },
  // Vaelthryx variants are baked at DIFFERENT native sizes (measured in-game): _new6 14.3 m tall (79 m long), _new 2.0 m, _straight_rig 0.65 m. Boss quote ~18.7 m coiled; edit height here once confirmed.
  'n:vaelthryx_new': { height: 2.0, radius: 0.6, speed: 1.0, step: 0.4, reach: 1.1, camDist: 1.05, camHeight: 1.05, camMin: 0.5, camMax: 1.7 },
  'n:vaelthryx_new6': { height: 14.3, radius: 4.0, speed: 1.5, step: 2.6, reach: 4.0, camDist: 3.8, camHeight: 3.7, camMin: 0.6, camMax: 1.7 },
  // PLAYABLE Balthrix: 6x the player. height = 6 * HERO_M (11.43 m), derived from the base constant. `native` = the GLB's authored height (0.65 m); the model is scaled at LOAD by loadScale() = height/native, the file on disk is untouched.
  'n:vaelthryx_straight_rig': { height: 6 * HERO_M, native: 0.65, fitMeasuredHeight: true, radius: 3.4, speed: 1.5, step: 2.0, reach: 3.2, camDist: 3.6, camHeight: 3.4, camMin: 0.6, camMax: 1.7 },
  // Balthrix / Vaelthryx 50x visual test: SAME GLB as 10x; no extra binary, skeleton or animation edits.
  'n:vaelthryx_straight_rig_50': { height: 50 * HERO_M, native: 0.65, fitMeasuredHeight: true, radius: 20, speed: 1.5, step: 8, reach: 8, camDist: 8, camHeight: 8, camMin: 0.6, camMax: 1.7 },
  'n:frosttroll_a': { height: 3.5 * HERO_M, fitMeasuredHeight: true, radius: 1.9, speed: 1.25, step: 1.2, reach: 2.15, camDist: 2.2, camHeight: 2, camMin: 0.5, camMax: 1.7 },              // trolls = 3x the hero
  'n:frosttroll_b': { height: 3.5 * HERO_M, fitMeasuredHeight: true, radius: 1.9, speed: 1.25, step: 1.2, reach: 2.15, camDist: 2.2, camHeight: 2, camMin: 0.5, camMax: 1.7 },
  'o:vaelthryx': { height: 3.59, radius: 1.0, speed: 1.1, step: 0.7, reach: 1.4, camDist: 1.5, camHeight: 1.4, camMin: 0.45, camMax: 1.7 },                  // blocky builder (authored 5.1 world units)
};
const clampN = (v, lo, hi, d) => { v = +v; return Number.isFinite(v) ? Math.max(lo, Math.min(hi, v)) : d; };
/* profile in METRES with every field filled + clamped (safe even if the config is edited badly) */
/* load-time model scale for models whose authored size differs from the config height (1 = use the normal fit) */
export const loadScale = (id, measuredHeight = 0) => { const c = CHARS[id] || (id.startsWith('n:') && id.endsWith('_smooth') ? CHARS[id.slice(2,-7)] : null); const native = c && c.fitMeasuredHeight && Number.isFinite(measuredHeight) && measuredHeight > 0.01 ? measuredHeight : c && c.native; return native > 0 ? clampN(c.height, 0.3, MAX_HEIGHT_M, DEFAULT.height) / native : 1; };
export function profileFor(id) {
  const c = Object.assign({}, DEFAULT, CHARS[id] || (id.startsWith('n:') && id.endsWith('_smooth') ? CHARS[id.slice(2,-7)] : null) || {});
  return { id: id || '', height: clampN(c.height, 0.3, MAX_HEIGHT_M, DEFAULT.height), radius: clampN(c.radius, 0.1, 20, DEFAULT.radius), speed: clampN(c.speed, 0.3, SPEED_CAP, 1), step: clampN(c.step, 0.05, 8, DEFAULT.step), reach: clampN(c.reach, 0.5, 8, 1),
    camDist: clampN(c.camDist, 0.5, 8, 1), camHeight: clampN(c.camHeight, 0.5, 8, 1), camMin: clampN(c.camMin, 0.2, 1.7, 0.4), camMax: clampN(c.camMax, 0.4, 2.5, 1.7), scale: clampN(c.height, 0.3, MAX_HEIGHT_M, DEFAULT.height) / HERO_M, custom: !!CHARS[id] };
}
/* same profile in WORLD units (height/radius/step) for the engine */
export function worldProfile(id, HS = 1.5) { const p = profileFor(id), k = WORLD_PER_M(HS); return Object.assign({}, p, { heightW: p.height * k, radiusW: Math.min(p.radius, COLLIDE_RADIUS_CAP) * k, stepW: p.step * k }); }
/* does a character of this id fit through a door of this height/width (metres)? Lucky: giants may stand outside / enter without fitting (giant-mode fallback). */
export function fitsDoor(id, doorH, doorW) { const p = profileFor(id); return p.height <= doorH && p.radius * 2 <= doorW; }
export const isGiant = (id) => profileFor(id).height > HERO_M * 2;
