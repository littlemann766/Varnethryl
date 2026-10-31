/* Player prefs for the 3D game (camera view, zoom, sensitivity, graphics). Pure: no DOM, no Three.js, so node tests cover it.
 * Stored in localStorage under PREF_KEY as one small JSON object; anything missing or out of range falls back to the default. */
export const PREF_KEY = 'vn_p3d_prefs_v1';
export const ZOOM_MIN = 0.4, ZOOM_MAX = 1.7, SENS_MIN = 0.4, SENS_MAX = 2.5;
export const CAM_MODES = ['follow', 'free'], VIEWS = ['third', 'first'], QUALITIES = ['auto', 'high', 'balanced', 'low'];
export const DEFAULT_PREFS = Object.freeze({ view: 'third', zoom: 1, zoomSens: 1, lookSens: 1, quality: 'auto', shadows: true, showFps: false, fpsSet: false, combatSet: false, combat: true, camMode: 'follow' });
const clamp = (n, a, b) => Math.max(a, Math.min(b, n));
const num = (v, d) => (typeof v === 'number' && Number.isFinite(v) ? v : d);
export const clampZoom = (z) => clamp(num(z, 1), ZOOM_MIN, ZOOM_MAX);
export function sanitizePrefs(p) {
  const o = p && typeof p === 'object' ? p : {}, d = DEFAULT_PREFS;
  return { view: VIEWS.includes(o.view) ? o.view : d.view, zoom: clampZoom(o.zoom), zoomSens: clamp(num(o.zoomSens, 1), SENS_MIN, SENS_MAX), lookSens: clamp(num(o.lookSens, 1), SENS_MIN, SENS_MAX),
    quality: QUALITIES.includes(o.quality) ? o.quality : d.quality, shadows: o.shadows !== false, fpsSet: o.fpsSet === true, showFps: o.fpsSet === true && o.showFps === true, combatSet: o.combatSet === true, combat: o.combatSet === true ? o.combat === true : true, camMode: CAM_MODES.includes(o.camMode) ? o.camMode : d.camMode };
}
export function loadPrefs(storage) { try { return sanitizePrefs(JSON.parse(storage.getItem(PREF_KEY))); } catch (e) { return sanitizePrefs(null); } }
export function savePrefs(storage, p) { try { storage.setItem(PREF_KEY, JSON.stringify(sanitizePrefs(p))); return true; } catch (e) { return false; } }
/* Pixel-ratio ceiling for a quality level. dpr is the device pixel ratio. 'auto' keeps the adaptive behaviour (adaptive:true). */
export function qualityPlan(q, dpr) {
  const d = num(dpr, 1);
  if (q === 'high') return { ceil: Math.min(d, 2), adaptive: false };
  if (q === 'balanced') return { ceil: Math.min(d, 1), adaptive: false };
  if (q === 'low') return { ceil: Math.min(d, 0.7), adaptive: false };
  return { ceil: Math.min(d, 1.5), adaptive: true };
}
/* Segment (ax,az)->(bx,bz) against 2D colliders. Returns the smallest t in [0,1] where the segment first enters a collider grown by `margin`, or 1.
 * A collider the start point is already inside is skipped; one the start is only inside because of the margin uses margin 0, so hugging a wall still blocks it.
 * interior furniture (small interior colliders) is ignored: only walls and outdoor things block the camera. */
export function segmentClearT(cols, ax, az, bx, bz, margin) {
  let best = 1; const dx = bx - ax, dz = bz - az, m = margin || 0;
  for (let i = 0; i < cols.length; i++) {
    const c = cols[i];
    if (c.type === 'box') {
      if (c.interior && c.maxX - c.minX < 1.2 && c.maxZ - c.minZ < 1.2) continue;
      let mm = m; if (ax > c.minX - mm && ax < c.maxX + mm && az > c.minZ - mm && az < c.maxZ + mm) { if (ax > c.minX && ax < c.maxX && az > c.minZ && az < c.maxZ) continue; mm = 0; }
      let t0 = 0, t1 = best, ok = true;
      for (let k = 0; k < 2 && ok; k++) {
        const o = k ? az : ax, d = k ? dz : dx, lo = (k ? c.minZ : c.minX) - mm, hi = (k ? c.maxZ : c.maxX) + mm;
        if (Math.abs(d) < 1e-9) { if (o <= lo || o >= hi) ok = false; }
        else { let ta = (lo - o) / d, tb = (hi - o) / d; if (ta > tb) { const s = ta; ta = tb; tb = s; } if (ta > t0) t0 = ta; if (tb < t1) t1 = tb; if (t0 >= t1) ok = false; }
      }
      if (ok && t0 < best) best = t0;
    } else {
      if (c.interior && c.r < 0.7) continue;
      const fx = ax - c.x, fz = az - c.z, d0 = Math.hypot(fx, fz);
      let r = c.r + m; if (d0 < r) { if (d0 < c.r) continue; r = c.r; }
      const a = dx * dx + dz * dz; if (a < 1e-12) continue;
      const b = 2 * (fx * dx + fz * dz), cc = fx * fx + fz * fz - r * r, disc = b * b - 4 * a * cc; if (disc < 0) continue;
      const t = (-b - Math.sqrt(disc)) / (2 * a); if (t >= 0 && t < best) best = t;
    }
  }
  return best;
}

/* Behind-the-character follow: returns the new camYaw. The camera sits at +(sin,cos)*dist from the hero, so 'behind' the hero's travel (vx,vz) is yaw = atan2(-vx,-vz).
   Only eases while the hero is moving mostly away from the camera (>0.5 forward component), so strafing / turning in place never spins the view. Exponential damping, rate-capped: no wobble. */
export function followYaw(cur, vx, vz, dt, rate = 2.4, maxRate = 1.8) {
  const sp = Math.hypot(vx, vz); if (!(sp > 0.5) || !(dt > 0)) return cur;
  const fwd = (-vx * Math.sin(cur) - vz * Math.cos(cur)) / sp; if (fwd < 0.5) return cur;
  let d = Math.atan2(-vx, -vz) - cur; d = Math.atan2(Math.sin(d), Math.cos(d));
  const step = Math.max(-maxRate * dt, Math.min(maxRate * dt, d * (1 - Math.exp(-rate * dt)))); return cur + step;
}
