/* In-game Settings menu (DOM only: zero draw calls, lazy-loaded by settingsboot.js on first open).
 * Sections: Camera, Combat, Animation Lab, Graphics, Display. All owner-only
 * movement, damage and cheat controls reside behind the separate owner gate.
 * No sound section: the 3D game has no audio yet. */
import { ZOOM_MIN, ZOOM_MAX, SENS_MIN, SENS_MAX, DEFAULT_PREFS, QUALITIES } from './camprefs.js';
import { applyPrefs, persist } from './settingsboot.js';
import { createTapCounter } from './cheatboot.js';

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
const DESCS = { 'Game & version': 'Version information, characters and diagnostics.', 'Camera': 'How the view follows your hero.', 'Combat': 'Fight mode, hotkeys and on-screen buttons.', 'Loadout': 'Signature weapon, armor set and skills of your current hero.', 'Graphics': 'Quality and shadows. Lower is faster.', 'Animation Lab': 'Preview Beth rigs and Meshy bodies while moving in game. Temporary: does not change saves.', 'Display': 'On-screen info.' };
const TITLES = { 'Game & version':'Game', 'Camera':'Camera & movement', 'Combat':'Combat controls', 'Loadout':'Equipment & skills', 'Graphics':'Graphics & performance', 'Animation Lab':'Animation Lab (test)', 'Display':'On-screen display' };
let selectedSection = 'Camera';
let animationLabNotes = ''; // local, temporary tester feedback; never written into game saves
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
  const { rig, prefs } = E;
  body.textContent = '';
  body.appendChild(el('div', { className: 'vn-settings-intro', textContent: 'Choose a category below. Changes save automatically.' }));
  const sec = (t) => el('div', { className: 'sec', textContent: t }), row = (...k) => el('div', { className: 'row' }, k);
  const syncs = [];
  const save = () => { persist(E); };
  const view = (v, label) => { const b = el('button', { type: 'button', textContent: label }); b.dataset.set = 'view-' + v; const s = () => b.classList.toggle('on', prefs.view === v); b.addEventListener('click', () => { rig.setView(v); save(); syncs.forEach((f) => f()); }); s(); syncs.push(s); return b; };
  body.appendChild(sec('Game & version'));
  const version = el('button', { type: 'button', textContent: 'Varnethryl 3D · v1.2.4' });
  version.dataset.set = 'version-cheats';
  version.setAttribute('aria-label', 'Version');
  version.style.cssText = 'color:#f1d28a;font-weight:700;cursor:pointer;touch-action:manipulation';
  const versionTaps = createTapCounter();
  version.addEventListener('pointerup', e => { if (versionTaps(e.timeStamp || performance.now())) { hide(); E.openCheatPanel?.(); } });
  body.appendChild(row(version));
  body.appendChild(el('small',{textContent:'The entire game now runs in 3D. No Classic 2D switching.'}));
  const lineBtn=el('button',{type:'button',textContent:'Choose a character'});
  lineBtn.addEventListener('click',()=>{hide();document.querySelector('#heroes button.cur')?.click();});
  const galBtn=el('button',{type:'button',textContent:'View 3D lineup'});
  galBtn.addEventListener('click',()=>location.assign('proto3d/model-viewer.html'));
  const modelBtn=el('button',{type:'button',textContent:'Switch 3D / Classic character models'});
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
  const cb = el('button', { type: 'button', textContent: 'Enable combat testing' }); cb.dataset.set = 'combat';
  const csync = () => cb.classList.toggle('on', !!(E.combatOn && E.combatOn())); csync(); syncs.push(csync);
  cb.addEventListener('click', async () => { await E.setCombat(!(E.combatOn && E.combatOn())); csync(); });
  body.appendChild(row(cb)); body.appendChild(el('small', { textContent: 'F attack · G dodge · T lock-on · Tab next target · 1-6 abilities (owner). On phone use the buttons by the stick.' }));
  const hudEd = () => (window.__p3d && window.__p3d.combat && window.__p3d.combat.hud && window.__p3d.combat.hud.editor) || null;
  const eb = el('button', { type: 'button', textContent: 'Move or resize buttons' }); eb.dataset.set = 'editbtns';
  const rb = el('button', { type: 'button', textContent: 'Restore button layout' }); rb.dataset.set = 'resetbtns';
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
  body.appendChild(sec('Animation Lab'));
  const lab=E.animationLab;
  if(lab) {
    const labHelp=el('small',{textContent:'Experimental movement tests on the REAL map. Your hero stats, original models and saved selection remain unchanged. Not all Meshy files can be rebound automatically.'});
    body.appendChild(labHelp);
    const people=el('select',{id:'labHero'});
    people.dataset.set='lab-hero';
    for(const p of lab.candidates()) people.appendChild(el('option',{value:p.id,textContent:p.name}));
    const styles=el('select',{id:'labStyle'});
    styles.dataset.set='lab-style';
    for (const [value,label] of [
      ['bridge','Experimental: Beth skeleton + Meshy surface'],
      ['detailed','Detailed Meshy / original GLB rig'],
      ['classic','Original Beth blocky rig']]) {
      styles.appendChild(el('option',{value,textContent:label}));
    }
    const source=el('select',{id:'labSource'});
    source.dataset.set='lab-source';
    for(const [value,label] of [['original','Original detailed mesh'],['new','Newer detailed mesh (when available)']])
      source.appendChild(el('option',{value,textContent:label}));
    body.appendChild(row(el('span',{className:'lab',textContent:'Character'}),people));
    body.appendChild(row(el('span',{className:'lab',textContent:'Rig test'}),styles));
    body.appendChild(row(el('span',{className:'lab',textContent:'Mesh source'}),source));
    const labMessage=el('small',{textContent:lab.status().active
      ? 'Running: '+lab.status().character+' · '+lab.status().style+' (temporary)'
      : 'No rig experiment active.'});
    const tryBtn=el('button',{type:'button',id:'animationLabStart',textContent:'Test character in-game'});
    tryBtn.dataset.set='lab-start';
    const restore=el('button',{type:'button',id:'animationLabStop',textContent:'Restore original'});
    restore.dataset.set='lab-stop';
    const working=(busy)=>{tryBtn.disabled=busy;restore.disabled=busy;};
    tryBtn.addEventListener('click',async()=>{
      working(true);
      labMessage.textContent='Preparing character preview…';
      try{
        const response=await lab.start(people.value,styles.value,source.value);
        labMessage.textContent=response.message;
        if(response.ok)hide(); // Walk, run and fight with standard in-game controls.
      }finally{working(false);}
    });
    restore.addEventListener('click',()=>{
      const r=lab.stop(); labMessage.textContent=r.message;
    });
    body.appendChild(row(tryBtn,restore));body.appendChild(labMessage);
    const issues=el('textarea',{id:'animationLabNotes',rows:3,value:animationLabNotes,
      placeholder:'Examples: knees snap; feet slide when running; cape clips; attack pose twists'});
    issues.dataset.set='lab-notes';issues.style.cssText='width:100%;box-sizing:border-box;background:#12182a;color:#fff;border:1px solid #c9a24a;border-radius:8px;padding:8px;font:inherit';
    issues.addEventListener('input',()=>{animationLabNotes=issues.value;});
    body.appendChild(issues);
    const reportBtn=el('button',{type:'button',id:'animationLabCopy',textContent:'Copy animation test report'});
    reportBtn.dataset.set='lab-copy';
    reportBtn.addEventListener('click',async()=>{
      const report=lab.report(animationLabNotes);
      try{
        await navigator.clipboard.writeText(report);
        labMessage.textContent='Report copied. Paste it into our chat with your feedback.';
      }catch(e){
        issues.value=report;animationLabNotes=report;
        issues.focus();issues.select();
        labMessage.textContent='Copy access unavailable. Report selected above; use Copy.';
      }
    });
    body.appendChild(row(reportBtn));
    body.appendChild(el('small',{textContent:'To exit test mode, reopen Settings → Animation Lab → Restore original. If the experiment cannot bind a model, the original stays visible.'}));
  }
  body.appendChild(sec('Graphics'));
  // Natural visuals change only rendering; saved world, combat and character skins are untouched.
  const look = el('select', { id: 'setVisualStyle' });
  look.dataset.set = 'visual-style';
  const activeLook = E.getVisualStyle ? E.getVisualStyle() : 'natural';
  for (const [value, label] of [['natural', 'Natural 3D (soft shadows & lighting)'], ['classic', 'Classic (original rendering)']]) {
    look.appendChild(el('option', { value, textContent: label, selected: value === activeLook }));
  }
  look.addEventListener('change', () => { E.setVisualStyle?.(look.value); });
  body.appendChild(row(el('span', { className: 'lab', textContent: 'Rendering style' }), look));
  body.appendChild(el('small', { textContent: 'Natural improves lighting and soft shadows without replacing your world. Restart the game after changing style to update edge smoothing.' }));
  const q = el('select', { id: 'setQuality' }); q.dataset.set = 'quality';
  const names = { auto: 'Auto (adapts to your device)', high: 'High (sharpest)', balanced: 'Balanced', low: 'Low (fastest)' };
  for (const k of QUALITIES) q.appendChild(el('option', { value: k, textContent: names[k], selected: prefs.quality === k }));
  q.addEventListener('change', () => { prefs.quality = q.value; applyPrefs(E); save(); });
  body.appendChild(row(el('span', { className: 'lab', textContent: 'Quality' }), q));
  body.appendChild(row(toggleBtn('Shadows', () => prefs.shadows, (v) => { prefs.shadows = v; applyPrefs(E); save(); }, 'shadows')));
  body.appendChild(sec('Display'));
  body.appendChild(row(toggleBtn('Show FPS', () => prefs.showFps, (v) => { prefs.showFps = v; applyPrefs(E); save(); }, 'showFps')));

  const reset = el('button', { type: 'button', textContent: 'Restore default settings' }); reset.dataset.set = 'reset';
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
    // Keep introductory help outside the accordion, and move reset into
    // the Game section instead of leaving an unexplained button at the end.
    const intro=body.querySelector('.vn-settings-intro');
    if(intro)body.prepend(intro);
    const resetButton=body.querySelector('[data-set="reset"]');
    const gameCard=[...body.querySelectorAll('.card')].find(x=>x.querySelector(':scope > .sec')?.textContent==='Game & version');
    if(resetButton && gameCard)gameCard.appendChild(resetButton);
    // Only one category is expanded at a time, with the last chosen
    // category remembered while the settings panel is reopened.
    for(const card of body.querySelectorAll('.card')){
      if(!card.classList.contains('vn-collapsible')){
        const header=card.querySelector(':scope > .sec');
        if(!header)continue;
        const name=header.textContent;
        const title=TITLES[name] || name;
        const button=el('button',{type:'button',className:'vn-settings-toggle',textContent:title+' ▾'});
        button.setAttribute('aria-expanded','false');
        const inner=el('div',{className:'vn-setting-body'});
        for(const child of [...card.children])inner.appendChild(child);
        card.append(button,inner);
        card.classList.add('vn-collapsible');
        if(name===selectedSection){card.classList.add('vn-card-open');button.textContent=title+' ▴';button.setAttribute('aria-expanded','true');}
        button.addEventListener('click',()=>{
          const opened=!card.classList.contains('vn-card-open');
          for(const other of body.querySelectorAll('.card.vn-collapsible')){
            other.classList.remove('vn-card-open');
            const otherButton=other.querySelector(':scope > .vn-settings-toggle');
            if(otherButton){otherButton.textContent=otherButton.textContent.replace(' ▴',' ▾');otherButton.setAttribute('aria-expanded','false');}
          }
          if(opened){card.classList.add('vn-card-open');selectedSection=name;}
          else selectedSection='';
          button.textContent=title+(opened?' ▴':' ▾');
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
