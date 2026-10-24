import http from 'node:http';
import { randomUUID, randomBytes, pbkdf2Sync, timingSafeEqual } from 'node:crypto';
import { pathToFileURL } from 'node:url';
import { WebSocketServer, WebSocket } from 'ws';

// Ephemeral multiplayer presence server (world-wide room, map-local visibility).
// No client-authoritative damage, currency, or inventory messages are accepted.
const ZONES=new Set(['town','wilds','frost','hydra','sailing','coliseum']);
const MAX_PLAYERS=12, MAX_BYTES=2048, RATE_MS=80, CHAT_INTERVAL_MS=700;
const COOWNER_ITER=260000, COOWNER_MAX_ATTEMPTS=4, COOWNER_LOCK_MS=15*60*1000;
// CoOwner verifier exists ONLY in Railway environment variables, never in
// GitHub source, APK, JavaScript assets or the public multiplayer protocol.
function verifyCoOwnerPass(pass,options){
 if(typeof options.verifyCoOwner==='function')return !!options.verifyCoOwner(pass);
 const salt=process.env.VARNETHRYL_COOWNER_SALT||'';
 const hash=process.env.VARNETHRYL_COOWNER_HASH||'';
 if(!/^[0-9a-f]{40}$/.test(salt)||!/^[0-9a-f]{64}$/.test(hash))return false;
 const derived=pbkdf2Sync(pass,Buffer.from(salt,'hex'),COOWNER_ITER,32,'sha256');
 return timingSafeEqual(derived,Buffer.from(hash,'hex'));
}
const SKIN_RE=/^(?:[nop]:)?[a-z0-9_]{2,48}$/;
const CODE_RE=/^[A-Z0-9]{10,20}$/;
const skin=s=>typeof s==='string'&&SKIN_RE.test(s)?s:'aldric';
const friendCode=s=>typeof s==='string'&&CODE_RE.test(s)?s:'';
// The same salted verifier as the existing Owner unlock in ownergate.js.
// Never place the actual passphrase in code, logs, URLs, or localStorage.
const OWNER_SALT='150a1c54ab232044870dcb521f1468ba';
const OWNER_HASH='6a14971cd36e613ecebccedf46344f1fcf74bef61c0be542baad29048733c480';
const OWNER_ITER=210000, MAX_OWNER_ATTEMPTS=4, LOCK_MS=15*60*1000;
// Three stable public world instances live on this one dedicated Varnethryl
// server. Unlike private invite codes, these worlds are discoverable in-game.
export const PUBLIC_WORLDS=Object.freeze([
 {code:'WORLD1',name:'Kingdom One'},
 {code:'WORLD2',name:'Kingdom Two'},
 {code:'WORLD3',name:'Kingdom Three'}
]);
const clean=(value,max)=>String(value??'').replace(/[^\p{L}\p{N} _-]/gu,'').trim().slice(0,max);
const finite=(n,min,max)=>typeof n==='number'&&Number.isFinite(n)&&n>=min&&n<=max;
const validState=m=>!!m&&typeof m==='object'&&ZONES.has(m.zone)&&finite(m.x,-10000,10000)&&finite(m.z,-10000,10000)&&finite(m.y,-1000,5000)&&finite(m.yaw,-1000,1000);
const currentRole=p=>p.socket.ownerAuthorized?'owner':p.socket.coOwnerAuthorized?'coowner':'player';
const COOWNER_BOSSES=new Set(['titan','titan40','vaelthryx','frosttroll_a','frosttroll_b','hydra']);
const visible=p=>({id:p.id,name:p.name,slot:p.slot,zone:p.zone,x:p.x,y:p.y,z:p.z,yaw:p.yaw,
  hero:p.hero,skin:p.skin,friendCode:p.friendCode,moving:p.moving,role:currentRole(p)});
