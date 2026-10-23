/* Owner cheat panel UI (DOM only, no canvas / WebGL work, so zero draw calls whether open or closed).
 * Loaded lazily by cheatboot.js. Shows nothing unless ownergate.isOwner(); otherwise shows only the passphrase prompt (local mode)
 * or does nothing at all (server mode and not the owner). Remember: client-side gating is a speed bump, not security (see README). */
import { getOwnerGate } from './ownergate.js';
import { createCheats, createFlags, MAX_LEVEL, MAX_ITEM_LEVEL, ITEM_KINDS } from './cheats.js';

const CSS = '#ownerPanel,#ownerLogin{position:fixed;z-index:8100;background:#12182af2;color:#fff;border:1px solid #c9a24a;border-radius:14px;font:13px system-ui,sans-serif;box-shadow:0 8px 30px #000a;touch-action:pan-y;-webkit-user-select:none;user-select:none}'
 + '#ownerPanel{top:max(8px,env(safe-area-inset-top));right:8px;width:min(340px,calc(100vw - 16px));max-height:calc(100vh - 24px);max-height:calc(100dvh - 24px);overflow:auto;padding:10px;display:none}'
 + '#ownerLogin{left:50%;top:30%;transform:translateX(-50%);width:min(300px,calc(100vw - 24px));padding:14px;display:none}'
 + '#ownerPanel h3{margin:0 0 6px;font-size:14px;color:#e8c868;display:flex;justify-content:space-between;align-items:center}'
 + '#ownerPanel .sec{margin:8px 0 2px;font-size:11px;letter-spacing:.08em;color:#9fb3d6;text-transform:uppercase}'
 + '#ownerPanel .row{display:flex;flex-wrap:wrap;gap:6px;align-items:center}'
 + '#ownerPanel button,#ownerLogin button{min-height:44px;min-width:44px;padding:6px 10px;border-radius:10px;border:1px solid #fff5;background:#243050;color:#fff;font:inherit;touch-action:manipulation}'
 + '#ownerPanel button.on{background:#c9a24a;color:#1b2433;font-weight:700}'
 + '#ownerPanel select,#ownerPanel input,#ownerLogin input{min-height:40px;border-radius:8px;border:1px solid #fff5;background:#0c1222;color:#fff;font:inherit;padding:4px 8px;-webkit-user-select:text;user-select:text}'
 + '#ownerPanel input[type=number]{width:70px}#ownerLogin input{width:100%;box-sizing:border-box;margin:8px 0}'
 + '#ownerMsg,#ownerLoginMsg{font-size:12px;min-height:16px;color:#ffd58a;margin-top:4px}#ownerLoginMsg{color:#ffb4a8}'
 + '#ownerFly{position:fixed;z-index:59;right:12px;top:42%;display:none;flex-direction:column;gap:10px}#ownerFly button{width:58px;height:58px;border-radius:50%;border:2px solid #fff;background:#0009;color:#fff;font-size:22px;touch-action:none}'
 + '#ownerBadge{position:fixed;z-index:58;left:10px;top:max(64px,calc(env(safe-area-inset-top) + 56px));font:700 11px system-ui;letter-spacing:.1em;color:#1b2433;background:#c9a24a;border-radius:8px;padding:2px 8px;display:none;pointer-events:none}';

let ui = null, cheats = null;

function el(tag, props, kids) { const e = document.createElement(tag); if (props) Object.assign(e, props); if (kids) for (const k of kids) e.appendChild(typeof k === 'string' ? document.createTextNode(k) : k); return e; }
/* keys typed into the panel must not steer the hero or re-trigger the gesture */
function isolateKeys(node) { for (const t of ['keydown', 'keyup']) node.addEventListener(t, (e) => { e.stopPropagation(); }); }

