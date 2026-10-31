/* In-game Settings menu (DOM only: zero draw calls, lazy-loaded by settingsboot.js on first open).
 * Sections: Camera, Graphics, Display, and (owner only, rebuilt each time it opens) the owner cheat toggles + god mode.
 * No sound section: the 3D game has no audio yet. */
import { ZOOM_MIN, ZOOM_MAX, SENS_MIN, SENS_MAX, DEFAULT_PREFS, QUALITIES } from './camprefs.js';
import { applyPrefs, persist } from './settingsboot.js';

const CSS = '#settingsPanel{position:fixed;z-index:70;top:calc(max(8px,env(safe-area-inset-top)) + 44px);right:8px;width:min(360px,calc(100vw - 16px));max-height:calc(100vh - 64px);max-height:calc(100dvh - 64px);overflow:auto;box-sizing:border-box;padding:10px 12px;background:#12182af5;color:#fff;border:1px solid #7fb2e6;border-radius:14px;font:13px system-ui,sans-serif;box-shadow:0 8px 30px #000a;display:none;touch-action:pan-y;-webkit-user-select:none;user-select:none;-webkit-overflow-scrolling:touch}'
 + '#settingsPanel h3{margin:0 0 4px;font-size:15px;display:flex;justify-content:space-between;align-items:center}'
 + '#settingsPanel .sec{margin:12px 0 4px;font-size:11px;letter-spacing:.08em;color:#9fb3d6;text-transform:uppercase}'
 + '#settingsPanel .own .sec{color:#e8c868}'
 + '#settingsPanel .row{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin:4px 0}'
 + '#settingsPanel .lab{flex:1 1 110px}'
 + '#settingsPanel button,#settingsPanel select{min-height:44px;min-width:44px;padding:6px 10px;border-radius:10px;border:1px solid #fff5;background:#243050;color:#fff;font:inherit;touch-action:manipulation}'
 + '#settingsPanel button.on{background:#7fb2e6;color:#10182a;font-weight:700}'
 + '#settingsPanel .own button.on{background:#c9a24a}'
 + '#settingsPanel input[type=range]{flex:1 1 150px;min-height:40px;accent-color:#7fb2e6}'
 + '#settingsPanel small{opacity:.7;font-size:11px;display:block}';

const CSS2 = '#settingsPanel{background:linear-gradient(180deg,#171127f2,#0d0b17f5)!important;border:1px solid #c9a24a88!important;border-radius:16px!important;color:#efe8ff;width:min(400px,calc(100vw - 16px))!important;box-shadow:0 8px 30px #000a,0 0 0 1px #6b3fd433}'
 + '#settingsPanel h3{font-size:18px;color:#f1d98a;letter-spacing:.04em}'
 + '#settingsPanel .card{background:#1d1632cc;border:1px solid #6b3fd466;border-radius:14px;padding:10px 12px 12px;margin:10px 0}'
 + '#settingsPanel .card>.sec{margin:0 0 2px;font-size:13px;font-weight:700;color:#f1d98a;letter-spacing:.1em}'
 + '#settingsPanel .card>.desc{opacity:.7;font-size:12px;margin:0 0 8px}'
 + '#settingsPanel .card.own{border-color:#c9a24a99;background:#241a35cc}'
 + '#settingsPanel button,#settingsPanel select{min-height:48px!important;background:#2b2147!important;border:1px solid #8a5cf655!important;border-radius:12px!important}'
 + '#settingsPanel button.on{background:linear-gradient(180deg,#e2bd5c,#b8892f)!important;color:#1a1224!important}'
 + '#settingsPanel .own button.on{background:linear-gradient(180deg,#e2bd5c,#b8892f)!important}'
 + '#settingsPanel input[type=range]{accent-color:#c9a24a!important;min-height:48px!important}'
 + '#settingsPanel .stp{min-width:48px!important;font-size:20px;font-weight:700}';
