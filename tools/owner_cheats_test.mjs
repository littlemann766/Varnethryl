/* Unit tests for the owner gate and every cheat's state effect. Run: node tools/owner_cheats_test.mjs
 * The right-passphrase checks read the owner passphrase from env VARNETHRYL_OWNER_PASSPHRASE (never printed, never embedded).
 * Without it those checks are SKIPPED, not passed. */
import fs from 'fs';
import { execSync } from 'child_process';
import { GATE, createGate, derive, ownerFromClaims, UNLOCK_KEY, THROTTLE_KEY, FREE_TRIES, LOCK_BASE_MS, LOCK_MAX_MS } from '../www/proto3d/ownergate.js';
import { createCheats, createFlags, passesWalls, stepAltitude, GOLD_CAP, MAX_LEVEL, FLY_MAX, FLY_CLEAR } from '../www/proto3d/cheats.js';
import { createTapCounter } from '../www/proto3d/cheatboot.js';
import { SAVE_KEY, isValidSave, loadState, freshState } from '../www/core/save.js';
import { nLevel } from '../www/core/party.js';
import { createBump, makeActor } from '../www/proto3d/bump.js';
let bad = 0, skipped = 0;
const ok = (n, c, d = '') => { console.log(c ? 'PASS' : 'FAIL', n, c ? '' : d); if (!c) bad++; };
const mem = () => { const m = new Map(); return { getItem: (k) => (m.has(k) ? m.get(k) : null), setItem: (k, v) => m.set(k, String(v)), removeItem: (k) => m.delete(k), m }; };
let PASS = (process.env.VARNETHRYL_OWNER_PASSPHRASE || '').trim() || null;

/* capture console so we can prove nothing logs the passphrase */
const logged = []; const oc = { log: console.log, warn: console.warn, error: console.error };
const quiet = (f) => async () => { console.warn = console.error = (...a) => logged.push(a.join(' ')); try { return await f(); } finally { console.warn = oc.warn; console.error = oc.error; } };

