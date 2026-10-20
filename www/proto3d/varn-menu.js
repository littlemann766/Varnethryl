/* Functional Varnethryl 3D entry/menu. Gameplay/save state is left untouched. */
(function () {
  const panel = document.getElementById('vnMenu');
  if (!panel) return;
  const show = () => { panel.hidden = false; document.body.classList.add('vn-menu-open'); document.getElementById('vnEnter')?.focus(); };
  const hide = () => { panel.hidden = true; document.body.classList.remove('vn-menu-open'); };
  document.getElementById('vnEnter')?.addEventListener('click', hide);
  const quick=document.getElementById('vnQuickMenu');
  const toggleQuick=(v=!quick.hidden)=>{quick.hidden=!v;document.getElementById('vnMenuBtn')?.setAttribute('aria-expanded',String(v));};
  const closeQuick=()=>toggleQuick(false);
  document.getElementById('vnMenuBtn')?.addEventListener('click',()=>toggleQuick(quick.hidden));
  document.getElementById('vnQuickClose')?.addEventListener('click',closeQuick);
  document.getElementById('vnTitleBtn')?.addEventListener('click',()=>{closeQuick();show();});
  document.getElementById('vnChooseCharacter')?.addEventListener('click',()=>{closeQuick();document.querySelector('#heroes button.cur')?.click();});
  document.getElementById('vnOpenSettings')?.addEventListener('click',()=>{closeQuick();document.getElementById('setBtn')?.click();});
  document.getElementById('vnCombatToggle')?.addEventListener('click',()=>{closeQuick();window.__p3d?.fightToggle?.();});
  document.getElementById('vnStatusOpen')?.addEventListener('click',()=>{closeQuick();document.getElementById('diagBtn')?.click();});
  document.getElementById('vnModelsToggle')?.addEventListener('click',()=>{closeQuick();document.getElementById('mdlBtn')?.click();});
  document.addEventListener('pointerdown',e=>{if(quick&&!quick.hidden&&!quick.contains(e.target)&&e.target?.id!=='vnMenuBtn')closeQuick();},true);
  document.getElementById('vnHero')?.addEventListener('click', () => { hide(); document.querySelector('#heroes button.cur')?.click(); });
  document.getElementById('vnOptions')?.addEventListener('click', () => { hide(); document.getElementById('setBtn')?.click(); });
  document.getElementById('vnCamp')?.addEventListener('click', async () => {
    hide();
    const game=window.__p3d;
    if(!game?.setZone)return;
    try{
      await game.setZone('town');
      const site={x:-323,z:-178};
      if(game.teleportTo)game.teleportTo(site.x+24,site.z+5);
      else if(game.state){game.state.heroX=site.x+24;game.state.heroZ=site.z+5;}
      else if(game.cheats?.teleport)game.cheats.teleport(site.x+24,site.z+5);
    }catch(e){console.warn('camp travel unavailable',e);}
  });
  // Prevent combat/movement hotkeys from firing while the front menu is open.
  addEventListener('keydown', e => {
    if(panel.hidden){
      if(e.key==='Escape'&&quick&&!quick.hidden){e.preventDefault();e.stopImmediatePropagation();closeQuick();return;}
      if((e.key==='p'||e.key==='P')&&!/INPUT|TEXTAREA|SELECT/.test(e.target?.tagName||'')){e.preventDefault();show();}
      return;
    }
    if (e.key === 'Escape' || e.key === 'Enter') { e.preventDefault(); e.stopImmediatePropagation(); hide(); return; }
    if (e.key !== 'Tab') { e.preventDefault(); e.stopImmediatePropagation(); }
  }, true);
  // Keep the menu accessible until the player chooses to enter; no auto reset.
  show();
})();