const CSS3 = '#settingsPanel .vn-set-tabs{display:flex;gap:6px;margin:6px 0 2px;position:sticky;top:-10px;z-index:2;padding:6px 0;background:#150f24}#settingsPanel .vn-set-tab{flex:1 1 0;min-height:44px!important;font:700 13px VarnCinzel,Georgia,serif!important;color:#f5ddab!important;background:linear-gradient(#253851,#111b2c)!important;border:1px solid #8d7041!important}#settingsPanel .vn-set-tab.on{background:linear-gradient(180deg,#e2bd5c,#b8892f)!important;color:#1a1224!important}#settingsPanel .vn-set-pane[hidden]{display:none}#settingsPanel .vn-about-version{color:#f1d28a;font-weight:700;padding:10px 2px;min-height:44px;box-sizing:border-box;cursor:default;touch-action:manipulation;-webkit-tap-highlight-color:transparent}#settingsPanel .card.vn-collapsible{padding:4px 6px;margin:5px 0}#settingsPanel .vn-setting-body{display:none;padding:8px 7px 11px}#settingsPanel .vn-card-open>.vn-setting-body{display:block}#settingsPanel .vn-settings-toggle{display:block!important;width:100%;min-height:42px!important;text-align:left!important;padding:8px 12px!important;background:linear-gradient(#253851,#111b2c)!important;border:1px solid #8d7041!important;color:#f5ddab!important;font:700 13px VarnCinzel,Georgia,serif!important}#settingsPanel .vn-settings-toggle:focus-visible{outline:2px solid #ffdd92}';
let root = null, body = null, timer = 0, E = null;
function el(tag, props, kids) { const e = document.createElement(tag); if (props) Object.assign(e, props); if (kids) for (const k of kids) e.appendChild(typeof k === 'string' ? document.createTextNode(k) : k); return e; }
const isOpen = () => !!root && root.style.display === 'block';
const hide = () => { if (root) root.style.display = 'none'; document.body.classList.remove('vn-settings-open'); clearInterval(timer); };

function toggleBtn(label, get, set, key) {
  const b = el('button', { type: 'button', textContent: label }); b.dataset.set = key;
  const sync = () => b.classList.toggle('on', !!get());
  b.addEventListener('click', () => { set(!get()); sync(); }); sync(); b._sync = sync; return b;
}
function slider(key, min, max, step, get, set, fmt) {
  const out = el('span', { style: 'min-width:42px;text-align:right' }), inp = el('input', { type: 'range', min, max, step, value: get() }); inp.dataset.set = key;
  const sync = () => { if (document.activeElement !== inp) inp.value = get(); out.textContent = fmt(get()); };
  inp.addEventListener('input', () => { set(+inp.value); out.textContent = fmt(+inp.value); });
  sync(); inp._sync = sync; return [inp, out];
}


/* Player tabs (v1.5.34 cleanup). Owner / CoOwner / dev items live in a hidden tab that
 * only appears after 5 quick taps on the About version line (or the ` key). */