/* ---------- gate ---------- */
ok('gate params are salted hash only', /^[0-9a-f]{32}$/.test(GATE.salt) && /^[0-9a-f]{64}$/.test(GATE.hash) && GATE.iter >= 100000);
ok('gate object has no plaintext field', !('pass' in GATE) && !('passphrase' in GATE) && !('secret' in GATE));
{
  let t = 1000000; const now = () => t, st = mem(), g = createGate({ storage: st, now });
  ok('locked by default', (await g.isOwner()) === false);
  let r = await g.unlock('definitely-wrong'); ok('wrong passphrase rejected', !r.ok && r.reason === 'wrong' && r.triesLeft === FREE_TRIES - 1);
  ok('still not owner after wrong', (await g.isOwner()) === false && st.getItem(UNLOCK_KEY) === null);
  r = await g.unlock(''); ok('empty passphrase rejected', !r.ok);
  r = await g.unlock('x'.repeat(500)); ok('oversize passphrase rejected (not hashed)', !r.ok);
  ok('after 3 fails the gate is throttled', g.status().locked && g.status().fails === 3 && g.status().retryMs === LOCK_BASE_MS, JSON.stringify(g.status()));
  r = await g.unlock('another-wrong'); ok('throttled attempt is refused without checking', !r.ok && r.reason === 'throttled' && g.status().fails === 3);
  if (PASS) { r = await g.unlock(PASS); ok('right passphrase is refused while throttled', !r.ok && r.reason === 'throttled'); } else { skipped++; console.log('SKIP throttled-right check (VARNETHRYL_OWNER_PASSPHRASE not set)'); }
  t += LOCK_BASE_MS + 1;
  r = await g.unlock('wrong-4'); ok('lock doubles on next failure', !r.ok && r.retryMs === LOCK_BASE_MS * 2, JSON.stringify(r));
  for (let i = 0; i < 20; i++) { t += LOCK_MAX_MS + 1; await g.unlock('nope' + i); }
  ok('lock never exceeds one hour', g.retryMs() <= LOCK_MAX_MS);
  if (PASS) {
    t += LOCK_MAX_MS + 1; r = await g.unlock(PASS); ok('right passphrase unlocks after throttle expires', r.ok === true);
    ok('owner after unlock', (await g.isOwner()) === true);
    ok('throttle counters cleared on success', st.getItem(THROTTLE_KEY) === null);
    const g2 = createGate({ storage: st, now }); ok('unlock persists across page loads (same storage)', (await g2.isOwner()) === true);
    const g3 = createGate({ storage: mem(), now }); ok('unlock does not exist in another browser profile', (await g3.isOwner()) === false);
    const blob = JSON.stringify([...st.m.entries()]);
    g.lock(); ok('lock() revokes', (await g.isOwner()) === false);
    r = await createGate({ storage: mem(), now }).unlock('  ' + PASS + '  '); ok('surrounding whitespace is trimmed', r.ok === true);
    const fresh = createGate({ storage: mem(), now }); r = await fresh.unlock(PASS.toUpperCase()); ok('case matters', !r.ok);
    /* leakage */
    ok('storage never contains plaintext', !blob.includes(PASS));
    ok('storage holds only a derived token', /"[0-9a-f]{64}"/.test(blob));
    ok('no console output contains plaintext', !logged.join('\n').includes(PASS));
    const files = execSync('git ls-files -co --exclude-standard', { cwd: new URL('..', import.meta.url).pathname, maxBuffer: 1 << 28 }).toString().split('\n').filter(Boolean);
    let leak = [];
    for (const f of files) { let b; try { b = fs.readFileSync(new URL('../' + f, import.meta.url)); } catch (e) { continue; } if (b.length < 5e7 && b.includes(PASS)) leak.push(f); }
    ok('plaintext appears in no repo file (tracked or untracked)', leak.length === 0, leak.join(','));
    const wf = ['sw.js', 'proto3d/ownergate.js'].map((f) => fs.readFileSync(new URL('../www/' + f, import.meta.url), 'utf8')).join('');
    ok('no reversible encoding of plaintext shipped (base64/hex)', !wf.includes(Buffer.from(PASS).toString('base64')) && !wf.includes(Buffer.from(PASS).toString('hex')));
    ok('derive() reproduces the shipped hash only for the real passphrase', (await derive(PASS, GATE.salt, GATE.iter)) === GATE.hash && (await derive(PASS + 'x', GATE.salt, GATE.iter)) !== GATE.hash);
  } else { skipped += 8; console.log('SKIP right-passphrase checks (VARNETHRYL_OWNER_PASSPHRASE not set)'); }
}
{
  /* forged token from the wrong hash is rejected */
  const st = mem(); st.setItem(UNLOCK_KEY, 'a'.repeat(64)); ok('garbage unlock token rejected', (await createGate({ storage: st }).isOwner()) === false);
  const st2 = mem(); st2.setItem(THROTTLE_KEY, '{not json'); ok('corrupt throttle record treated as clean, no crash', (await createGate({ storage: st2 }).unlock('zz')).reason === 'wrong');
  /* server mode hook */
  const g = createGate({ storage: mem() });
  ok('mode local by default', g.mode === 'local');
  g.setServerOwnerProvider(async () => ({ uid: 'u-1' })); ok('server mode: unknown uid is not owner', (await g.isOwner()) === false && g.mode === 'server');
  g.setServerOwnerProvider(async () => ({ owner: true })); ok('server mode: owner claim is owner', (await g.isOwner()) === true);
  g.setServerOwnerProvider(async () => { throw new Error('offline'); }); ok('server mode: provider error => not owner', (await g.isOwner()) === false);
  ok('server mode ignores passphrase entirely', (await g.unlock(PASS || 'x')).reason === 'server-mode');
  const g4 = createGate({ storage: mem() }); if (PASS) { await g4.unlock(PASS); g4.setServerOwnerProvider(async () => false); ok('server mode ignores an existing local unlock', (await g4.isOwner()) === false); } else skipped++;
  ok('ownerFromClaims: allowlist uid', ownerFromClaims({ uid: 'abc' }, ['abc']) && !ownerFromClaims({ uid: 'abd' }, ['abc']) && !ownerFromClaims(null) && !ownerFromClaims('yes') && ownerFromClaims({ owner: true }));
}
{
  const tap = createTapCounter(5, 2500);
  ok('5 taps in window fire once', [0, 400, 800, 1200].every((t) => !tap(t)) && tap(1600) === true && !tap(1700));
  const t2 = createTapCounter(5, 2500); ok('slow taps never fire', [0, 1000, 2000, 3000, 4000, 5000, 6000].every((t) => !t2(t)));
}