function buildLogin(gate, onOk) {
  const box = el('div', { id: 'ownerLogin' }), pass = el('input', { id: 'ownerPass', type: 'password', autocomplete: 'off', placeholder: 'Owner passphrase', maxLength: 128 });
  const msg = el('div', { id: 'ownerLoginMsg' }), go = el('button', { id: 'ownerGo', type: 'button', textContent: 'Unlock' });
  const cancel = el('button', { type: 'button', textContent: 'Cancel', style: 'margin-left:8px' });
  box.append(el('div', { textContent: 'Owner access', style: 'font-weight:700;color:#e8c868' }), pass, go, cancel, msg);
  isolateKeys(box);
  const submit = async () => {
    go.disabled = true; msg.textContent = '';
    const r = await gate.unlock(pass.value); pass.value = ''; go.disabled = false;
    if (r.ok) { box.style.display = 'none'; onOk(); return; }
    msg.textContent = r.reason === 'throttled' ? 'Too many tries. Wait ' + Math.ceil(r.retryMs / 1000) + 's.' : r.reason === 'crypto-unavailable' ? 'Needs a secure (https) page.' : 'Wrong passphrase.' + (r.triesLeft === 0 ? ' Locked for a bit.' : '');
  };
  go.addEventListener('click', submit); pass.addEventListener('keydown', (e) => { if (e.key === 'Enter') submit(); });
  cancel.addEventListener('click', () => { pass.value = ''; box.style.display = 'none'; });
  document.body.appendChild(box); return box;
}

