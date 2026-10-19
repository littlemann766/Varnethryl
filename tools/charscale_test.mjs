// Node tests for the central character-scale config (pure data).
import { loadScale, CHARS, DEFAULT, HERO_M, SPEED_CAP, COLLIDE_RADIUS_CAP, profileFor, worldProfile, fitsDoor, isGiant, WORLD_PER_M } from '../www/proto3d/charscale.js';
import { CombatController } from '../www/proto3d/combat/controller.js';
let ok = 0, bad = 0; const T = (n, c) => { c ? ok++ : bad++; console.log(c ? 'PASS' : 'FAIL', n); };
T('hero default is 1.905 m', DEFAULT.height === 1.905 && HERO_M === 1.905 && profileFor('n:owner').height === 1.905 && !profileFor('n:owner').custom);
T('Titan 11.4 m, trolls 5.7 m (3x hero), Vaelthryx variants carry their measured native sizes', profileFor('n:ashentitan_new').height === 11.4 && profileFor('n:vaelthryx_new6').height === 14.3 && Math.abs(profileFor('n:frosttroll_b').height / HERO_M - 3) < 0.02 && profileFor('n:frosttroll_a').height === 5.7);
T('vaelthryx variants each have a profile', ['n:vaelthryx_new', 'n:vaelthryx_new6', 'n:vaelthryx_straight_rig'].every(i => profileFor(i).height > 0));
const w = worldProfile('n:ashentitan_new', 1.5); T('world units: Titan = 11.4 m x 1.4205 = 16.2', Math.abs(w.heightW - 16.19) < 0.05 && Math.abs(WORLD_PER_M(1.5) - 1.4205) < 1e-9 && Math.abs(worldProfile('x').heightW - 2.706) < 0.01);
T('giants: bigger radius/step/reach/camera than the hero, speed capped', Object.keys(CHARS).filter(k => CHARS[k].height > 3).every(k => { const p = profileFor(k), d = profileFor('x'); return p.radius > d.radius && p.step > d.step && p.reach > d.reach && p.camDist > d.camDist && p.camHeight > d.camHeight && p.speed <= SPEED_CAP && p.speed >= 1; }));
T('player collision radius is capped (giants can still walk the town)', worldProfile('n:vaelthryx_new').radiusW <= COLLIDE_RADIUS_CAP * WORLD_PER_M(1.5) + 1e-9 && worldProfile('n:ashentitan_new').radiusW > worldProfile('x').radiusW);
T('zoom clamps are sane per character (min < max, inside 0.2..2.5)', Object.keys(CHARS).every(k => { const p = profileFor(k); return p.camMin < p.camMax && p.camMin >= 0.2 && p.camMax <= 2.5; }));
const saved = CHARS['n:x'] = { height: 'abc', speed: 99, radius: -4, reach: 0, camMin: 5, camMax: 0 }; const b = profileFor('n:x'); delete CHARS['n:x'];
T('bad config values are sanitized (never NaN, speed capped)', Object.values(b).every(v => typeof v !== 'number' || Number.isFinite(v)) && b.speed === SPEED_CAP && b.radius >= 0.1 && b.reach >= 0.5 && b.height === HERO_M);
T('door/giant helpers for buildings: hero fits 3.5x2 m door, titan does not, titan isGiant', fitsDoor('n:aldric', 3.5, 2) && !fitsDoor('n:ashentitan_new', 3.5, 2) && isGiant('n:ashentitan_new') && !isGiant('n:aldric') && isGiant('n:frosttroll_b'));
const mkk = id => { const k = new CombatController({ HS: 1.5, rng: () => 0.5 }); k.setHero({ id: 'aldric', saber: false }); k.setPlayer(0, 0, 0); k.setScale(worldProfile(id)); k.res.unlimited = true; return k; };
const hitAt = (id, z) => { const k = mkk(id); const e = k.addEnemy('wolf', 0, z); e.hp = e.max = 1e6; k.on('damage', () => 0); k.use('aldric.2'); for (let i = 0; i < 40; i++) k.update(1 / 60); return e.hp < e.max; };
T('combat reach scales with size: a 14 world-unit AoE hits only for the giant', !hitAt('n:aldric', 14) && hitAt('n:ashentitan_new', 14));
T('combat reach 1.0 for the default hero', mkk('n:owner').RM === 1 && mkk('n:ashentitan_new').RM === CHARS['n:ashentitan_new'].reach);
T('playable Vaelthryx = 10 x hero height derived from HERO_M, loaded with a scale (file untouched)', Math.abs(profileFor('n:vaelthryx_straight_rig').height - 10 * HERO_M) < 1e-9 && Math.abs(loadScale('n:vaelthryx_straight_rig') - 10 * HERO_M / 0.65) < 1e-9 && loadScale('n:aldric') === 1 && isGiant('n:vaelthryx_straight_rig'));
// v1.1.15 real hero heights (boss-approved Beth table)
{ const m = await import('../www/proto3d/charscale.js'); const P = profileFor;
  T('real heights: pip 0.52, phoenix 0.756, wren 1.35, ember 1.296, thrain 1.477, garruk 2.02, owner 1.905', P('n:pip_new2').height === 0.52 && P('n:phoenix_new3').height === 0.756 && P('n:wren_new3').height === 1.35 && P('n:ember_new3').height === 1.296 && P('n:thrain_new4').height === 1.477 && P('n:garruk_new5').height === 2.02 && P('n:owner').height === 1.905 && P('n:owner_pika1').height === 1.905);
  T('every variant of a hero shares its height (blocky, v1, New, armor2)', ['aldric', 'o:wren', 'n:wren_new3', 'n:orin_armor2', 'orin', 'n:garruk_armor2', 'garruk', 'n:garruk_new4'].every(id => P(id).height === m.heroHeight(id)) && P('o:wren').height === P('n:wren_new3').height && P('n:orin_armor2').height === P('orin').height);
  T('armor2 scaled at load from its baked height to the hero height', Math.abs(m.loadScale('n:orin_armor2') - 1.829 / 1.84) < 1e-9 && m.loadScale('n:garruk_armor2') === 1 && m.loadScale('n:pip_new2') === 1);
  T('gameplay scales with height (radius/reach/camera grow, speed sqrt-clamped, step floor 0.35)', P('n:pip_new2').radius < P('n:wren_new3').radius && P('n:wren_new3').radius < P('n:garruk_new5').radius + 1e-9 && P('n:garruk_new5').radius <= 0.53 && P('n:pip_new2').speed >= 0.78 && P('n:garruk_new5').speed <= 1.1 && P('n:pip_new2').step === 0.35 && P('n:pip_new2').camDist < P('n:owner').camDist && P('n:pip_new2').reach >= 0.6);
  T('bosses unchanged (titan 11.4, trolls 5.7, vaelthryx 19.05)', P('n:ashentitan_new').height === 11.4 && P('n:frosttroll_a').height === 5.7 && Math.abs(P('n:vaelthryx_new7').height - 19.05) < 1e-9); }

console.log(ok + ' pass, ' + bad + ' fail'); process.exit(bad ? 1 : 0);
