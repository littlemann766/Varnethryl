// Armory engine tests: validation is server-trust (engine side), bonuses reach combat, owner isolation.
import { Armory, SLOTS, catalogFor, defaultsFor, enhanceCost, modelVariants } from '../www/proto3d/combat/armory.js';
import { KITS } from '../www/proto3d/combat/herokits.js';
import { CombatController } from '../www/proto3d/combat/controller.js';
let ok = 0, bad = 0; const T = (n, c) => { c ? ok++ : bad++; console.log(c ? 'PASS' : 'FAIL', n); };
const mem = () => { const m = {}; return { getItem: k => m[k] ?? null, setItem: (k, v) => { m[k] = String(v); } }; };
let gate = false; const mk = (hero = 'n:aldric_new', owner = false, st) => { const a = new Armory({ ownerOk: () => gate, storage: st || mem() }); a.setHero(hero, owner); return a; };
T('12 slots', SLOTS.length === 12 && new Set(SLOTS.map(s => s.id)).size === 12);
const a = mk(); const base = a.statsOf();
T('hero default = real herokits weapon+armor', a.s.equipment.weapon === 'sig-w-aldric' && a.s.equipment.chest === 'sig-a-aldric' && Math.abs(a.bonuses().dmgPct - KITS.aldric.weapon.dmgPct) < 1e-9 && Math.abs(a.bonuses().hpPct - KITS.aldric.armor.hpPct) < 1e-9 && Math.abs(a.bonuses().defPct - KITS.aldric.armor.defPct) < 1e-9);
T('every one of the 20 kit heroes has a signature weapon+armor in its catalog', Object.keys(KITS).every(k => catalogFor(k, false).some(i => i.id === 'sig-w-' + k) && catalogFor(k, false).some(i => i.id === 'sig-a-' + k)));
T('non-owner heroes never see owner items', Object.keys(KITS).every(k => catalogFor(k, false).every(i => !i.ownerOnly)));
let r = a.request({ type: 'equip', itemId: 'sovereign-end' }); T('non-owner cannot equip owner item (unknown for this hero)', !r.ok);
r = a.request({ type: 'equip', itemId: 'iron-helm' }); T('equip valid item', r.ok && a.s.equipment.head === 'iron-helm');
r = a.request({ type: 'equip', itemId: 'iron-helm', slot: 'chest' }); T('wrong slot refused', !r.ok && r.error === 'wrong-slot');
r = a.request({ type: 'equip', itemId: 'iron-helm' }); T('already equipped refused', !r.ok);
r = a.request({ type: 'equip', itemId: 'nope' }); T('unknown item refused', !r.ok);
r = a.request({ type: 'equip', itemId: 'plain-ring' }); r = a.request({ type: 'equip', itemId: 'plain-ring', slot: 'ring2' });
T('same ring cannot sit in both slots', a.s.equipment.ring1 !== 'plain-ring' || a.s.equipment.ring2 !== 'plain-ring' ? (a.s.equipment.ring1 === null || a.s.equipment.ring2 === null) : false);
T('garbage requests refused', !a.request(null).ok && !a.request({ type: 'x' }).ok && !a.request({ type: 'equip', slot: 'weapon' }).ok);
T('hero-restricted items refused for other heroes', !a.request({ type: 'equip', itemId: 'w-longbow' }).ok && mk('n:elira_new').request({ type: 'equip', itemId: 'w-longbow' }).ok);
const R = { elira: 'w-longbow', orin: 'w-war_spear', kael: 'w-arcane_staff', rowan: 'w-arcane_staff', talia: 'w-arcane_staff' };
T('Beth new weapons available as OPTIONAL items (Elira longbow, Orin spear, Kael/Rowan/Talia staff); originals stay default', Object.entries(R).every(([h, w]) => { const x = mk('n:' + h + '_new'); return catalogFor(h, false).some(i => i.id === w && i.optional) && x.s.equipment.weapon === 'sig-w-' + h; }));
T('7 new weapons exist with glb paths', ['frost_greatsword', 'war_axe', 'war_spear', 'arcane_staff', 'longbow', 'dual_kukri', 'round_shield'].every(w => catalogFor('nyx', false).concat(catalogFor('garruk', false), catalogFor('aldric', false), catalogFor('orin', false), catalogFor('elira', false), catalogFor('kael', false)).some(i => i.id === 'w-' + w && i.glb.endsWith(w + '.glb'))));
// enhancement + gold
const b = mk(); b.wallet = null; b._gold = 2000; const c0 = b.statsOf().dmg; r = b.request({ type: 'enhance', itemId: 'sig-w-aldric' });
T('enhance spends gold, raises stats 10% of base', r.ok && b._gold === 2000 - enhanceCost(0) && b.level('sig-w-aldric') === 1 && Math.abs(b.statsOf().dmg - c0 * 1.1) < 0.11);
b._gold = 10; T('enhance refused without gold', !b.request({ type: 'enhance', itemId: 'sig-w-aldric' }).ok && b.level('sig-w-aldric') === 1);
b._gold = 1e9; for (let i = 0; i < 9; i++) b.request({ type: 'enhance', itemId: 'sig-w-aldric' }); T('enhance cap +5', b.level('sig-w-aldric') === 5);
// presets
const p = mk(); p.request({ type: 'equip', itemId: 'cinderplate' }); p.request({ type: 'savePreset', index: 0 }); p.request({ type: 'unequip', slot: 'chest' }); T('unequip clears', !p.s.equipment.chest);
r = p.request({ type: 'loadPreset', index: 0 }); T('preset restores', r.ok && p.s.equipment.chest === 'cinderplate'); T('empty/bad preset refused', !p.request({ type: 'loadPreset', index: 2 }).ok && !p.request({ type: 'loadPreset', index: 9 }).ok && !p.request({ type: 'savePreset', index: -1 }).ok);
// owner gate is ENGINE-side
gate = false; const o = mk('n:owner', true); T('owner without gate: items not listed', o.items().length === 0);
r = o.request({ type: 'equip', itemId: 'dusk-reaver' }); T('owner item refused without the gate (client cannot bypass)', !r.ok && r.error === 'owner-only');
T('owner enhance refused without gate', !o.request({ type: 'enhance', itemId: 'sovereign-end' }).ok);
gate = true; const o2 = mk('n:owner', true); o2.key = ''; o2.setHero('n:owner', true);
T('owner with gate: items listed, defaults equipped', o2.items().length >= 12 && o2.s.equipment.weapon === 'sovereign-end');
r = o2.request({ type: 'equip', itemId: 'dusk-reaver' }); T('owner with gate can equip', r.ok && o2.s.equipment.weapon === 'dusk-reaver');
T('Owner bonuses are zero (fixed rules untouched)', o2.bonuses().owner === true && o2.bonuses().hpPct === 0 && o2.bonuses().dmgPct === 0);
gate = false; r = o2.request({ type: 'equip', itemId: 'sovereign-end' }); T('gate dropped mid-session: refused again', !r.ok && r.error === 'owner-only');
// storage is untrusted
const st = mem(); st.setItem('varn:armory:v1', JSON.stringify({ aldric: { equipment: { weapon: 'sovereign-end', head: 'iron-helm', chest: 'iron-helm', ring1: 'nope', bogus: 'iron-helm' }, enh: { 'iron-helm': 99, ghost: 3 }, presets: [{ weapon: 'sovereign-end', head: 'iron-helm' }, 7, null] } }));
const l = mk('n:aldric_new', false, st); T('tampered save re-validated (owner item, duplicate, bad slot dropped; enh clamped)', l.s.equipment.weapon === 'sig-w-aldric' && l.s.equipment.head === 'iron-helm' && l.s.equipment.chest !== 'iron-helm' && !l.s.equipment.bogus && l.level('iron-helm') === 5 && !('ghost' in l.s.enh) && l.s.presets[0].weapon === undefined && l.s.presets[1] === null);
const sv = mk('n:garruk_new', false, st); sv.request({ type: 'equip', itemId: 'iron-helm' }); const sv2 = mk('n:garruk_new', false, st); T('persists per hero', sv2.s.equipment.head === 'iron-helm' && mk('n:aldric_new', false, st).s.equipment.head === 'iron-helm');
// combat integration
const cc = new CombatController({ HS: 1.5 }); cc.setHero({ id: 'n:aldric_new', saber: false });
const hp0 = cc.res.max.hp, k0 = cc.kit.armor.hpPct; const g = mk(); g.request({ type: 'equip', itemId: 'obsidian-helm' }); cc.setGear(g.bonuses());
T('equipped gear changes the combat kit (copy, shared KITS untouched) and max HP', cc.kit.armor.hpPct > k0 && cc.res.max.hp > hp0 && KITS.aldric.armor.hpPct === k0 && cc.kit.weapon.dmgPct > KITS.aldric.weapon.dmgPct);
cc.setGear(null); T('clearing gear restores the kit', cc.kit.armor.hpPct === k0 && cc.res.max.hp === hp0);
const ow = new CombatController({ HS: 1.5 }); ow.setHero({ id: 'n:owner', saber: true }); const oh = ow.res.max.hp; ow.setGear({ dmgPct: 5, hpPct: 5, mpPct: 5, spPct: 5, defPct: 5 }); T('Owner HP/rules untouched by any gear object', ow.res.max.hp === oh && oh === ow.P.ownerHp);
T('refined variant is data only and optional (default stays)', modelVariants('aldric').default === true && modelVariants('aldric').refined.shipped === false && mk().s.variant === 'default' && mk().request({ type: 'variant', value: 'refined' }).ok && !mk().request({ type: 'variant', value: 'x' }).ok);
console.log(ok + ' pass, ' + bad + ' fail'); process.exit(bad ? 1 : 0);
