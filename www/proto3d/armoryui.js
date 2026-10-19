/* Equipment Armory UI (port of Varnethryl-Equipment-Armory). Pure view: renders armory.snapshot() and sends REQUESTS to armory.request();
   the engine (combat/armory.js) validates everything, so hiding/disabling here is only presentation. No 3D viewer / no gear mesh swapping. Runs in a shadow root (no CSS leaks). */
import { CSS, SPRITE } from './armorycss.js';
import { SLOTS, ENH_MAX, enhanceCost } from './combat/armory.js';
const RC = { common: '#adb1ba', uncommon: '#76c991', rare: '#79c8ff', epic: '#c589ff', legendary: '#f4c77a' };
const NAMES = { dmg: 'Damage', hp: 'Health', mp: 'Mana', sp: 'Stamina', def: 'Defense', atk: 'Attack', crit: 'Crit Rate', critDamage: 'Crit Damage', moveSpeed: 'Move Speed', shadow: 'Shadow' };
const FILTERS = ['All', 'Weapons', 'Armor', 'Accessories'];
const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
let host = null;
export function closeArmory() { if (host) { host.remove(); host = null; } }
export function openArmory(armory, opts) {
  closeArmory(); const o = opts || {}, pctUnit = (k, own) => (own ? '' : '%');
  host = document.createElement('div'); host.id = 'armoryHost'; host.style.cssText = 'position:fixed;inset:0;z-index:100000;overflow:auto;-webkit-overflow-scrolling:touch;background:#090915';
  const root = host.attachShadow({ mode: 'open' }); document.body.appendChild(host);
  root.innerHTML = '<style>' + CSS + '.xbtn{position:sticky;top:6px;float:right;margin:6px;z-index:5}.heroSig{display:grid;place-items:center;height:100%;min-height:200px;text-align:center;color:#dcb879;font-size:13px}.heroSig b{font-size:22px;color:#f3d9a0}</style>' + SPRITE +
    '<div class="root"><button type="button" class="thin-btn xbtn" id="x">Close ✕</button>' +
    '<div class="underbar"><div><span class="crumb">THE ARMORY</span><strong id="ttl">Equipment</strong></div><div class="under-actions"><span class="wallet"><span>◈ <b id="gold">0</b> <small>GOLD</small></span></span><button type="button" id="reset" class="thin-btn">Reset</button></div></div>' +
    '<main class="layout"><aside class="stats-panel panel"><div class="section-line"><span>BONUSES</span><span class="tiny-diamond">✦</span></div><div id="stats" class="stats-list"></div><div class="owner-info" id="note"></div></aside>' +
    '<section class="character-panel panel"><div class="character-header"><div><div class="overline" id="ov">LOADOUT</div><h1 id="hname">Hero</h1></div></div><div class="character-body"><div class="gear-column gear-left" id="gl"></div><div class="hero-stage"><div class="heroSig" id="sig"></div></div><div class="gear-column gear-right" id="gr"></div></div>' +
    '<div class="preset-panel"><div class="preset-title">LOADOUT PRESETS</div><div class="presets" id="pre"></div><p class="preset-help">Select to load · Save stores current gear</p></div></section>' +
    '<section class="inventory-panel panel"><div class="inventory-top"><div><div class="overline">YOUR COLLECTION</div><h2>Inventory <span id="cnt"></span></h2></div></div><div class="inventory-search"><svg><use href="#i-search"/></svg><input id="q" type="search" placeholder="Search items…" autocomplete="off"></div><div class="filters" id="flt"></div><div class="inventory-grid" id="grid"></div><div class="details" id="det"></div></section></main>' +
    '<div id="toast" class="toast" role="status"></div></div>';
  const $ = (id) => root.getElementById(id); let filter = 'All', sel = null, slot = 'weapon', tt = 0;
  const toast = (m) => { const t = $('toast'); t.textContent = m; t.classList.add('show'); clearTimeout(tt); tt = setTimeout(() => t.classList.remove('show'), 2400); };
  const ERR = { 'owner-only': 'Owner only', 'wrong-slot': 'Does not fit that slot', 'unknown-item': 'Item not available for this hero', 'not-enough-gold': 'Not enough gold', 'max-level': 'Enhancement cap reached', 'already-equipped': 'Already equipped', 'bad-preset': 'Empty preset' };
  const send = (r, okMsg) => { const res = armory.request(r); if (res.ok) { if (okMsg) toast(okMsg); } else toast(ERR[res.error] || 'Refused: ' + res.error); render(); return res; };
  const ico = (it) => '<svg aria-hidden="true"><use href="#i-' + it.icon + '"/></svg>';
  const fmt = (k, v) => (v > 0 ? '+' : '') + Math.round(v * 10) / 10 + pctUnit(k, armory.isOwnerHero);
  function render() {
    const s = armory.snapshot(), items = armory.items(), by = Object.fromEntries(items.map((i) => [i.id, i])), own = armory.isOwnerHero;
    $('ttl').textContent = (own ? 'Owner' : armory.key.replace(/^./, (c) => c.toUpperCase())) + ' Equipment'; $('hname').textContent = own ? 'The Sovereign' : armory.key.replace(/^./, (c) => c.toUpperCase());
    $('ov').textContent = own ? 'ROYAL LOADOUT · OWNER (display only, fixed rules)' : 'HERO LOADOUT · bonuses apply in combat'; $('gold').textContent = s.gold.toLocaleString();
    const st = armory.statsOf(); $('stats').innerHTML = Object.keys(st).length ? Object.entries(st).map(([k, v]) => '<div class="stat-row"><div class="stat-label">' + esc(NAMES[k] || k) + '</div><span class="stat-value" data-stat="' + k + '">' + fmt(k, v) + '</span></div>').join('') : '<div class="stat-row"><div class="stat-label">No bonuses equipped</div></div>';
    $('note').innerHTML = own ? '<b>OWNER ONLY</b><p>Owner gear is display/preview: the Owner\u2019s fixed rules (999,999 HP, 99,999 damage rules) are never changed by equipment.</p>' : '<b>HERO GEAR</b><p>Bonuses are percent points applied to this hero (damage, HP, MP, SP, DEF). Enhance adds +10% of an item\u2019s base per level (max +' + ENH_MAX + '). The model never changes.</p>';
    $('sig').innerHTML = '<div><b>' + esc(by[s.equipment.weapon] ? by[s.equipment.weapon].name : 'Unarmed') + '</b><br>' + esc(by[s.equipment.chest] ? by[s.equipment.chest].name : 'No armor') + '<br><small>Appearance is not swapped by gear</small></div>';
    for (const side of ['left', 'right']) { const c = $(side === 'left' ? 'gl' : 'gr'); c.replaceChildren(); for (const sl of SLOTS.filter((x) => x.side === side)) { const it = by[s.equipment[sl.id]], b = document.createElement('button'); b.type = 'button'; b.className = 'gear-slot' + (sl.id === slot ? ' selected' : ''); b.dataset.slot = sl.id; b.title = sl.name + ': ' + (it ? it.name : 'Empty'); b.innerHTML = '<svg><use href="#i-' + (it ? it.icon : sl.icon) + '"/></svg>' + (it ? '<i class="r-dot"></i>' : ''); if (it) b.style.borderColor = RC[it.rarity]; b.onclick = () => { slot = sl.id; sel = it ? it.id : null; render(); }; c.appendChild(b); } }
    const fl = $('flt'); fl.replaceChildren(); for (const f of FILTERS) { const b = document.createElement('button'); b.type = 'button'; b.className = 'filter-btn' + (f === filter ? ' active' : ''); b.textContent = f; b.onclick = () => { filter = f; render(); }; fl.appendChild(b); }
    const q = $('q').value.trim().toLowerCase(), list = items.filter((i) => (filter === 'All' || i.category === filter) && (!q || i.name.toLowerCase().includes(q) || i.rarity.includes(q)));
    $('cnt').textContent = list.length + ' / ' + items.length; const g = $('grid'); g.replaceChildren();
    for (const it of list) { const b = document.createElement('button'); b.type = 'button'; b.className = 'item-tile r-' + it.rarity + (sel === it.id ? ' selected' : ''); b.dataset.item = it.id; b.title = it.name + ' · ' + it.rarity; const lv = s.enh[it.id] || 0; b.innerHTML = ico(it) + (lv ? '<span class="lv">+' + lv + '</span>' : '') + (Object.values(s.equipment).includes(it.id) ? '<span class="eq">EQUIPPED</span>' : ''); b.onclick = () => { sel = it.id; slot = armory.slotFor(it, slot) || slot; render(); }; g.appendChild(b); }
    const d = $('det'), it = by[sel];
    if (!it) d.innerHTML = '<div class="detail-empty"><div>Select an item to see details and compare.</div></div>';
    else {
      const cs = armory.slotFor(it, slot), eqNow = Object.values(s.equipment).includes(it.id), old = by[s.equipment[cs]], a = armory.effective(it), b2 = old ? armory.effective(old) : {}, keys = Object.keys(Object.assign({}, a, b2)), lv = s.enh[it.id] || 0, next = lv < it.enhanceMax ? Object.fromEntries(Object.entries(it.stats).map(([k, v]) => [k, Math.round(v * (1 + (lv + 1) * 0.1) * 10) / 10])) : null;
      d.innerHTML = '<div class="details-top"><div class="details-icon" style="--rare:' + RC[it.rarity] + '">' + ico(it) + '</div><div class="details-name"><div class="overline">' + it.rarity.toUpperCase() + ' ' + (SLOTS.find((x) => x.id === cs) || { name: it.category }).name.toUpperCase() + '</div><h3>' + esc(it.name) + (lv ? ' +' + lv : '') + '</h3><small>' + (it.ownerOnly ? 'Owner Exclusive' : it.beth ? 'Optional · new model' : 'Eligible') + '</small>' + (eqNow ? '<span class="equipped-mark">✓ EQUIPPED</span>' : '') + '</div></div><p class="details-desc">' + esc(it.description) + '</p>' +
        '<div class="stat-compare">' + keys.map((k) => { const dl = (a[k] || 0) - (b2[k] || 0); return '<div class="compare-line"><span>' + esc(NAMES[k] || k) + '</span><b>' + fmt(k, a[k] || 0) + ' <span class="' + (dl > 0 ? 'plus' : dl < 0 ? 'minus' : '') + '">' + (!eqNow && dl ? '(' + (dl > 0 ? '+' : '') + Math.round(dl * 10) / 10 + ')' : '') + '</span></b></div>'; }).join('') + '</div>' +
        (next ? '<p class="detail-note" id="prev">Enhance preview +' + (lv + 1) + ': ' + Object.entries(next).map(([k, v]) => esc(NAMES[k] || k) + ' ' + fmt(k, v)).join(' · ') + ' · ' + enhanceCost(lv).toLocaleString() + ' G</p>' : '<p class="detail-note">Max enhancement</p>') + '<div class="detail-actions" id="act"></div>';
      const act = d.querySelector('#act'), add = (t, c, fn, dis) => { const bb = document.createElement('button'); bb.type = 'button'; bb.textContent = t; bb.className = c; bb.disabled = !!dis; bb.onclick = fn; act.appendChild(bb); };
      add(eqNow ? 'UNEQUIP' : 'EQUIP', 'primary-btn', () => eqNow ? send({ type: 'unequip', slot: Object.keys(s.equipment).find((k) => s.equipment[k] === it.id) }, 'Unequipped') : send({ type: 'equip', itemId: it.id, slot: cs }, it.name + ' equipped'));
      add(next ? 'ENHANCE · ' + enhanceCost(lv).toLocaleString() + ' G' : 'MAX', 'secondary-btn', () => send({ type: 'enhance', itemId: it.id }, 'Enhanced'), !next);
    }
    const pb = $('pre'); pb.replaceChildren(); s.presets.forEach((p, i) => { const u = document.createElement('div'); u.className = 'preset-unit'; const b = document.createElement('button'); b.type = 'button'; b.className = 'preset-card' + (s.active === i ? ' selected' : ''); b.dataset.preset = i; b.innerHTML = '<span>Preset ' + (i + 1) + '</span><small>' + (p ? '●' : '○') + '</small>'; b.onclick = () => send({ type: 'loadPreset', index: i }, 'Loaded Preset ' + (i + 1)); const sv = document.createElement('button'); sv.type = 'button'; sv.className = 'preset-save'; sv.dataset.save = i; sv.textContent = 'SAVE'; sv.onclick = () => send({ type: 'savePreset', index: i }, 'Saved Preset ' + (i + 1)); u.append(b, sv); pb.appendChild(u); });
  }
  $('q').addEventListener('input', render); $('x').onclick = closeArmory;
  $('reset').onclick = () => { if (root.getElementById('x') && confirm('Reset this hero\u2019s armory (gear and enhancement)?')) send({ type: 'reset' }, 'Reset'); };
  render(); return { render, root, host };
}
