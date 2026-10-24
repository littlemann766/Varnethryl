// Node tests for the central character-scale config (pure data).
import { loadScale, CHARS, DEFAULT, HERO_M, SPEED_CAP, COLLIDE_RADIUS_CAP, profileFor, worldProfile, fitsDoor, isGiant, WORLD_PER_M } from '../www/proto3d/charscale.js';
import { CombatController } from '../www/proto3d/combat/controller.js';
let ok = 0, bad = 0; const T = (n, c) => { c ? ok++ : bad++; console.log(c ? 'PASS' : 'FAIL', n); };
T('hero default is 1.905 m', DEFAULT.height === 1.905 && HERO_M === 1.905 && profileFor('n:aldric').height === 1.905 && !profileFor('n:aldric').custom);
// v1.5.33 sizes (deliberate, commits 8554b78/d42df18 on 20 Oct): Titan 10x Owner, Frost Brothers 3.5x, playable Balthrix 6x; plus the boss-approved tiny heroes
T('Titan 10x hero, trolls 3.5x hero, Vaelthryx variants carry their measured native sizes', Math.abs(profileFor('n:ashentitan_new').height - 10 * HERO_M) < 1e-9 && profileFor('n:vaelthryx_new6').height === 14.3 && Math.abs(profileFor('n:frosttroll_b').height / HERO_M - 3.5) < 0.02 && Math.abs(profileFor('n:frosttroll_a').height / HERO_M - 3.5) < 0.02);
T('approved real heights: Pip 0.52, Phoenix 0.756, Wren 1.35, Owner 1.905 m; tiny step >= 0.35', profileFor('n:pip_new2').height === 0.52 && profileFor('n:phoenix_new3').height === 0.756 && profileFor('n:wren_new3').height === 1.35 && profileFor('n:owner').height === 1.905 && profileFor('n:pip_new2').step >= 0.35);
T('vaelthryx variants each have a profile', ['n:vaelthryx_new', 'n:vaelthryx_new6', 'n:vaelthryx_straight_rig'].every(i => profileFor(i).height > 0));
const w = worldProfile('n:ashentitan_new', 1.5); T('world units: Titan = 19.05 m x 1.4205 = 27.06', Math.abs(w.heightW - 10 * HERO_M * 1.4205) < 0.05 && Math.abs(WORLD_PER_M(1.5) - 1.4205) < 1e-9 && Math.abs(worldProfile('x').heightW - 2.706) < 0.01);
T('giants: bigger radius/step/reach/camera than the hero, speed capped', Object.keys(CHARS).filter(k => CHARS[k].height > 3).every(k => { const p = profileFor(k), d = profileFor('x'); return p.radius > d.radius && p.step > d.step && p.reach > d.reach && p.camDist > d.camDist && p.camHeight > d.camHeight && p.speed <= SPEED_CAP && p.speed >= 1; }));
T('player collision radius is capped (giants can still walk the town)', worldProfile('n:vaelthryx_new').radiusW <= COLLIDE_RADIUS_CAP * WORLD_PER_M(1.5) + 1e-9 && worldProfile('n:ashentitan_new').radiusW > worldProfile('x').radiusW);
T('zoom clamps are sane per character (min < max, inside 0.2..2.5)', Object.keys(CHARS).every(k => { const p = profileFor(k); return p.camMin < p.camMax && p.camMin >= 0.2 && p.camMax <= 2.5; }));
const saved = CHARS['n:x'] = { height: 'abc', speed: 99, radius: -4, reach: 0, camMin: 5, camMax: 0 }; const b = profileFor('n:x'); delete CHARS['n:x'];
T('bad config values are sanitized (never NaN, speed capped)', Object.values(b).every(v => typeof v !== 'number' || Number.isFinite(v)) && b.speed === SPEED_CAP && b.radius >= 0.1 && b.reach >= 0.5 && b.height === HERO_M);
T('door/giant helpers for buildings: hero fits 3.5x2 m door, titan does not, titan isGiant', fitsDoor('n:aldric', 3.5, 2) && !fitsDoor('n:ashentitan_new', 3.5, 2) && isGiant('n:ashentitan_new') && !isGiant('n:aldric') && isGiant('n:frosttroll_b'));
const mkk = id => { const k = new CombatController({ HS: 1.5, rng: () => 0.5 }); k.setHero({ id: 'aldric', saber: false }); k.setPlayer(0, 0, 0); k.setScale(worldProfile(id)); k.res.unlimited = true; return k; };
const hitAt = (id, z) => { const k = mkk(id); const e = k.addEnemy('wolf', 0, z); e.hp = e.max = 1e6; k.on('damage', () => 0); k.use('aldric.2'); for (let i = 0; i < 40; i++) k.update(1 / 60); return e.hp < e.max; };
T('combat reach scales with size: a 14 world-unit AoE hits only for the giant', !hitAt('n:aldric', 14) && hitAt('n:ashentitan_new', 14));
T('combat reach 1.0 for the default hero', mkk('n:aldric').RM === 1 && mkk('n:ashentitan_new').RM === CHARS['n:ashentitan_new'].reach);
T('playable Balthrix (vaelthryx_straight_rig) = 6 x hero height derived from HERO_M, loaded with a scale (file untouched)', Math.abs(profileFor('n:vaelthryx_straight_rig').height - 6 * HERO_M) < 1e-9 && Math.abs(loadScale('n:vaelthryx_straight_rig') - 6 * HERO_M / 0.65) < 1e-9 && loadScale('n:aldric') === 1 && isGiant('n:vaelthryx_straight_rig'));
console.log(ok + ' pass, ' + bad + ' fail'); process.exit(bad ? 1 : 0);
