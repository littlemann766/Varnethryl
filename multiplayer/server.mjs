import http from 'node:http';
import { randomUUID } from 'node:crypto';
import { pathToFileURL } from 'node:url';
import { WebSocketServer, WebSocket } from 'ws';

// Ephemeral multiplayer presence server (world-wide room, map-local visibility).
// No client-authoritative damage, currency, or inventory messages are accepted.
const ZONES=new Set(['town','wilds','frost','hydra','sailing','coliseum']);
const MAX_PLAYERS=12, MAX_BYTES=2048, RATE_MS=80;
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
const visible=p=>({id:p.id,name:p.name,slot:p.slot,zone:p.zone,x:p.x,y:p.y,z:p.z,yaw:p.yaw,hero:p.hero});
export function createWorldServer(){
 const rooms=new Map();
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
    // Joining from the START SCREEN always enters town, even when an older
    // local save last exited in a cave. Existing live players never move.
    // Joining mid-game to an empty world preserves that player's current map.
    const enterFromTitle=m.entry==='title';
    const initial=first&&!enterFromTitle&&validState(m.state)?m.state:null;
    const shouldSpawn=enterFromTitle||!first;
    const p={id:randomUUID(),socket,code,name,slot,
      zone:initial?.zone||'town',x:initial?.x??spawn.x,z:initial?.z??spawn.z,
      y:initial?.y??0,yaw:initial?.yaw??0,hero:clean(initial?.hero,30)||'Adventurer',lastUpdate:0};
    send(socket,{type:'welcome',id:p.id,code,slot,first,spawn:shouldSpawn?spawn:null,players:[...room.values()].map(visible),maxPlayers:MAX_PLAYERS});
    socket.player=p;room.set(p.id,p);broadcast(room,{type:'joined',player:visible(p)},socket);
    return;
   }
   const p=socket.player;if(!p)return;
   if(m.type==='state'){
    if(Date.now()-p.lastUpdate<RATE_MS||!validState(m))return;
    p.lastUpdate=Date.now();p.zone=m.zone;p.x=m.x;p.y=m.y;p.z=m.z;p.yaw=m.yaw;p.hero=clean(m.hero,30)||'Adventurer';
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
