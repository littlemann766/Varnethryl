/* Functional Varnethryl 3D entry/menu. Gameplay/save state is left untouched. */
(function () {
  const panel = document.getElementById('vnMenu');
  if (!panel) return;
  // Android can suspend the WebView without navigation or destroy/recreate it
  // under memory pressure. Remember the last active 3D world independently
  // from the village-only legacy save, without modifying that save schema.
  const ACTIVE='vn.active3d.v1', MAX_AGE=30*24*60*60*1000;
  const read=()=>{try{const v=JSON.parse(localStorage.getItem(ACTIVE)||'null');
    return v&&v.active===true&&Number.isFinite(v.time)&&Date.now()-v.time>=0&&Date.now()-v.time<MAX_AGE?v:null;
  }catch{return null;}};
  let lastSession=read(),resumePending=!!lastSession&&!new URLSearchParams(location.search).has('nosave');
  let mode=lastSession?.mode==='multi'?'multi':'solo';
  let world=lastSession?.world||'',nickname=lastSession?.nickname||'';
  const save=()=>{
    if(!panel.hidden)return;
    const snap=window.__p3d?.sessionSnapshot?.();
    if(!snap||!Number.isFinite(snap.x)||!Number.isFinite(snap.z))return;
    try{localStorage.setItem(ACTIVE,JSON.stringify({active:true,time:Date.now(),mode,
      world:window.__p3d?.multiplayer?.room||world,nickname,snapshot:snap}));}catch{}
  };
  const setMode=(newMode,room='',name='')=>{
    mode=newMode==='multi'?'multi':'solo';
    if(room)world=room;if(name)nickname=name;save();
  };
  const clearSession=()=>{resumePending=false;lastSession=null;
    try{localStorage.removeItem(ACTIVE);}catch{}};
  window.__vnActiveSession={save,setMode,clear:clearSession};
  addEventListener('pagehide',save);
  document.addEventListener('visibilitychange',()=>{if(document.hidden)save();});
  setInterval(save,5000);
  document.addEventListener('varn:world-connected',e=>{
    setMode('multi',e.detail?.room,e.detail?.name);
  });
  document.addEventListener('varn:world-left',()=>setMode('solo'));

  const show = () => { document.getElementById('vnQuickMenu')?.setAttribute('hidden', ''); document.getElementById('vnMenuBtn')?.setAttribute('aria-expanded', 'false'); panel.classList.remove('vn-multiplayer-selecting'); const mp=document.getElementById('vnMpTitleLobby');if(mp)mp.hidden=true;panel.hidden = false; document.body.classList.add('vn-menu-open'); document.getElementById('vnEnter')?.focus(); };
  const hide = () => { panel.hidden = true; document.body.classList.remove('vn-menu-open'); };
  document.getElementById('vnEnter')?.addEventListener('click',()=>{hide();setMode('solo');save();});
  document.getElementById('vnMpEnterGame')?.addEventListener('click',()=>{hide();setMode('multi');save();});
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
      if(travelButton)travelButton.setAttribute('aria-expanded','false');document.getElementById('vnQuickMp')?.setAttribute('aria-expanded','false');}
  };
  const closeQuick=()=>toggleQuick(false);
  document.getElementById('vnMenuBtn')?.addEventListener('click',()=>toggleQuick(quick.hidden));
  document.getElementById('vnQuickResume')?.addEventListener('click',closeQuick);
  travelButton?.addEventListener('click',()=>{
    if(quick.hidden||!travelSection)return;
    travelSection.open=!travelSection.open;
    if(travelSection.open)travelSection.scrollIntoView({block:'nearest'});
  });
  const mpSection=document.getElementById('vnQuickMultiplayer'),mpButton=document.getElementById('vnQuickMp');
  mpButton?.addEventListener('click',()=>{
    if(quick.hidden||!mpSection)return;
    mpSection.open=!mpSection.open;mpButton.setAttribute('aria-expanded',String(mpSection.open));
    if(mpSection.open)mpSection.scrollIntoView({block:'nearest'});
  });
  // Gear readout + Armory (moved here from Settings).
  const gearSection=document.getElementById('vnQuickGear'),gearOut=document.getElementById('vnGearReadout');
  const gearSync=()=>{if(!gearOut)return;const F=window.__p3d&&window.__p3d.fight,kit=F&&F.cc&&F.cc.kit;
    if(!kit||!kit.weapon){gearOut.textContent=F&&F.on?'This hero uses the generic kit.':'Start Fight mode to see the active hero\u2019s weapon, armor and skills.';return;}
    const w=kit.weapon,a=kit.armor||{},pc=v=>'+'+Math.round(v*100)+'%';
    const st=[a.hpPct&&'HP '+pc(a.hpPct),a.mpPct&&'MP '+pc(a.mpPct),a.spPct&&'SP '+pc(a.spPct),a.defPct&&'DEF '+pc(a.defPct)].filter(Boolean).join(' \u00b7 ');
    gearOut.textContent='';for(const [h,t] of [['Weapon',w.name+' (damage '+pc(w.dmgPct)+')'],['Armor',(a.name||'')+(st?' \u2014 '+st:'')],['Skills',(kit.skills||[]).map(x=>x.name).join(' \u00b7 ')]]){
      const d=document.createElement('div'),b=document.createElement('b');b.textContent=h+': ';d.append(b,t);gearOut.appendChild(d);}};
  gearSection?.addEventListener('toggle',()=>{if(gearSection.open)gearSync();});
  document.getElementById('vnOpenArmory')?.addEventListener('click',async()=>{
    const F=window.__p3d&&window.__p3d.fight;
    if(!F||!F.armory){if(gearOut)gearOut.textContent='Start Fight mode first to open the Armory (Settings \u203a Gameplay \u203a Combat).';return;}
    closeQuick();const m=await import('./armoryui.js');m.openArmory(F.armory);
  });
  document.getElementById('vnQuickClose')?.addEventListener('click',closeQuick);
  document.getElementById('vnTitleBtn')?.addEventListener('click',()=>{
    closeQuick();clearSession();window.__p3d?.multiplayer?.disconnect?.();show();
  });
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
    if (e.key === 'Escape') { e.preventDefault(); e.stopImmediatePropagation();
      const lobby=document.getElementById('vnMpTitleLobby');
      if(lobby&&!lobby.hidden){lobby.hidden=true;panel.classList.remove('vn-multiplayer-selecting');return;}
      hide(); return; }
    // Let Enter and Space activate the focused menu button naturally.
    if (e.key === 'Enter' || e.key === ' ') return;
    if (e.key !== 'Tab') { e.preventDefault(); e.stopImmediatePropagation(); }
  }, true);
  // A brief Android leave/return must NEVER re-open the start menu. If the
  // WebView survived, nothing here runs again. If recreated, restore the game
  // automatically after the 3D world and player are ready.
  if(resumePending){
    hide();
    document.addEventListener('varn:game-ready',async()=>{
      const snap=lastSession?.snapshot;
      try{
        if(snap)await window.__p3d?.restoreSession?.(snap);
        if(!panel.hidden||!resumePending)return; // user deliberately opened title
        if(mode==='multi'){
          // Keep the game active while reconnecting; a server outage never
          // traps somebody in the title screen or erases their local progress.
          document.getElementById('vnMpEnterGame')?.click();
          window.__p3d?.multiplayer?.resume?.(world,nickname);
        }else document.getElementById('vnMpEnterGame')?.click();
      }catch(e){console.warn('Could not resume saved zone',e);
        if(resumePending&&panel.hidden)document.getElementById('vnMpEnterGame')?.click();
      }finally{resumePending=false;}
    },{once:true});
  }else show();
})();
