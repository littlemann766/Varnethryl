import assert from 'node:assert/strict';
import { test } from 'node:test';
import { once } from 'node:events';
import { WebSocket } from 'ws';
import { createWorldServer } from '../server.mjs';

function recv(ws,type){
 return new Promise((resolve,reject)=>{
  const timer=setTimeout(()=>{ws.off('message',handler);reject(new Error('Timed out: '+type));},2500);
  function handler(raw){let msg;try{msg=JSON.parse(raw.toString());}catch{return;}if(msg.type!==type)return;clearTimeout(timer);ws.off('message',handler);resolve(msg);}
  ws.on('message',handler);
 });
}
async function connected(url){const sock=new WebSocket(url);await once(sock,'open');return sock;}
test('late join starts in town without teleporting an existing cave player; states stay map-specific',async t=>{
 const srv=createWorldServer();srv.server.listen(0,'127.0.0.1');await once(srv.server,'listening');
 t.after(()=>srv.close());const url='ws://127.0.0.1:'+srv.server.address().port;
 const a=await connected(url);t.after(()=>a.terminate());
 const firstWelcome=recv(a,'welcome');
 a.send(JSON.stringify({type:'join',code:'PARTY7',name:'CaveExplorer',state:{zone:'frost',x:220,y:14,z:330,yaw:2,hero:'Selene'}}));
 const first=await firstWelcome;
 assert.equal(first.first,true);assert.equal(first.spawn,null);
 assert.equal(srv.rooms.get('PARTY7').get(first.id).zone,'frost');
 const b=await connected(url);t.after(()=>b.terminate());
 const aNotified=recv(a,'joined'),secondWelcome=recv(b,'welcome');
 b.send(JSON.stringify({type:'join',code:'PARTY7',name:'NewTester',state:{zone:'hydra',x:999,y:1,z:999,yaw:0,hero:'Aldric'}}));
 const second=await secondWelcome;await aNotified;
 assert.equal(second.first,false);assert.deepEqual(second.players.map(p=>p.zone),['frost']);
 assert.ok(second.spawn&&Number.isFinite(second.spawn.x));
 assert.equal(srv.rooms.get('PARTY7').get(first.id).x,220); // incumbent is NOT relocated
 assert.equal(srv.rooms.get('PARTY7').get(second.id).zone,'town');
 const aSawTown=recv(a,'state');
 b.send(JSON.stringify({type:'state',zone:'town',x:8,y:1,z:9,yaw:0,hero:'Aldric'}));
 assert.equal((await aSawTown).player.zone,'town');
 const bSawCave=recv(b,'state');
 a.send(JSON.stringify({type:'state',zone:'frost',x:228,y:14,z:332,yaw:2,hero:'Selene'}));
 const event=await bSawCave;
 assert.equal(event.player.zone,'frost');assert.equal(event.player.x,228);
 assert.equal(srv.rooms.get('PARTY7').get(first.id).zone,'frost');
 const aLeave=recv(a,'left');b.close();assert.equal((await aLeave).id,second.id);
 assert.equal(srv.rooms.get('PARTY7').get(first.id).x,228);
});
test('room code validation does not create game progress or a playable session',async t=>{
 const srv=createWorldServer();srv.server.listen(0,'127.0.0.1');await once(srv.server,'listening');
 t.after(()=>srv.close());
 const s=await connected('ws://127.0.0.1:'+srv.server.address().port);t.after(()=>s.terminate());
 const err=recv(s,'error');s.send(JSON.stringify({type:'join',code:'A',name:'x'}));
 assert.match((await err).message,/code/i);assert.equal(srv.rooms.size,0);
});

test('public world browser shows three stable world names and truthful player counts',async t=>{
 const srv=createWorldServer();srv.server.listen(0,'127.0.0.1');await once(srv.server,'listening');
 t.after(()=>srv.close());const base='http://127.0.0.1:'+srv.server.address().port;
 const getRooms=async()=>{const res=await fetch(base+'/rooms');assert.equal(res.status,200);
  assert.equal(res.headers.get('access-control-allow-origin'),'*');return (await res.json()).worlds;};
 const initial=await getRooms();
 assert.deepEqual(initial.map(w=>w.code),['WORLD1','WORLD2','WORLD3']);
 assert.deepEqual(initial.map(w=>w.players),[0,0,0]);
 assert.ok(initial.every(w=>w.capacity===12));
 const a=await connected(base.replace('http:','ws:'));t.after(()=>a.terminate());
 let welcome=recv(a,'welcome');
 a.send(JSON.stringify({type:'join',entry:'title',code:'WORLD1',name:'TesterOne',
   state:{zone:'frost',x:777,y:100,z:222,yaw:0,hero:'Selene'}}));
 const first=await welcome;
 assert.equal(first.first,true);
 assert.ok(first.spawn,'entering from the start menu must spawn in town, even with a cave save');
 assert.equal(srv.rooms.get('WORLD1').get(first.id).zone,'town');
 assert.equal((await getRooms()).find(w=>w.code==='WORLD1').players,1);
 const b=await connected(base.replace('http:','ws:'));t.after(()=>b.terminate());
 welcome=recv(b,'welcome');
 b.send(JSON.stringify({type:'join',code:'PRIVATE7',name:'PrivateTester',
   state:{zone:'hydra',x:3,y:0,z:4,yaw:0,hero:'Aldric'}}));
 await welcome;
 assert.ok(!(await getRooms()).some(w=>w.code==='PRIVATE7'),'private codes must not be advertised publicly');
 assert.equal((await getRooms()).find(w=>w.code==='WORLD1').players,1);
});
test('late arrivals join the same public world without moving cave players',async t=>{
 const srv=createWorldServer();srv.server.listen(0,'127.0.0.1');await once(srv.server,'listening');
 t.after(()=>srv.close());const url='ws://127.0.0.1:'+srv.server.address().port;
 const a=await connected(url);t.after(()=>a.terminate());
 let response=recv(a,'welcome');a.send(JSON.stringify({type:'join',entry:'game',code:'WORLD2',name:'AlreadyInCave',
  state:{zone:'frost',x:1600,y:60,z:1700,yaw:1,hero:'Selene'}}));
 const first=await response;
 assert.equal(first.spawn,null);assert.equal(srv.rooms.get('WORLD2').get(first.id).zone,'frost');
 const b=await connected(url);t.after(()=>b.terminate());
 response=recv(b,'welcome');b.send(JSON.stringify({type:'join',entry:'title',code:'WORLD2',name:'JoinedFromTitle',
  state:{zone:'coliseum',x:50,y:0,z:70,yaw:1,hero:'Orin'}}));
 const second=await response;
 assert.equal(second.players.length,1);assert.equal(second.players[0].zone,'frost');
 assert.ok(second.spawn);assert.equal(srv.rooms.get('WORLD2').get(second.id).zone,'town');
 assert.equal(srv.rooms.get('WORLD2').get(first.id).x,1600);
});

test('missing movement state cannot crash the public Varnethryl server',async t=>{
 const srv=createWorldServer();srv.server.listen(0,'127.0.0.1');await once(srv.server,'listening');
 t.after(()=>srv.close());const base='ws://127.0.0.1:'+srv.server.address().port;
 const sock=await connected(base);t.after(()=>sock.terminate());
 const reply=recv(sock,'welcome');
 sock.send(JSON.stringify({type:'join',code:'WORLD3',name:'NoState'}));
 const msg=await reply;
 assert.equal(msg.first,true);assert.equal(srv.rooms.get('WORLD3').get(msg.id).zone,'town');
 assert.equal(sock.readyState,WebSocket.OPEN);
});
