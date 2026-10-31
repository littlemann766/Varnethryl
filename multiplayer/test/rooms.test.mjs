import assert from 'node:assert/strict';
import { test } from 'node:test';
import { once } from 'node:events';
import { WebSocket } from 'ws';
import { createWorldServer } from '../server.mjs';
import { nextRemoteYaw,remoteFacing } from '../../legacy-web/www/proto3d/multiplayer-client.js';

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

test('server verifies Owner access and teleports the Owner between worlds without moving the target',async t=>{
 const srv=createWorldServer({verifyOwner:pass=>pass==='test-only-owner-pass'});
 srv.server.listen(0,'127.0.0.1');await once(srv.server,'listening');
 t.after(()=>srv.close());const url='ws://127.0.0.1:'+srv.server.address().port;
 const owner=await connected(url),target=await connected(url),visitor=await connected(url);
 t.after(()=>{owner.terminate();target.terminate();visitor.terminate();});
 async function enter(ws,code,name){
   const reply=recv(ws,'welcome');
   ws.send(JSON.stringify({type:'join',entry:'game',code,name,
      state:{zone:'town',x:7,y:0,z:8,yaw:0,hero:'Adventurer'}}));
   return reply;
 }
 const a=await enter(owner,'WORLD1','OwnerTester');
 const b=await enter(target,'WORLD2','OtherPlayer');
 await enter(visitor,'WORLD3','Unverified');
 let forbidden=recv(visitor,'owner-error');
 visitor.send(JSON.stringify({type:'owner-list'}));
 assert.match((await forbidden).message,/verify/i);
 forbidden=recv(visitor,'owner-error');
 visitor.send(JSON.stringify({type:'owner-jump',id:b.id}));
 assert.match((await forbidden).message,/verify/i);
 const denied=recv(owner,'owner-auth');
 owner.send(JSON.stringify({type:'owner-auth',pass:'not-the-pass'}));
 assert.equal((await denied).ok,false);
 const auth=recv(owner,'owner-auth'),listing=recv(owner,'owner-players');
 owner.send(JSON.stringify({type:'owner-auth',pass:'test-only-owner-pass'}));
 assert.equal((await auth).ok,true);
 const directory=await listing;
 assert.ok(directory.players.some(p=>p.id===b.id&&p.world==='WORLD2'));
 const targetOriginal={...srv.rooms.get('WORLD2').get(b.id)};
 const targetSeesOwner=recv(target,'joined'),ownerJump=recv(owner,'owner-jump');
 owner.send(JSON.stringify({type:'owner-jump',id:b.id}));
 const jump=await ownerJump;
 assert.equal(jump.world,'WORLD2');assert.equal(jump.target.id,b.id);
 assert.equal((await targetSeesOwner).player.id,a.id);
 assert.equal(srv.rooms.get('WORLD2').get(a.id).zone,targetOriginal.zone);
 assert.equal(srv.rooms.get('WORLD2').get(a.id).x,targetOriginal.x+2);
 assert.equal(srv.rooms.get('WORLD2').get(b.id).x,targetOriginal.x);
 assert.equal(srv.rooms.get('WORLD2').get(b.id).z,targetOriginal.z);
 assert.equal(srv.rooms.get('WORLD1'),undefined);
});
test('automatic reconnect resumes cave location even when other players remain in the world',async t=>{
 const srv=createWorldServer();srv.server.listen(0,'127.0.0.1');await once(srv.server,'listening');
 t.after(()=>srv.close());const url='ws://127.0.0.1:'+srv.server.address().port;
 const player=await connected(url),friend=await connected(url);
 t.after(()=>{player.terminate();friend.terminate();});
 const first=recv(player,'welcome');player.send(JSON.stringify({type:'join',code:'WORLD1',entry:'game',
    name:'CavePlayer',state:{zone:'frost',x:550,y:20,z:580,yaw:0,hero:'Selene'}}));await first;
 const second=recv(friend,'welcome');friend.send(JSON.stringify({type:'join',code:'WORLD1',entry:'title',
    name:'FriendInTown',state:{zone:'town',x:0,y:0,z:0,yaw:0,hero:'Aldric'}}));
 const friendInfo=await second;assert.equal(friendInfo.first,false);
 player.close();await once(player,'close');
 const reconnect=await connected(url);t.after(()=>reconnect.terminate());
 const welcome=recv(reconnect,'welcome');reconnect.send(JSON.stringify({type:'join',code:'WORLD1',entry:'resume',
    name:'CavePlayer',state:{zone:'frost',x:551,y:20,z:581,yaw:0,hero:'Selene'}}));
 const result=await welcome;
 assert.equal(result.first,false);assert.equal(result.spawn,null);
 const actual=srv.rooms.get('WORLD1').get(result.id);
 assert.equal(actual.zone,'frost');assert.equal(actual.x,551);
 assert.equal(srv.rooms.get('WORLD1').get(friendInfo.id).zone,'town');
});

