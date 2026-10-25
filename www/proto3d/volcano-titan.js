/* Volcano-only Ashen Titan (Beth, models-new/ashentitan_volcano_11x.glb; data models/volcano-titan/ashentitan_volcano_11x.json).
   Size: charscale.js VOLCANO_TITAN_MULT (11 = 20.955 m, boss-confirmed 24 Oct; 6 = old 6x look). The GLB is baked at 11x,
   so only the 6x setting scales it (loadScale = height / 20.955).
   This module adds what the shared enemy AI does not have: the four special attacks (windup -> eruption_slam / boulder_hurl /
   volcano_roar, magma_sweep) with their 17 timed events (AoE circles + ballistic projectiles with landing rings, lava pools,
   impact craters), footstep camera shake and the volcano leash (body <= 107 from TITAN_CENTER; > 162 away he walks home). */
import { GLTFLoader } from './vendor/jsm/loaders/GLTFLoader.js';
import { TITAN_CENTER } from './bossregions.js';
import { HERO_M, VOLCANO_TITAN_MULT, WORLD_PER_M } from './charscale.js';
const BASE = new URL('./models/volcano-titan/', import.meta.url).href;
const G = -9.81, LEASH_BODY = 107, LEASH_CHASE = 162;
export function createVolcanoTitan({ THREE, scene, heightAt, HS = 1.5, playClip, hurt, shake }) {
  const K = WORLD_PER_M(HS) * (VOLCANO_TITAN_MULT * HERO_M / 20.955);   // model metres -> world units at the configured size
  let cfg = null, geos = {}, mats = {}, ready = false; const live = [], marks = [], pools = [], craters = [];
  (async () => { try { cfg = await (await fetch(BASE + 'ashentitan_volcano_11x.json')).json(); const L = new GLTFLoader();
    for (const [k, p] of Object.entries(cfg.projectiles)) { const g = await L.loadAsync(BASE + p.file); g.scene.traverse(o => { if (o.isMesh && !geos[k]) { geos[k] = o.geometry; mats[k] = o.material; } }); }
    ready = true; } catch (e) { console.warn('volcano titan data unavailable', e); } })();
  const ringGeo = new THREE.RingGeometry(0.86, 1, 40); ringGeo.rotateX(-Math.PI / 2);
  const discGeo = new THREE.CircleGeometry(1, 32); discGeo.rotateX(-Math.PI / 2);
  const mark = (x, z, r, sec, color) => { const m = new THREE.Mesh(ringGeo, new THREE.MeshBasicMaterial({ color, transparent: true, opacity: .85, depthWrite: false }));
    const f = new THREE.Mesh(discGeo, new THREE.MeshBasicMaterial({ color, transparent: true, opacity: .25, depthWrite: false })); const g = new THREE.Group(); g.add(m, f);
    g.position.set(x, heightAt(x, z) + .2, z); g.scale.setScalar(r); f.scale.setScalar(0.01); scene.add(g); marks.push({ g, f, t: 0, sec }); };
  const toWorld = (e, yaw, off) => { const [ox, oy, oz] = off || [0, 0, 0], s = Math.sin(yaw), c = Math.cos(yaw); return [e.x + (ox * c + oz * s) * K, (oy || 0) * K, e.z + (-ox * s + oz * c) * K]; };
  const rnd = (a) => Array.isArray(a) ? a[0] + Math.random() * (a[1] - a[0]) : a;
  function launch(ev, S, L, T) { const n = ev.projectile, g = geos[n]; if (!g) return; const m = new THREE.Mesh(g, mats[n]); m.scale.setScalar((ev.projectileScale || 1) * K); scene.add(m);
    const v0 = [(L[0] - S[0]) / T, (L[1] - S[1]) / T - 0.5 * G * T, (L[2] - S[2]) / T]; live.push({ ev, m, S, v0, T, t: 0, L });
    mark(L[0], L[2], (ev.impactRadius || 2) * K, T, 0xff3b1f); }
  function fireProjectiles(e, yaw, ev, hero) {
    const S = toWorld(e, yaw, ev.spawn && ev.spawn.offset); S[1] += heightAt(e.x, e.z);
    for (let i = 0; i < (ev.count || 1); i++) { let L, T;
      if (ev.pattern === 'rain_zone') { let x, z; if (Math.random() < (ev.biasToPlayer || 0)) { const a = Math.random() * 6.283, d = Math.random() * 10; x = hero.x + Math.cos(a) * d; z = hero.z + Math.sin(a) * d; }
          else { const a = Math.random() * 6.283, d = Math.sqrt(Math.random()) * TITAN_CENTER.radius; x = TITAN_CENTER.x + Math.cos(a) * d; z = TITAN_CENTER.z + Math.sin(a) * d; }
        L = [x, heightAt(x, z), z]; const s0 = [x + (Math.random() - .5) * 6, L[1] + (ev.spawn?.offset?.[1] || 60) * K * .5, z + (Math.random() - .5) * 6]; T = Math.max(.8, (s0[1] - L[1]) / (ev.fallSpeed || 30)); launch(ev, s0, L, T); continue; }
      if (ev.target === 'player') { const sp = ev.spread || 0, x = hero.x + (Math.random() - .5) * sp, z = hero.z + (Math.random() - .5) * sp; L = [x, heightAt(x, z), z];
        const fs = ev.arc?.flightSec || [1.4, 2.2]; T = Math.max(fs[0], Math.min(fs[1], Math.hypot(x - S[0], z - S[2]) / (40 * K))); }
      else { const base = ev.pattern === 'ring' ? i / ev.count * 360 + (Math.random() - .5) * 10 : (ev.aimYawDeg || 0) + (Math.random() - .5) * (ev.spread || 30);
        const a = yaw + base * Math.PI / 180, d = rnd(ev.landRadius || [10, 20]) * K, x = S[0] + Math.sin(a) * d, z = S[2] + Math.cos(a) * d; L = [x, heightAt(x, z), z];
        const v = rnd(ev.speed || 20), ang = rnd(ev.arc?.launchAngleDeg || [45, 60]) * Math.PI / 180; T = Math.max(.6, 2 * v * Math.sin(ang) / 9.81); }
      launch(ev, S, L, T); }
  }
  let sp = null, cd = { eruption_slam: 4, boulder_hurl: 2, magma_sweep: 3, volcano_roar: 12 }, last = 0;
  const SEQ = { eruption_slam: 1.2, boulder_hurl: 0.8, volcano_roar: 1.5, magma_sweep: 0 };
  function update(dt, e, hero, base) {
    for (const k in cd) cd[k] -= dt;
    for (let i = marks.length - 1; i >= 0; i--) { const M = marks[i]; M.t += dt; M.f.scale.setScalar(Math.max(.01, Math.min(1, M.t / M.sec))); if (M.t > M.sec + .15) { scene.remove(M.g); M.g.children.forEach(c => c.material.dispose()); marks.splice(i, 1); } }
    for (let i = live.length - 1; i >= 0; i--) { const P = live[i]; P.t += dt; const t = Math.min(P.t, P.T);
      P.m.position.set(P.S[0] + P.v0[0] * t, P.S[1] + P.v0[1] * t + .5 * G * t * t, P.S[2] + P.v0[2] * t); P.m.rotation.x += dt * 3; P.m.rotation.z += dt * 2;
      if (P.t >= P.T) { scene.remove(P.m); live.splice(i, 1); const r = (P.ev.impactRadius || 2) * K;
        if (Math.hypot(hero.x - P.L[0], hero.z - P.L[2]) < r) hurt(Math.round(base * (P.ev.damageMult || 1)), P.ev.name);
        if (geos.impact_crater) { const c = new THREE.Mesh(geos.impact_crater, mats.impact_crater); c.position.set(P.L[0], P.L[1] + .05, P.L[2]); c.scale.setScalar(r); scene.add(c); craters.push({ c, t: 0 }); if (craters.length > 24) scene.remove(craters.shift().c); }
        if (P.ev.dot) pools.push({ x: P.L[0], z: P.L[2], r: P.ev.dot.poolRadius * K, t: P.ev.dot.sec, dps: P.ev.dot.dps, acc: 0 });
        shake(Math.min(1, .6 * r / Math.max(8, Math.hypot(hero.x - P.L[0], hero.z - P.L[2]))), .25);
        if (P.ev.splinters) for (let s = 0; s < 8; s++) { const a = s / 8 * 6.283, d = (4 + Math.random() * 8) * K, x = P.L[0] + Math.cos(a) * d, z = P.L[2] + Math.sin(a) * d;
          launch({ projectile: 'ember_rock_small', projectileScale: 1, impactRadius: 1.2, damageMult: .3, name: 'splinter' }, [P.L[0], P.L[1] + 1, P.L[2]], [x, heightAt(x, z), z], .9); } } }
    for (let i = craters.length - 1; i >= 0; i--) { craters[i].t += dt; if (craters[i].t > 6) { scene.remove(craters[i].c); craters.splice(i, 1); } }
    for (let i = pools.length - 1; i >= 0; i--) { const p = pools[i]; p.t -= dt; p.acc += dt; if (p.acc >= .5) { p.acc = 0; if (Math.hypot(hero.x - p.x, hero.z - p.z) < p.r) hurt(Math.max(1, Math.round(base * p.dps * .5)), 'lava'); } if (p.t <= 0) pools.splice(i, 1); }
    if (!ready || !e || e.state === 'defeated' || !e.view) { sp = null; return; }
    // leash: the body never leaves the crater; past 162 the shared AI is pointed home
    const dx = e.x - TITAN_CENTER.x, dz = e.z - TITAN_CENTER.z, d = Math.hypot(dx, dz); if (d > LEASH_BODY) { e.x = TITAN_CENTER.x + dx / d * LEASH_BODY; e.z = TITAN_CENTER.z + dz / d * LEASH_BODY; }
    const hd = Math.hypot(hero.x - TITAN_CENTER.x, hero.z - TITAN_CENTER.z), far = hd > LEASH_CHASE;
    const yaw = e.view.rotation.y, toHero = Math.hypot(hero.x - e.x, hero.z - e.z);
    if (!sp && e.state !== 'idle') { const opts = far ? ['boulder_hurl'] : Object.keys(SEQ); const pick = opts.filter(k => cd[k] <= 0 && (k !== 'boulder_hurl' || toHero < 110 * K)).sort(() => Math.random() - .5)[0];
      if (pick) { cd[pick] = cfg.attackSequenceSuggestion.cooldownsSec[pick]; sp = { clip: SEQ[pick] ? 'windup' : pick, next: pick, t: 0, wind: SEQ[pick] }; playClip(e.view, sp.clip, true); last = 0;
        for (const ev of cfg.attackEvents) if (ev.clip === pick && ev.type === 'aoe' && ev.telegraphSec) { const c = toWorld(e, yaw, ev.center); mark(c[0], c[2], ev.radius * K, ev.telegraphSec + (SEQ[pick] || 0), 0xffd23a); } } }
    if (!sp) return;
    sp.t += dt;
    if (sp.clip === 'windup' && sp.t >= sp.wind) { sp.clip = sp.next; sp.t = 0; last = 0; playClip(e.view, sp.clip, true); }
    else if (sp.clip !== 'windup') {
      for (const ev of cfg.attackEvents) if (ev.clip === sp.clip && last < ev.t && ev.t <= sp.t) {
        if (ev.type === 'aoe') { const c = toWorld(e, yaw, ev.center); if (Math.hypot(hero.x - c[0], hero.z - c[2]) < ev.radius * K) hurt(Math.round(base * ev.damageMult), ev.name); shake(.8, .35); }
        else if (ev.type === 'spawn_projectile') fireProjectiles(e, yaw, ev, hero); }
      for (const f of (cfg.clips[sp.clip]?.footsteps || [])) if (last < f.t && f.t <= sp.t) { const fd = Math.hypot(hero.x - e.x, hero.z - e.z) / K; if (fd < cfg.suggestedShake.radiusMeters) shake(Math.max(.15, (f.strength || 1) * Math.pow(1 - fd / cfg.suggestedShake.radiusMeters, 2)), .5); }
      last = sp.t; if (sp.t > (cfg.clips[sp.clip]?.durationSec || 3) + .1) sp = null; }
  }
  return { update, get busy() { return !!sp; }, get projectiles() { return live.length; }, get ready() { return ready; }, K };
}
