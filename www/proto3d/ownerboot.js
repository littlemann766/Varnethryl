/* Owner defaults for the 3D game: when the owner gate says yes, the active hero is maxed and god mode is ON unless the owner turned it off
 * (persisted under GOD_KEY). Non-owners never load this file. All the real checks live in ownergate.js; this only reacts to them. */
import { getOwnerGate } from './ownergate.js';
import { createCheats } from './cheats.js';
import { maxOwnerHero } from './ownermax.js';

export const GOD_KEY = 'vn_owner_god_v1', POLL_MS = 1500;
export const godPref = (storage) => { try { return storage.getItem(GOD_KEY) !== '0'; } catch (e) { return true; } };
export const UNLIM_KEY = 'vn_owner_unlim_v1';
export const unlimPref = (storage) => { try { return storage.getItem(UNLIM_KEY) !== '0'; } catch (e) { return true; } };
export const saveGodPref = (storage, on) => { try { storage.setItem(GOD_KEY, on ? '1' : '0'); } catch (e) { /* storage blocked: choice lasts this session only */ } };

let running = null;
/* env: the same env main.js gives the cheat panel ({flags, storage, ...}) plus onOwner(cheats). Resolves true if the owner path started. */
export function initOwner(env) {
  if (running) return running;
  const p = (async () => {
    if (!(await getOwnerGate().isOwner())) return false;
    const cheats = createCheats(env); if (env.onOwner) env.onOwner(cheats);
    if (godPref(env.storage)) cheats.setGod(true);
    if (unlimPref(env.storage)) cheats.setUnlimited(true);
    let last = null;
    const tick = () => {
      let id = null; try { id = JSON.parse(env.storage.getItem('guildbound_rpg_save_v1') || 'null'); } catch (e) { id = null; }
      const active = id && typeof id.active === 'number' ? id.active : -1;
      if (active === last && last !== null) return;
      const r = maxOwnerHero(env.storage); last = r ? r.id : active;
    };
    tick(); setInterval(tick, POLL_MS);
    return true;
  })();
  running = p; p.then((ok) => { if (!ok && running === p) running = null; });
  return p;
}