test('selected 3D skin is broadcast at join and updated as players switch skins',async t=>{
 const srv=createWorldServer();srv.server.listen(0,'127.0.0.1');await once(srv.server,'listening');
 t.after(()=>srv.close());const url='ws://127.0.0.1:'+srv.server.address().port;
 const a=await connected(url),b=await connected(url);
 t.after(()=>{a.terminate();b.terminate();});
 const first=recv(a,'welcome');
 a.send(JSON.stringify({type:'join',code:'WORLD1',name:'SkinTester',friendCode:'AAAABBBBCCCCDDDDEEEE',
 state:{zone:'town',x:1,y:0,z:2,yaw:0,skin:'n:owner',hero:'Owner'}}));
 const info=await first;
 const second=recv(b,'welcome');
 b.send(JSON.stringify({type:'join',code:'WORLD1',name:'SecondPlayer',friendCode:'FFFF0000111122223333'}));
 const incoming=await second;
 assert.equal(incoming.players[0].skin,'n:owner');
 assert.equal(incoming.players[0].friendCode,'AAAABBBBCCCCDDDDEEEE');
 const next=recv(b,'state');
 a.send(JSON.stringify({type:'state',zone:'town',x:4,y:0,z:6,yaw:1,
  moving:true,skin:'n:selene_new',hero:'Selene'}));
 const changed=await next;
 assert.equal(changed.player.skin,'n:selene_new');
 assert.equal(changed.player.moving,true);
 assert.equal(srv.rooms.get('WORLD1').get(info.id).skin,'n:selene_new');
});
test('world chat is limited to current world; private messages only reach recipient',async t=>{
 const srv=createWorldServer();srv.server.listen(0,'127.0.0.1');await once(srv.server,'listening');
 t.after(()=>srv.close());const url='ws://127.0.0.1:'+srv.server.address().port;
 const a=await connected(url),b=await connected(url),c=await connected(url),d=await connected(url);
 t.after(()=>[a,b,c,d].forEach(w=>w.terminate()));
 async function join(ws,code,name,fc){
  const r=recv(ws,'welcome');
  ws.send(JSON.stringify({type:'join',code,name,friendCode:fc}));return r;
 }
 const p=await join(a,'WORLD1','OwnerTester','AAAABBBBCCCCDDDDEEEE');
 const q=await join(b,'WORLD1','CoOwnerTester','FFFF0000111122223333');
 const stranger=await join(c,'WORLD1','OtherTester','1234567890ABCDEF1234');
 const remote=await join(d,'WORLD2','InSecondWorld','55556666777788889999');
 const roster=recv(a,'chat-roster');
 // A new recipient joining refreshes available players across public worlds.
 const temp=await connected(url);t.after(()=>temp.terminate());
 await join(temp,'WORLD2','NewFriend','66667777888899990000');
 const available=await roster;
 assert.ok(available.players.some(v=>v.id===remote.id));
 assert.ok(available.players.some(v=>v.id===q.id&&v.friendCode==='FFFF0000111122223333'));
 const recipient=recv(b,'chat'),self=recv(a,'chat');
 a.send(JSON.stringify({type:'chat',text:'Meet in the town square',to:q.id}));
 const priv=await recipient;
 assert.equal(priv.kind,'private');assert.equal(priv.name,'OwnerTester');
 assert.equal(priv.text,'Meet in the town square');assert.equal(priv.to,q.id);
 assert.equal((await self).id,priv.id);
 const publicMsg=recv(c,'chat');
 // The next message is artificially outside rate limit; no real-world delay.
 srv.rooms.get('WORLD1').get(p.id).lastChat=0;
 a.send(JSON.stringify({type:'chat',text:'Public world hello'}));
 const world=await publicMsg;
 assert.equal(world.kind,'world');assert.equal(world.text,'Public world hello');
 assert.equal(world.world,'WORLD1');
 // A cross-public-world private message reaches the intended player, not a world broadcast.
 srv.rooms.get('WORLD1').get(p.id).lastChat=0;
 const across=recv(d,'chat');
 a.send(JSON.stringify({type:'chat',text:'Other world whisper',to:remote.id}));
 const dm=await across;
 assert.equal(dm.kind,'private');assert.equal(dm.to,remote.id);
 // Private room membership never leaks to public chat directory.
 const privatePlayer=await connected(url);t.after(()=>privatePlayer.terminate());
 const hidden=await join(privatePlayer,'SECRETROOM','PrivateGuest','AAAABBBB000099998888');
 srv.rooms.get('WORLD1').get(p.id).lastChat=0;
 const err=recv(a,'chat-error');
 a.send(JSON.stringify({type:'chat',text:'Cannot enter private room',to:hidden.id}));
 assert.match((await err).message,/unavailable/i);
});
test('chat validates empty, oversized and rapid messages before broadcasting',async t=>{
 const srv=createWorldServer();srv.server.listen(0,'127.0.0.1');await once(srv.server,'listening');
 t.after(()=>srv.close());const url='ws://127.0.0.1:'+srv.server.address().port;
 const a=await connected(url);t.after(()=>a.terminate());
 const wel=recv(a,'welcome');a.send(JSON.stringify({type:'join',name:'Tester',code:'WORLD3'}));await wel;
 const empty=recv(a,'chat-error');a.send(JSON.stringify({type:'chat',text:'   '}));
 assert.match((await empty).message,/1–280/i);
 const oversized=recv(a,'chat-error');a.send(JSON.stringify({type:'chat',text:'A'.repeat(281)}));
 assert.match((await oversized).message,/1–280/i);
 const good=recv(a,'chat');a.send(JSON.stringify({type:'chat',text:'Hello'}));await good;
 const rapid=recv(a,'chat-error');a.send(JSON.stringify({type:'chat',text:'Too fast'}));
 assert.match((await rapid).message,/slow down/i);
});

