/* Node checks for camprefs.js (prefs + camera collision math) and ownermax.js (owner-only max stats). Run: node tools/owner_settings_test.mjs */
import { sanitizePrefs, loadPrefs, savePrefs, qualityPlan, clampZoom, segmentClearT, ZOOM_MIN, ZOOM_MAX, PREF_KEY, DEFAULT_PREFS } from '../www/proto3d/camprefs.js';
import { maxOwnerHero } from '../www/proto3d/ownermax.js';
import { SAVE_KEY, freshState, writeState, loadState } from '../www/core/save.js';
import { MAX_LEVEL, MAX_ITEM_LEVEL } from '../www/proto3d/cheats.js';
import fs from 'node:fs';
let bad = 0; const ok = (n, c, d) => { console.log((c ? 'PASS ' : 'FAIL ') + n, c ? '' : String(d ?? '')); if (!c) bad++; };
const mem = () => { const m = new Map(); return { getItem: (k) => (m.has(k) ? m.get(k) : null), setItem: (k, v) => { m.set(k, String(v)); }, removeItem: (k) => { m.delete(k); } }; };

ok('defaults on garbage', JSON.stringify(sanitizePrefs('x')) === JSON.stringify(DEFAULT_PREFS) && JSON.stringify(sanitizePrefs({ view: 'bad', zoom: 'a', quality: 9 })) === JSON.stringify(DEFAULT_PREFS));
ok('fight mode defaults ON; stored choice overrides', DEFAULT_PREFS.combat === true && sanitizePrefs({ combat: false }).combat === true && sanitizePrefs({ combat: false, combatSet: true }).combat === false && sanitizePrefs({ combat: true, combatSet: true }).combat === true);
ok('zoom clamps', clampZoom(99) === ZOOM_MAX && clampZoom(-5) === ZOOM_MIN && clampZoom(NaN) === 1);
const st = mem(); savePrefs(st, { view: 'first', zoom: 5, zoomSens: 2, lookSens: 0.1, quality: 'low', shadows: false, showFps: false });
const lp = loadPrefs(st); ok('prefs round-trip + clamp', lp.view === 'first' && lp.zoom === ZOOM_MAX && lp.lookSens === 0.4 && lp.quality === 'low' && lp.shadows === false && lp.showFps === false, JSON.stringify(lp));
ok('quality plan', qualityPlan('auto', 3).ceil === 1.5 && qualityPlan('auto', 3).adaptive && qualityPlan('high', 3).ceil === 2 && qualityPlan('balanced', 3).ceil === 1 && qualityPlan('low', 3).ceil === 0.7 && !qualityPlan('low', 3).adaptive);

const wall = { type: 'box', minX: -5, maxX: 5, minZ: 10, maxZ: 12 };
ok('segment blocked by wall (stops short)', segmentClearT([wall], 0, 5, 0, 20, 0.5) < 0.31 && segmentClearT([wall], 0, 5, 0, 20, 0.5) > 0.2, segmentClearT([wall], 0, 5, 0, 20, 0.5));
ok('segment clear when wall not in the way', segmentClearT([wall], 20, 5, 20, 20, 0.5) === 1);
ok('hugging a wall still blocks (start inside margin only)', segmentClearT([wall], 0, 9.8, 0, 20, 0.5) < 0.02, segmentClearT([wall], 0, 9.8, 0, 20, 0.5));
ok('start inside collider is skipped', segmentClearT([wall], 0, 11, 0, 20, 0.5) === 1);
const tree = { type: 'circle', x: 0, z: 10, r: 1 };
ok('circle blocks', segmentClearT([tree], 0, 0, 0, 20, 0.5) > 0.4 && segmentClearT([tree], 0, 0, 0, 20, 0.5) < 0.5);
ok('small interior furniture ignored', segmentClearT([{ type: 'box', minX: -.4, maxX: .4, minZ: 10, maxZ: 10.8, interior: 'x' }, { type: 'circle', x: 0, z: 10, r: 0.5, interior: 'x' }], 0, 0, 0, 20, 0.5) === 1);
ok('interior wall blocks', segmentClearT([{ type: 'box', minX: -5, maxX: 5, minZ: 10, maxZ: 10.4, interior: 'x' }], 0, 0, 0, 20, 0.5) < 0.5);

const s0 = mem(); const r0 = maxOwnerHero(s0, () => 1234);
let s = loadState(s0); const id = s.active;
ok('fresh save: hero maxed and marked cheated', r0.changed && s.heroLevels[id] === MAX_LEVEL && s.cheated === true && s.cheatedAt === 1234 && s.cheatCount === 1);
const eq = ['weapon', 'armor', 'charm'].map((k) => s.gear.find((g) => g.id === s.loadouts[id][k]));
ok('3 gear pieces equipped at max level', eq.every((g) => g && g.level === MAX_ITEM_LEVEL), JSON.stringify(eq.map((g) => g && g.level)));
const before = s0.getItem(SAVE_KEY), r1 = maxOwnerHero(s0);
ok('idempotent: second call writes nothing', !r1.changed && s0.getItem(SAVE_KEY) === before);
const s2 = mem(); const fs2 = freshState(); fs2.active = 1; fs2.heroLevels[1] = 7; writeState(s2, fs2); maxOwnerHero(s2);
const l2 = loadState(s2); ok('only the active hero changes', l2.heroLevels[1] === MAX_LEVEL && l2.heroLevels[0] === 1 && l2.gold === fs2.gold);
const bads = mem(); bads.setItem(SAVE_KEY, '{nope'); ok('corrupt save is never clobbered', maxOwnerHero(bads) === null && bads.getItem(SAVE_KEY) === '{nope');
ok('sticky cheated stays on repeated edits', (() => { const q = mem(); maxOwnerHero(q); const x = loadState(q); x.heroLevels[x.active] = 3; writeState(q, x); maxOwnerHero(q); return loadState(q).cheatCount >= 1 && loadState(q).cheated === true; })());

for (const f of ['camprefs.js', 'camrig.js', 'ownermax.js', 'ownerboot.js', 'settingsboot.js', 'settings3d.js']) {
  const src = fs.readFileSync(new URL('../www/proto3d/' + f, import.meta.url), 'utf8');
  ok(f + ': no // comments inside one-line functions', !/=>\s*[^\n{]*[^:'"`]\/\/[^\n]*$/m.test(src.split('\n').filter((l) => /=>\s*[^{\n]*\/\//.test(l) && !/^\s*\/\//.test(l)).join('\n')), f);
}
ok('only owner modules reference ownergate/cheats (settingsboot is token-gated)', !/from '\.\/(ownergate|cheats|ownerboot)\.js'/.test(fs.readFileSync(new URL('../www/proto3d/settingsboot.js', import.meta.url), 'utf8')));
console.log(bad ? 'FAILURES: ' + bad : 'ALL PASS'); process.exit(bad ? 1 : 0);
