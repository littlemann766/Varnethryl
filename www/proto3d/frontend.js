// Front end: loading -> title (live village backdrop, camera drift) -> character select -> game, plus pause/settings/credits.
// Active only when the URL has no query params, or ?fe=1 (fe=0 disables). The in-game HUD (combat/hud.js) is untouched.
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
    <div class="stage"><div class="tag" id="fe-tag">Preview</div></div>
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
  function show(id) { hist.push(id); const Z = P()?.state; if (Z) { if (id === 'sel' && z0 === null) { z0 = Z.zoom; Z.zoom = .75; } else if (id !== 'sel' && z0 !== null) { Z.zoom = z0; z0 = null; } }
    cur = id; root.querySelectorAll('.scr').forEach(s => s.classList.toggle('on', s.id === 'fe-' + id));
    document.body.classList.toggle('fe-on', id !== 'game'); document.body.classList.toggle('fe-game', id === 'game');
    document.body.dataset.fe = id; }
  function tip() { if (!opts.tips) { $('#fe-tip').textContent = ''; return; } const [h, t] = TIPS[tipI++ % TIPS.length]; $('#fe-tip').innerHTML = `<b>${h}</b><br>${t}`; }
  function loading(ms, then) { show('load'); tip(); progress = 0; const t0 = performance.now(); const ti = setInterval(tip, 2600);
    (function step() { const ready = !!(P() && P().frames > 2); const k = Math.min(1, (performance.now() - t0) / ms); progress = ready ? k : Math.min(k, .85);
      $('#fe-bar').style.width = (progress * 100).toFixed(0) + '%';
      if (progress >= 1) { clearInterval(ti); then(); } else requestAnimationFrame(step); })(); }
  function driftLoop() { cancelAnimationFrame(drift); let last = performance.now();
    const f = (t) => { const dt = Math.min(.1, (t - last) / 1000); last = t;
      if ((cur === 'title' || cur === 'cred' || (cur === 'set' && back === 'title')) && opts.drift && P()?.state) P().state.camYaw += dt * .12;
      if (cur === 'sel' && P()?.state) P().state.camYaw += dt * .35;
      drift = requestAnimationFrame(f); }; drift = requestAnimationFrame(f); }
  function title() { P()?.setRunning?.(true); show('title'); $('#fe-ver').textContent = document.getElementById('ver')?.textContent || ''; driftLoop(); }
  const fmt = (n) => n >= 1e6 ? (n / 1e6).toFixed(n % 1e6 ? 2 : 0) + 'M' : n >= 1e4 ? Math.round(n / 1e3) + 'k' : String(n);
  function stat(lbl, v, max, txt) { return `<div class="fe-stat"><span>${lbl}</span><div class="vn-bar"><i style="width:${Math.max(4, Math.min(100, v / max * 100))}%"></i></div><b>${txt}</b></div>`; }
  function renderSel() {
    const ro = P()?.roster || []; const box = $('#fe-roster');
    box.innerHTML = ro.map((r, i) => `<button data-i="${i}" class="${i === sel ? 'on' : ''}">${r.name}${r.n > 1 ? ` <small style="opacity:.6">×${r.n}</small>` : ''}</button>`).join('');
    const r = ro[sel]; if (!r) return; P().pickRoster(sel);
    const owner = /owner/i.test(r.name + r.key) || !!P().owner;
    const hp = owner ? PLAYER.ownerHp : PLAYER.hp, atk = owner ? SABER : 120;
    $('#fe-name').textContent = r.name; $('#fe-tag').textContent = r.name;
    $('#fe-stats').innerHTML = stat('Health', Math.log10(hp), 6, fmt(hp)) + stat('Power', Math.log10(atk + 1), 5, fmt(atk)) + stat('Defense', PLAYER.def, 1000, String(PLAYER.def)) + stat('Agility', PLAYER.agi, 40, String(PLAYER.agi));
    let h = 1.8; try { h = (P().charScale?.().heroH ?? 2.7) / 1.5; } catch {}
    const px = (m) => Math.max(6, Math.min(80, m / Math.max(h, 1.8) * 80));
    $('#fe-size').innerHTML = `<div class="fig ref" style="height:${px(1.8)}px"></div><small>Human<br>1.8 m</small><div class="fig" style="height:${px(h)}px"></div><small><b style="color:var(--vn-gold-hi)">${h.toFixed(2)} m</b><br>${(h / 1.8).toFixed(2)}× human</small>`;
    $('#fe-skills').innerHTML = (ABILITIES || []).map(a => `<div class="${a.saber && !owner ? 'lock' : ''}"><i>◆</i>${a.name || a.id}</div>`).join('');
  }
  function enterGame() { cancelAnimationFrame(drift); P()?.setRunning?.(true); show('game'); }
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
  window.__fe = { show: (s) => act(s), get screen() { return cur; }, hist, pause, title };
}
