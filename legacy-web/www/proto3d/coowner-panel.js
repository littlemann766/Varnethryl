/* CoOwner rank controls. Verification is strictly server-side. This UI cannot
 * grant a role by changing a nickname, localStorage or a JavaScript flag.
 */
export function createCoOwnerPanel({login,resume,lock,list,jump,summonBoss,isOnline,getSavedToken,clearSavedToken}){
 const panel=document.getElementById('vnCoOwnerPanel');
 const openButton=document.getElementById('vnCoOwnerTools');
 if(!panel||!openButton)return {onEvent(){},onConnected(){},dispose(){}};
 const make=(tag,cls,text)=>{const el=document.createElement(tag);if(cls)el.className=cls;
   if(text!==undefined)el.textContent=text;return el;};
 const heading=make('div','vn-coowner-heading');
 const title=make('strong','','✦ Varnethryl · CoOwner');
 const close=make('button','','✕');close.type='button';close.setAttribute('aria-label','Close CoOwner tools');
 heading.append(title,close);
 const info=make('p','vn-coowner-desc','Private CoOwner access. Separate from the Owner password and cheats. No automatic logout — Lock CoOwner when finished.');
 const field=make('input','vn-coowner-password');field.type='password';field.maxLength=128;
 field.placeholder='CoOwner password';field.autocomplete='off';
 field.setAttribute('aria-label','Private CoOwner password');
 const signIn=make('button','','Unlock CoOwner');signIn.type='button';
 const loginRow=make('div','vn-coowner-login');loginRow.append(field,signIn);
 const status=make('div','vn-coowner-status','Locked. Join a Varnethryl multiplayer world to unlock.');
 status.setAttribute('role','status');
 const tools=make('div','vn-coowner-tools');tools.hidden=true;
 const abilities=make('p','vn-coowner-desc','CoOwner can summon all available bosses for local tests, find online testers, teleport, and use chat. Other Owner-only cheats remain restricted.');
 const refresh=make('button','','Refresh online players');refresh.type='button';
 const player=make('select','');player.setAttribute('aria-label','Select online player');
 const jumpBtn=make('button','','Teleport beside player');jumpBtn.type='button';
 const lockBtn=make('button','vn-coowner-lock','🔒 Lock CoOwner');lockBtn.type='button';
 const travelGroup=make('details','vn-rank-fold');
 travelGroup.open=true;
 const travelTitle=make('summary','','⌖ Player travel');
 const travelBody=make('div','vn-rank-fold-body');
 travelBody.append(refresh,player,jumpBtn);
 travelGroup.append(travelTitle,travelBody);
 const infoGroup=make('details','vn-rank-fold');
 const infoTitle=make('summary','','⚔ Rank privileges');
 const infoBody=make('div','vn-rank-fold-body');
 infoBody.append(abilities);
 const codeNote=make('p','vn-coowner-desc',
   'CoOwner sees online testers and may travel beside them. Owner-only commands and server settings are not available.');
 infoBody.appendChild(codeNote);
 infoGroup.append(infoTitle,infoBody);
 const bossGroup=make('details','vn-rank-fold');
 const bossTitle=make('summary','','⚔ Summon boss');
 const bossBody=make('div','vn-rank-fold-body');
 const bossChoice=make('select','');
 bossChoice.setAttribute('aria-label','Select boss to summon');
 for(const [key,label] of [
   ['titan','Ashen Titan'],['titan40','Ashen Titan — Giant'],
   ['vaelthryx','Balthrix — perimeter only'],['frosttroll_a','Frost Troll — Krag'],
   ['frosttroll_b','Frost Troll — Mog'],['hydra','Hydra — Mire only']
 ]){const opt=make('option','',label);opt.value=key;bossChoice.appendChild(opt);}
 const bossBtn=make('button','','Spawn selected boss');bossBtn.type='button';
 const bossNote=make('p','vn-coowner-desc',
   'Verified local test. One active boss at a time; Hydra requires Mire and Balthrix requires Town.');
 bossBody.append(bossChoice,bossBtn,bossNote);
 bossGroup.append(bossTitle,bossBody);
 tools.append(travelGroup,bossGroup,infoGroup,lockBtn);
 panel.replaceChildren(heading,info,loginRow,status,tools);
 let authorized=false;
 function setAuthorized(value){
   authorized=!!value;loginRow.hidden=authorized;tools.hidden=!authorized;
   openButton.textContent=authorized?'✦ CoOwner Tools':'🔒 CoOwner Tools';
   openButton.setAttribute('aria-label',authorized?'Open unlocked CoOwner tools':'Open CoOwner password entry');
 }
 function setPlayers(players){
   const before=player.value;player.replaceChildren();
   const entries=Array.isArray(players)?players.filter(p=>p&&typeof p.id==='string'):[];
   if(!entries.length){
     const opt=make('option','','No other players online');opt.value='';player.appendChild(opt);
   }
   for(const p of entries){
     const opt=make('option','',(p.name||'Player')+' · '+(p.world||'World')+' · '+(p.zone||'Map'));
     opt.value=p.id;player.appendChild(opt);
   }
   if(entries.some(p=>p.id===before))player.value=before;
   jumpBtn.disabled=!entries.length;
 }
 function open(){panel.hidden=false;openButton.setAttribute('aria-expanded','true');
   if(authorized)list();else field.focus();}
 function closePanel(){panel.hidden=true;openButton.setAttribute('aria-expanded','false');field.value='';}
 openButton.addEventListener('click',()=>panel.hidden?open():closePanel());
 close.addEventListener('click',closePanel);
 field.addEventListener('keydown',e=>{
   e.stopPropagation();if(e.key==='Enter')signIn.click();
   if(e.key==='Escape'){e.preventDefault();closePanel();}
 });
 field.addEventListener('keyup',e=>e.stopPropagation());
 field.addEventListener('pointerdown',e=>e.stopPropagation());
 player.addEventListener('keydown',e=>e.stopPropagation());
 signIn.addEventListener('click',()=>{
   const pass=field.value;field.value='';
   if(!isOnline()){status.textContent='Join a multiplayer world first.';return;}
   if(!pass){status.textContent='Enter the CoOwner password.';return;}
   status.textContent='Verifying CoOwner access with Varnethryl server…';
   if(!login(pass))status.textContent='Cannot reach the Varnethryl server.';
 });
 refresh.addEventListener('click',()=>{if(!list())status.textContent='No CoOwner server connection.';});
 bossChoice.addEventListener('keydown',e=>e.stopPropagation());
 bossBtn.addEventListener('click',()=>{
   if(!authorized){status.textContent='Unlock CoOwner first.';return;}
   status.textContent='Requesting verified boss summon…';
   if(!summonBoss(bossChoice.value))status.textContent='Connect to the game server first.';
 });
 jumpBtn.addEventListener('click',()=>{
   const id=player.value;if(!authorized||!id)return;
   status.textContent='Traveling to selected player…';
   if(!jump(id))status.textContent='Teleport not available.';
 });
 lockBtn.addEventListener('click',()=>{
   // Do not store the passphrase anywhere; the only persisted credential is
   // a server-issued random opaque bearer token, revoked by the server.
   clearSavedToken();lock();setAuthorized(false);setPlayers([]);
   status.textContent='CoOwner locked manually.';
 });
 function onEvent(message){
   if(!message||typeof message!=='object')return;
   if(message.type==='coowner-auth'){
     setAuthorized(!!message.ok);
     status.textContent=message.message|| (message.ok?'CoOwner unlocked.':'CoOwner locked.');
     if(message.ok)list();
   }else if(message.type==='coowner-players')setPlayers(message.players);
   else if(message.type==='coowner-error')status.textContent=String(message.message||'CoOwner action unavailable.');
   else if(message.type==='coowner-boss-result'){
     status.textContent=message.ok?'Boss summoned for local testing.':
       'Boss unavailable: one active at once; Hydra requires Mire and Balthrix requires Town.';
   }
   else if(message.type==='coowner-locked'){
     setAuthorized(false);setPlayers([]);status.textContent='CoOwner locked manually.';
   }else if(message.type==='coowner-arrived'){
     status.textContent='Arrived beside '+String(message.target?.name||'player')+'.';
     closePanel();
   }
 }
 function onConnected(online){
   if(!online){setAuthorized(false);setPlayers([]);
     status.textContent=getSavedToken()?'Disconnected — CoOwner will reverify on reconnection.':'Offline — join multiplayer to use CoOwner tools.';
   }else if(getSavedToken()){
     status.textContent='Restoring saved CoOwner authorization…';
     resume();
   }
 }
 setAuthorized(false);setPlayers([]);
 return {onEvent,onConnected,isAuthorized:()=>authorized,dispose:closePanel};
}
