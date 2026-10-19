/* Owner cheats: pure state logic (no DOM, no Three.js) so node tests cover every effect.
 * The 3D loop (main.js) reads ONLY the plain `flags` object each frame; this module mutates it plus the shared save.
 * Any cheat use marks the save with cheated:true (sticky, additive: the 2D/3D save schema is otherwise unchanged).
 * Gating is NOT done here: cheatpanel.js only loads this after ownergate says the user is the owner. See README for the limits. */
import { SAVE_KEY, isValidSave, loadState, writeState, freshState } from '../core/save.js';
import { applyExperience } from '../core/party.js';
import { baseItem } from '../core/items.js';
import { HEROES } from '../data.js';
import { createFlags } from './cheatflags.js';

export const GOLD_CAP = 999999999, MAX_LEVEL = 80, MAX_ITEM_LEVEL = 15, SPEED_MIN = 0.25, SPEED_MAX = 10;
export { createFlags, passesWalls, stepAltitude, FLY_MAX, FLY_SPEED, FLY_CLEAR } from './cheatflags.js';
export const ITEM_KINDS = ['weapon', 'armor', 'charm'];
const clamp = (n, a, b) => Math.max(a, Math.min(b, n));
const fin = (n, d) => (typeof n === 'number' && Number.isFinite(n) ? n : d);

/* env: {storage, flags, bumpSys?, hooks?, places?:()=>[{id,name,x,z}], zones?:string[], teleport?:(x,z)=>void, onChange?:()=>void}
 * hooks (TODO attach points, called when combat/quests exist): healParty(), killEnemies(), skipQuest(), godMode(on). Each returns truthy if handled. */