test('CoOwner password authentication is separate from Owner, private, server-authorized and manually revoked',async t=>{
 const srv=createWorldServer({verifyCoOwner:pass=>pass==='coowner-test-password'});
 srv.server.listen(0,'127.0.0.1');await once(srv.server,'listening');t.after(()=>srv.close());
 const url='ws://127.0.0.1:'+srv.server.address().port;
 const ws=await connected(url),other=await connected(url);t.after(()=>{ws.terminate();other.terminate();});
 const state={zone:'frost',x:211,y:13,z:245,yaw:.3,hero:'Selene',skin:'n:selene'};
 async function join(sock,code,name){
   const welcome=recv(sock,'welcome');
   sock.send(JSON.stringify({type:'join',code,name,entry:'game',state}));
   return welcome;
 }
 const co=await join(ws,'WORLD1','TestCoOwner');
 const player=await join(other,'WORLD2','TestPlayer');
 const forbidden=recv(ws,'coowner-error');
 ws.send(JSON.stringify({type:'coowner-list'}));
 assert.match((await forbidden).message,/unlock/i);
 const wrong=recv(ws,'coowner-auth');
 ws.send(JSON.stringify({type:'coowner-auth',pass:'incorrect-password'}));
 assert.equal((await wrong).ok,false);
 const valid=recv(ws,'coowner-auth'),firstList=recv(ws,'coowner-players');
 ws.send(JSON.stringify({type:'coowner-auth',pass:'coowner-test-password'}));
 const auth=await valid;assert.equal(auth.ok,true);
 assert.match(auth.token,/^[0-9a-f]{64}$/);
 assert.equal((await firstList).players.find(p=>p.id===player.id)?.world,'WORLD2');
 assert.equal(srv.rooms.get('WORLD1').get(co.id).socket.coOwnerAuthorized,true);
 assert.equal(srv.rooms.get('WORLD1').get(co.id).socket.ownerAuthorized,undefined);
 const rejectedOwner=recv(ws,'owner-error');ws.send(JSON.stringify({type:'owner-list'}));
 assert.match((await rejectedOwner).message,/owner/i);
 const notify=recv(other,'joined'),teleport=recv(ws,'coowner-jump');
 ws.send(JSON.stringify({type:'coowner-jump',id:player.id}));
 const arrival=await teleport;
 assert.equal(arrival.world,'WORLD2');
 assert.equal(arrival.target.name,'TestPlayer');
 assert.equal((await notify).player.id,co.id);
 assert.equal(srv.rooms.get('WORLD2').get(co.id).x,211+2);
 assert.equal(srv.rooms.get('WORLD2').get(player.id).x,211);
 const locked=recv(ws,'coowner-locked');
 ws.send(JSON.stringify({type:'coowner-lock'}));
 assert.equal((await locked).ok,true);
 const denied=recv(ws,'coowner-error');ws.send(JSON.stringify({type:'coowner-jump',id:player.id}));
 assert.match((await denied).message,/unlock/i);
 const untrusted=await connected(url);t.after(()=>untrusted.terminate());
 await join(untrusted,'WORLD1','OtherTester');
 const rejectedResume=recv(untrusted,'coowner-auth');
 untrusted.send(JSON.stringify({type:'coowner-resume',token:auth.token}));
 assert.equal((await rejectedResume).ok,false,'manual lock revokes bearer token on server');
});
test('CoOwner session token resumes across reconnect until explicit manual lock',async t=>{
 const srv=createWorldServer({verifyCoOwner:pass=>pass==='coowner-test-password'});
 srv.server.listen(0,'127.0.0.1');await once(srv.server,'listening');t.after(()=>srv.close());
 const url='ws://127.0.0.1:'+srv.server.address().port;
 const a=await connected(url);t.after(()=>a.terminate());
 const state={zone:'town',x:0,y:0,z:14,yaw:0,hero:'Aldric'};
 let welcome=recv(a,'welcome');
 a.send(JSON.stringify({type:'join',code:'WORLD1',name:'CoOwnerTester',state}));
 await welcome;
 let auth=recv(a,'coowner-auth');
 a.send(JSON.stringify({type:'coowner-auth',pass:'coowner-test-password'}));
 const token=(await auth).token;assert.ok(token);
 a.close();await once(a,'close');
 const b=await connected(url);t.after(()=>b.terminate());
 welcome=recv(b,'welcome');
 b.send(JSON.stringify({type:'join',code:'WORLD1',name:'CoOwnerTester',entry:'resume',state}));
 const p=await welcome;
 auth=recv(b,'coowner-auth');
 b.send(JSON.stringify({type:'coowner-resume',token}));
 const resumed=await auth;
 assert.equal(resumed.ok,true);assert.equal(resumed.resumed,true);
 assert.equal(srv.rooms.get('WORLD1').get(p.id).socket.coOwnerAuthorized,true);
});

