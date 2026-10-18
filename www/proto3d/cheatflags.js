/* Per-frame cheat flags + helpers used by main.js. Zero dependencies and tiny: always loaded, never allocates after creation. */
export const FLY_MAX = 60, FLY_SPEED = 7, FLY_CLEAR = 2.5;
const clamp = (n, a, b) => Math.max(a, Math.min(b, n));
/* The flags object main.js reads each frame. Fields are plain numbers/booleans so the loop never allocates. */
export const createFlags = () => ({ god: false, fly: false, noclip: false, speedMul: 1, alt: 0, up: 0, down: 0, bump: true, infGold: false });
/* Effective collision bypass: noclip, or flying above FLY_CLEAR metres. */
export const passesWalls = (f) => f.noclip || (f.fly && f.alt > FLY_CLEAR);
/* Altitude integrator for the loop. dir is +1 up, -1 down, 0 hold. Returns the new altitude (no allocation). */
export function stepAltitude(f, dir, dt) {
  if (f.fly) return (f.alt = clamp(f.alt + dir * FLY_SPEED * dt, 0, FLY_MAX));
  return f.alt > 0 ? (f.alt = Math.max(0, f.alt - 12 * dt)) : 0;
}
