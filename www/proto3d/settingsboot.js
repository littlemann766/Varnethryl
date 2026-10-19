/* Always-loaded tiny entry for the in-game Settings menu: applies saved prefs, adds the HUD button and Esc / M key, and lazy-loads settings3d.js on first open.
 * It also starts the owner defaults (ownerboot.js) but ONLY if this device holds an owner unlock token, so ordinary players download nothing extra. */
import { savePrefs } from './camprefs.js';

export const OWNER_TOKEN_KEY = 'vn_owner_unlock_v1';
/* env: {rig, prefs, storage, applyQuality(q), setShadows(on), fpsEl, cheatEnv, openCheatPanel()} */
export function applyPrefs(env) {
  const p = env.prefs;
  env.applyQuality(p.quality); env.setShadows(p.shadows); if (env.fpsEl) env.fpsEl.style.display = p.showFps ? '' : 'none';
}
export function persist(env) { savePrefs(env.storage, env.prefs); }
export function initSettings(env) {
  applyPrefs(env);
  let loading = false;
  const open = () => {
    if (loading) return; loading = true;
    import('./settings3d.js').then((m) => m.toggleSettings(env)).catch((e) => { try { console.warn('settings unavailable', e && e.message); } catch (_) { /* ignore */ } }).finally(() => { loading = false; });
  };
  const hud = document.getElementById('hud');
  if (hud) {
    const b = document.createElement('button'); b.id = 'setBtn'; b.type = 'button'; b.textContent = '⚙'; b.setAttribute('aria-label', 'Settings');
    b.style.cssText = 'pointer-events:auto;margin-left:6px;min-width:44px;min-height:34px;color:#fff;background:#0007;border:1px solid #fff4;border-radius:14px;font-size:18px;touch-action:manipulation;padding:2px 10px';
    b.addEventListener('click', open); hud.appendChild(b);
  }
  addEventListener('keydown', (e) => {
    const t = e.target, typ = t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.tagName === 'SELECT');
    if (typ || e.ctrlKey || e.metaKey || e.altKey) return;
    if (e.key === 'Escape' || e.key === 'm' || e.key === 'M') { e.preventDefault(); open(); }
  });
  let token = null; try { token = localStorage.getItem(OWNER_TOKEN_KEY); } catch (e) { token = null; }
  const ownerInit = () => import('./ownerboot.js').then((m) => m.initOwner(env.cheatEnv)).catch((e) => { try { console.warn('owner init failed', e && e.message); } catch (_) { /* ignore */ } });
  if (token) ownerInit();
  return { open, ownerInit };
}