export function createWorldServer(options={}){
 const rooms=new Map(),ownerAttempts=new Map(),coOwnerAttempts=new Map(),coOwnerTokens=new Map(),ownerTokens=new Map();
 function publishRole(p){
  const room=rooms.get(p.code);if(room)broadcast(room,{type:'role-state',id:p.id,role:currentRole(p)});
  publishRoster();
 }
 function coOwnerAuth(socket,pass){
  const ip=socket._socket?.remoteAddress||'unknown',now=Date.now();
  const record=coOwnerAttempts.get(ip)||{fails:0,lockedUntil:0};
  if(record.lockedUntil>now)return {ok:false,message:'CoOwner sign-in temporarily locked after repeated attempts.'};
  if(typeof pass!=='string'||pass.length<8||pass.length>128)
   return {ok:false,message:'CoOwner password must be 8–128 characters.'};
  let valid=false;
  try{valid=verifyCoOwnerPass(pass,options);}catch{valid=false;}
  if(!valid){
   record.fails++;
   if(record.fails>=COOWNER_MAX_ATTEMPTS){record.fails=0;record.lockedUntil=now+COOWNER_LOCK_MS;}
   coOwnerAttempts.set(ip,record);
   return {ok:false,message:record.lockedUntil>now?'CoOwner sign-in temporarily locked after repeated attempts.':'Incorrect CoOwner password.'};
  }
  coOwnerAttempts.delete(ip);
  // Opaque random bearer for this device. Never place the password in local
  // storage. Reconnect stays signed in until manual Lock CoOwner or server
  // restart; only a server-side token can grant CoOwner permissions.
  const token=randomBytes(32).toString('hex');
  coOwnerTokens.set(token,true);
  socket.coOwnerToken=token;socket.coOwnerAuthorized=true;
  return {ok:true,token,message:'CoOwner unlocked. Use Lock CoOwner to revoke access.'};
 }

 const isPublic=code=>PUBLIC_WORLDS.some(w=>w.code===code);
 const chatVisible=(p,q)=>p.code===q.code||(isPublic(p.code)&&isPublic(q.code));
 const chatPeers=()=>[...rooms.values()].flatMap(r=>[...r.values()]);
 function publishRoster(){
   const online=chatPeers();
   for(const p of online)send(p.socket,{type:'chat-roster',players:online
     .filter(q=>q.socket!==p.socket&&chatVisible(p,q))
     .map(q=>({id:q.id,name:q.name,world:q.code,friendCode:q.friendCode,role:currentRole(q)}))});
 }

 const allOnline=()=>[...rooms.values()].flatMap(room=>[...room.values()]);
 const ownerVisible=p=>({...visible(p),world:p.code});
 const ownerPlayers=socket=>allOnline().filter(p=>p.socket!==socket).map(ownerVisible);
 function checkOwnerPass(socket,pass){
   const ip=socket._socket?.remoteAddress||'unknown', now=Date.now();
   const rec=ownerAttempts.get(ip)||{fails:0,lockedUntil:0};
   if(rec.lockedUntil>now)return {ok:false,message:'Owner access locked. Try later.'};
   // Never allow clients to submit the derived digest as their credential.
   if(typeof pass!=='string'||pass.length<1||pass.length>128)return {ok:false,message:'Owner passphrase required.'};
   const ok=typeof options.verifyOwner==='function' ? !!options.verifyOwner(pass) : (()=>{
     const key=pbkdf2Sync(pass.trim(),Buffer.from(OWNER_SALT,'hex'),OWNER_ITER,32,'sha256');
     const expected=Buffer.from(OWNER_HASH,'hex');return key.length===expected.length&&timingSafeEqual(key,expected);
   })();
   if(!ok){
     rec.fails++;if(rec.fails>=MAX_OWNER_ATTEMPTS){rec.lockedUntil=now+LOCK_MS;rec.fails=0;}
     ownerAttempts.set(ip,rec);return {ok:false,message:rec.lockedUntil>now?'Owner access temporarily locked.':'Owner passphrase incorrect.'};
   }
   ownerAttempts.delete(ip);return {ok:true};
 }
 const server=http.createServer((req,res)=>{
  // Only room counts and names are published; never reveal private invite
  // codes, player nicknames, session IDs, or positions to unauthenticated GETs.
  if(req.method==='GET'&&req.url?.split('?')[0]==='/rooms'){
   const worlds=PUBLIC_WORLDS.map(({code,name})=>({code,name,
      players:rooms.get(code)?.size||0,capacity:MAX_PLAYERS}));
   res.writeHead(200,{'Content-Type':'application/json','Cache-Control':'no-store','Access-Control-Allow-Origin':'*'});
   res.end(JSON.stringify({ok:true,worlds,maxPlayers:MAX_PLAYERS}));return;
  }
  if(req.method==='GET'&&req.url?.split('?')[0]==='/health'){
   res.writeHead(200,{'Content-Type':'application/json','Cache-Control':'no-store'});
   res.end(JSON.stringify({ok:true,rooms:rooms.size,players:[...rooms.values()].reduce((n,r)=>n+r.size,0)}));return;
  }
  res.writeHead(404,{'Content-Type':'text/plain'});res.end('Varnethryl multiplayer relay');
 });
 const wss=new WebSocketServer({server,maxPayload:MAX_BYTES,perMessageDeflate:false});
 const send=(sock,obj)=>{if(sock.readyState===WebSocket.OPEN)sock.send(JSON.stringify(obj));};
 const broadcast=(room,obj,except)=>{for(const p of room.values())if(p.socket!==except)send(p.socket,obj);};
 function leave(sock){
  const p=sock.player;if(!p)return;sock.player=null;
  const room=rooms.get(p.code);if(!room)return;
  room.delete(p.id);broadcast(room,{type:'left',id:p.id},sock);
  if(room.size===0)rooms.delete(p.code);
  publishRoster();
 }
 wss.on('connection',(socket,request)=>{
  const origin=request.headers.origin;
  const origins=(process.env.ALLOWED_ORIGINS||'').split(',').map(s=>s.trim()).filter(Boolean);
  if(origins.length&&origin&&!origins.includes(origin)){socket.close(1008,'Origin not permitted');return;}
  socket.isAlive=true;socket.on('pong',()=>{socket.isAlive=true;});
  socket.on('message',raw=>{
   let m;try{m=JSON.parse(raw.toString());}catch{return;}
   if(!m||typeof m!=='object')return;
   if(m.type==='join'){
    if(socket.player)return;
    const code=clean(m.code,12).toUpperCase(),name=clean(m.name,20);
    if(!/^[A-Z0-9]{4,12}$/.test(code)||name.length<2){send(socket,{type:'error',message:'Use a 4–12 character code and a nickname.'});return;}
    let room=rooms.get(code);if(!room){room=new Map();rooms.set(code,room);}
    if(room.size>=MAX_PLAYERS){send(socket,{type:'error',message:'Room full (12 players).'});return;}
    const taken=new Set([...room.values()].map(p=>p.slot));
    let slot=0;while(taken.has(slot))slot++;
    const angle=slot*Math.PI*2/12,spawn={x:Math.sin(angle)*4,z:14+Math.cos(angle)*4};
    // The first member keeps their EXISTING game location, even if deep in a cave.
    // Later members enter at town. Nobody else is teleported or interrupted.
    const first=room.size===0;
    // An automatic reconnect retains the local hero's actual zone and position,
    // even when the room already contains other players.
    const reconnecting=m.entry==='resume';
    // Joining from the START SCREEN always enters town, even when an older
    // local save last exited in a cave. Existing live players never move.
    // Joining mid-game to an empty world preserves that player's current map.
    const enterFromTitle=m.entry==='title';
    const initial=(first&&!enterFromTitle||reconnecting)&&validState(m.state)?m.state:null;
    const shouldSpawn=!reconnecting&&(enterFromTitle||!first);
    const p={id:randomUUID(),socket,code,name,slot,
      zone:initial?.zone||'town',x:initial?.x??spawn.x,z:initial?.z??spawn.z,
      y:initial?.y??0,yaw:initial?.yaw??0,hero:clean(initial?.hero,30)||'Adventurer',
      skin:skin(initial?.skin),friendCode:friendCode(m.friendCode),
      moving:false,lastChat:0,lastUpdate:0};
    send(socket,{type:'welcome',id:p.id,code,slot,first,spawn:shouldSpawn?spawn:null,players:[...room.values()].map(visible),maxPlayers:MAX_PLAYERS});
    socket.player=p;room.set(p.id,p);broadcast(room,{type:'joined',player:visible(p)},socket);
    publishRoster();
    return;
   }
   const p=socket.player;if(!p)return;
   if(m.type==='coowner-auth'){
     const result=coOwnerAuth(socket,m.pass);
     send(socket,{type:'coowner-auth',...result});
     if(result.ok){publishRole(p);send(socket,{type:'coowner-players',players:ownerPlayers(socket)});}
     return;
   }
   if(m.type==='coowner-resume'){
     const token=typeof m.token==='string'?m.token:'';
     const ok=/^[a-f0-9]{64}$/.test(token)&&coOwnerTokens.has(token);
     socket.coOwnerAuthorized=ok;
     if(ok){socket.coOwnerToken=token;publishRole(p);}
     send(socket,{type:'coowner-auth',ok,resumed:true,
       message:ok?'CoOwner session restored.':'CoOwner session unavailable. Enter your password to unlock.'});
     if(ok)send(socket,{type:'coowner-players',players:ownerPlayers(socket)});
     return;
   }
   if(m.type==='coowner-lock'){
     if(socket.coOwnerToken)coOwnerTokens.delete(socket.coOwnerToken);
     socket.coOwnerToken=null;socket.coOwnerAuthorized=false;
     send(socket,{type:'coowner-locked',ok:true});
     publishRole(p);return;
   }
   if(m.type==='coowner-list'){
     if(!socket.coOwnerAuthorized){send(socket,{type:'coowner-error',message:'Unlock CoOwner first.'});return;}
     send(socket,{type:'coowner-players',players:ownerPlayers(socket)});return;
   }
   if(m.type==='coowner-boss'){
     if(!socket.coOwnerAuthorized){
       send(socket,{type:'coowner-error',message:'Unlock CoOwner to summon bosses.'});return;
     }
     if(typeof m.boss!=='string'||!COOWNER_BOSSES.has(m.boss)){
       send(socket,{type:'coowner-error',message:'Unsupported boss.'});return;
     }
     const now=Date.now();
     if(now-(socket.lastBossSummonAt||0)<4500){
       send(socket,{type:'coowner-error',message:'Boss summon cooldown: try again shortly.'});return;
     }
     socket.lastBossSummonAt=now;
     // Local approved test summon only; multiplayer damage is not synchronized.
     send(socket,{type:'coowner-boss-approved',boss:m.boss});
     return;
   }
   if(m.type==='owner-auth'){
     // Owner and CoOwner are independent, server-verified ranks.
     const result=checkOwnerPass(socket,m.pass);
     let token=null;
     if(result.ok){
       token=randomBytes(32).toString('hex');ownerTokens.set(token,true);
       socket.ownerToken=token;socket.ownerAuthorized=true;publishRole(p);
     }
     send(socket,{type:'owner-auth',ok:result.ok,
       ...(token?{token}:{}),
       message:result.ok?'Owner access verified.':result.message});
     if(result.ok)send(socket,{type:'owner-players',players:ownerPlayers(socket)});
     return;
   }
   if(m.type==='owner-resume'){
     const token=typeof m.token==='string'?m.token:'';
     const ok=/^[0-9a-f]{64}$/.test(token)&&ownerTokens.has(token);
     socket.ownerAuthorized=ok;
     if(ok){socket.ownerToken=token;publishRole(p);}
     send(socket,{type:'owner-auth',ok,resumed:true,
       message:ok?'Owner server access restored.':'Owner verification required for player teleport.'});
     if(ok)send(socket,{type:'owner-players',players:ownerPlayers(socket)});
     return;
   }
   if(m.type==='owner-lock'){
     if(socket.ownerToken)ownerTokens.delete(socket.ownerToken);
     socket.ownerToken=null;socket.ownerAuthorized=false;
     send(socket,{type:'owner-locked',ok:true});
     publishRole(p);return;
   }
   if(m.type==='owner-list'){
     if(!socket.ownerAuthorized){send(socket,{type:'owner-error',message:'Verify Owner server access first.'});return;}
     send(socket,{type:'owner-players',players:ownerPlayers(socket)});return;
   }
   if(m.type==='owner-jump'||m.type==='coowner-jump'){
     const isCoOwner=m.type==='coowner-jump';
     if(isCoOwner?!socket.coOwnerAuthorized:!socket.ownerAuthorized){
       send(socket,{type:isCoOwner?'coowner-error':'owner-error',
         message:isCoOwner?'Unlock CoOwner first.':'Verify Owner server access first.'});return;
     }
     const target=allOnline().find(q=>q.id===m.id&&q.socket!==socket);
     if(!target){send(socket,{type:isCoOwner?'coowner-error':'owner-error',message:'That player has left the server.'});return;}
     let movedWorld=false;
     if(p.code!==target.code){movedWorld=true;
       const next=rooms.get(target.code);
       if(!next||next.size>=MAX_PLAYERS){send(socket,{type:isCoOwner?'coowner-error':'owner-error',message:'That world is full.'});return;}
       const old=rooms.get(p.code),oldCode=p.code;
       old.delete(p.id);broadcast(old,{type:'left',id:p.id},socket);
       if(old.size===0)rooms.delete(oldCode);
       const taken=new Set([...next.values()].map(q=>q.slot));
       let slot=0;while(taken.has(slot))slot++;
       p.code=target.code;p.slot=slot;next.set(p.id,p);
     }
     // Never modify the target. Only assign the Owner position beside them.
     p.zone=target.zone;p.x=target.x+2;p.y=target.y;p.z=target.z+2;p.yaw=target.yaw;
     const current=rooms.get(p.code);
     broadcast(current,{type:movedWorld?'joined':'state',player:visible(p)},socket);
     publishRoster();
     send(socket,{type:m.type,world:p.code,target:ownerVisible(target),
       players:[...current.values()].filter(q=>q.socket!==socket).map(visible)});
     return;
   }
   if(m.type==='chat'){
     const now=Date.now();
     if(now-p.lastChat<CHAT_INTERVAL_MS){send(socket,{type:'chat-error',message:'Please slow down before sending another message.'});return;}
     if(typeof m.text!=='string'){send(socket,{type:'chat-error',message:'Message must be text.'});return;}
     const text=m.text.trim();
     if(!text||text.length>280||/[\x00-\x08\x0b\x0e-\x1f]/.test(text)){
       send(socket,{type:'chat-error',message:'Messages must be 1–280 characters.'});return;
     }
     const target=typeof m.to==='string'&&m.to?chatPeers().find(q=>q.id===m.to):null;
     if(m.to&&(!target||!chatVisible(p,target))){
       send(socket,{type:'chat-error',message:'Recipient is offline or unavailable.'});return;
     }
     p.lastChat=now;
     const event={type:'chat',kind:target?'private':'world',id:randomUUID(),from:p.id,
       name:p.name,role:currentRole(p),to:target?.id||null,text,world:p.code,time:now};
     if(target){send(target.socket,event);send(socket,event);}
     else broadcast(rooms.get(p.code),event,null);
     return;
   }
   if(m.type==='state'){
    if(Date.now()-p.lastUpdate<RATE_MS||!validState(m))return;
    p.lastUpdate=Date.now();p.zone=m.zone;p.x=m.x;p.y=m.y;p.z=m.z;p.yaw=m.y;
    p.hero=clean(m.hero,30)||'Adventurer';p.skin=skin(m.skin);p.moving=m.moving===true;
    broadcast(rooms.get(p.code),{type:'state',player:visible(p)},socket);
   }
  });
  socket.on('close',()=>leave(socket));socket.on('error',()=>leave(socket));
 });
 const heartbeat=setInterval(()=>{for(const sock of wss.clients){if(!sock.isAlive){sock.terminate();continue;}sock.isAlive=false;sock.ping();}},30000);
 heartbeat.unref?.();
 server.on('close',()=>clearInterval(heartbeat));
 return {server,wss,rooms,close:()=>new Promise(resolve=>{for(const sock of wss.clients)sock.terminate();wss.close(()=>server.close(resolve));})};
}
if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href){
 const {server}=createWorldServer();const port=Number(process.env.PORT)||3001;
 server.listen(port,'0.0.0.0',()=>console.log('Varnethryl multiplayer listening on '+port));
}
