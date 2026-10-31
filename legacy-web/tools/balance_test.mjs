// Weapon/armor balance pass: equal budgets per role, optional weapons never beat signatures, owner untouched.
import { LOADOUT, BALANCE_FRONT, BALANCE_BUDGET } from '../www/proto3d/combat/herokits.js';
import * as A from '../www/proto3d/combat/armory.js';
let ok = 0, bad = 0; const T = (n, c, d) => { c ? ok++ : bad++; console.log(c ? 'PASS' : 'FAIL', n, c ? '' : (d ?? '')); };
const B = (w, a) => 3 * w.dmgPct + a.hpPct + a.defPct + 0.5 * (a.mpPct + a.spPct);
for (const [k, L] of Object.entries(LOADOUT)) { const t = BALANCE_FRONT.includes(k) ? BALANCE_BUDGET.front : BALANCE_BUDGET.other, b = B(L.weapon, L.armor); T(k + ' budget ' + b.toFixed(3) + ' ~ ' + t, Math.abs(b - t) <= 0.02, b); }
const dm = Object.values(LOADOUT).map(L => L.weapon.dmgPct); T('signature weapon dmg within 5..8%', Math.min(...dm) >= 0.05 && Math.max(...dm) <= 0.08, dm);
const front = BALANCE_FRONT.map(k => LOADOUT[k].armor.hpPct + LOADOUT[k].armor.defPct), back = Object.keys(LOADOUT).filter(k => !BALANCE_FRONT.includes(k)).map(k => LOADOUT[k].armor.hpPct + LOADOUT[k].armor.defPct);
T('frontliners are the tankiest (min front hp+def > max back hp+def)', Math.min(...front) > Math.max(...back), [front, back]);
const items = [...new Map(Object.keys(LOADOUT).flatMap(k => A.catalogFor(k, false)).map(i => [i.id, i])).values()];
T('item catalog found', Array.isArray(items) && items.length > 10);
if (items) { const opt = items.filter(i => i.glb && i.slot === 'weapon'); T('optional new weapons (' + opt.length + ') cap at 8%', opt.length > 0 && opt.every(i => i.stats.dmg <= 8), opt.map(i => i.stats.dmg));
  const gen = items.filter(i => !i.ownerOnly && !i.glb && !String(i.id).startsWith('sig-')); T('generic gear stays modest (<= 6 per stat)', gen.every(i => Object.values(i.stats).every(v => v <= 6)), gen.map(i => i.id)); }
console.log(ok + ' pass, ' + bad + ' fail'); process.exit(bad ? 1 : 0);
