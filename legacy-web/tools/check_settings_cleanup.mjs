/* Settings cleanup (boss-approved): 3 player tabs, hidden Owner & Dev tab, trimmed game menu, old prefs compatible.
 * Browser behaviour (tabs, every control, 5-tap, owner buttons hidden) is covered by tools/e2e_settings_cleanup.py. */
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { sanitizePrefs, DEFAULT_PREFS, loadPrefs, savePrefs } from '../www/proto3d/camprefs.js';
import { createTapCounter, TAP_COUNT } from '../www/proto3d/cheatboot.js';
const src = (p) => readFileSync(new URL('../' + p, import.meta.url), 'utf8');
// Old v1.5.33 prefs (FPS was saved true by default) stay valid; FPS now defaults off until chosen again.
const old = { view: 'first', zoom: 1.3, zoomSens: 1.6, lookSens: 0.8, quality: 'low', shadows: false, showFps: true, combatSet: true, combat: false, camMode: 'free' };
const s = sanitizePrefs(old);
for (const k of ['view', 'zoom', 'zoomSens', 'lookSens', 'quality', 'shadows', 'combat', 'camMode']) assert.equal(s[k], old[k], 'old pref kept: ' + k);
assert.equal(s.showFps, false, 'Show FPS defaults off, including old saves');
assert.equal(DEFAULT_PREFS.showFps, false);
assert.equal(sanitizePrefs({ fpsSet: true, showFps: true }).showFps, true, 'explicit Show FPS choice is remembered');
const m = new Map(), st = { getItem: (k) => m.get(k) ?? null, setItem: (k, v) => m.set(k, v) };
savePrefs(st, { ...s, fpsSet: true, showFps: true }); assert.equal(loadPrefs(st).showFps, true);
// 5-tap counter
const t = createTapCounter(); let fired = 0; for (let i = 0; i < TAP_COUNT; i++) fired += t(i * 100) ? 1 : 0; assert.equal(fired, 1, '5 quick taps fire once');
const slow = createTapCounter(); let f2 = 0; for (let i = 0; i < 5; i++) f2 += slow(i * 1000) ? 1 : 0; assert.equal(f2, 0, 'slow taps do not fire');
// Settings source
const set = src('www/proto3d/settings3d.js'), boot = src('www/proto3d/settingsboot.js'), nav = src('www/proto3d.html');
assert(set.includes("['graphics', 'Graphics'], ['controls', 'Controls'], ['gameplay', 'Gameplay']"), 'three player tabs');
assert(!/'Audio'/.test(set), 'no Audio tab yet');
assert(set.includes("'Camera sensitivity'") && set.includes('prefs.lookSens = v; prefs.zoomSens = v;'), 'one merged sensitivity slider');
assert(!set.includes("'Zoom (third person)'") && !set.includes("'Restore button layout'") && !set.includes("'Choose a character'") && !set.includes('Open Armory'), 'duplicates cut from Settings');
assert(set.includes("hiddenUnlocked ? [['hidden', 'Owner & Dev']]"), 'Owner & Dev tab only after unlock');
assert(boot.includes("closest('[data-vn-about]')") && boot.includes("e.key === '`'"), '5 taps on About version or backtick opens hidden tab');
assert(!src('www/proto3d/cheatpanel.js').includes('Quest skip'), 'quest skip no-op removed');
const actions = nav.slice(nav.indexOf('class="vn-quick-actions"'), nav.indexOf('class="vn-quick-sections"'));
assert.deepEqual([...actions.matchAll(/id="(\w+)"/g)].map((x) => x[1]), ['vnQuickResume', 'vnChooseCharacter', 'vnQuickTravel', 'vnQuickMp', 'vnOpenSettings', 'vnTitleBtn'], 'trimmed game menu');
assert(nav.includes('<div id="vnHiddenTools" hidden') && nav.indexOf('id="vnOwnerTools"') > nav.indexOf('id="vnHiddenTools"') && nav.indexOf('id="vnCoOwnerTools"') > nav.indexOf('id="vnHiddenTools"'), 'owner gate buttons hidden');
assert(!nav.includes('3D Model Gallery</a>'), 'gallery link removed from title');
assert(nav.includes('id="vnOpenArmory"') && nav.includes('id="vnGearReadout"'), 'Armory + gear in game menu');
console.log('PASS: settings cleanup (tabs, merged sensitivity, hidden Owner & Dev, trimmed menu, prefs compatible)');
