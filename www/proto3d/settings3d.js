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

let root = null, body = null, timer = 0, E = null;
function el(tag, props, kids) { const e = document.createElement(tag); if (props) Object.assign(e, props); if (kids) for (const k of kids) e.appendChild(typeof k === 'string' ? document.createTextNode(k) : k); return e; }
const isOpen = () => !!root && root.style.display === 'block';
const hide = () => { if (root) root.style.display = 'none'; clearInterval(timer); };

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

function build() {
  const { rig, prefs } = E, c = () => (window.__p3d && window.__p3d.cheats) || null, owner = () => !!(window.__p3d && window.__p3d.owner && c());
  body.textContent = '';
  const sec = (t) => el('div', { className: 'sec', textContent: t }), row = (...k) => el('div', { className: 'row' }, k);
  const syncs = [];
  const save = () => { persist(E); };
  const view = (v, label) => { const b = el('button', { type: 'button', textContent: label }); b.dataset.set = 'view-' + v; const s = () => b.classList.toggle('on', prefs.view === v); b.addEventListener('click', () => { rig.setView(v); save(); syncs.forEach((f) => f()); }); s(); syncs.push(s); return b; };
  body.appendChild(sec('Camera'));
  body.appendChild(row(view('third', 'Third person'), view('first', 'First person')));
  const [zi, zo] = slider('zoom', ZOOM_MIN, ZOOM_MAX, 0.01, () => rig.zoomTarget, (v) => { rig.setZoom(v); save(); }, (v) => v.toFixed(2) + '×');
  syncs.push(zi._sync); body.appendChild(row(el('span', { className: 'lab', textContent: 'Zoom (third person)' }), zi, zo));
  const [si, so] = slider('zoomSens', SENS_MIN, SENS_MAX, 0.05, () => prefs.zoomSens, (v) => { prefs.zoomSens = v; save(); }, (v) => v.toFixed(2) + '×');
  body.appendChild(row(el('span', { className: 'lab', textContent: 'Zoom sensitivity' }), si, so));
  const [li, lo] = slider('lookSens', SENS_MIN, SENS_MAX, 0.05, () => prefs.lookSens, (v) => { prefs.lookSens = v; save(); }, (v) => v.toFixed(2) + '×');
  body.appendChild(row(el('span', { className: 'lab', textContent: 'Look sensitivity' }), li, lo));
  body.appendChild(el('small', { textContent: 'Zoom: mouse wheel, pinch, or + / −.  View: V.  The camera never goes through walls.' }));

  body.appendChild(sec('Combat'));
  const cb = el('button', { type: 'button', textContent: 'Fight mode (spawns a few enemies)' }); cb.dataset.set = 'combat';
  const csync = () => cb.classList.toggle('on', !!(E.combatOn && E.combatOn())); csync(); syncs.push(csync);
  cb.addEventListener('click', async () => { await E.setCombat(!(E.combatOn && E.combatOn())); csync(); });
  body.appendChild(row(cb)); body.appendChild(el('small', { textContent: 'F attack · G dodge · T lock-on · Tab next target · 1-6 abilities (owner). On phone use the buttons by the stick.' }));
  const hudEd = () => (window.__p3d && window.__p3d.combat && window.__p3d.combat.hud && window.__p3d.combat.hud.editor) || null;
  const eb = el('button', { type: 'button', textContent: 'Edit buttons' }); eb.dataset.set = 'editbtns';
  const rb = el('button', { type: 'button', textContent: 'Reset buttons' }); rb.dataset.set = 'resetbtns';
  const esync = () => { const e = hudEd(); eb.classList.toggle('on', !!(e && e.editing)); }; syncs.push(esync);
  eb.addEventListener('click', async () => { if (!(E.combatOn && E.combatOn())) await E.setCombat(true); const e = hudEd(); if (!e) return; e.enable(!e.editing); esync(); if (e.editing) hide(); });
  rb.addEventListener('click', () => { const e = hudEd(); if (e) { e.reset(); esync(); } });
  body.appendChild(row(eb, rb));
  body.appendChild(el('small', { textContent: 'Edit buttons: the menu closes; drag a button to move it, pinch it (two fingers) or use the size slider. Saved on this device. Tap Done when finished.' }));
  body.appendChild(sec('Graphics'));
  const q = el('select', { id: 'setQuality' }); q.dataset.set = 'quality';
  const names = { auto: 'Auto (adapts to your device)', high: 'High (sharpest)', balanced: 'Balanced', low: 'Low (fastest)' };
  for (const k of QUALITIES) q.appendChild(el('option', { value: k, textContent: names[k], selected: prefs.quality === k }));
  q.addEventListener('change', () => { prefs.quality = q.value; applyPrefs(E); save(); });
  body.appendChild(row(el('span', { className: 'lab', textContent: 'Quality' }), q));
  body.appendChild(row(toggleBtn('Shadows', () => prefs.shadows, (v) => { prefs.shadows = v; applyPrefs(E); save(); }, 'shadows')));
  body.appendChild(sec('Display'));
  body.appendChild(row(toggleBtn('Show FPS', () => prefs.showFps, (v) => { prefs.showFps = v; applyPrefs(E); save(); }, 'showFps')));

  if (owner()) {
    const ch = c(), f = ch.flags, box = el('div', { className: 'own' });
    const own = (key, label, fn, get) => { const b = toggleBtn(label, get, (v) => { fn(v); syncs.forEach((s) => s()); }, 'owner-' + key); syncs.push(b._sync); return b; };
    box.appendChild(sec('Owner (save is marked cheated)'));
    box.appendChild(row(own('god', 'God mode', (v) => ch.setGod(v), () => f.god), own('fly', 'Fly', (v) => ch.setFly(v), () => f.fly), own('noclip', 'Noclip', (v) => ch.setNoclip(v), () => f.noclip), own('bump', 'Bumps', (v) => ch.setBump(v), () => f.bump)));
    box.appendChild(row(own('unlimited', 'Unlimited MP/SP', (v) => ch.setUnlimited(v), () => f.unlimited)));
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
    box.appendChild(row(mx, full, tt)); box.appendChild(msg); body.appendChild(box);
  }
  const reset = el('button', { type: 'button', textContent: 'Reset camera & settings' }); reset.dataset.set = 'reset';
  reset.addEventListener('click', () => { Object.assign(prefs, DEFAULT_PREFS); rig.setView('third'); rig.setZoom(1); applyPrefs(E); save(); build(); });
  body.appendChild(el('div', { className: 'sec', textContent: ' ' })); body.appendChild(reset);
  build.syncs = syncs;
}

export function toggleSettings(env) {
  E = env;
  if (!root) {
    document.head.appendChild(el('style', { textContent: CSS }));
    root = el('div', { id: 'settingsPanel', role: 'dialog', 'aria-label': 'Settings' }); body = el('div');
    const close = el('button', { type: 'button', textContent: '✕', style: 'min-height:40px', id: 'setClose' }); close.addEventListener('click', hide);
    root.append(el('h3', null, [el('span', { textContent: 'Settings' }), close]), body);
    for (const t of ['keydown', 'keyup']) root.addEventListener(t, (e) => { e.stopPropagation(); if (t === 'keydown' && e.key === 'Escape') hide(); });
    document.body.appendChild(root);
  }
  if (isOpen()) { hide(); return false; }
  build(); root.style.display = 'block';
  timer = setInterval(() => { if (build.syncs) build.syncs.forEach((f) => f()); }, 400);
  return true;
}