const TABS = [['graphics', 'Graphics'], ['controls', 'Controls'], ['gameplay', 'Gameplay']];
let selectedTab = 'graphics', hiddenUnlocked = false;
export function unlockHidden() { hiddenUnlocked = true; selectedTab = 'hidden'; }
export const isHiddenUnlocked = () => hiddenUnlocked;
function build() {
  const { rig, prefs } = E, c = () => (window.__p3d && window.__p3d.cheats) || null, owner = () => !!(window.__p3d && window.__p3d.owner && c());
  body.textContent = '';
  const sec = (t) => el('div', { className: 'sec', textContent: t }), row = (...k) => el('div', { className: 'row' }, k);
  const syncs = [];
  const save = () => { persist(E); };
  const card = (title, desc, own) => { const d = el('div', { className: 'card' + (own ? ' own' : '') }); d.appendChild(sec(title)); if (desc) d.appendChild(el('div', { className: 'desc', textContent: desc })); return d; };
  const tabs = TABS.concat(hiddenUnlocked ? [['hidden', 'Owner & Dev']] : []);
  if (!tabs.some(([k]) => k === selectedTab)) selectedTab = 'graphics';
  const bar = el('div', { className: 'vn-set-tabs', role: 'tablist' });
  const panes = {};
  for (const [k, label] of tabs) {
    const t = el('button', { type: 'button', textContent: label, className: 'vn-set-tab' + (k === selectedTab ? ' on' : '') });
    t.dataset.tab = k; t.setAttribute('role', 'tab'); t.setAttribute('aria-selected', String(k === selectedTab));
    t.addEventListener('click', () => { selectedTab = k; build(); });
    bar.appendChild(t);
    const p = el('div', { className: 'vn-set-pane' }); p.dataset.pane = k; p.setAttribute('role', 'tabpanel'); p.hidden = k !== selectedTab; panes[k] = p;
  }
  body.appendChild(bar);
  for (const [k] of tabs) body.appendChild(panes[k]);

  /* ---- Graphics ---- */
  const g = card('Graphics', 'Quality and shadows. Lower is faster.');
  const q = el('select', { id: 'setQuality' }); q.dataset.set = 'quality';
  const names = { auto: 'Auto (adapts to your device)', high: 'High (sharpest)', balanced: 'Balanced', low: 'Low (fastest)' };
  for (const k of QUALITIES) q.appendChild(el('option', { value: k, textContent: names[k], selected: prefs.quality === k }));
  q.addEventListener('change', () => { prefs.quality = q.value; applyPrefs(E); save(); });
  g.appendChild(row(el('span', { className: 'lab', textContent: 'Quality' }), q));
  g.appendChild(row(toggleBtn('Shadows', () => prefs.shadows, (v) => { prefs.shadows = v; applyPrefs(E); save(); }, 'shadows')));
  panes.graphics.appendChild(g);

  /* ---- Controls ---- */
  const view = (v, label) => { const b = el('button', { type: 'button', textContent: label }); b.dataset.set = 'view-' + v; const s = () => b.classList.toggle('on', prefs.view === v); b.addEventListener('click', () => { rig.setView(v); save(); syncs.forEach((f) => f()); }); s(); syncs.push(s); return b; };
  const cm = (v, label) => { const b = el('button', { type: 'button', textContent: label }); b.dataset.set = 'cam-' + v; const s = () => b.classList.toggle('on', prefs.camMode === v); b.addEventListener('click', () => { prefs.camMode = v; save(); syncs.forEach((f) => f()); }); s(); syncs.push(s); return b; };
  const cc = card('Camera', 'How the view follows your hero.');
  cc.appendChild(row(el('span', { className: 'lab', textContent: 'View' }), view('third', 'Third person'), view('first', 'First person')));
  cc.appendChild(row(el('span', { className: 'lab', textContent: 'Camera follow' }), cm('follow', 'On'), cm('free', 'Off')));
  // One slider drives both look (drag) and zoom (pinch / wheel) sensitivity.
  const [si, so] = slider('camSens', SENS_MIN, SENS_MAX, 0.05, () => prefs.lookSens, (v) => { prefs.lookSens = v; prefs.zoomSens = v; save(); }, (v) => v.toFixed(2) + '×');
  syncs.push(si._sync); cc.appendChild(row(el('span', { className: 'lab', textContent: 'Camera sensitivity' }), si, so));
  panes.controls.appendChild(cc);
  const hc = card('On-screen buttons', 'Drag controls to move them, tap + or − to resize, then Save HUD. Reset is inside the editor.');
  const hudEd = () => window.__vnHudEditor || null;
  const eb = el('button', { type: 'button', textContent: 'Customize HUD' }); eb.dataset.set = 'editbtns';
  eb.addEventListener('click', () => { hide(); hudEd()?.open?.(); });
  hc.appendChild(row(eb));
  hc.appendChild(el('small', { textContent: 'Joystick or tap to move · drag to look · pinch to zoom. Keys: F attack · Space dodge · Q lock-on · 1–4 skills · R potion · V view.' }));
  panes.controls.appendChild(hc);

  /* ---- Gameplay ---- */
  const gc = card('Combat', 'Fight mode and on-screen combat buttons.');
  const cb = el('button', { type: 'button', textContent: 'Combat' }); cb.dataset.set = 'combat';
  const csync = () => { const active = !!(E.combatOn && E.combatOn()); cb.classList.toggle('on', active); cb.textContent = active ? 'Combat: On' : 'Combat: Off'; }; csync(); syncs.push(csync);
  cb.addEventListener('click', async () => { await E.setCombat(!(E.combatOn && E.combatOn())); csync(); });
  gc.appendChild(row(cb));
  panes.gameplay.appendChild(gc);
  const ac = card('About', '');
  const activeVersion = document.getElementById('vnVersion')?.textContent?.trim() || 'unknown';
  const version = el('div', { className: 'vn-about-version', textContent: 'Varnethryl · v' + activeVersion });
  version.dataset.vnAbout = '1'; version.dataset.set = 'about-version';
  ac.appendChild(version);
  const reset = el('button', { type: 'button', textContent: 'Restore default settings' }); reset.dataset.set = 'reset';
  reset.addEventListener('click', () => { Object.assign(prefs, DEFAULT_PREFS); rig.setView('third'); rig.setZoom(1); applyPrefs(E); save(); build(); });
  ac.appendChild(row(reset));
  panes.gameplay.appendChild(ac);

  /* ---- Hidden: Owner & Dev ---- */
  if (hiddenUnlocked) {
    const hp = panes.hidden;
    const oc = card('Access', 'Password-protected. Gates are unchanged.', true);
    const ob = el('button', { type: 'button', textContent: '🔒 Owner Cheats' }); ob.dataset.set = 'owner-cheats';
    ob.addEventListener('click', () => { hide(); E.openCheatPanel?.(); });
    const co = el('button', { type: 'button', textContent: '🔒 CoOwner Tools' }); co.dataset.set = 'coowner-tools';
    co.addEventListener('click', () => { hide(); document.getElementById('vnCoOwnerTools')?.click(); });
    oc.appendChild(row(ob, co)); hp.appendChild(oc);
    const dc = card('Developer', 'Testing and diagnostics.', true);
    dc.appendChild(row(toggleBtn('Show FPS', () => prefs.showFps, (v) => { prefs.showFps = v; prefs.fpsSet = true; applyPrefs(E); save(); }, 'showFps')));
    const modelBtn = el('button', { type: 'button', textContent: 'Switch model style' }); modelBtn.dataset.set = 'model-style';
    modelBtn.addEventListener('click', () => document.getElementById('mdlBtn')?.click());
    const galBtn = el('button', { type: 'button', textContent: '3D model gallery' }); galBtn.dataset.set = 'gallery';
    galBtn.addEventListener('click', () => location.assign('proto3d/model-viewer.html'));
    const bossBtn = el('button', { type: 'button', textContent: 'Approved boss models' }); bossBtn.dataset.set = 'boss-models';
    bossBtn.addEventListener('click', () => { hide(); if (window.__openBossRoster) window.__openBossRoster(); else document.querySelector('#heroes button.cur')?.click(); });
    const statusBtn = el('button', { type: 'button', textContent: 'Diagnostics' }); statusBtn.dataset.set = 'diagnostics';
    statusBtn.addEventListener('click', () => { hide(); document.getElementById('diagBtn')?.click(); });
    dc.appendChild(row(modelBtn, galBtn)); dc.appendChild(row(bossBtn, statusBtn)); hp.appendChild(dc);
    const body0 = body; body = hp;   // owner cards append into the hidden pane
    try {
  if (owner()) {
    const ch = c(), f = ch.flags, box = el('div', { className: 'card own' });
    const own = (key, label, fn, get) => { const b = toggleBtn(label, get, (v) => { fn(v); syncs.forEach((s) => s()); }, 'owner-' + key); syncs.push(b._sync); return b; };
    box.appendChild(sec('Owner (save is marked cheated)'));
    box.appendChild(row(own('god', 'God mode', (v) => ch.setGod(v), () => f.god), own('fly', 'Fly', (v) => ch.setFly(v), () => f.fly), own('noclip', 'Noclip', (v) => ch.setNoclip(v), () => f.noclip), own('bump', 'Bumps', (v) => ch.setBump(v), () => f.bump)));
    box.appendChild(row(own('unlimited', 'Unlimited MP/SP', (v) => ch.setUnlimited(v), () => f.unlimited), own('nocd', 'No cooldowns (Owner skin)', (v) => ch.setNoCooldown(v), () => f.noCooldown)));
    const spd = el('select', { id: 'setSpeed' }); for (const m of [0.5, 1, 2, 4, 8]) spd.appendChild(el('option', { value: m, textContent: m + '×', selected: m === f.speedMul }));
    spd.addEventListener('change', () => ch.setSpeed(+spd.value));
    box.appendChild(row(el('span', { className: 'lab', textContent: 'Speed' }), spd));
    const msg = el('small', { textContent: 'God mode starts ON for the owner; your choice is remembered.' });
    const mx = el('button', { type: 'button', textContent: 'Re-max active hero' }); mx.dataset.set = 'owner-max';
    mx.addEventListener('click', async () => { const m = await import('./ownermax.js'); const r = m.maxOwnerHero(E.storage); msg.textContent = r ? (r.changed ? 'Active hero maxed.' : 'Already maxed.') : 'Could not read the save.'; });
    const full = el('button', { type: 'button', textContent: 'Full cheat panel' }); full.dataset.set = 'owner-panel';
    full.addEventListener('click', () => { hide(); if (E.openCheatPanel) E.openCheatPanel(); });
    const tt = el('button', { type: 'button', textContent: 'Spawn Ashen Titan' }); tt.dataset.set = 'owner-titan';
    tt.addEventListener('click', () => { msg.textContent = ch.spawnTitan() ? 'The Ashen Titan awakens.' : 'A Titan is already alive.'; });
    const bb = toggleBtn('Bamboo Stick (test weapon)', () => { const F = window.__p3d && window.__p3d.fight; return !!(F && F.cc && F.cc.bamboo); }, (v) => { const F = window.__p3d && window.__p3d.fight; if (F && F.setBamboo) F.setBamboo(v); }, 'owner-bamboo'); syncs.push(bb._sync); box.appendChild(row(bb));
    box.appendChild(row(mx, full, tt)); box.appendChild(msg); body.appendChild(box);
    const dm = el('div', { className: 'card own' }); dm.appendChild(sec('Owner damage'));
    const sd = () => import('./combat/data.js');
    const stepper = (key, label, lo, hi, get, set, fmt) => {
      const out = el('span', { className: 'val', style: 'min-width:64px;text-align:center;font-weight:700;color:#f1d98a' });
      const mk2 = (t, d, k) => { const b = el('button', { type: 'button', textContent: t, className: 'stp' }); b.dataset.set = key + '-' + k; b.addEventListener('click', () => { set(Math.max(lo, Math.min(hi, get() + d))); sy(); }); return b; };
      const rg = el('input', { type: 'range', min: lo, max: hi, step: 1, value: get() }); rg.dataset.set = key; rg.addEventListener('input', () => { set(+rg.value); sy(); });
      const sy = () => { out.textContent = fmt(get()); if (document.activeElement !== rg) rg.value = get(); }; sy(); syncs.push(sy);
      return [el('div', { className: 'row' }, [el('span', { className: 'lab', textContent: label })]), el('div', { className: 'row' }, [mk2('−', -1, 'dec'), rg, mk2('+', 1, 'inc'), out])];
    };
    sd().then((D) => {
      const P = D.TUNING.perks, U = D.TUNING.ult, sv = () => D.saveSaberPrefs();
      const [l1, r1] = stepper('saberMul', 'Saber damage multiplier (× target current health; 0 = flat 99,999)', 0, 50, () => P.saberMul, (v) => { P.saberMul = v; sv(); }, (v) => v === 0 ? 'Flat' : '×' + v);
      const bt = toggleBtn('Saber multiplier also hits bosses', () => P.saberBossesX12, (v) => { P.saberBossesX12 = v; sv(); }, 'saberBossesX12'); syncs.push(bt._sync);
      const bk = toggleBtn('Ultimates instantly kill bosses (incl. Ashen Titan)', () => U.bossesInstantKill, (v) => { U.bossesInstantKill = v; sv(); }, 'bossesInstantKill'); syncs.push(bk._sync);
      const [l2, r2] = stepper('ultMul', 'Ultimate damage multiplier (Unholy Destruction)', 1, 100, () => U.dmgMul, (v) => { U.dmgMul = v; sv(); }, (v) => '×' + v);
      dm.append(l1, r1, row(bt), l2, r2, row(bk), el('small', { textContent: 'Ultimates (incl. Thunderstorm) kill bosses too while instant-kill is on (default); turn it off for a normal 99,999 hit. Never affects you, your party, NPCs or props.' }));
      regroup();
    });
    body.appendChild(dm);
  }
    } finally { body = body0; }
  }
  build.syncs = syncs;
  function regroup() {}
}

export function toggleSettings(env, opts) {
  E = env;
  const reveal = !!(opts && opts.hidden); if (reveal) unlockHidden();
  if (!root) {
    document.head.appendChild(el('style', { textContent: CSS + CSS2 + CSS3 }));
    root = el('div', { id: 'settingsPanel', role: 'dialog', 'aria-label': 'Settings' }); body = el('div');
    const close = el('button', { type: 'button', textContent: '✕', style: 'min-height:40px', id: 'setClose' }); close.addEventListener('click', hide);
    root.append(el('h3', null, [el('span', { textContent: 'Settings' }), close]), body);
    for (const t of ['keydown', 'keyup']) root.addEventListener(t, (e) => { e.stopPropagation(); if (t === 'keydown' && e.key === 'Escape') hide(); });
    document.body.appendChild(root);
  }
  if (isOpen()) { if (reveal) { build(); return true; } hide(); return false; }
  window.__vnHudEditor?.close?.(false);
  build(); root.style.display = 'block'; document.body.classList.add('vn-settings-open');
  timer = setInterval(() => { if (build.syncs) build.syncs.forEach((f) => f()); }, 400);
  return true;
}
