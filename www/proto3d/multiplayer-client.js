/* Optional multiplayer test presence for ALL Varnethryl world zones.
 * Town welcomes newcomers; the room's first player remains exactly where they were.
 * Remote movement is visual only. Damage, quests, loot and NPC AI stay single-player.
 */
export function createMultiplayer({THREE,scene,state,getZone,setZone,getHeroName,updateLevel,snapFollowers,camRig,miniMap}){
 const root=new THREE.Group();root.name='Varnethryl-Remote-Players';root.userData.keepAlways=true;scene.add(root);
 const peers=new Map();let socket=null,joined=false,selfId='',room='',lastSend=0,epoch=0,onlineCount=0;
 const get=k=>{try{return localStorage.getItem(k)||'';}catch{return '';}};
 const put=(k,v)=>{try{localStorage.setItem(k,v);}catch{}};
 const section=document.createElement('details');section.id='vnQuickMultiplayer';
 section.innerHTML=`<summary>Multiplayer · Test rooms</summary><div class="vn-opts" style="display:grid;gap:7px">
 <label for="vnMpName">Your nickname</label><input id="vnMpName" maxlength="20" autocomplete="nickname" placeholder="Adventurer">
 <label for="vnMpRoom">Room code — share with friends</label>
 <div style="display:flex;gap:5px"><input id="vnMpRoom" maxlength="12" style="min-width:0;flex:1" placeholder="ROOMCODE"><button id="vnMpCopy" type="button">Copy</button></div>
 <label for="vnMpServer">Multiplayer server (wss://)</label><input id="vnMpServer" inputmode="url" autocomplete="url" placeholder="wss://your-server.example.com">
 <div style="display:flex;gap:5px"><button id="vnMpJoin" type="button">Join room</button><button id="vnMpLeave" type="button">Leave</button></div>
 <small id="vnMpStatus" role="status" aria-live="polite">Offline — single-player still works.</small>
 <small>Up to 12 testers per room. A newcomer starts in town; existing players are never teleported. Same-map players appear together. PvP damage and shared enemies are not online yet.</small>
 </div>`;
 const host=document.querySelector('#vnQuickMenu .vn-quick-sections');
 if(host)host.insertBefore(section,host.children[1]||null);else document.body.appendChild(section);
 const $=s=>section.querySelector(s),nameEl=$('#vnMpName'),roomEl=$('#vnMpRoom'),serverEl=$('#vnMpServer'),statusEl=$('#vnMpStatus');
 const makeRoom=()=>Math.random().toString(36).slice(2,8).toUpperCase().padEnd(6,'X');
 nameEl.value=get('vn.mp.name')||'Adventurer';roomEl.value=get('vn.mp.room')||makeRoom();
 serverEl.value=get('vn.mp.server');
 const status=s=>{statusEl.textContent=s;};
 const validUrl=url=>{try{const u=new URL(url);return (u.protocol==='wss:'||(u.protocol==='ws:'&&['localhost','127.0.0.1'].includes(u.hostname)))&&Boolean(u.host);}catch{return false;}};
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
  const prev=socket;socket=null;if(prev)try{prev.close(1000,'Leave room');}catch{}
  resetPeers();status('Offline — single-player still works.');
 }
 function sendState(){
  if(!joined||!socket||socket.readyState!==WebSocket.OPEN)return;
  const zone=getZone();if(!['town','wilds','frost','hydra','sailing','coliseum'].includes(zone))return;
  socket.send(JSON.stringify({type:'state',zone,x:state.heroX,y:state.dispY||state.heroY||0,z:state.heroZ,yaw:state.yaw||0,hero:getHeroName()}));
 }
 async function join(){
  disconnect();const url=serverEl.value.trim(),code=roomEl.value.trim().toUpperCase().replace(/[^A-Z0-9]/g,'').slice(0,12);
  const name=nameEl.value.trim().replace(/[^\p{L}\p{N} _-]/gu,'').slice(0,20);
  if(!validUrl(url)){status('Set a secure wss:// server address first.');return;}
  if(code.length<4||name.length<2){status('Use a room code (4–12 characters) and nickname (2+ characters).');return;}
  roomEl.value=code;nameEl.value=name;
  put('vn.mp.name',name);put('vn.mp.room',code);put('vn.mp.server',url);
  const seq=++epoch;let s;
  try{s=new WebSocket(url);}catch{status('Server address is invalid.');return;}
  socket=s;status('Connecting to multiplayer server…');
  s.onopen=()=>{if(seq!==epoch)return;s.send(JSON.stringify({type:'join',code,name,state:{
    zone:getZone(),x:state.heroX,y:state.heroY||0,z:state.heroZ,yaw:state.yaw||0,hero:getHeroName()
  }}));};
  s.onmessage=async event=>{
   if(seq!==epoch)return;
   let m;try{m=JSON.parse(event.data);}catch{return;}
   if(m.type==='error'){status('Server: '+String(m.message||'Cannot join room'));return;}
   if(m.type==='welcome'){
    selfId=m.id;room=m.code;resetPeers();
    // Only newcomers are moved to the town. Existing connected players never move.
    if(!m.first&&m.spawn){
     try{
      if(getZone()!=='town')await setZone('town');
      if(seq!==epoch)return;
      state.heroX=m.spawn.x;state.heroZ=m.spawn.z;state.level=0;state.yaw=0;
      state.target=null;updateLevel();snapFollowers();camRig.snap=true;miniMap.invalidate();
     }catch(e){status('Town travel failed: '+String(e?.message||e));s.close();return;}
    }
    if(seq!==epoch)return;joined=true;onlineCount=(m.players?.length||0)+1;
    for(const p of m.players||[])sync(p);
    status('Room '+room+' · '+onlineCount+'/12 players · '+(m.first?'You stayed in your current map.':'Joined at town.'));
    sendState();return;
   }
   if(m.type==='joined'){onlineCount++;sync(m.player);status('Room '+room+' · '+onlineCount+'/12 players');}
   if(m.type==='state')sync(m.player);
   if(m.type==='left'){onlineCount=Math.max(1,onlineCount-1);removePeer(m.id);status('Room '+room+' · '+onlineCount+'/12 players');}
  };
  s.onerror=()=>{if(seq===epoch)status('Connection failed — check server URL or hosting.');};
  s.onclose=()=>{if(seq===epoch){joined=false;selfId='';socket=null;resetPeers();status('Disconnected. You can keep playing solo or rejoin.');}};
 }
 $('#vnMpJoin').addEventListener('click',join);
 $('#vnMpLeave').addEventListener('click',disconnect);
 $('#vnMpCopy').addEventListener('click',()=>{if(navigator.clipboard?.writeText)navigator.clipboard.writeText(roomEl.value).then(()=>status('Room code copied. Share the same server URL too.')).catch(()=>status('Copy failed; select the room code.'));else status('Select and copy the room code.');});
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
 return {join,disconnect,update,get online(){return joined;},get room(){return room;},get playerCount(){return onlineCount;},dispose(){disconnect();section.remove();root.parent?.remove(root);}};
}