function buildPanel(c, gate, env) {
  const panel = el('div', { id: 'ownerPanel' }), msg = el('div', { id: 'ownerMsg' }), btns = {};
  const say = (t) => { msg.textContent = t; };
  const toggle = (key, label, fn, get) => { const b = el('button', { type: 'button', textContent: label }); b.dataset.cheat = key; b.addEventListener('click', () => { fn(!get()); sync(); }); btns[key] = { b, get }; return b; };
  const act = (key, label, fn, noMsg) => { const b = el('button', { type: 'button', textContent: label }); b.dataset.cheat = key; b.addEventListener('click', () => { const r = fn(); say(label + (r === false ? ': ' + (noMsg || 'nothing to do (is Fight mode on?)') : ': done')); sync(); }); return b; };
  const sec = (t) => el('div', { className: 'sec', textContent: t });
  const row = (...k) => el('div', { className: 'row' }, k);
  const f = c.flags;
  const close = el('button', { type: 'button', textContent: '✕', style: 'min-height:36px' }); close.addEventListener('click', () => hide());
  panel.appendChild(el('h3', null, [el('span', { textContent: 'Owner cheats (save will be marked cheated)' }), close]));
  panel.appendChild(sec('Movement'));
  panel.appendChild(row(toggle('god', 'God', c.setGod, () => f.god), toggle('fly', 'Fly', c.setFly, () => f.fly), toggle('noclip', 'Noclip', c.setNoclip, () => f.noclip), toggle('bump', 'Bumps', c.setBump, () => f.bump)));
  const spd = el('select', { id: 'ownerSpeed' }); for (const m of [0.5, 1, 2, 4, 8]) spd.appendChild(el('option', { value: m, textContent: m + '×', selected: m === 1 }));
  spd.addEventListener('change', () => { c.setSpeed(+spd.value); sync(); }); isolateKeys(spd);
  panel.appendChild(row(el('span', { textContent: 'Speed' }), spd));
  panel.appendChild(el('div', { textContent: 'Fly: Space/E up, Q/C/Shift down, or the ▲▼ buttons.', style: 'font-size:11px;opacity:.7' }));
  panel.appendChild(sec('Gold / XP / level'));
  panel.appendChild(row(toggle('inf', '∞ Gold', c.setInfiniteGold, () => f.infGold), act('gold+', '+1M gold', () => c.addGold(1000000))));
  panel.appendChild(row(act('xp+', '+1k XP', () => c.addXp(1000)), act('xp++', '+50k XP', () => c.addXp(50000))));
  const lvl = el('input', { id: 'ownerLevel', type: 'number', min: 1, max: MAX_LEVEL, value: 40 }); isolateKeys(lvl);
  panel.appendChild(row(lvl, act('lvl-a', 'Set active', () => c.setLevel(+lvl.value, 'active')), act('lvl-p', 'Set party', () => c.setLevel(+lvl.value, 'party'))));
  panel.appendChild(sec('Items'));
  const kind = el('select', { id: 'ownerKind' }); for (const k of ITEM_KINDS) kind.appendChild(el('option', { value: k, textContent: k })); isolateKeys(kind);
  const il = el('select', { id: 'ownerItemLv' }); for (let i = 0; i <= MAX_ITEM_LEVEL; i++) il.appendChild(el('option', { value: i, textContent: 'Lv ' + i, selected: i === MAX_ITEM_LEVEL })); isolateKeys(il);
  panel.appendChild(row(kind, il, act('item', 'Spawn', () => c.spawnItem(kind.value, +il.value))));
  panel.appendChild(sec('Party / enemies / quests'));
  panel.appendChild(row(act('heal', 'Heal party', c.healParty), act('kill', 'Kill enemies', c.killEnemies, 'no live enemies'), act('skipq', 'Skip quest', c.skipQuest, 'there are no quests in the 3D game yet, nothing changed')));
  const foe = el('select', { id: 'ownerFoe' }); for (const k of ['wolf', 'raider', 'wraith', 'skeleton']) foe.appendChild(el('option', { value: k, textContent: k })); isolateKeys(foe);
  panel.appendChild(row(foe, act('spawn', 'Spawn enemy', () => c.spawnEnemy(foe.value), 'fight mode is full'), act('spawn-titan', 'Spawn Ashen Titan', () => c.spawnTitan(), 'a Titan is already alive')));
  if (env.hooks && env.hooks.fightTest) { panel.appendChild(sec('Fight test')); panel.appendChild(row(act('fight', 'Start / stop fight test', () => { env.hooks.fightTest(); hide(); return true; }))); panel.appendChild(el('div', { textContent: 'Owner + lightsaber vs chasing monsters. Attack: button or F/J.', style: 'font-size:11px;opacity:.7' })); }
  panel.appendChild(sec('Teleport'));
  const zone = el('select', { id: 'ownerZone', ariaLabel: 'Select map destination' });
  const zoneNames={village:'Kingdom / Main Overworld',wilds:'The Wilds',frost:'Frost Troll Ice Cave',hydra:'Hydra Mire — Five-Headed Boss',sailing:'Tidewrack Ocean — 1 × 1 km'};
  for(const z of c.zones())zone.appendChild(el('option',{value:z,textContent:zoneNames[z]||z}));
  isolateKeys(zone);
  const travel=(key,label,z)=>{
    const b=el('button',{type:'button',textContent:label});
    b.dataset.cheat=key;
    b.addEventListener('click',()=>{
      const ok=c.teleportZone(z);
      say(ok?'Entering '+(zoneNames[z]||z)+'…':'Destination unavailable');
      if(ok)hide();
    });
    return b;
  };
  panel.appendChild(row(zone, act('tpz', 'Go zone', () => {const ok=c.teleportZone(zone.value);if(ok)hide();return ok;})));
  // Dedicated owner-only shortcuts in addition to the dropdown.
  panel.appendChild(row(
    travel('tp-hydra','🐉 Hydra Mire','hydra'),
    travel('tp-sailing','⛵ Sailing Ocean','sailing'),
    travel('tp-frost','❄ Frost Cave','frost'),
    travel('tp-main','↩ Main Map','village')
  ));
  const place = el('select', { id: 'ownerPlace' }); for (const p of c.places()) place.appendChild(el('option', { value: p.id, textContent: p.name })); isolateKeys(place);
  panel.appendChild(row(place, act('tpb', 'Go building', () => c.teleportPlace(place.value))));
  // Cross-world teleport is Owner-only. Unlike local cheat gating, the
  // multiplayer relay ALSO validates the passphrase before listing anyone.
  // Password is never stored, echoed to logs, or embedded into network URLs.
  let unsubscribeOwner=()=>{};
  if(env.hooks?.ownerPlayerEvents){
    panel.appendChild(sec('Teleport to online player (Owner only)'));
    const ownerPass=el('input',{id:'ownerServerPass',type:'password',
      autocomplete:'off',maxLength:128,placeholder:'Owner server passphrase',
      ariaLabel:'Owner server passphrase'});
    isolateKeys(ownerPass);
    const connect=el('button',{type:'button',textContent:'Verify Owner access'});connect.dataset.cheat='player-auth';
    const refresh=el('button',{type:'button',textContent:'Refresh players'});refresh.dataset.cheat='player-refresh';
    const playerSelect=el('select',{id:'ownerOnlinePlayer',ariaLabel:'Choose online player'});isolateKeys(playerSelect);
    const goPlayer=el('button',{type:'button',textContent:'Teleport beside player'});goPlayer.dataset.cheat='player-jump';
    playerSelect.disabled=true;goPlayer.disabled=true;
    const hint=el('div',{textContent:'Join any multiplayer world first. After verification, select a player from any public or private world. Only your character moves.',
      style:'font-size:11px;opacity:.75;line-height:1.4'});
    const ownerHelp=el('div',{style:'font-size:11px;color:#e8c868',textContent:'Owner server verification required to see online players.'});
    panel.appendChild(row(ownerPass,connect));
    panel.appendChild(row(refresh));
    panel.appendChild(row(playerSelect,goPlayer));
    panel.appendChild(hint);panel.appendChild(ownerHelp);
    const renderPlayers=players=>{
      const prior=playerSelect.value;
      playerSelect.replaceChildren();
      const valid=Array.isArray(players)?players.filter(p=>p&&typeof p.id==='string'&&p.id&&typeof p.world==='string'):[];
      if(!valid.length)playerSelect.appendChild(el('option',{value:'',textContent:'No other players online'}));
      for(const p of valid){
        const label=(p.name||'Player')+' · '+p.world+' · '+p.zone;
        playerSelect.appendChild(el('option',{value:p.id,textContent:label}));
      }
      if(valid.some(p=>p.id===prior))playerSelect.value=prior;
      playerSelect.disabled=!valid.length;goPlayer.disabled=!valid.length;
      ownerHelp.textContent=valid.length?valid.length+' player(s) available across Varnethryl.':'No other players online or Owner list not loaded.';
    };
    connect.addEventListener('click',()=>{
      const pass=ownerPass.value;ownerPass.value='';
      if(!pass){ownerHelp.textContent='Enter your Owner passphrase to verify with the game server.';return;}
      if(env.hooks.ownerLoginPlayer?.(pass))ownerHelp.textContent='Verifying with Varnethryl World Server…';
      else ownerHelp.textContent='Join a multiplayer world before verifying Owner access.';
    });
    refresh.addEventListener('click',()=>{
      if(env.hooks.ownerListPlayers?.())ownerHelp.textContent='Refreshing online player list…';
      else ownerHelp.textContent='Join a multiplayer world first.';
    });
    goPlayer.addEventListener('click',()=>{
      const id=playerSelect.value;
      if(!id){ownerHelp.textContent='Select an online player.';return;}
      if(env.hooks.ownerJumpToPlayer?.(id))ownerHelp.textContent='Traveling to selected player…';
      else ownerHelp.textContent='Join and verify Owner access first.';
    });
    unsubscribeOwner=env.hooks.ownerPlayerEvents(message=>{
      if(message?.type==='owner-auth'){
        ownerHelp.textContent=message.message||'Owner access response received.';
        if(message.ok)env.hooks.ownerListPlayers?.();
      }else if(message?.type==='owner-players')renderPlayers(message.players);
      else if(message?.type==='owner-error')ownerHelp.textContent=message.message||'Owner teleport unavailable.';
      else if(message?.type==='owner-arrived'){
        say('Arrived beside '+(message.target?.name||'player')+'.');
        ownerHelp.textContent='Teleport complete.';
        hide();
      }
    });
  }
  panel.appendChild(row(act('reset', 'Reset cheats', () => { c.reset(); return true; }), act('lock', 'Lock owner', () => {
    gate.lock(); c.reset();
    // reset() restores saved owner preferences; a true lock must override all of them.
    Object.assign(c.flags, createFlags());
    if (typeof env.onLocked === 'function') env.onLocked();
    // Do not retain an unlocked cheats object/DOM after signing out.
    ui.main?.dispose?.(); ui.main?.panel.remove(); ui.main = null; cheats = null;
    ui.fly.style.display = 'none'; ui.badge.style.display = 'none';
    hide(); return true;
  })));
  panel.appendChild(msg); isolateKeys(panel);
  function sync() {
    for (const k in btns) btns[k].b.classList.toggle('on', !!btns[k].get());
    spd.value = String(f.speedMul);
    ui.fly.style.display = f.fly ? 'flex' : 'none';
    ui.badge.style.display = (f.god || f.fly || f.noclip || f.infGold || f.speedMul !== 1 || !f.bump) ? 'block' : 'none';
    ui.badge.textContent = 'OWNER ' + (f.god ? 'GOD ' : '') + (f.fly ? 'FLY ' : '') + (f.noclip ? 'NOCLIP ' : '') + (f.speedMul !== 1 ? f.speedMul + '× ' : '');
  }
  function hide() { panel.style.display = 'none'; }
  document.body.appendChild(panel);
  return { panel, sync, hide, dispose(){unsubscribeOwner();}, show() { sync(); panel.style.display = 'block'; } };
}

