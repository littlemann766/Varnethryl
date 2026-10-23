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
