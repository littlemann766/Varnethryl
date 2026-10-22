/* Functional Varnethryl 3D entry/menu. Gameplay/save state is left untouched. */
(function () {
  const panel = document.getElementById('vnMenu');
  if (!panel) return;
  const show = () => { document.getElementById('vnQuickMenu')?.setAttribute('hidden', ''); document.getElementById('vnMenuBtn')?.setAttribute('aria-expanded', 'false'); panel.hidden = false; document.body.classList.add('vn-menu-open'); document.getElementById('vnEnter')?.focus(); };
  const hide = () => { panel.hidden = true; document.body.classList.remove('vn-menu-open'); };
  document.getElementById('vnEnter')?.addEventListener('click', hide);
  const quick=document.getElementById('vnQuickMenu');
  const sections=[...quick.querySelectorAll('details')];
  const travelSection=document.getElementById('vnQuickWorld');
  const travelButton=document.getElementById('vnQuickTravel');
  // A compact accordion: only one submenu can be open at a time.
  for(const section of sections)section.addEventListener('toggle',()=>{
    if(section.open)for(const other of sections)if(other!==section)other.open=false;
    if(travelButton)travelButton.setAttribute('aria-expanded',String(!!travelSection?.open));
  });
  const toggleQuick=(v=!quick.hidden)=>{
    quick.hidden=!v;
    document.getElementById('vnMenuBtn')?.setAttribute('aria-expanded',String(v));
    if(!v){for(const section of sections)section.open=false;
      if(travelButton)travelButton.setAttribute('aria-expanded','false');}
  };
  const closeQuick=()=>toggleQuick(false);
  document.getElementById('vnMenuBtn')?.addEventListener('click',()=>toggleQuick(quick.hidden));
  document.getElementById('vnQuickResume')?.addEventListener('click',closeQuick);
  travelButton?.addEventListener('click',()=>{
    if(quick.hidden||!travelSection)return;
    travelSection.open=!travelSection.open;
    if(travelSection.open)travelSection.scrollIntoView({block:'nearest'});
  });
  document.getElementById('vnQuickClose')?.addEventListener('click',closeQuick);
  document.getElementById('vnTitleBtn')?.addEventListener('click',()=>{closeQuick();show();});
  document.getElementById('vnChooseCharacter')?.addEventListener('click',()=>{closeQuick();document.querySelector('#heroes button.cur')?.click();});
  document.getElementById('vnApprovedBosses')?.addEventListener('click',()=>{closeQuick();if(window.__openBossRoster)window.__openBossRoster();else document.querySelector('#heroes button.cur')?.click();});
  document.getElementById('vnOpenSettings')?.addEventListener('click',()=>{closeQuick();document.getElementById('setBtn')?.click();});
  document.getElementById('vnCombatToggle')?.addEventListener('click',()=>{closeQuick();window.__p3d?.fightToggle?.();});
  document.getElementById('vnStatusOpen')?.addEventListener('click',()=>{closeQuick();document.getElementById('diagBtn')?.click();});
  document.getElementById('vnModelsToggle')?.addEventListener('click',()=>{closeQuick();document.getElementById('mdlBtn')?.click();});
  document.addEventListener('pointerdown',e=>{if(quick&&!quick.hidden&&!quick.contains(e.target)&&e.target?.id!=='vnMenuBtn')closeQuick();},true);
  document.getElementById('vnHero')?.addEventListener('click', () => { hide(); document.querySelector('#heroes button.cur')?.click(); });
  document.getElementById('vnOptions')?.addEventListener('click', () => { hide(); document.getElementById('setBtn')?.click(); });
  // Hobgoblin camps are discovered in the open world, not from the title menu.
  // Prevent combat//movement hotkeys from firing while the front menu is open.
  addEventListener('keydown', e => {
    if(panel.hidden){
      if(e.key==='Escape'&&quick&&!quick.hidden){e.preventDefault();e.stopImmediatePropagation();closeQuick();return;}
      if((e.key==='p'||e.key==='P')&&!/INPUT|TEXTAREA|SELECT/.test(e.target?.tagName||'')){e.preventDefault();show();}
      return;
    }
    if (e.key === 'Escape') { e.preventDefault(); e.stopImmediatePropagation(); hide(); return; }
    // Let Enter and Space activate the focused menu button naturally.
    if (e.key === 'Enter' || e.key === ' ') return;
    if (e.key !== 'Tab') { e.preventDefault(); e.stopImmediatePropagation(); }
  }, true);
  // Keep the menu accessible until the player chooses to enter; no auto reset.
  show();
})();
