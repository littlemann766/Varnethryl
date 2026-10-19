// Front end: loading -> title (live village backdrop, camera drift) -> character select -> game, plus pause/settings/credits.
// Active only when the URL has no query params, or ?fe=1 (fe=0 disables). The in-game HUD (combat/hud.js) is untouched.
import * as THREE from 'three';
import { PLAYER, SABER, ABILITIES } from './combat/data.js';
const Q = new URLSearchParams(location.search);
const ON = Q.get('fe') === '1' || (!location.search && Q.get('fe') !== '0');
if (ON) boot();

function boot() {
  const TIPS = [
    ['Movement', 'Drag the left side of the screen to move; swipe the right side to turn the camera.'],
    ['Companions', 'Allies who fall are not lost: they rise again at your side after a short while.'],
    ['Portals', 'Glowing gates lead out to the Wilds, and a return portal always waits to bring you home.'],
    ['Stairs', 'Your followers climb ladders and stairs with you; if they lag far behind they catch up.'],
    ['Abilities', 'Each ability has its own cooldown; watch the ring around its button.'],
    ['The Owner', 'Some say a wielder of the golden saber walks these lands, unmatched by any foe.'],
  ];
  const el = (h) => { const d = document.createElement('div'); d.innerHTML = h.trim(); return d.firstChild; };
  const hasSave = (() => { try { return !!localStorage.getItem('p3d'); } catch { return false; } })();
  const root = el(`<div id="fe">
  <div class="scr on" id="fe-load"><img src="assets/brand/emblem.webp" alt=""><div class="vn-title" style="font-size:22px">Varnethryl</div>
    <div class="vn-bar"><i id="fe-bar"></i></div><div id="fe-tip"></div></div>
  <div class="scr" id="fe-title"><div class="logo"><img src="assets/brand/emblem.webp" alt=""><h1 class="vn-title">Varnethryl</h1><div class="sub">Realm of the Golden Blade</div></div>
    <div class="menu vn-panel"><button class="vn-btn primary" data-a="play">Play</button><button class="vn-btn" data-a="cont" ${hasSave ? '' : 'disabled'}>Continue</button>
    <button class="vn-btn" data-a="set">Settings</button><button class="vn-btn" data-a="cred">Credits</button></div>
    <div class="foot"><span id="fe-ver"></span><span>Tap to begin your legend</span></div></div>
  <div class="scr" id="fe-sel"><div class="list vn-panel"><h2 class="vn-title">Heroes</h2><div id="fe-roster"></div></div>
    <div class="stage" id="fe-stage"><div class="tag" id="fe-tag">Preview</div></div>
    <div class="info vn-panel"><h2 class="vn-title" id="fe-name"></h2><div class="vn-rule"></div><div id="fe-stats"></div>
      <div style="font-size:12px;color:var(--vn-ink-dim)">Size</div><div id="fe-size"></div><div style="font-size:12px;color:var(--vn-ink-dim)">Skills</div><div id="fe-skills"></div>
      <div class="acts"><button class="vn-btn" data-a="back">Back</button><button class="vn-btn primary" data-a="begin">Begin</button></div></div></div>
  <div class="scr" id="fe-pause"><div class="vn-panel"><h2 class="vn-title">Paused</h2><button class="vn-btn primary" data-a="resume">Resume</button>
    <button class="vn-btn" data-a="chars">Characters</button><button class="vn-btn" data-a="set">Settings</button><button class="vn-btn" data-a="quit">Quit to Title</button></div></div>
  <div class="scr" id="fe-set"><div class="vn-panel"><h2 class="vn-title">Settings</h2>
    <label class="fe-row">Camera drift on title<input type="checkbox" id="fe-o-drift" checked></label>
    <label class="fe-row">Reduced effects<input type="checkbox" id="fe-o-lite"></label>
    <label class="fe-row">Show loading tips<input type="checkbox" id="fe-o-tips" checked></label>
    <button class="vn-btn primary" data-a="close">Done</button></div></div>
  <div class="scr" id="fe-cred"><div class="vn-panel"><h2 class="vn-title">Credits</h2><div class="vn-rule"></div>
    <p><b>Vanquished God</b><br>Creator &amp; Owner</p><p><b>Lucian</b><br>Combat HUD &amp; integration</p><p><b>Three.js</b><br>Rendering</p><p>Fonts: Cinzel (OFL)</p>
    <button class="vn-btn primary" data-a="close">Close</button></div></div>
</div>`);
  const pbtn = el(`<button id="fe-pbtn" aria-label="Pause">❚❚</button>`);
  const OPT_K = 'p3d_fe_opts';
  const opts = Object.assign({ drift: true, lite: false, tips: true }, (() => { try { return JSON.parse(localStorage.getItem(OPT_K)) || {}; } catch { return {}; } })());
  const $ = (s) => root.querySelector(s);
  let cur = 'load', back = 'title', drift = 0, sel = 0, progress = 0, tipI = Math.floor(Math.random() * TIPS.length);
  const P = () => window.__p3d;

  let z0 = null; const hist = [];
  function show(id) { hist.push(id); const Z = P()?.state; if (Z) { if (id === 'sel') P().setRunning?.(false); }
    cur = id; P()?.titleWander?.(id === 'title'); root.querySelectorAll('.scr').forEach(s => s.classList.toggle('on', s.id === 'fe-' + id));
    document.body.classList.toggle('fe-on', id !== 'game'); document.body.classList.toggle('fe-game', id === 'game');
    document.body.dataset.fe = id; }
  function tip() { if (!opts.tips) { $('#fe-tip').textContent = ''; return; } const [h, t] = TIPS[tipI++ % TIPS.length]; $('#fe-tip').innerHTML = `<b>${h}</b><br>${t}`; }
  function loading(ms, then) { pvDispose(); show('load'); tip(); progress = 0; const t0 = performance.now(); const ti = setInterval(tip, 2600);
    (function step() { const ready = !!(P() && P().frames > 2); const k = Math.min(1, (performance.now() - t0) / ms); progress = ready ? k : Math.min(k, .85);
      $('#fe-bar').style.width = (progress * 100).toFixed(0) + '%';
      if (progress >= 1) { clearInterval(ti); then(); } else requestAnimationFrame(step); })(); }
  function driftLoop() { cancelAnimationFrame(drift); let last = performance.now();
    const f = (t) => { const dt = Math.min(.1, (t - last) / 1000); last = t;
      if ((cur === 'title' || cur === 'cred' || (cur === 'set' && back === 'title')) && opts.drift && P()?.state) P().state.camYaw += dt * .12;
      drift = requestAnimationFrame(f); }; drift = requestAnimationFrame(f); }
  function title() { pvDispose(); if (!P()) root.querySelector('#fe-title').classList.add('static'); P()?.setRunning?.(true); show('title'); $('#fe-ver').textContent = document.getElementById('ver')?.textContent || ''; driftLoop(); }
  const fmt = (n) => n >= 1e6 ? (n / 1e6).toFixed(n % 1e6 ? 2 : 0) + 'M' : n >= 1e4 ? Math.round(n / 1e3) + 'k' : String(n);
  function stat(lbl, v, max, txt) { return `<div class="fe-stat"><span>${lbl}</span><div class="vn-bar"><i style="width:${Math.max(4, Math.min(100, v / max * 100))}%"></i></div><b>${txt}</b></div>`; }
  function renderSel() {
    const ro = P()?.roster || []; const box = $('#fe-roster');
    box.innerHTML = ro.map((r, i) => `<button data-i="${i}" class="${i === sel ? 'on' : ''}">${r.name}${r.n > 1 ? ` <small style="opacity:.6">×${r.n}</small>` : ''}</button>`).join('');
    const r = ro[sel]; if (!r) return; P().pickRoster(sel); pvShow(sel);
    const owner = /owner/i.test(r.name + r.key) || !!P().owner;
    const hp = owner ? PLAYER.ownerHp : PLAYER.hp, atk = owner ? SABER : 120;
    $('#fe-name').textContent = r.name; $('#fe-tag').textContent = r.name;
    $('#fe-stats').innerHTML = stat('Health', Math.log10(hp), 6, fmt(hp)) + stat('Power', Math.log10(atk + 1), 5, fmt(atk)) + stat('Defense', PLAYER.def, 1000, String(PLAYER.def)) + stat('Agility', PLAYER.agi, 40, String(PLAYER.agi));
    let h = 1.905; try { h = (P().charScale?.().heroH ?? 2.7) / (0.947 * 1.5); } catch {}
    const px = (m) => Math.max(4, Math.min(80, m / Math.max(h, 1.905) * 80));
    $('#fe-size').innerHTML = `<div class="fig ref" style="height:${px(1.905)}px"></div><small>Human<br>1.905 m</small><div class="fig" style="height:${px(h)}px"></div><small><b style="color:var(--vn-gold-hi)">${h.toFixed(2)} m</b><br>${(h / 1.905).toFixed(2)}× human</small>`;
    $('#fe-skills').innerHTML = (ABILITIES || []).map(a => `<div class="${a.saber && !owner ? 'lock' : ''}"><i>◆</i>${a.name || a.id}</div>`).join('');
  }
  // ---- character-select model preview: one small dedicated renderer, real GLB at its in-game (charscale) size on a pedestal
  const PV = { r: null };
  function pvInit() {
    if (PV.r) return PV; const st = $('#fe-stage');
    let r; try { r = new THREE.WebGLRenderer({ antialias: !matchMedia('(pointer:coarse)').matches, alpha: true, powerPreference: 'low-power' }); } catch { return null; }
    r.setPixelRatio(Math.min(devicePixelRatio || 1, 1.5)); r.outputColorSpace = THREE.SRGBColorSpace; r.domElement.id = 'fe-pv'; st.prepend(r.domElement);
    const sc = new THREE.Scene(), cam = new THREE.PerspectiveCamera(30, 1, 0.05, 200);
    sc.add(new THREE.HemisphereLight(0xfff1d6, 0x2a2232, 1.4)); const key = new THREE.DirectionalLight(0xffe2b0, 2.2); key.position.set(3, 6, 5); sc.add(key);
    const rim = new THREE.DirectionalLight(0x8fb4ff, 1.1); rim.position.set(-4, 3, -5); sc.add(rim);
    const ped = new THREE.Group(); const stone = new THREE.MeshStandardMaterial({ color: 0x2a2f3a, roughness: .85 }), gold = new THREE.MeshStandardMaterial({ color: 0xd4ae5a, metalness: .8, roughness: .35 });
    const c1 = new THREE.Mesh(new THREE.CylinderGeometry(1.25, 1.4, .28, 40), stone); c1.position.y = -.14; ped.add(c1);
    const c2 = new THREE.Mesh(new THREE.TorusGeometry(1.26, .035, 8, 48), gold); c2.rotation.x = Math.PI / 2; ped.add(c2); sc.add(ped);
    const turn = new THREE.Group(); sc.add(turn);
    const HU = 1.905 * 0.947 * 1.5;   // a 1.905 m human in world units (charscale HERO_M * WORLD_PER_M)
    const ref = new THREE.Group(), refM = new THREE.MeshBasicMaterial({ color: 0xd4ae5a, transparent: true, opacity: .28, depthWrite: false });
    const body = new THREE.Mesh(new THREE.CapsuleGeometry(HU * .1, HU * .56, 4, 10), refM); body.position.y = HU * .38; ref.add(body);
    const head = new THREE.Mesh(new THREE.SphereGeometry(HU * .085, 12, 8), refM); head.position.y = HU * .9; ref.add(head); sc.add(ref);
    Object.assign(PV, { r, sc, cam, ped, turn, ref, HU, w: 1, yaw: Math.PI + .45, vel: 0, zoom: 1, drag: null, lastT: 0, idleT: 0, model: null, mixer: null, req: 0, h: 1, token: 0, clock: performance.now() });
    const el = r.domElement, pts = new Map();
    el.addEventListener('pointerdown', e => { el.setPointerCapture(e.pointerId); pts.set(e.pointerId, [e.clientX, e.clientY]); PV.idleT = 0; });
    el.addEventListener('pointermove', e => { const p = pts.get(e.pointerId); if (!p) return;
      if (pts.size === 2) { const [a, b] = [...pts.values()], d0 = Math.hypot(a[0] - b[0], a[1] - b[1]); pts.set(e.pointerId, [e.clientX, e.clientY]); const [c, d] = [...pts.values()], d1 = Math.hypot(c[0] - d[0], c[1] - d[1]); if (d0 > 0) PV.zoom = Math.min(1.6, Math.max(.6, PV.zoom * d0 / d1)); return; }
      const dx = e.clientX - p[0]; pts.set(e.pointerId, [e.clientX, e.clientY]); PV.yaw += dx * .012; PV.vel = dx * .012; PV.idleT = 0; });
    const up = e => pts.delete(e.pointerId); el.addEventListener('pointerup', up); el.addEventListener('pointercancel', up);
    el.addEventListener('wheel', e => { e.preventDefault(); PV.zoom = Math.min(1.6, Math.max(.6, PV.zoom * (e.deltaY > 0 ? 1.08 : .93))); }, { passive: false });
    return PV;
  }
  function pvFrame() {
    if (!PV.r) return; PV.req = requestAnimationFrame(pvFrame);
    const now = performance.now(), dt = Math.min(.1, (now - PV.clock) / 1000); PV.clock = now; PV.idleT += dt;
    const st = PV.r.domElement.parentElement, w = st.clientWidth, h = st.clientHeight; if (!w || !h) return;
    const cv = PV.r.domElement; if (cv.width !== Math.round(w * PV.r.getPixelRatio()) || cv.height !== Math.round(h * PV.r.getPixelRatio())) { PV.r.setSize(w, h); PV.cam.aspect = w / h; PV.cam.updateProjectionMatrix(); }
    PV.vel *= Math.pow(.05, dt); if (PV.idleT > 2.5) PV.yaw += dt * .45; else PV.yaw += PV.vel * dt * 4;
    PV.turn.rotation.y = PV.yaw; if (PV.mixer) PV.mixer.update(dt);
    // frame the model AND the human reference: tiny heroes stay readable next to a human, giants fit whole
    const H = Math.max(PV.h, PV.HU) * 1.12 * PV.zoom, W = (PV.wx || PV.HU) * 1.15 * PV.zoom, t = Math.tan(PV.cam.fov * Math.PI / 360);
    const dist = Math.max(H / 2 / t, W / 2 / (t * PV.cam.aspect)) * 1.05, cy = H * .45, cx = PV.cx || 0;
    PV.cam.position.set(cx, cy + H * .06, dist); PV.cam.lookAt(cx, cy, 0); PV.cam.near = dist / 200; PV.cam.far = dist * 6; PV.cam.updateProjectionMatrix(); PV.r.render(PV.sc, PV.cam); if (PV.fitN > 0 && --PV.fitN === 0) { pvFit(); PV.fitted = true; }
  }
  function pvFree(m) {   // free a preview model (fresh GLB parse, not shared with the game); blocky builders may share materials, so leave those
    if (!m || !m.userData?.glb) return; m.traverse(o => { if (!o.isMesh) return; o.geometry?.dispose(); for (const mt of [].concat(o.material)) { if (!mt) continue; for (const k in mt) if (mt[k]?.isTexture) mt[k].dispose(); mt.dispose(); } });
  }
  function pvFit() { const m = PV.model; if (!m) return;
    const ry = PV.turn.rotation.y; PV.turn.rotation.y = 0; m.position.set(0, 0, 0); PV.turn.updateMatrixWorld(true); const b = new THREE.Box3().setFromObject(m, true); PV.turn.rotation.y = ry; const hh = Math.max(.5, b.max.y - b.min.y); m.position.y = -b.min.y;
    // pedestal sized to the model's footprint; the camera frames at least a human's height so relative size (charscale) reads true
    m.position.x = -(b.min.x + b.max.x) / 2; m.position.z = -(b.min.z + b.max.z) / 2;   // centre the footprint on the pedestal
    const fw = Math.max(b.max.x - b.min.x, b.max.z - b.min.z), pr = Math.max(.3, fw * .54); PV.ped.scale.set(pr / 1.25, Math.min(1, pr / 1.25), pr / 1.25);
    // human reference stands just right of the pedestal; framing spans pedestal-left .. reference-right, centred between
    const rx = pr + PV.HU * .25; PV.ref.position.set(rx, 0, 0); const left = -Math.max(pr, fw / 2), right = rx + PV.HU * .12;
    PV.wx = right - left; PV.cx = (left + right) / 2; PV.h = hh; PV.hM = +(hh / (0.947 * 1.5)).toFixed(2); if (PV.cur) { PV.cur.hM = PV.hM; PV.cur.h = +hh.toFixed(2); }
  }
  function pvFrameInfo() {   // screen-space box of the model (0..1), for tests
    if (!PV.model) return null; const b = new THREE.Box3().setFromObject(PV.model, true), r = { x0: 1e9, x1: -1e9, y0: 1e9, y1: -1e9 }, v = new THREE.Vector3();
    for (let k = 0; k < 8; k++) { v.set(k & 1 ? b.max.x : b.min.x, k & 2 ? b.max.y : b.min.y, k & 4 ? b.max.z : b.min.z).project(PV.cam); r.x0 = Math.min(r.x0, v.x); r.x1 = Math.max(r.x1, v.x); r.y0 = Math.min(r.y0, v.y); r.y1 = Math.max(r.y1, v.y); }
    v.set(PV.ref.position.x, PV.HU, 0).project(PV.cam); return { x0: (r.x0 + 1) / 2, x1: (r.x1 + 1) / 2, y0: (1 - r.y1) / 2, y1: (1 - r.y0) / 2, refTop: (1 - v.y) / 2, refX: (v.x + 1) / 2, hM: PV.cur.hM };
  }
  async function pvShow(i, byId) {
    if (!pvInit()) return; const tok = ++PV.token; if (!PV.req) { PV.clock = performance.now(); pvFrame(); }
    const res = await (byId ? P()?.previewById?.(byId) : P()?.previewModel?.(i)); if (!res || tok !== PV.token || !PV.r) return;
    if (PV.model) { PV.turn.remove(PV.model); PV.mixer?.stopAllAction(); pvFree(PV.model); }
    const m = res.model, u = m.userData || {}; m.position.set(0, 0, 0); m.rotation.set(0, 0, 0);
    if (u.act) { for (const k in u.act) { try { u.act[k].stop(); } catch {} } if (u.act.idle) u.act.idle.reset().setEffectiveWeight(1).play(); }
    u.mixer?.update(0.016); m.updateMatrixWorld(true); m.traverse(o => { if (o.isSkinnedMesh) o.skeleton.update(); });   // posed bone matrices, so the box is the idle pose (a lying serpent), not the bind pose
    PV.model = m; PV.mixer = u.mixer || null; pvFit(); PV.fitN = 3;   // fit now, then refit once the renderer has posed the skeleton
    PV.turn.add(m); if (byId) $('#fe-tag').textContent = res.name; PV.fitted = false; PV.cur = { hM: PV.hM, id: res.id, name: res.name, h: +PV.h.toFixed(2), idle: !!(u.act && u.act.idle) };
  }
  function pvDispose() {
    if (!PV.r) return; cancelAnimationFrame(PV.req); PV.req = 0; PV.token++;
    PV.ped.traverse(o => { if (o.isMesh) { o.geometry.dispose(); o.material.dispose(); } });
    PV.mixer?.stopAllAction(); pvFree(PV.model); PV.r.dispose(); PV.r.forceContextLoss?.(); PV.r.domElement.remove(); PV.r = null; PV.model = null; PV.mixer = null; PV.cur = null;
  }
  function enterGame() { pvDispose(); P()?.dropTitleExtras?.(); cancelAnimationFrame(drift); P()?.setRunning?.(true); show('game'); }
  function pause() { if (cur !== 'game') return; P()?.setRunning?.(false); show('pause'); }
  function act(a) {
    switch (a) {
      case 'play': back = 'title'; show('sel'); renderSel(); break;
      case 'cont': loading(900, enterGame); break;
      case 'set': back = cur; show('set'); break;
      case 'cred': back = 'title'; show('cred'); break;
      case 'close': if (back === 'pause') show('pause'); else title(); break;
      case 'back': if (back === 'pause') show('pause'); else title(); break;
      case 'begin': loading(1400, enterGame); break;
      case 'resume': enterGame(); break;
      case 'chars': back = 'pause'; show('sel'); renderSel(); driftLoop(); break;
      case 'quit': title(); break;
    }
  }
  root.addEventListener('click', (e) => { const b = e.target.closest('[data-a]'); if (b && !b.disabled) act(b.dataset.a);
    const r = e.target.closest('#fe-roster button'); if (r) { sel = +r.dataset.i; renderSel(); } });
  root.addEventListener('change', (e) => { const m = e.target.id?.match(/^fe-o-(\w+)/); if (m) { opts[m[1]] = e.target.checked;
    try { localStorage.setItem(OPT_K, JSON.stringify(opts)); } catch {} document.body.classList.toggle('fe-lite', opts.lite); } });
  // Hidden cheats: the title's version label forwards each tap to #ver, so the same 5-tap gesture in cheatboot.js works.
  root.addEventListener('pointerup', (e) => { if (e.target.id === 'fe-ver') document.getElementById('ver')?.dispatchEvent(new PointerEvent('pointerup', { bubbles: true })); });
  pbtn.addEventListener('click', pause);
  addEventListener('keydown', (e) => { if (e.key !== 'Escape') return; if (cur === 'game') pause(); else if (cur === 'pause') enterGame(); });
  document.addEventListener('visibilitychange', () => { if (document.hidden) pause(); });
  const mount = () => { document.body.append(root, pbtn); for (const k in opts) { const c = $('#fe-o-' + k); if (c) c.checked = !!opts[k]; }
    show('load'); loading(1800, title); };
  document.body ? mount() : addEventListener('DOMContentLoaded', mount);
  window.__fe = { previewId: (id) => pvShow(0, id), get frame() { return pvFrameInfo(); }, get preview() { return PV.r ? { on: true, fitted: !!PV.fitted, ...PV.cur, canvas: !!document.getElementById('fe-pv'), yaw: PV.yaw } : { on: false, canvas: !!document.getElementById('fe-pv') }; }, show: (s) => act(s), get screen() { return cur; }, hist, pause, title };
}