test('3D multiplayer players turn through angle wrap and preserve idle facing',()=>{
 assert.ok(Math.abs(nextRemoteYaw(Math.PI-.05,-Math.PI+.05,.05)-Math.PI)<.12,'heading crosses -pi / pi seam');
 assert.ok(nextRemoteYaw(0,Math.PI/2,.1)>1,'remote player visibly turns toward transmitted heading');
 assert.equal(nextRemoteYaw(1.2,1.2,.05),1.2,'idle character holds its facing');
 assert.equal(nextRemoteYaw(0,NaN,.05),0,'invalid network heading does not corrupt rig');
});
test('world chat sender role is determined on server, not claimed in message',async t=>{
 const srv=createWorldServer({verifyCoOwner:pass=>pass==='test-only-pass'});
 srv.server.listen(0,'127.0.0.1');await once(srv.server,'listening');t.after(()=>srv.close());
 const url='ws://127.0.0.1:'+srv.server.address().port;
 const a=await connected(url),b=await connected(url);
 t.after(()=>{a.terminate();b.terminate();});
 const state={zone:'town',x:0,y:0,z:14,yaw:0,hero:'Aldric'};
 const wa=recv(a,'welcome');a.send(JSON.stringify({type:'join',code:'WORLD1',name:'Deputy',state}));await wa;
 const wb=recv(b,'welcome');b.send(JSON.stringify({type:'join',code:'WORLD1',name:'Friend',state}));await wb;
 const verify=recv(a,'coowner-auth');a.send(JSON.stringify({type:'coowner-auth',pass:'test-only-pass'}));assert.equal((await verify).ok,true);
 const delivered=recv(b,'chat');
 a.send(JSON.stringify({type:'chat',text:'Meeting in town',role:'owner'}));
 const message=await delivered;
 assert.equal(message.role,'coowner');
 assert.equal(message.text,'Meeting in town');
 const unauthorized=recv(b,'chat-error');
 b.send(JSON.stringify({type:'chat',text:'\u0000hidden'}));
 assert.match((await unauthorized).message,/characters|text/i);
});
test('Owner server access token persists across reconnect and Lock Owner revokes it',async t=>{
 const srv=createWorldServer({verifyOwner:pass=>pass==='test-owner-secret'});
 srv.server.listen(0,'127.0.0.1');await once(srv.server,'listening');t.after(()=>srv.close());
 const url='ws://127.0.0.1:'+srv.server.address().port;
 const state={zone:'town',x:0,y:0,z:14,yaw:0,hero:'Aldric'};
 const a=await connected(url);t.after(()=>a.terminate());
 let welcome=recv(a,'welcome');a.send(JSON.stringify({type:'join',code:'WORLD1',name:'VerifiedOwner',state}));await welcome;
 let auth=recv(a,'owner-auth');a.send(JSON.stringify({type:'owner-auth',pass:'test-owner-secret'}));
 const token=(await auth).token;assert.match(token,/^[a-f0-9]{64}$/);
 a.close();await once(a,'close');
 const b=await connected(url);t.after(()=>b.terminate());
 welcome=recv(b,'welcome');b.send(JSON.stringify({type:'join',code:'WORLD1',name:'VerifiedOwner',entry:'resume',state}));await welcome;
 auth=recv(b,'owner-auth');b.send(JSON.stringify({type:'owner-resume',token}));
 assert.equal((await auth).ok,true);
 const locked=recv(b,'owner-locked');b.send(JSON.stringify({type:'owner-lock'}));assert.equal((await locked).ok,true);
 const refused=recv(b,'owner-auth');b.send(JSON.stringify({type:'owner-resume',token}));
 assert.equal((await refused).ok,false);
});

test('legacy multiplayer orientation uses stable transmitted yaw before fallback',()=>{
 assert.equal(remoteFacing(0,0,1,0,true),Math.PI/2,'moving east faces east when legacy heading is frozen');
 assert.equal(remoteFacing(0,0,1,0,true),Math.PI/2,'does not oscillate when next frozen frame arrives');
 assert.equal(remoteFacing(0,1.1,1,0,true),1.1,'a real in-place yaw change wins over fallback');
 assert.equal(remoteFacing(0,0,1,0,false),0,'idle skin holds its facing');
});