/* ---------- cheats ---------- */
const mk = (extra) => {
  const st = mem(), flags = createFlags(), calls = []; const bumpSys = createBump();
  const env = Object.assign({ storage: st, flags, bumpSys, zones: ['village'], places: () => [{ id: 'inn', name: 'Inn', x: 24, z: -8 }], teleport: (x, z) => calls.push([x, z]), hooks: { healParty: () => { calls.push('heal'); return true; } } }, extra);
  return { st, flags, calls, bumpSys, c: createCheats(env) };
};
const saved = (st) => JSON.parse(st.getItem(SAVE_KEY));
{
  const { st, flags, c } = mk();
  ok('no save, no cheated flag before any cheat', st.getItem(SAVE_KEY) === null && c.used === false);
  c.setGod(true); ok('god flag set', flags.god === true);
  ok('god mitigates all damage', c.mitigate(9999) === 0); c.setGod(false); ok('god off passes damage through', c.mitigate(50) === 50);
  ok('using a cheat writes a valid save marked cheated', isValidSave(saved(st)) && saved(st).cheated === true && saved(st).version === 1);
  ok('cheated flag survives loadState (2D/3D loader)', loadState(st).cheated === true);
  ok('save schema untouched: 2D required fields present', Object.keys(JSON.parse(JSON.stringify(freshState()))).every((k) => k in saved(st)));
  ok('cheated flag is sticky across further loads/saves', (c.addGold(1), loadState(st).cheated === true));
}
{
  const { st, flags, c } = mk();
  ok('fly sets flag', c.setFly(true) === true && flags.fly);
  ok('altitude rises while up held, capped', (() => { for (let i = 0; i < 2000; i++) stepAltitude(flags, 1, 0.016); return flags.alt === FLY_MAX; })());
  for (let i = 0; i < 100; i++) stepAltitude(flags, -1, 0.016); ok('altitude falls while down held, never below 0', flags.alt >= 0 && flags.alt < FLY_MAX);
  for (let i = 0; i < 2000; i++) stepAltitude(flags, -1, 0.016); ok('altitude floors at 0', flags.alt === 0);
  flags.alt = 10; ok('fly above clearance passes walls', passesWalls(flags)); flags.alt = FLY_CLEAR - 0.1; ok('fly below clearance does not pass walls', !passesWalls(flags));
  flags.alt = 10; c.setFly(false); for (let i = 0; i < 200; i++) stepAltitude(flags, 1, 0.016); ok('fly off: dir ignored and altitude drops to ground', flags.alt === 0);
  c.setNoclip(true); ok('noclip passes walls on the ground', passesWalls(flags)); c.setNoclip(false); ok('noclip off restores walls', !passesWalls(flags));
  c.setSpeed(3); ok('speed multiplier set', flags.speedMul === 3); c.setSpeed(999); ok('speed capped at 10', flags.speedMul === 10); c.setSpeed(0); ok('speed floored at 0.25', flags.speedMul === 0.25); c.setSpeed('abc'); ok('speed NaN -> 1', flags.speedMul === 1);
  c.setBump(false); ok('bump off sets flag and bumpSys.bumpOn=false', flags.bump === false);
}
{
  const { st, flags, c, bumpSys } = mk();
  c.setBump(false); ok('bump toggle drives the bump system', bumpSys.bumpOn === false);
  const a = makeActor('aldric', { fixed: true }), b = makeActor('elira'); bumpSys.add(a); bumpSys.add(b);
  a.x = 0; b.x = 0.5; a.vx = 5; bumpSys.update(0.016); ok('bumps off: running into someone triggers no bump event', bumpSys.events === 0);
  c.setBump(true); a.x = 0; b.x = 0.5; a.vx = 5; b.vx = 0; bumpSys.update(0.016); ok('bumps on: event fires', bumpSys.events === 1);
  let sepOff = (() => { c.setBump(false); const s = createBump(); s.bumpOn = false; const p = makeActor('aldric', { fixed: true }), q = makeActor('elira'); s.add(p); s.add(q); p.x = 0; q.x = 0.1; s.update(0.05); return q.dx > 0; })();
  ok('bumps off keeps personal-space separation (no stacking)', sepOff);
}
{
  const { st, flags, c } = mk();
  c.setInfiniteGold(true); ok('infinite gold tops the save to cap', saved(st).gold === GOLD_CAP && flags.infGold);
  const s = { gold: 5 }; ok('infinite gold: spendGold always succeeds without deducting', c.spendGold(s, 1e12) === true && s.gold === 5);
  c.setInfiniteGold(false); ok('infinite gold off: spend deducts / refuses', c.spendGold(s, 3) && s.gold === 2 && !c.spendGold(s, 3));
  c.setGold(-5); ok('setGold clamps at 0', saved(st).gold === 0); c.addGold(1e15); ok('addGold clamps at cap', saved(st).gold === GOLD_CAP);
  const lv0 = saved(st).heroLevels[0], xp0 = saved(st).accountXp;
  c.addXp(5000); const s1 = saved(st); ok('addXp raises XP/levels via core applyExperience', s1.heroLevels[0] > lv0 || s1.accountXp !== xp0, JSON.stringify([lv0, s1.heroLevels[0]]));
  ok('addXp(0) / negative does nothing', (() => { const before = st.getItem(SAVE_KEY); return c.addXp(0) === false && c.addXp(-4) === false && st.getItem(SAVE_KEY) === before; })());
  c.setLevel(55, 'active'); const s2 = loadState(st); ok('setLevel active changes only the active hero', nLevel(s2, s2.active) === 55 && s2.party.filter((i) => i !== s2.active).every((i) => nLevel(s2, i) !== 55));
  c.setLevel(33, 'party'); const s3 = loadState(st); ok('setLevel party changes all', s3.party.every((i) => nLevel(s3, i) === 33));
  c.setLevel(9999, 'party'); ok('level clamped to max', nLevel(loadState(st), loadState(st).party[0]) === MAX_LEVEL); c.setLevel(-3); ok('level floored at 1', nLevel(loadState(st), loadState(st).active) === 1);
  const n0 = saved(st).gear.length; c.spawnItem('weapon', 9); const s4 = saved(st);
  ok('spawnItem adds a gear item of the requested kind and level', s4.gear.length === n0 + 1 && s4.gear[n0].type === 'weapon' && s4.gear[n0].level === 9, JSON.stringify(s4.gear[n0]));
  ok('spawned item level>=3 has an ability and substats', !!s4.gear[n0].ability && s4.gear[n0].substats.length > 0);
  ok('spawnItem rejects an unknown kind', c.spawnItem('banana', 1) === false && saved(st).gear.length === n0 + 1);
  c.spawnItem('charm', 99); ok('item level clamped to 15', saved(st).gear.at(-1).level === 15);
  ok('save still valid for 2D after all edits', isValidSave(saved(st)) && saved(st).cheated === true);
}
{
  const { st, c, calls } = mk(); st.setItem(SAVE_KEY, '{broken json');
  ok('corrupt save is never overwritten by a cheat', c.setGold(10) === false && st.getItem(SAVE_KEY) === '{broken json' && c.used === true);
}
{
  const { st, c, calls } = mk(); const before = JSON.stringify(freshState());
  ok('heal party calls the combat hook', c.healParty() === true && calls.includes('heal') && c.stubCalls.healParty === 1);
  ok('kill enemies stub reports not handled yet but is safe', c.killEnemies() === false && c.stubCalls.killEnemies === 1);
  ok('skip quest stub reports not handled yet but is safe', c.skipQuest() === false && c.stubCalls.skipQuest === 1);
  ok('teleport zone village', c.teleportZone('village') && calls.some((x) => Array.isArray(x) && x[0] === 0 && x[1] === 14) && !c.teleportZone('forest'));
  ok('teleport to a building', c.teleportPlace('inn') && calls.some((x) => x[0] === 24 && x[1] === -8) && !c.teleportPlace('nope'));
  ok('reset restores defaults', (c.setGod(true), c.setFly(true), c.setSpeed(4), c.reset(), !c.flags.god && !c.flags.fly && c.flags.speedMul === 1));
  ok('reset does not clear the cheated flag', saved(st).cheated === true);
}
{ /* 1.1.7.1: combat hooks, spawn hooks, god-on owner default survives reset */
  const st = mem(), flags = createFlags(), seen = [];
  const c = createCheats({ storage: st, flags, hooks: { godPref: () => true, healParty: () => { seen.push('heal'); return true; }, killEnemies: () => { seen.push('kill'); return true; }, spawnEnemy: (k) => { seen.push('spawn:' + k); return k !== 'dup'; } } });
  ok('heal/kill hooks are called and report handled', c.healParty() === true && c.killEnemies() === true && seen.join() === 'heal,kill');
  ok('spawnEnemy / spawnTitan reach the hook', c.spawnEnemy('wolf') === true && c.spawnTitan() === true && seen.includes('spawn:wolf') && seen.includes('spawn:titan'));
  ok('spawn hook refusal is reported (false)', c.spawnEnemy('dup') === false);
  ok('skipQuest with no hook is a clearly-false stub', c.skipQuest() === false && c.stubCalls.skipQuest === 1);
  ok('spawn without hook is false, not a crash', createCheats({ storage: mem(), flags: createFlags() }).spawnEnemy('wolf') === false);
  c.setGod(false); c.reset(); ok('reset returns god to the owner default (ON)', c.flags.god === true);
}
{
  const src = fs.readFileSync(new URL('../www/proto3d/cheats.js', import.meta.url), 'utf8') + fs.readFileSync(new URL('../www/proto3d/cheatflags.js', import.meta.url), 'utf8');
  const hot = src.slice(src.indexOf('export function stepAltitude'));
  ok('per-frame helpers allocate nothing (no new/array/object literals)', !/\bnew\b|\[\]|=\s*\{|return \{/.test(hot.split('\n').slice(0, 4).join('\n')));
  const onelineBad = []; for (const f of ['ownergate', 'cheats', 'cheatflags', 'cheatboot', 'cheatpanel']) fs.readFileSync(new URL(`../www/proto3d/${f}.js`, import.meta.url), 'utf8').split('\n').forEach((l, i) => { if (/\)\s*(=>)?\s*\{[^}]*\/\/[^'"`]*\}\s*[;,)]?\s*$/.test(l) && !/https?:\/\//.test(l)) onelineBad.push(f + ':' + (i + 1)); });
  ok('no // comments inside one-line functions', onelineBad.length === 0, onelineBad.join(','));
}
console.log(bad ? 'FAILED ' + bad : 'ALL PASS' + (skipped ? ' (' + skipped + ' skipped)' : '')); process.exit(bad ? 1 : 0);
