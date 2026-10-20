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
const CSS3 = '#settingsPanel .card.vn-collapsible{padding:4px 6px;margin:5px 0}#settingsPanel .vn-setting-body{display:none;padding:8px 7px 11px}#settingsPanel .vn-card-open>.vn-setting-body{display:block}#settingsPanel .vn-settings-toggle{display:block!important;width:100%;min-height:42px!important;text-align:left!important;padding:8px 12px!important;background:linear-gradient(#253851,#111b2c)!important;border:1px solid #8d7041!important;color:#f5ddab!important;font:700 13px VarnCinzel,Georgia,serif!important}#settingsPanel .vn-settings-toggle:focus-visible{outline:2px solid #ffdd92}';
const DESCS = { 'Game & version': 'Version information, characters and diagnostics.', 'Camera': 'How the view follows your hero.', 'Combat': 'Fight mode, hotkeys and on-screen buttons.', 'Loadout': 'Signature weapon, armor set and skills of your current hero.', 'Graphics': 'Quality and shadows. Lower is faster.', 'Display': 'On-screen info.', 'Owner (save is marked cheated)': 'Owner-account tools and power settings.', 'Owner damage': 'Saber and Unholy Destruction damage. Owner account only.' };
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
  body.appendChild(sec('Game & version'));
  body.appendChild(row(el('b',{textContent:'Varnethryl 3D · v1.2.2',style:'color:#f1d28a'})));
  body.appendChild(el('small',{textContent:'The entire game now runs in 3D. No Classic 2D switching.'}));
  const lineBtn=el('button',{type:'button',textContent:'Choose a character'});
  lineBtn.addEventListener('click',()=>{hide();document.querySelector('#heroes button.cur')?.click();});
  const galBtn=el('button',{type:'button',textContent:'View 3D lineup'});
  galBtn.addEventListener('click',()=>location.assign('proto3d/model-viewer.html'));
  const modelBtn=el('button',{type:'button',textContent:'Switch model style'});
  modelBtn.addEventListener('click',()=>document.getElementById('mdlBtn')?.click());
  const statusBtn=el('button',{type:'button',textContent:'3D model diagnostics'});
  statusBtn.addEventListener('click',()=>{hide();document.getElementById('diagBtn')?.click();});
  body.appendChild(row(lineBtn,galBtn,modelBtn,statusBtn));
  body.appendChild(sec('Camera'));
  body.appendChild(row(view('third', 'Third person'), view('first', 'First person')));
  const cm = (v, label) => { const b = el('button', { type: 'button', textContent: label }); b.dataset.set = 'cam-' + v; const s = () => b.classList.toggle('on', prefs.camMode === v); b.addEventListener('click', () => { prefs.camMode = v; save(); syncs.forEach((f) => f()); }); s(); syncs.push(s); return b; };
  body.appendChild(row(cm('follow', 'Behind character'), cm('free', 'Free camera')));
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
  body.appendChild(sec('Loadout'));
  const ld = el('div', { className: 'ld', style: 'font-size:13px;line-height:1.5' }); body.appendChild(ld);
  const ldSync = () => { const F = window.__p3d && window.__p3d.fight, kit = F && F.cc && F.cc.kit; if (!kit || !kit.weapon) { ld.textContent = F && F.on ? 'This hero uses the generic kit.' : 'Start Fight mode to see the active hero\u2019s weapon, armor and skills.'; return; }
    const w = kit.weapon, a = kit.armor, pc = (v) => '+' + Math.round(v * 100) + '%', st = [a.hpPct && 'HP ' + pc(a.hpPct), a.mpPct && 'MP ' + pc(a.mpPct), a.spPct && 'SP ' + pc(a.spPct), a.defPct && 'DEF ' + pc(a.defPct)].filter(Boolean).join(' \u00b7 ');
    ld.innerHTML = ''; for (const [h, t] of [['Weapon', w.name + ' (damage ' + pc(w.dmgPct) + ')'], ['Armor', a.name + ' \u2014 ' + st], ['Skills', kit.skills.map((x) => x.name).join(' \u00b7 ')]]) ld.appendChild(el('div', null, [el('b', { textContent: h + ': ', style: 'color:#f1d98a' }), t])); };
  const ab = el('button', { type: 'button', className: 'ctl', id: 'openArmory', textContent: 'Open Armory (12 slots, inventory, compare, presets)' }); ab.style.cssText = 'width:100%;min-height:48px;margin-top:8px;border:1px solid #c9a24d;background:linear-gradient(180deg,#3a2a5c,#1d1533);color:#f3d9a0;border-radius:12px;font-weight:700';
  ab.addEventListener('click', async () => { const F = window.__p3d && window.__p3d.fight; if (!F || !F.armory) { ld.textContent = 'Start Fight mode first to open the Armory.'; return; } const m = await import('./armoryui.js'); m.openArmory(F.armory); });
  body.appendChild(ab);
  ldSync(); syncs.push(ldSync);
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
    const dm = el('div', { className: 'own' }); dm.appendChild(sec('Owner damage'));
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
  const reset = el('button', { type: 'button', textContent: 'Reset camera & settings' }); reset.dataset.set = 'reset';
  reset.addEventListener('click', () => { Object.assign(prefs, DEFAULT_PREFS); rig.setView('third'); rig.setZoom(1); applyPrefs(E); save(); build(); });
  body.appendChild(el('div', { className: 'sec', textContent: ' ' })); body.appendChild(reset);
  build.syncs = syncs; regroup();
  function regroup() {   // wrap each section header + its controls into a card
    const kids = [...body.childNodes]; let card = null;
    for (const k of kids) {
      if (k.classList && k.classList.contains('card')) { card = null; continue; }
      const isSec = k.classList && k.classList.contains('sec'), box = k.classList && k.classList.contains('own');
      if (box) { const h = k.querySelector('.sec'); if (h) { k.className = 'card own'; const d = el('div', { className: 'desc', textContent: DESCS[h.textContent] || '' }); h.after(d); } card = null; continue; }
      if (isSec && k.textContent.trim()) { card = el('div', { className: 'card' }); body.insertBefore(card, k); card.appendChild(k); const d = DESCS[k.textContent]; if (d) card.appendChild(el('div', { className: 'desc', textContent: d })); continue; }
      if (card) card.appendChild(k);
    }
    // Each settings category is a one-tap accordion; no enormous scrolling menu.
    for(const card of body.querySelectorAll('.card')){
      if(!card.classList.contains('vn-collapsible')){
        const header=card.querySelector(':scope > .sec');
        if(!header)continue;
        const button=el('button',{type:'button',className:'vn-settings-toggle',textContent:header.textContent+' ▾'});
        button.setAttribute('aria-expanded','false');
        const inner=el('div',{className:'vn-setting-body'});
        for(const child of [...card.children])inner.appendChild(child);
        card.append(button,inner);
        card.classList.add('vn-collapsible');
        button.addEventListener('click',()=>{
          const opened=card.classList.toggle('vn-card-open');
          button.textContent=header.textContent+(opened?' ▴':' ▾');
          button.setAttribute('aria-expanded',String(opened));
        });
      } else {
        const inner=card.querySelector(':scope > .vn-setting-body');
        if(inner)for(const n of [...card.children])if(n!==inner&&!n.classList.contains('vn-settings-toggle'))inner.appendChild(n);
      }
    }
  }
}

export function toggleSettings(env) {
  E = env;
  if (!root) {
    document.head.appendChild(el('style', { textContent: CSS + CSS2 + CSS3 }));
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
