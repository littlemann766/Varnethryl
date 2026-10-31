/* Varnethryl test chat: world conversation + private messages + locally saved friends.
 * Messages are server-relayed, never inserted as HTML. Player codes are
 * convenience contacts, NOT authenticated accounts or verified CoOwner roles.
 */
export function createMultiplayerChat({sendChat,isOnline}){
 const STORE='vn.multiplayer.friends.v1', CODE='vn.multiplayer.friendCode.v1';
 const load=k=>{try{return localStorage.getItem(k)||'';}catch{return '';}};
 const save=(k,v)=>{try{localStorage.setItem(k,v);}catch{}};
 const validCode=s=>/^[A-Z0-9]{10,20}$/.test(s);
 let myCode=load(CODE);
 if(!validCode(myCode)){
   const bytes=new Uint8Array(10);
   crypto.getRandomValues(bytes);
   myCode=Array.from(bytes,b=>b.toString(16).padStart(2,'0')).join('').toUpperCase();
   save(CODE,myCode);
 }
 let friends=[];
 try{const parsed=JSON.parse(load(STORE)||'[]');if(Array.isArray(parsed))
   friends=parsed.filter(x=>x&&validCode(x.code)&&typeof x.name==='string')
     .slice(0,100).map(x=>({code:x.code,name:x.name.slice(0,20)}));}catch{}
 const root=document.getElementById('vnChatPanel');
 if(!root)return {getFriendCode:()=>myCode,receiveChat(){},setRoster(){},setOnline(){},dispose(){}};
 const trigger=document.getElementById('vnChatBtn');
 const create=(type,cls,txt)=>{const e=document.createElement(type);
   if(cls)e.className=cls;if(txt!==undefined)e.textContent=txt;return e;};
 const header=create('div','vn-chat-header');
 const title=create('strong','', 'Varnethryl Chat');
 const close=create('button','vn-chat-close','✕');close.type='button';close.setAttribute('aria-label','Close chat');
 header.append(title,close);
 const tabs=create('div','vn-chat-tabs');
 const worldTab=create('button','vn-chat-tab','World chat'),friendTab=create('button','vn-chat-tab','Friends');
 for(const b of [worldTab,friendTab])b.type='button';
 tabs.append(worldTab,friendTab);
 const status=create('small','vn-chat-status','Join multiplayer to send messages.');
 const worldTitle=create('div','vn-chat-subtitle','WORLD CHAT · same world');
 const worldFeed=create('div','vn-chat-feed');worldFeed.setAttribute('aria-live','polite');
 const friendsPane=create('div','vn-chat-friends');friendsPane.hidden=true;
 const friendHeading=create('div','vn-chat-subtitle','FRIENDS · this device');
 const friendCodeLine=create('div','vn-chat-code','Your friend code: '+myCode);
 const friendEntry=create('input','vn-chat-friend-code');friendEntry.type='text';
 friendEntry.maxLength=20;friendEntry.placeholder='Enter friend code';friendEntry.autocapitalize='characters';
 const friendAdd=create('button','','Add friend');friendAdd.type='button';
 const friendControls=create('div','vn-chat-add-row');friendControls.append(friendEntry,friendAdd);
 const friendsList=create('div','vn-chat-friend-list');
 const onlineTitle=create('div','vn-chat-subtitle','PLAYERS ONLINE · add as friend');
 const onlineList=create('div','vn-chat-online-list');
 friendsPane.append(friendHeading,friendCodeLine,friendControls,friendsList,onlineTitle,onlineList);
 const privateTitle=create('div','vn-chat-subtitle vn-chat-private-title','PRIVATE MESSAGES · only you and the recipient');
 const privateFeed=create('div','vn-chat-private-feed');
 privateFeed.setAttribute('role','log');privateFeed.setAttribute('aria-label','Private messages');
 privateFeed.setAttribute('aria-live','polite');
 const sendRow=create('form','vn-chat-compose');
 const recipient=create('select','vn-chat-recipient');
 recipient.setAttribute('aria-label','Message destination');
 const input=create('input','vn-chat-input');input.type='text';input.maxLength=280;
 input.placeholder='Type your message…';input.autocomplete='off';input.setAttribute('aria-label','Chat message');
 const sendBtn=create('button','vn-chat-send','Send');sendBtn.type='submit';
 sendRow.append(recipient,input,sendBtn);
 const note=create('small','vn-chat-note','Private messages go only to the selected online player. Friends are saved locally; they are not verified identities.');
 root.replaceChildren(header,tabs,status,worldTitle,worldFeed,friendsPane,privateTitle,privateFeed,sendRow,note);
 // A small in-world message log stays readable even when the full chat is closed.
 // This is only local UI; private messages are never broadcast as world chat.
 const live=create('div','vn-chat-live');live.id='vnChatLive';live.hidden=true;
 live.setAttribute('role','log');live.setAttribute('aria-label','Recent multiplayer messages');
 root.insertAdjacentElement('afterend',live);
 // Typing messages must not make the hero run, jump, cast skills or move the
 // camera. Stop chat events before the game's window keyboard shortcuts.
 for(const type of ['keydown','keyup','pointerdown'])root.addEventListener(type,e=>e.stopPropagation());
 let roster=[],worldCode='',connected=false,selfId='';
 // Relay message IDs are used to avoid duplicate displays after reconnects.
 // Keep the memory cost bounded during long multiplayer sessions.
 const messageIds=new Set(),idOrder=[];
 function firstDelivery(id){
  if(typeof id!=='string'||!id)return true;
  if(messageIds.has(id))return false;
  messageIds.add(id);idOrder.push(id);
  if(idOrder.length>300)messageIds.delete(idOrder.shift());
  return true;
 }
 const pending=[];let liveTimer=null;
 const markDelivery=(p,label,failed=false)=>{
   if(!p)return;
   clearTimeout(p.timer);
   p.line?.classList.toggle('vn-chat-failed',failed);
   if(p.delivery)p.delivery.textContent=' · '+label;
 };
 const clearPending=(reason)=>{
   for(const p of pending.splice(0))markDelivery(p,reason,true);
 };
 const persist=()=>save(STORE,JSON.stringify(friends));
 const sayStatus=s=>{status.textContent=s;};
 const open=()=>{root.hidden=false;live.hidden=true;trigger?.setAttribute('aria-expanded','true');trigger?.classList.remove('vn-chat-unread');refresh();};
 const closeChat=()=>{root.hidden=true;trigger?.setAttribute('aria-expanded','false');};
 trigger?.addEventListener('click',()=>root.hidden?open():closeChat());
 close.addEventListener('click',closeChat);
 function showFriends(value){
   friendsPane.hidden=!value;worldTitle.hidden=value;worldFeed.hidden=value;
   friendTab.setAttribute('aria-pressed',String(value));
   worldTab.setAttribute('aria-pressed',String(!value));
   refresh();
 }
 worldTab.addEventListener('click',()=>showFriends(false));
 friendTab.addEventListener('click',()=>showFriends(true));
 const addFriend=(code,name)=>{
   code=String(code||'').trim().toUpperCase();
   if(!validCode(code)){sayStatus('Friend codes must contain 10–20 letters/numbers.');return;}
   if(code===myCode){sayStatus('That is your own friend code.');return;}
   if(friends.some(f=>f.code===code)){sayStatus('Already on your friends list.');return;}
   if(friends.length>=100){sayStatus('The test friends list is full.');return;}
   friends.push({code,name:(name||'Player').slice(0,20)});persist();sayStatus('Added to your device friends list.');refresh();
 };
 friendAdd.addEventListener('click',()=>{const code=friendEntry.value;const match=roster.find(p=>p.friendCode===code.trim().toUpperCase());addFriend(code,match?.name);friendEntry.value='';});
 const option=(value,label)=>{const o=document.createElement('option');o.value=value;o.textContent=label;return o;};
 function choosePrivate(id){recipient.value=id;showFriends(false);input.focus();}
 function refresh(){
   const selected=recipient.value;
   recipient.replaceChildren(option('','World chat (everyone in this world)'));
   for(const p of roster)recipient.appendChild(option(p.id,'Private → '+p.name+' ('+p.world+')'));
   if(roster.some(p=>p.id===selected))recipient.value=selected;
   friendsList.replaceChildren();
   for(const f of friends){
     const live=roster.find(p=>p.friendCode===f.code);
     const row=create('div','vn-chat-contact');
     const name=create('span','',f.name+(live?' · Online ('+live.world+')':' · Offline'));
     const actions=create('div','vn-chat-contact-actions');
     if(live){const dm=create('button','','Message');dm.type='button';dm.addEventListener('click',()=>choosePrivate(live.id));actions.appendChild(dm);}
     const remove=create('button','','Remove');remove.type='button';
     remove.addEventListener('click',()=>{friends=friends.filter(x=>x.code!==f.code);persist();refresh();});
     actions.appendChild(remove);row.append(name,actions);friendsList.appendChild(row);
   }
   if(!friends.length)friendsList.appendChild(create('small','','No saved friends yet. Select an online player below or enter a friend code.'));
   onlineList.replaceChildren();
   for(const p of roster){
     const row=create('div','vn-chat-contact');
     const name=create('span','',p.name+' · '+p.world);
     const actions=create('div','vn-chat-contact-actions');
     const dm=create('button','','Private chat');dm.type='button';dm.addEventListener('click',()=>choosePrivate(p.id));
     actions.appendChild(dm);
     if(p.friendCode&&!friends.some(f=>f.code===p.friendCode)){
       const add=create('button','','+ Friend');add.type='button';add.addEventListener('click',()=>addFriend(p.friendCode,p.name));
       actions.appendChild(add);
     }
     row.append(name,actions);onlineList.appendChild(row);
   }
   if(!roster.length)onlineList.appendChild(create('small','','No other available players online.'));
 }
 function showLive(m){
   if(!connected)return;
   const recent=create('div',m.kind==='private'?'vn-chat-live-entry vn-chat-live-private':'vn-chat-live-entry');
   const who=m.from===selfId?'You':String(m.name||'Player').slice(0,20);
   recent.append(create('strong','',who+(m.kind==='private'?' · Private':'')+': '),
     create('span','',m.text.slice(0,280)));
   live.appendChild(recent);
   while(live.children.length>3)live.firstElementChild.remove();
   if(root.hidden)live.hidden=false;
   clearTimeout(liveTimer);
   liveTimer=setTimeout(()=>{live.hidden=true;},18000);
 }
 function showMessage(m,waiting=false){
   if(!m||typeof m.text!=='string')return null;
   const privateMsg=m.kind==='private';
   const dest=privateMsg?privateFeed:worldFeed;
   const line=create('div',privateMsg?'vn-chat-line vn-chat-dm':'vn-chat-line');
   const role=m.role==='coowner'?' · CoOwner':m.role==='owner'?' · Owner':'';
   const sender=(m.from===selfId?'You':String(m.name||'Player').slice(0,20))+role;
   const stamp=Number.isFinite(m.time)?new Date(m.time).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'}):'';
   const delivery=waiting?create('span','vn-chat-delivery',' · Sending…'):null;
   line.append(create('strong','',sender+(privateMsg?' · PRIVATE':'')),
     create('span','vn-chat-time',stamp),
     create('div','vn-chat-body',m.text.slice(0,280)));
   if(delivery)line.appendChild(delivery);
   dest.appendChild(line);
   while(dest.children.length>60)dest.firstElementChild.remove();
   dest.scrollTop=dest.scrollHeight;
   showLive(m);
   if(root.hidden)trigger?.classList.add('vn-chat-unread');
   return {line,delivery};
 }
 function receiveChat(m){
   if(!m||typeof m.text!=='string'||!firstDelivery(m.id))return;
   if(m.from===selfId){
     const index=pending.findIndex(p=>p.text===m.text && p.kind===m.kind &&
       p.to===(m.to||null));
     if(index>=0){
       const p=pending.splice(index,1)[0];
       markDelivery(p,'Delivered');
       sayStatus(p.to?'Private message delivered.':'World message delivered.');
       return; // The pending line is already visible: no duplicate self echo.
     }
   }
   showMessage(m);
 }
 function chatError(message){
   const p=pending.shift();
   if(p){
     markDelivery(p,'Not sent',true);
     if(!input.value)input.value=p.text; // Make retry possible without retyping.
   }
   sayStatus(String(message||'Chat unavailable.'));
 }
 sendRow.addEventListener('submit',e=>{
   e.preventDefault();const text=input.value.trim();if(!text)return;
   if(!connected||!isOnline()){sayStatus('Join a multiplayer world to chat.');return;}
   const to=recipient.value||null;
   if(!sendChat(text,to)){sayStatus('Message not sent — connection unavailable.');return;}
   const kind=to?'private':'world';
   const item=showMessage({kind,to,from:selfId,name:'You',text,time:Date.now()},true);
   const p={text,to,kind,...item,timer:null};
   p.timer=setTimeout(()=>{
     const at=pending.indexOf(p);
     if(at>=0){pending.splice(at,1);markDelivery(p,'Not confirmed — check connection',true);
       sayStatus('Message not confirmed by the server. Reconnect or try again.');}
   },10000);
   pending.push(p);
   input.value='';
   sayStatus('Sending…');
 });
 // Initialize chat only after recipient-option helper and roster are ready.
 showFriends(false);
 return {
  getFriendCode:()=>myCode,
  setOnline:(online,code,id)=>{connected=!!online;worldCode=code||'';selfId=id||'';
   if(!online){roster=[];clearPending('Not sent — disconnected');live.hidden=true;clearTimeout(liveTimer);refresh();}
   sayStatus(online?'Connected to '+worldCode+' · chat available.':'Offline — chat requires multiplayer.');
  },
  setRoster:peers=>{roster=Array.isArray(peers)?peers.filter(p=>typeof p?.id==='string'&&p.id!==selfId):[];refresh();},
  receiveChat,
  error:chatError,
  dispose:()=>{clearPending('Disconnected');clearTimeout(liveTimer);closeChat();live.remove();root.replaceChildren();}
 };
}
