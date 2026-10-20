/* Functional Varnethryl 3D entry/menu. Gameplay/save state is left untouched. */
(function () {
  const panel = document.getElementById('vnMenu');
  if (!panel) return;
  const show = () => { panel.hidden = false; document.body.classList.add('vn-menu-open'); document.getElementById('vnEnter')?.focus(); };
  const hide = () => { panel.hidden = true; document.body.classList.remove('vn-menu-open'); };
  document.getElementById('vnEnter')?.addEventListener('click', hide);
  document.getElementById('vnMenuBtn')?.addEventListener('click', show);
  document.getElementById('vnHero')?.addEventListener('click', () => { hide(); document.querySelector('#heroes button.cur')?.click(); });
  document.getElementById('vnOptions')?.addEventListener('click', () => { hide(); document.getElementById('setBtn')?.click(); });
  // Prevent combat/movement hotkeys from firing while the front menu is open.
  addEventListener('keydown', e => {
    if (panel.hidden) { if ((e.key==='p'||e.key==='P') && !/INPUT|TEXTAREA|SELECT/.test(e.target?.tagName||'')) { e.preventDefault(); show(); } return; }
    if (e.key === 'Escape' || e.key === 'Enter') { e.preventDefault(); e.stopImmediatePropagation(); hide(); return; }
    if (e.key !== 'Tab') { e.preventDefault(); e.stopImmediatePropagation(); }
  }, true);
  // Keep the menu accessible until the player chooses to enter; no auto reset.
  show();
})();