export function createCheats(env) {
  const flags = env.flags || createFlags(), hooks = env.hooks || {}, storage = env.storage;
  const c = { flags, used: false, stubCalls: { healParty: 0, killEnemies: 0, skipQuest: 0 }, flagged: false };
  const changed = () => { if (env.onChange) env.onChange(c); };
  const readRaw = () => { try { return storage.getItem(SAVE_KEY); } catch (e) { return undefined; } };
  /* Load the live save (fresh if none). Returns null if the stored save is unreadable so we never clobber it. */
  function load() {
    const raw = readRaw(); if (raw === undefined) return null;
    if (raw === null) return freshState();
    try { if (isValidSave(JSON.parse(raw))) return loadState(storage); } catch (e) { return null; }
    return null;
  }
  function commit(s) { try { writeState(storage, s); return true; } catch (e) { return false; } }
  /* Sticky marker so the backend / leaderboards can exclude this save later. */
  c.markCheated = () => {
    c.used = true; const s = load(); if (!s) return false;
    if (s.cheated !== true) { s.cheated = true; s.cheatedAt = Date.now(); }
    s.cheatCount = fin(s.cheatCount, 0) + 1; c.flagged = commit(s); return c.flagged;
  };
  /* mutate(s) edits a loaded save; returns false to abort */
  function edit(mutate) {
    c.used = true; const s = load(); if (!s) return false;
    if (mutate(s) === false) return false;
    s.cheated = true; s.cheatedAt = fin(s.cheatedAt, Date.now()); s.cheatCount = fin(s.cheatCount, 0) + 1;
    c.used = true; c.flagged = commit(s); changed(); return c.flagged;
  }
  const flag = (name, on) => { flags[name] = !!on; c.markCheated(); changed(); return flags[name]; };

  c.setGod = (on) => { flag('god', on); if (hooks.godMode) hooks.godMode(!!on); return flags.god; };
  /* Attach point for combat: damage = c.mitigate(damage). God mode returns 0. */
  c.mitigate = (dmg) => (flags.god ? 0 : dmg);
  /* Owner-only unlimited MP/SP (combat reads flags.unlimited; the pref persists via hooks.unlimMode). Non-owners never get a cheats object. */
  c.setUnlimited = (on) => { flag('unlimited', on); if (hooks.unlimMode) hooks.unlimMode(!!on); return flags.unlimited; };
  /* Owner-only: no cooldowns while the Owner skin is active (combat gates on hero.owner too). Pref persists via hooks.nocdMode. */
  c.setNoCooldown = (on) => { flag('noCooldown', on); if (hooks.nocdMode) hooks.nocdMode(!!on); return flags.noCooldown; };
  c.setFly = (on) => { flag('fly', on); if (!on) { flags.up = 0; flags.down = 0; } return flags.fly; };
  c.setNoclip = (on) => flag('noclip', on);
  c.setSpeed = (m) => { flags.speedMul = clamp(fin(+m, 1), SPEED_MIN, SPEED_MAX); c.markCheated(); changed(); return flags.speedMul; };
  c.setBump = (on) => { flags.bump = !!on; if (env.bumpSys) env.bumpSys.bumpOn = !!on; c.markCheated(); changed(); return flags.bump; };
  c.setInfiniteGold = (on) => { flags.infGold = !!on; if (on) c.setGold(GOLD_CAP); else { c.markCheated(); changed(); } return flags.infGold; };
  /* Attach point for shops: if (!cheats.spendGold(state, cost)) refuse. Infinite gold never deducts. */
  c.spendGold = (s, cost) => { if (flags.infGold) return true; if (s.gold < cost) return false; s.gold -= cost; return true; };
  c.setGold = (n) => edit((s) => { s.gold = clamp(Math.floor(fin(+n, 0)), 0, GOLD_CAP); });
  c.addGold = (n) => edit((s) => { s.gold = clamp(Math.floor(s.gold + fin(+n, 0)), 0, GOLD_CAP); });
  c.addXp = (n) => edit((s) => { const a = Math.floor(fin(+n, 0)); if (a <= 0) return false; applyExperience(s, a); });
  /* scope 'active' (default) or 'party' */
  c.setLevel = (lv, scope) => edit((s) => {
    const L = clamp(Math.floor(fin(+lv, 1)), 1, MAX_LEVEL), ids = scope === 'party' ? s.party : [s.active];
    for (const id of ids) { s.heroLevels[id] = L; s.heroXp[id] = 0; if (!s.unlocked.includes(id)) s.unlocked.push(id); }
    if (scope === 'party') s.accountLevel = Math.max(s.accountLevel, L);
  });
  /* Adds a gear item to the inventory (not auto-equipped). heroId defaults to the active hero. */
  c.spawnItem = (kind, level, heroId) => {
    if (!ITEM_KINDS.includes(kind)) return false;
    return edit((s) => { const id = HEROES[heroId] ? heroId : s.active; s.gear.push(baseItem(kind, id, clamp(Math.floor(fin(+level, 0)), 0, MAX_ITEM_LEVEL))); });
  };
  /* Stubs: no HP/enemies/quests exist in 3D yet. TODO(combat): wire hooks.healParty / killEnemies; TODO(quests): hooks.skipQuest. */
  const stub = (name) => { c.stubCalls[name]++; c.markCheated(); const r = hooks[name] ? !!hooks[name]() : false; changed(); return r; };
  c.healParty = () => stub('healParty');
  c.killEnemies = () => stub('killEnemies');
  c.skipQuest = () => stub('skipQuest');

  /* Spawn enemies (combat3d): key = wolf|raider|wraith|skeleton|titan. Returns false when fight mode can't take it (e.g. a Titan is already alive). */
  c.spawnEnemy = (key) => { c.markCheated(); const r = hooks.spawnEnemy ? !!hooks.spawnEnemy(key) : false; changed(); return r; };
  c.spawnTitan = () => c.spawnEnemy('titan');

  c.zones = () => (env.zones || ['village']).slice();
  c.places = () => (env.places ? env.places() : []);
  c.teleportZone = (zone) => { if (!c.zones().includes(zone) || !env.teleport) return false; env.teleport(0, 14, zone); c.markCheated(); changed(); return true; };
  c.teleportPlace = (id) => { const p = c.places().find((q) => q.id === id); if (!p || !env.teleport) return false; env.teleport(p.x, p.z); c.markCheated(); changed(); return true; };
  /* Back to normal play (does not clear the cheated flag; that stays for the life of the save). */
  c.reset = () => { Object.assign(flags, createFlags()); if (hooks.godPref && hooks.godPref()) flags.god = true; if (hooks.unlimPref && hooks.unlimPref()) flags.unlimited = true; if (hooks.nocdPref && hooks.nocdPref()) flags.noCooldown = true; if (env.bumpSys) env.bumpSys.bumpOn = true; changed(); };
  return c;
}
