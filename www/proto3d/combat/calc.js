/* DamageCalculator: the only place damage is computed (UI never does). Reuses Lucian's enemyHurt() from www/core/combat.js when it loads
   (same formula as fallback). Owner lightsaber damage is flat 99,999 per hit; other weapons use the 2D crit rule (6% base, x1.55). */
import { SABER, UNARMED, PLAYER } from './data.js';
let L = null;
export async function loadLucian() { try { L = await import('../../core/combat.js'); return !!L.enemyHurt; } catch (e) { L = null; return false; } }
export const usingLucian = () => !!L;
const fallbackHurt = (atk, def, agi, rng) => { let h = Math.max(12, Math.round(atk * 1000 / (1000 + def))); if (rng() < agi * 0.005) h = 0; return h; };
export const DamageCalculator = {
  /* player -> enemy. weapon: 'saber' | 'unarmed'. Returns {dmg, crit} */
  playerHit(weapon, mult, rng) {
    if (weapon === 'saber') return { dmg: SABER.max, crit: false };   // flat 99,999 per hit: no variance, no crit, no ability multiplier
    const w = UNARMED, base = w.min + (w.max - w.min) * rng();
    const crit = rng() < PLAYER.crit; return { dmg: Math.round(base * mult * (crit ? PLAYER.critMult : 1)), crit };
  },
  /* enemy -> player (before dodge/block/shield, which the controller applies) */
  enemyHit(atk, def, agi, rng) { return (L && L.enemyHurt ? L.enemyHurt : fallbackHurt)(atk, def, agi, rng); },
};
