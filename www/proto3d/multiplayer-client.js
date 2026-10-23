import { createMultiplayerChat } from './multiplayer-chat.js';
import { createCoOwnerPanel } from './coowner-panel.js';
// Interpolate across the -π/π seam. Animation clips never override this
// world-facing heading, including when a remote player turns while idle.
export function nextRemoteYaw(current,target,dt){
 if(!Number.isFinite(target)||!Number.isFinite(current))return Number.isFinite(target)?target:0;
 const delta=Math.atan2(Math.sin(target-current),Math.cos(target-current));
 return current+delta*Math.min(1,Math.max(0,dt)*20);
}
/* Optional multiplayer test presence for ALL Varnethryl world zones.
 * Town welcomes newcomers; the room's first player remains exactly where they were.
 * Remote movement is visual only. Damage, quests, loot and NPC AI stay single-player.
 */
export function createMultiplayer({THREE,scene,state,getZone,setZone,getHeroName,getSkinId,loadRemoteSkin,updateLevel,snapFollowers,camRig,miniMap,teleportNearPlayer,onOwnerTeleport}){
 const root=new THREE.Group();root.name='Varnethryl-Remote-Players';root.userData.keepAlways=true;scene.add(root);
 const peers=new Map();let socket=null,joined=false,selfId='',room='',lastSend=0,epoch=0,onlineCount=0,teleporting=false;
 let reconnectTimer=null,reconnectAttempts=0,keepConnected=false;
 const ownerListeners=new Set();
 const tellOwner=event=>{for(const cb of ownerListeners){try{cb(event);}catch(e){console.warn('Owner player selection listener failed',e);}}};
 const ownerCommand=(type,payload={})=>{
  if(!joined||!socket||socket.readyState!==WebSocket.OPEN){
    tellOwner({type:'owner-error',message:'Join a multiplayer world before using Owner teleport.'});
    return false;
  }
  socket.send(JSON.stringify({type,...payload}));return true;
 };
 const get=k=>{try{return localStorage.getItem(k)||'';}catch{return '';}};
 const del=k=>{try{localStorage.removeItem(k);}catch{};};
 const COOWNER_TOKEN_KEY='vn.coowner.session.v1',OWNER_TOKEN_KEY='vn.owner.server.token.v1';
 const put=(k,v)=>{try{localStorage.setItem(k,v);}catch{}};
 const DEFAULT_SERVER='wss://varnethryl-world-server-production.up.railway.app';
 const PUBLIC_WORLDS=[
   {code:'WORLD1',name:'Kingdom One'},
   {code:'WORLD2',name:'Kingdom Two'},
   {code:'WORLD3',name:'Kingdom Three'}
 ];
 const HTTP_SERVER='https://varnethryl-world-server-production.up.railway.app';
 const section=document.getElementById('vnQuickMultiplayer');
 const quickHost=document.getElementById('vnMpQuickLobby');
 const titleHost=document.getElementById('vnMpTitleLobby');
 const lobbies=[];
 const makeRoom=()=>Math.random().toString(36).slice(2,8).toUpperCase().padEnd(6,'X');
 let worlds=PUBLIC_WORLDS.map(w=>({...w,players:null,capacity:12})),refreshBusy=false;
 let currentName=get('vn.mp.name')||'Adventurer',currentCode=get('vn.mp.room')||'WORLD1';
 let currentStatus='Offline — single-player is available.';
 const status=message=>{currentStatus=message;for(const l of lobbies)l.status.textContent=message;};
 const coOwnerCommand=(type,payload={})=>{
   if(!joined||!socket||socket.readyState!==WebSocket.OPEN)return false;
   socket.send(JSON.stringify({type,...payload}));return true;
 };
 const coOwner=createCoOwnerPanel({
   login:pass=>coOwnerCommand('coowner-auth',{pass}),
   resume:()=>{const token=get(COOWNER_TOKEN_KEY);
     return /^[0-9a-f]{64}$/.test(token)&&coOwnerCommand('coowner-resume',{token});},
   lock:()=>coOwnerCommand('coowner-lock'),
   list:()=>coOwnerCommand('coowner-list'),
   jump:id=>coOwnerCommand('coowner-jump',{id}),
   isOnline:()=>joined&&socket?.readyState===WebSocket.OPEN,
   getSavedToken:()=>get(COOWNER_TOKEN_KEY),
   clearSavedToken:()=>del(COOWNER_TOKEN_KEY)
 });
 const chat=createMultiplayerChat({
   isOnline:()=>joined&&socket?.readyState===WebSocket.OPEN,
   sendChat:(text,to)=>{
     if(!joined||socket?.readyState!==WebSocket.OPEN)return false;
     socket.send(JSON.stringify({type:'chat',text,to}));return true;
   }
 });
 const makeLobby=(host,isTitle)=>{
   if(!host)return;
   host.innerHTML=`<div class="vn-mp-lobby">
    <label>Adventurer name<input class="vnMpName" maxlength="20" autocomplete="nickname" placeholder="Adventurer"></label>
    <div class="vn-mp-heading"><strong>Public worlds</strong><button type="button" class="vnMpRefresh">Refresh</button></div>
    <div class="vnMpWorlds" role="group" aria-label="Choose a Varnethryl multiplayer world"></div>
    <label>Private world code<input class="vnMpRoom" maxlength="12" autocapitalize="characters" placeholder="Your friend's code"></label>
    <div class="vn-mp-private-actions">
      <button type="button" class="vnMpJoin">Join code</button>
      <button type="button" class="vnMpCreate">Create private world</button>
      <button type="button" class="vnMpCopy">Copy code</button>
    </div>
    <button type="button" class="vnMpLeave">Leave multiplayer</button>
    <small class="vnMpStatus" aria-live="polite" role="status"></small>
    <small>One Varnethryl server, separate world instances. Select the SAME public world or private code to meet. Players already exploring are never moved.</small>
    ${isTitle?'<button type="button" class="vnMpBack">← Back to title</button>':''}
   </div>`;
   const l={host,isTitle,name:host.querySelector('.vnMpName'),room:host.querySelector('.vnMpRoom'),
     list:host.querySelector('.vnMpWorlds'),status:host.querySelector('.vnMpStatus')};
   l.name.value=currentName;l.room.value=currentCode;l.status.textContent=currentStatus;lobbies.push(l);
   l.name.addEventListener('input',()=>{currentName=l.name.value;});
   l.room.addEventListener('input',()=>{currentCode=l.room.value;});
   host.querySelector('.vnMpRefresh').addEventListener('click',refresh);
   host.querySelector('.vnMpJoin').addEventListener('click',()=>join(l.room.value,l));
   host.querySelector('.vnMpCreate').addEventListener('click',()=>join(makeRoom(),l));
   host.querySelector('.vnMpLeave').addEventListener('click',()=>{
     disconnect();document.dispatchEvent(new Event('varn:world-left'));
   });
   host.querySelector('.vnMpCopy').addEventListener('click',()=>{
     const code=joined?room:l.room.value.trim().toUpperCase();
     if(navigator.clipboard?.writeText)
       navigator.clipboard.writeText(code).then(()=>status('Copied world code '+code+'.')).catch(()=>status('Copy unavailable — share the code shown.'));
     else status('Share the world code shown in the box.');
   });
   host.querySelector('.vnMpBack')?.addEventListener('click',closeTitleLobby);
 };
 function closeTitleLobby(){
   if(titleHost)titleHost.hidden=true;
   document.getElementById('vnMenu')?.classList.remove('vn-multiplayer-selecting');
 }
 const showTitleLobby=()=>{
   if(!titleHost)return;
   titleHost.hidden=false;
   document.getElementById('vnMenu')?.classList.add('vn-multiplayer-selecting');
   refresh();
 };
 const selectCode=code=>{currentCode=code;for(const l of lobbies)l.room.value=code;};
 function drawWorlds(){
   for(const l of lobbies){
     l.list.replaceChildren();
     for(const w of worlds){
       const btn=document.createElement('button');btn.type='button';btn.className='vn-mp-world';
       const full=w.players!==null&&w.players>=w.capacity;
       btn.disabled=full;
       const desc=w.players===null?'Count unavailable':w.players+'/'+w.capacity+' online';
       btn.textContent=w.name+' · '+desc+(full?' · Full':'');
       if(joined&&room===w.code){btn.textContent+=' · Joined';btn.setAttribute('aria-current','true');}
       btn.addEventListener('click',()=>join(w.code,l));l.list.appendChild(btn);
     }
   }
 }
 async function refresh(){
   if(refreshBusy)return;refreshBusy=true;
   try{
     const resp=await fetch(HTTP_SERVER+'/rooms',{cache:'no-store'});
     if(!resp.ok)throw Error('HTTP '+resp.status);
     const data=await resp.json();
     if(!Array.isArray(data.worlds))throw Error('World list unavailable');
     const entries=new Map(data.worlds.filter(w=>typeof w.code==='string').map(w=>[w.code,w]));
     worlds=PUBLIC_WORLDS.map(w=>{
       const found=entries.get(w.code);
       return {...w,players:Number.isInteger(found?.players)?found.players:null,capacity:12};
     });
   }catch(e){
     worlds=PUBLIC_WORLDS.map(w=>({...w,players:null,capacity:12}));
     if(!joined)status('Server list unavailable. You may still try joining a world.');
   }finally{refreshBusy=false;drawWorlds();}
 }
 makeLobby(quickHost,false);makeLobby(titleHost,true);drawWorlds();
 document.getElementById('vnMultiplayer')?.addEventListener('click',showTitleLobby);
 section?.addEventListener('toggle',()=>{if(section.open)refresh();});
 document.getElementById('vnEnter')?.addEventListener('click',()=>{disconnect();closeTitleLobby();});
 function createGhost(p){
  const obj=new THREE.Group();obj.name='Other Player '+p.name;root.add(obj);
  const color=[0x638ce4,0x68c5aa,0xd4ad69,0xb181dd,0xdf8185,0x70b5ce][p.slot%6];
  const tunic=new THREE.MeshLambertMaterial({color,emissive:0x101019});
  const armor=new THREE.MeshLambertMaterial({color:0x41444d});
  const skin=new THREE.MeshLambertMaterial({color:0xc69b78});
  const add=(geo,mat,x,y,z)=>{const m=new THREE.Mesh(geo,mat);m.position.set(x,y,z);m.castShadow=false;obj.add(m);return m;};
  add(new THREE.CylinderGeometry(.36,.42,.94,9),tunic,0,1.05,0);
  add(new THREE.SphereGeometry(.24,10,7),skin,0,1.72,0);
  add(new THREE.BoxGeometry(.18,.82,.2),tunic,-.49,1.05,0);
  add(new THREE.BoxGeometry(.18,.82,.2),tunic,.49,1.05,0);
  const legA=add(new THREE.BoxGeometry(.21,.76,.24),armor,-.22,.34,0);
  const legB=add(new THREE.BoxGeometry(.21,.76,.24),armor,.22,.34,0);
  const canvas=document.createElement('canvas');canvas.width=256;canvas.height=64;
  const ctx=canvas.getContext('2d');
  if(ctx){ctx.fillStyle='#1a1725db';ctx.fillRect(0,8,256,48);ctx.strokeStyle='#e3bd7b';ctx.strokeRect(1,9,254,46);
   ctx.font='bold 25px sans-serif';ctx.textAlign='center';ctx.fillStyle='#fff0cd';ctx.fillText(String(p.name||'Player').slice(0,20),128,40,242);}
  const tex=new THREE.CanvasTexture(canvas),mat=new THREE.SpriteMaterial({map:tex,transparent:true,depthTest:false});
  const label=new THREE.Sprite(mat);label.scale.set(3.6,.9,1);label.position.y=2.65;obj.add(label);
  // Only the Varnethryl SERVER can assign CoOwner status. Client-provided
  // nicknames and local storage never affect this rank indicator.
  const coAura=new THREE.Mesh(new THREE.TorusGeometry(.65,.048,8,44),
    new THREE.MeshBasicMaterial({color:0xa967ff,transparent:true,opacity:.78,depthWrite:false}));
  coAura.rotation.x=Math.PI/2;coAura.position.y=1.96;coAura.visible=p.role==='coowner';
  obj.add(coAura);
  const fallback=new THREE.Group();fallback.name='Loading fallback';
  for(const part of [legA,legB,...obj.children.filter(o=>o.isMesh)]){
    if(part.parent===obj)fallback.add(part);
  }
  obj.add(fallback);
  const peer={id:p.id,obj,legA,legB,fallback,model:null,loadedSkin:'',pendingSkin:'',
    failedSkin:'',skinId:p.skin||'aldric',role:p.role||'player',coAura,moving:!!p.moving,
    zone:p.zone,x:p.x,y:p.y,z:p.z,yaw:p.yaw,walk:0,materials:[tunic,armor,skin,mat],tex};
  obj.rotation.order='YXZ';obj.position.set(p.x,p.y,p.z);obj.rotation.y=p.yaw;obj.visible=p.zone===getZone();return peer;
 }
 function disposeRemote(model){
   if(!model)return;
   model.traverse(o=>{
     o.geometry?.dispose?.();
     for(const m of (Array.isArray(o.material)?o.material:o.material?[o.material]:[])){
       for(const val of Object.values(m)){if(val?.isTexture)val.dispose();}
       m.dispose?.();
     }
   });
   model.parent?.remove(model);
 }
 async function showSkin(p){
   const requested=p.skinId;
   if(!p.obj.visible||!requested||p.loadedSkin===requested||p.pendingSkin===requested||p.failedSkin===requested)return;
   p.pendingSkin=requested;
   let model=null;
   try{model=await loadRemoteSkin(requested);}catch(e){console.warn('Remote GLB unavailable for',requested,e);}
   p.pendingSkin='';
   if(peers.get(p.id)!==p||p.skinId!==requested){
     disposeRemote(model);if(peers.get(p.id)===p)showSkin(p);return;
   }
   if(!model){p.failedSkin=requested;return;}
   disposeRemote(p.model);
   p.model=model;p.loadedSkin=requested;
   p.model.traverse(o=>{if(o.isMesh)o.castShadow=false;});
   p.model.position.set(0,0,0);
   p.obj.add(model);
   p.fallback.visible=false;
   const box=new THREE.Box3().setFromObject(model);
   if(Number.isFinite(box.max.y)&&Number.isFinite(box.min.y))
     p.obj.children.find(o=>o.isSprite)?.position.set(0,Math.min(10,Math.max(2,box.max.y-box.min.y+.65)),0);
 }
 function removePeer(id){
   const p=peers.get(id);if(!p)return;
   peers.delete(id);root.remove(p.obj);
   disposeRemote(p.model);
   p.fallback.traverse(o=>o.geometry?.dispose?.());
   for(const m of p.materials)m.dispose();p.tex.dispose();
 }
 function sync(p){
  if(!p||typeof p.id!=='string'||p.id===selfId||!Number.isFinite(p.x)||!Number.isFinite(p.z)||!Number.isFinite(p.y))return;
  if(!['town','wilds','frost','hydra','sailing','coliseum'].includes(p.zone))return;
  let e=peers.get(p.id);
  if(!e){e=createGhost(p);peers.set(p.id,e);}
  const prevX=e.x,prevZ=e.z,prevYaw=e.yaw;
  const incomingYaw=Number.isFinite(p.yaw)?p.yaw:prevYaw;
  const deltaX=p.x-prevX,deltaZ=p.z-prevZ;
  const walking=p.moving===true&&Math.hypot(deltaX,deltaZ)>.17;
  const yawChanged=Math.abs(Math.atan2(Math.sin(incomingYaw-prevYaw),Math.cos(incomingYaw-prevYaw)))>.025;
  // Follow network yaw when available; fall back to travel direction for
  // legacy clients that move but keep broadcasting a frozen heading.
  e.zone=p.zone;e.x=p.x;e.y=p.y;e.z=p.z;
  e.yaw=walking&&!yawChanged?Math.atan2(deltaX,deltaZ):incomingYaw;
  e.moving=p.moving===true;
  if(p.role){e.role=p.role;e.coAura.visible=p.role==='coowner';}
  const incoming=typeof p.skin==='string'?p.skin:'aldric';
  if(e.skinId!==incoming){
    e.skinId=incoming;e.failedSkin='';
    // GLB changes are processed without recreating the world or its camera.
    if(e.model){disposeRemote(e.model);e.model=null;e.loadedSkin='';e.fallback.visible=true;}
  }
  e.obj.visible=e.zone===getZone();
  if(e.obj.visible)showSkin(e);
 }
 function resetPeers(){for(const id of [...peers.keys()])removePeer(id);}
 function disconnect(){
  keepConnected=false;clearTimeout(reconnectTimer);reconnectTimer=null;
  epoch++;joined=false;selfId='';room='';onlineCount=0;
  const prev=socket;socket=null;if(prev)try{prev.close(1000,'Leave world');}catch{}
  resetPeers();chat.setOnline(false);coOwner.onConnected(false);
  status('Offline — single-player is available.');drawWorlds();
  tellOwner({type:'owner-players',players:[]});
 }
 function sendState(){
  if(!joined||teleporting||!socket||socket.readyState!==WebSocket.OPEN)return;
  const zone=getZone();if(!['town','wilds','frost','hydra','sailing','coliseum'].includes(zone))return;
  socket.send(JSON.stringify({type:'state',zone,x:state.heroX,y:state.dispY||state.heroY||0,
    z:state.heroZ,yaw:state.yaw||0,hero:getHeroName(),skin:getSkinId(),moving:state.moving===true}));
 }
 async function join(rawCode,lobby,entryMode='game'){
  const resuming=entryMode==='resume';
  const fromTitle=entryMode==='title'||(!resuming&&!!lobby?.isTitle&&!document.getElementById('vnMenu')?.hidden);
  const code=String(rawCode||'').trim().toUpperCase().replace(/[^A-Z0-9]/g,'').slice(0,12);
  const name=String(lobby?.name.value||currentName).trim().replace(/[^\p{L}\p{N} _-]/gu,'').slice(0,20);
  if(code.length<4||name.length<2){status('Enter a nickname (2+ letters) and a world code (4–12 characters).');return;}
  // Joining the selected world intentionally replaces the previous session;
  // it never changes game maps until the server confirms the new admission.
  disconnect();keepConnected=true;currentName=name;selectCode(code);
  for(const l of lobbies)l.name.value=name;
  put('vn.mp.name',name);put('vn.mp.room',code);
  const seq=++epoch;let s;
  try{s=new WebSocket(DEFAULT_SERVER);}catch{status('Could not reach the Varnethryl world server.');return;}
  socket=s;status('Connecting to '+code+'…');
  s.onopen=()=>{
   if(seq!==epoch)return;
   s.send(JSON.stringify({type:'join',entry:resuming?'resume':fromTitle?'title':'game',code,name,state:{
     zone:getZone(),x:state.heroX,y:state.heroY||0,z:state.heroZ,yaw:state.yaw||0,
     hero:getHeroName(),skin:getSkinId()
   },friendCode:chat.getFriendCode()}));
  };
  s.onmessage=async event=>{
   if(seq!==epoch)return;
   let m;try{m=JSON.parse(event.data);}catch{return;}
   if(m.type==='role-state'){
     const peer=peers.get(m.id);
     if(peer){peer.role=m.role==='coowner'?'coowner':m.role==='owner'?'owner':'player';
       peer.coAura.visible=peer.role==='coowner';}
     return;
   }
   if(m.type==='coowner-auth'){
     if(m.ok&&typeof m.token==='string'&&/^[a-f0-9]{64}$/.test(m.token))put(COOWNER_TOKEN_KEY,m.token);
     if(m.resumed&&!m.ok)del(COOWNER_TOKEN_KEY);
     coOwner.onEvent(m);return;
   }
   if(m.type==='coowner-players'||m.type==='coowner-error'||m.type==='coowner-locked'){
     if(m.type==='coowner-locked')del(COOWNER_TOKEN_KEY);
     coOwner.onEvent(m);return;
   }
   if(m.type==='chat-roster'){chat.setRoster(m.players);return;}
   if(m.type==='chat'){chat.receiveChat(m);return;}
   if(m.type==='chat-error'){chat.error(m.message);return;}
   if(m.type==='owner-auth'){
     if(m.ok&&typeof m.token==='string'&&/^[a-f0-9]{64}$/.test(m.token))put(OWNER_TOKEN_KEY,m.token);
     if(m.resumed&&!m.ok)del(OWNER_TOKEN_KEY);
     tellOwner(m);return;
   }
   if(m.type==='owner-locked'){del(OWNER_TOKEN_KEY);
     tellOwner({type:'owner-error',message:'Owner server access locked.'});return;}
   if(m.type==='owner-players'||m.type==='owner-error'){tellOwner(m);return;}
   if(m.type==='owner-jump'||m.type==='coowner-jump'){
     const coJump=m.type==='coowner-jump';
     teleporting=true;
     // Only our avatar moves. Target player's zone, camera, combat and save
     // are unaffected; the server already changed this Owner's room.
     try{
       const ok=await teleportNearPlayer(m.target);
       if(seq!==epoch)return;
       if(!ok){status('Unable to teleport beside this player.');
         if(coJump)coOwner.onEvent({type:'coowner-error',message:'Could not load the player map.'});
         else tellOwner({type:'owner-error',message:'Could not load the player map.'});return;}
       room=m.world;resetPeers();for(const peer of m.players||[])sync(peer);
       onlineCount=(m.players?.length||0)+1;
       teleporting=false;sendState();status((coJump?'CoOwner':'Owner')+' arrived beside '+m.target.name+' in '+room+'.');
       if(coJump)coOwner.onEvent({type:'coowner-arrived',target:m.target});
       else{onOwnerTeleport?.();tellOwner({type:'owner-arrived',target:m.target});}
       refresh();
      }catch(e){
         const error={type:coJump?'coowner-error':'owner-error',message:'Teleport failed: '+String(e?.message||e)};
         if(coJump)coOwner.onEvent(error);else tellOwner(error);
       }finally{teleporting=false;}
     return;
   }
   if(m.type==='error'){keepConnected=false;status('World unavailable: '+String(m.message||'cannot join'));s.close();return;}
   if(m.type==='welcome'){
    selfId=m.id;room=m.code;resetPeers();chat.setOnline(true,room,selfId);
    // Only this newcomer is sent to town; a player already in a cave,
    // on a boat, or in combat remains untouched by somebody else joining.
    if(m.spawn){
     try{
      if(getZone()!=='town')await setZone('town');
      if(seq!==epoch)return;
      state.heroX=m.spawn.x;state.heroZ=m.spawn.z;state.level=0;state.yaw=0;
      state.target=null;updateLevel();snapFollowers();camRig.snap=true;miniMap.invalidate();
     }catch(e){status('Town travel failed: '+String(e?.message||e));s.close();return;}
    }
    if(seq!==epoch)return;
    joined=true;reconnectAttempts=0;onlineCount=(m.players?.length||0)+1;
    coOwner.onConnected(true);
    const ownerToken=get(OWNER_TOKEN_KEY);
    if(/^[a-f0-9]{64}$/.test(ownerToken))ownerCommand('owner-resume',{token:ownerToken});
    for(const p of m.players||[])sync(p);
    status('In '+room+' · '+onlineCount+'/12 players. '+(m.spawn?'You entered town.':'Your location was preserved.'));
    document.dispatchEvent(new CustomEvent('varn:world-connected',{detail:{room,name}}));
    refresh();
    if(fromTitle){
      closeTitleLobby();
      document.getElementById('vnMpEnterGame')?.click();
    }else document.getElementById('vnQuickClose')?.click();
    return;
   }
   if(m.type==='joined'){onlineCount++;sync(m.player);status('World '+room+' · '+onlineCount+'/12 players');}
   if(m.type==='state')sync(m.player);
   if(m.type==='left'){onlineCount=Math.max(1,onlineCount-1);removePeer(m.id);status('World '+room+' · '+onlineCount+'/12 players');}
  };
  s.onerror=()=>{if(seq===epoch)status('Unable to reach Varnethryl World Server. Retry from the menu.');};
  s.onclose=()=>{
    if(seq!==epoch)return;
    joined=false;selfId='';socket=null;resetPeers();chat.setOnline(false);coOwner.onConnected(false);teleporting=false;
    tellOwner({type:'owner-players',players:[]});
    status('Connection lost. Continuing your game; reconnecting to '+code+'…');
    if(keepConnected){
      const delay=Math.min(30000,1200*2**Math.min(5,reconnectAttempts++));
      reconnectTimer=setTimeout(()=>{
        if(seq!==epoch||!keepConnected)return;
        join(code,{name:{value:name},isTitle:false},'resume');
      },delay);
    }else status('Disconnected. Solo play still works; choose a world to rejoin.');
    refresh();
  };
 }
 function update(dt,now){
  if(joined&&now-lastSend>=95){lastSend=now;sendState();}
  for(const p of peers.values()){
   const same=p.zone===getZone();p.obj.visible=same;
   if(!same)continue;
   showSkin(p);
   const dx=p.x-p.obj.position.x,dz=p.z-p.obj.position.z,dist=Math.hypot(dx,dz);
   if(dist>45)p.obj.position.set(p.x,p.y,p.z);else p.obj.position.lerp(new THREE.Vector3(p.x,p.y,p.z),Math.min(1,dt*9));
   p.obj.rotation.y=nextRemoteYaw(p.obj.rotation.y,p.yaw,dt);
   p.walk+=dt*(dist>.035?11:4);
   p.legA.rotation.x=dist>.035?Math.sin(p.walk)*.28:0;
   p.legB.rotation.x=-p.legA.rotation.x;
   if(p.model?.userData?.mixer){
     const act=p.model.userData.act||{};
     const moving=p.moving||dist>.08;
     if(act.walk&&act.walk!==act.idle)act.walk.setEffectiveWeight(moving?1:0);
     if(act.idle)act.idle.setEffectiveWeight(moving?0:1);
     p.model.userData.mixer.update(Math.min(dt,.1));
   }
  }
 }
 return {
  join,disconnect,refresh,update,
  resume:(code,name)=>join(code||currentCode,{name:{value:name||currentName},isTitle:false},'resume'),
  ownerLogin:pass=>ownerCommand('owner-auth',{pass}),
  ownerLock:()=>{del(OWNER_TOKEN_KEY);return ownerCommand('owner-lock');},
  ownerList:()=>ownerCommand('owner-list'),
  ownerJump:id=>ownerCommand('owner-jump',{id}),
  onOwnerEvent:callback=>{ownerListeners.add(callback);return ()=>ownerListeners.delete(callback);},
  get online(){return joined;},get room(){return room;},get playerCount(){return onlineCount;},
  dispose(){disconnect();chat.dispose();coOwner.dispose();ownerListeners.clear();root.parent?.remove(root);}
 };
}
