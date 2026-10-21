/* Hidden-gesture entry for the owner cheat panel. This file is tiny and always loaded; it only adds listeners.
 * The panel code (cheatpanel.js, cheats.js, ownergate.js) is imported on first gesture, so a normal player never downloads or runs it.
 * Gestures: desktop  ` (backtick)  or  Ctrl+Shift+G.   Phone: 5 quick taps on the version label (#ver) in the top-left HUD. */
export const TAP_COUNT = 5, TAP_WINDOW_MS = 2500;
/* Pure tap counter (testable). Returns true on the 5th tap inside the window; resets itself after firing. */
export function createTapCounter(count, windowMs) {
  const n = count || TAP_COUNT, win = windowMs || TAP_WINDOW_MS; let taps = 0, first = 0;
  return (t) => { if (!taps || t - first > win) { taps = 0; first = t; } taps++; if (taps >= n) { taps = 0; return true; } return false; };
}
export function initCheatBoot(env) {
  let loading = false;
  const open = () => {
    if (loading) return; loading = true;
    import('./cheatpanel.js').then((m) => m.togglePanel(env)).catch((e) => { try { console.warn('owner panel unavailable', e && e.message); } catch (_) { /* ignore */ } }).finally(() => { loading = false; });
  };
  addEventListener('keydown', (e) => {
    const t = e.target, typing = t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.tagName === 'SELECT');
    if (typing) return;
    if (e.key === '`' || (e.ctrlKey && e.shiftKey && (e.key === 'G' || e.key === 'g'))) { e.preventDefault(); open(); }
  });
  // One consistent hidden gesture: five quick taps on the visible version,
  // whether the player is at the title screen or inside the game HUD.
  for (const id of ['ver', 'vnVersion', 'vnTitleVersion']) {
    const ver = document.getElementById(id);
    if (!ver) continue;
    const tap = createTapCounter();
    ver.addEventListener('pointerup', e => { if (tap(e.timeStamp || performance.now())) open(); });
  }
  return { open };
}
