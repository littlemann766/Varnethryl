/* Owner-only: max out the ACTIVE hero in the shared save (level cap + the three equipped gear pieces at max level).
 * Only ever called from ownerboot.js after the owner gate says yes, so non-owner saves are never touched.
 * Idempotent: if the hero is already maxed nothing is written. Any real change keeps the sticky cheated flag exactly like cheats.js edit(). */
import { SAVE_KEY, isValidSave, loadState, writeState, freshState } from '../core/save.js';
import { advanceItem, baseItem } from '../core/items.js';
import { MAX_LEVEL, MAX_ITEM_LEVEL, ITEM_KINDS } from './cheats.js';

const fin = (n, d) => (typeof n === 'number' && Number.isFinite(n) ? n : d);
/* returns {changed, id} or null when the stored save is unreadable (it is never clobbered) */
export function maxOwnerHero(storage, now) {
  let raw; try { raw = storage.getItem(SAVE_KEY); } catch (e) { return null; }
  let s;
  if (raw === null) s = freshState();
  else { try { if (!isValidSave(JSON.parse(raw))) return null; s = loadState(storage); } catch (e) { return null; } }
  const id = s.active; let changed = false;
  if (!s.unlocked.includes(id)) { s.unlocked.push(id); changed = true; }
  if (s.heroLevels[id] !== MAX_LEVEL) { s.heroLevels[id] = MAX_LEVEL; s.heroXp[id] = 0; changed = true; }
  s.loadouts[id] = s.loadouts[id] || {};
  for (const kind of ITEM_KINDS) {
    let it = s.gear.find((g) => g.id === s.loadouts[id][kind]);
    if (!it) { it = baseItem(kind, id, 0); s.gear.push(it); s.loadouts[id][kind] = it.id; changed = true; }
    while (it.level < MAX_ITEM_LEVEL) { advanceItem(it); changed = true; }
  }
  if (!changed) return { changed: false, id };
  s.cheated = true; s.cheatedAt = fin(s.cheatedAt, (now || Date.now)()); s.cheatCount = fin(s.cheatCount, 0) + 1;
  try { writeState(storage, s); } catch (e) { return null; }
  return { changed: true, id };
}
