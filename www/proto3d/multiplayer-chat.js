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
 let roster=[],worldCode='',connected=false,selfId='';
 const persist=()=>save(STORE,JSON.stringify(friends));
 const sayStatus=s=>{status.textContent=s;};
 const open=()=>{root.hidden=false;trigger?.setAttribute('aria-expanded','true');refresh();};
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
 showFriends(false);
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
 function showMessage(m){
   if(!m||typeof m.text!=='string')return;
   const privateMsg=m.kind==='private';
   const dest=privateMsg?privateFeed:worldFeed;
   const line=create('div',privateMsg?'vn-chat-line vn-chat-dm':'vn-chat-line');
   const sender=m.from===selfId?'You':String(m.name||'Player').slice(0,20);
   const stamp=Number.isFinite(m.time)?new Date(m.time).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'}):'';
   line.appendChild(create('strong','',sender+(privateMsg?' · PRIVATE':'')),
     create('span','vn-chat-time',stamp),
     create('div','vn-chat-body',m.text.slice(0,280)));
   dest.appendChild(line);
   while(dest.children.length>60)dest.firstElementChild.remove();
   dest.scrollTop=dest.scrollHeight;
   if(privateMsg&&root.hidden)trigger?.classList.add('vn-chat-unread');
 }
 sendRow.addEventListener('submit',e=>{
   e.preventDefault();const text=input.value.trim();if(!text)return;
   if(!connected||!isOnline()){sayStatus('Join a multiplayer world to chat.');return;}
   const to=recipient.value||null;
   if(sendChat(text,to)){input.value='';sayStatus(to?'Private message sent.':'World message sent.');}
 });
 return {
  getFriendCode:()=>myCode,
  setOnline:(online,code,id)=>{connected=!!online;worldCode=code||'';selfId=id||'';
   if(!online){roster=[];refresh();}
   sayStatus(online?'Connected to '+worldCode+' · chat available.':'Offline — chat requires multiplayer.');
  },
  setRoster:peers=>{roster=Array.isArray(peers)?peers.filter(p=>typeof p?.id==='string'&&p.id!==selfId):[];refresh();},
  receiveChat:showMessage,
  error:s=>sayStatus(String(s||'Chat unavailable.')),
  dispose:()=>{closeChat();root.replaceChildren();}
 };
}