function buildFly(flags) {
  const box = el('div', { id: 'ownerFly' }), mk = (txt, key) => {
    const b = el('button', { type: 'button', textContent: txt });
    b.addEventListener('pointerdown', (e) => { e.preventDefault(); e.stopPropagation(); try { b.setPointerCapture(e.pointerId); } catch (_) { /* ignore */ } flags[key] = 1; });
    for (const t of ['pointerup', 'pointercancel', 'lostpointercapture']) b.addEventListener(t, () => { flags[key] = 0; });
    return b;
  };
  box.append(mk('▲', 'up'), mk('▼', 'down')); document.body.appendChild(box); return box;
}

/* env: see cheats.createCheats; env.flags is the object main.js reads each frame. */
async function ensureUi(env) {
  const gate = getOwnerGate();
  if (!ui) {
    document.head.appendChild(el('style', { textContent: CSS }));
    ui = { gate, login: null, main: null, fly: buildFly(env.flags), badge: el('div', { id: 'ownerBadge' }) };
    document.body.appendChild(ui.badge);
  }
  return ui;
}
function showMain(env) {
  if (!cheats) { cheats = createCheats(Object.assign({}, env, { onChange: () => { if (ui.main) ui.main.sync(); } })); if (env.onReady) env.onReady(cheats); }
  if (!ui.main) ui.main = buildPanel(cheats, ui.gate, env);
  if (env.hooks && env.hooks.onOwner) env.hooks.onOwner();
  ui.main.show();
}
/* Gesture entry. Owner: toggle the panel. Not owner: local mode shows the passphrase prompt; server mode does nothing. */
export async function togglePanel(env) {
  const g = getOwnerGate();
  if (g.mode === 'server' && !(await g.isOwner())) return;
  await ensureUi(env);
  if (ui.main && ui.main.panel.style.display === 'block') { ui.main.hide(); return; }
  if (ui.login && ui.login.style.display === 'block') { ui.login.style.display = 'none'; return; }
  if (await ui.gate.isOwner()) { showMain(env); return; }
  if (ui.gate.mode === 'server') return;
  if (!ui.login) ui.login = buildLogin(ui.gate, () => showMain(env));
  ui.login.style.display = 'block'; const p = ui.login.querySelector('input'); if (p) p.focus();
}
