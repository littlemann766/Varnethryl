/* Optional multiplayer test presence for ALL Varnethryl world zones.
 * Town welcomes newcomers; the room's first player remains exactly where they were.
 * Remote movement is visual only. Damage, quests, loot and NPC AI stay single-player.
 */
export function createMultiplayer({THREE,scene,state,getZone,setZone,getHeroName,updateLevel,snapFollowers,camRig,miniMap}){
 const root=new THREE.Group();root.name='Varnethryl-Remote-Players';root.userData.keepAlways=true;scene.add(root);
 const peers=new Map();let socket=null,joined=false,selfId='',room='',lastSend=0,epoch=0,onlineCount=0;
 const get=k=>{try{return localStorage.getItem(k)||'';}catch{return '';}};
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
   host.querySelector('.vnMpLeave').addEventListener('click',disconnect);
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
  const peer={id:p.id,obj,legA,legB,zone:p.zone,x:p.x,y:p.y,z:p.z,yaw:p.yaw,walk:0,materials:[tunic,armor,skin,mat],tex};
  obj.position.set(p.x,p.y,p.z);obj.rotation.y=p.yaw;obj.visible=p.zone===getZone();return peer;
 }
 function removePeer(id){
  const p=peers.get(id);if(!p)return;
  root.remove(p.obj);p.obj.traverse(o=>o.geometry?.dispose?.());
  for(const m of p.materials)m.dispose();p.tex.dispose();peers.delete(id);
 }
 function sync(p){
  if(!p||typeof p.id!=='string'||p.id===selfId||!Number.isFinite(p.x)||!Number.isFinite(p.z)||!Number.isFinite(p.y))return;
  if(!['town','wilds','frost','hydra','sailing','coliseum'].includes(p.zone))return;
  let e=peers.get(p.id);
  if(!e){e=createGhost(p);peers.set(p.id,e);}
  e.zone=p.zone;e.x=p.x;e.y=p.y;e.z=p.z;e.yaw=Number.isFinite(p.yaw)?p.yaw:0;
  e.obj.visible=e.zone===getZone();
 }
 function resetPeers(){for(const id of [...peers.keys()])removePeer(id);}
 function disconnect(){
  epoch++;joined=false;selfId='';room='';onlineCount=0;
  const prev=socket;socket=null;if(prev)try{prev.close(1000,'Leave world');}catch{}
  resetPeers();status('Offline — single-player is available.');drawWorlds();
 }
 function sendState(){
  if(!joined||!socket||socket.readyState!==WebSocket.OPEN)return;
  const zone=getZone();if(!['town','wilds','frost','hydra','sailing','coliseum'].includes(zone))return;
  socket.send(JSON.stringify({type:'state',zone,x:state.heroX,y:state.dispY||state.heroY||0,z:state.heroZ,yaw:state.yaw||0,hero:getHeroName()}));
 }
 async function join(rawCode,lobby){
  const fromTitle=!!lobby?.isTitle&&!document.getElementById('vnMenu')?.hidden;
  const code=String(rawCode||'').trim().toUpperCase().replace(/[^A-Z0-9]/g,'').slice(0,12);
  const name=String(lobby?.name.value||currentName).trim().replace(/[^\p{L}\p{N} _-]/gu,'').slice(0,20);
  if(code.length<4||name.length<2){status('Enter a nickname (2+ letters) and a world code (4–12 characters).');return;}
  // Joining the selected world intentionally replaces the previous session;
  // it never changes game maps until the server confirms the new admission.
  disconnect();currentName=name;selectCode(code);
  for(const l of lobbies)l.name.value=name;
  put('vn.mp.name',name);put('vn.mp.room',code);
  const seq=++epoch;let s;
  try{s=new WebSocket(DEFAULT_SERVER);}catch{status('Could not reach the Varnethryl world server.');return;}
  socket=s;status('Connecting to '+code+'…');
  s.onopen=()=>{
   if(seq!==epoch)return;
   s.send(JSON.stringify({type:'join',entry:fromTitle?'title':'game',code,name,state:{
     zone:getZone(),x:state.heroX,y:state.heroY||0,z:state.heroZ,yaw:state.yaw||0,hero:getHeroName()
   }}));
  };
  s.onmessage=async event=>{
   if(seq!==epoch)return;
   let m;try{m=JSON.parse(event.data);}catch{return;}
   if(m.type==='error'){status('World unavailable: '+String(m.message||'cannot join'));s.close();return;}
   if(m.type==='welcome'){
    selfId=m.id;room=m.code;resetPeers();
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
    joined=true;onlineCount=(m.players?.length||0)+1;
    for(const p of m.players||[])sync(p);
    status('In '+room+' · '+onlineCount+'/12 players. '+(m.spawn?'You entered town.':'Your location was preserved.'));
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
    if(seq===epoch){joined=false;selfId='';socket=null;resetPeers();
      status('Disconnected. Solo play still works; choose a world to rejoin.');refresh();}
  };
 }
 function update(dt,now){
  if(joined&&now-lastSend>=95){lastSend=now;sendState();}
  for(const p of peers.values()){
   const same=p.zone===getZone();p.obj.visible=same;
   if(!same)continue;
   const dx=p.x-p.obj.position.x,dz=p.z-p.obj.position.z,dist=Math.hypot(dx,dz);
   if(dist>45)p.obj.position.set(p.x,p.y,p.z);else p.obj.position.lerp(new THREE.Vector3(p.x,p.y,p.z),Math.min(1,dt*9));
   p.obj.rotation.y+=Math.atan2(Math.sin(p.yaw-p.obj.rotation.y),Math.cos(p.yaw-p.obj.rotation.y))*Math.min(1,dt*10);
   p.walk+=dt*(dist>.035?11:4);
   p.legA.rotation.x=dist>.035?Math.sin(p.walk)*.28:0;
   p.legB.rotation.x=-p.legA.rotation.x;
  }
 }
 return {join,disconnect,refresh,update,get online(){return joined;},get room(){return room;},get playerCount(){return onlineCount;},dispose(){disconnect();root.parent?.remove(root);}};
}
