/* Always-loaded tiny entry for the in-game Settings menu: applies saved prefs, adds the HUD button and Esc / M key, and lazy-loads settings3d.js on first open.
 * It also starts the owner defaults (ownerboot.js) but ONLY if this device holds an owner unlock token, so ordinary players download nothing extra. */
import { savePrefs } from './camprefs.js';
import { createTapCounter } from './cheatboot.js';

export const OWNER_TOKEN_KEY = 'vn_owner_unlock_v2';
/* env: {rig, prefs, storage, applyQuality(q), setShadows(on), fpsEl, cheatEnv, openCheatPanel()} */
export function applyPrefs(env) {
  const p = env.prefs;
  env.applyQuality(p.quality); env.setShadows(p.shadows);
  if (env.fpsEl) {
    // #hud is always hidden in the 3D build, so float the FPS readout on its own when it is shown.
    if (p.showFps && env.fpsEl.parentElement !== document.body && env.fpsEl.closest('[hidden]')) { env.fpsEl.classList.add('vn-fps-float'); document.body.appendChild(env.fpsEl); }
    env.fpsEl.style.display = p.showFps ? '' : 'none';
  }
}
export function persist(env) { savePrefs(env.storage, env.prefs); }
export function initSettings(env) {
  applyPrefs(env);
  let loading = false;
  const open = (opts) => {
    if (loading) return; loading = true;
    import('./settings3d.js').then((m) => m.toggleSettings(env, opts)).catch((e) => { try { console.warn('settings unavailable', e && e.message); } catch (_) { /* ignore */ } }).finally(() => { loading = false; });
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
    else if (e.key === '`') { e.preventDefault(); open({ hidden: true }); }
  });
  // Hidden Owner & Dev tab: 5 quick taps on the visible About version line (Settings > Gameplay).
  // Delegated on document so it works for the line that settings3d.js builds later, with touch or mouse.
  const tap = createTapCounter();
  document.addEventListener('pointerup', (e) => {
    const t = e.target && e.target.closest && e.target.closest('[data-vn-about]');
    if (t && tap(e.timeStamp || performance.now())) open({ hidden: true });
  });
  let token = null; try { token = localStorage.getItem(OWNER_TOKEN_KEY); } catch (e) { token = null; }
  const ownerInit = () => import('./ownerboot.js').then((m) => m.initOwner(env.cheatEnv)).catch((e) => { try { console.warn('owner init failed', e && e.message); } catch (_) { /* ignore */ } });
  if (token) ownerInit();
  return { open, ownerInit };
}
