// Varnethryl full-screen HUD: DOM overlay on the edge-to-edge world canvas. Reads game state; never writes to the render loop.
import * as Settings from './settings.js';
import {HUD_CONFIG} from './hud-config.js';
const $=id=>document.getElementById(id);
const clamp=(n,a,b)=>Math.max(a,Math.min(b,n));
let api=null,hud=null;
const I=(p,v='0 0 24 24')=>`<svg viewBox="${v}" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${p}</svg>`;
export const ICON={
 book:I('<path d="M4 5.5C4 4.7 4.7 4 5.5 4H11v15H5.5A1.5 1.5 0 0 0 4 20.5zM20 5.5c0-.8-.7-1.5-1.5-1.5H13v15h5.5c.8 0 1.5.7 1.5 1.5z"/><path d="M6.5 8H9M6.5 11H9M15 8h2.5M15 11h2.5"/>'),
 bag:I('<path d="M8 8V6.5A2.5 2.5 0 0 1 10.5 4h3A2.5 2.5 0 0 1 16 6.5V8"/><path d="M5.5 8h13l1 11.2a1 1 0 0 1-1 1.1H5.5a1 1 0 0 1-1-1.1z"/><path d="M9.5 12.5h5"/>'),
 compass:I('<circle cx="12" cy="12" r="8.5"/><path d="m15.6 8.4-2 5.2-5.2 2 2-5.2z" fill="currentColor" fill-opacity=".35"/><path d="M12 3.5v1.6M12 18.9v1.6M3.5 12h1.6M18.9 12h1.6"/>'),
 menu:I('<path d="M5 7h14M5 12h14M5 17h14"/>'),
 flask:I('<path d="M9.5 3.5h5M10.5 3.5v5.2L5.6 17a2.4 2.4 0 0 0 2.1 3.5h8.6a2.4 2.4 0 0 0 2.1-3.5l-4.9-8.3V3.5"/><path d="M8 14.5h8" />'),
 leaf:I('<path d="M5 19c0-8 5-13 14-14 0 9-5 14-13 14"/><path d="M5 19c3-5 6-8 10-10"/>'),
 chat:I('<path d="M4.5 6.5A2 2 0 0 1 6.5 4.5h11a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2H11l-4.5 3.5v-3.5h0a2 2 0 0 1-2-2z"/>'),
 send:I('<path d="M4 12 20 5l-4.5 15-3.5-6z"/>')};
// Crest colours for each hero (FACTIONS.md): Lionguard blue/gold, Verdant Fang green, Starforge sapphire, Umbral Veil purple/crimson, Dawnsong gold/sky.
const CREST={Lionguard:['#4a7fe0','#e0bb62'],'Verdant Fang':['#4aa564','#c9b98a'],Starforge:['#5aa0ff','#d7e4f5'],'Umbral Veil':['#a24bd8','#c0364f'],Dawnsong:['#f0c24f','#8fd0ff']};
const FACTION={};[['Lionguard','Sir Aldric','Dame Seraphine','Finn Valecourt','Orin Ashlance'],['Verdant Fang','Rook Wildbane','Lady Elira','Mirelle Thornroot','Garruk Stonefist'],['Starforge','Rowan Firebrand','Selene Frostveil','Kael Runebinder','Brynn Cogwright'],['Umbral Veil','Darius Umbral','Morwen Blackveil','Nyx Varrin','Vesper Crowe'],['Dawnsong','Brother Thorne','Cedric Vale','Asha Ironfist','Talia Stormcall']].forEach(([f,...n])=>n.forEach(x=>FACTION[x]=f));
export const factionOf=name=>FACTION[name]||'Lionguard';
// ---------- painted background slot (parallax layers) ----------
const bg={layers:[]};
function loadBg(){const q=new URLSearchParams(location.search).get('bgdemo');const cfg=q?HUD_CONFIG.demoBackground:HUD_CONFIG.background;
 bg.layers=(cfg.layers||[]).map(l=>{const img=new Image();img.src=l.src;return {...l,img}})}
loadBg();
export function drawBackground(C,cw,ch,camX,camY){const ready=bg.layers.filter(l=>l.img.complete&&l.img.naturalWidth);if(!ready.length)return false;
 const px=clamp(camX/Math.max(1,1850-cw),0,1),py=clamp(camY/Math.max(1,1210-ch),0,1);
 for(const l of ready){const iw=l.img.naturalWidth,ih=l.img.naturalHeight,k=Math.max(cw/iw,ch/ih)*(l.scale||1),dw=iw*k,dh=ih*k,sp=l.speed??.5;
  const x=-(dw-cw)*(.5+(px-.5)*sp),y=-(dh-ch)*clamp((l.y??.5)+(py-.5)*sp*.4,0,1);
  C.imageSmoothingEnabled=true;C.drawImage(l.img,x,y,dw,dh);C.imageSmoothingEnabled=false}
 return true}
// ---------- potions ----------
const POT={hp:{name:'Health potion',key:'Q',icon:'flask',cls:'hp'},mp:{name:'Focus potion',key:'E',icon:'flask',cls:'mp'},buff:{name:'Bloomtonic (+25% damage, 20s)',key:'R',icon:'leaf',cls:'buff'}};
let potCd=0;
export function grantPotion(chance=.12){if(!api||Math.random()>=chance)return;const k=['hp','hp','mp','buff'][Math.floor(Math.random()*4)];const p=potions();p[k]=Math.min(99,p[k]+1);api.toast(`Found a ${POT[k].name.toLowerCase().replace(/ \(.*/,'')}.`)}
function potions(){return api.state.potions??={hp:5,mp:3,buff:2}}
function usePotion(k){const p=potions(),rt=api.runtime,id=api.state.active;if(!p[k]){api.toast('None left. Defeat enemies to find more.');return}
 if(rt.time<potCd)return;
 if(k==='hp'){const m=api.heroMax(id);if((rt.hp[id]??m)>=m){api.toast('Already at full health.');return}rt.hp[id]=Math.min(m,(rt.hp[id]??m)+Math.round(m*.4));api.log(`${api.HEROES[id].name} drank a health potion.`)}
 else if(k==='mp'){if(api.Controls.chargeOf(id)>=100){api.toast('Ultimate is already charged.');return}api.Controls.addCharge(id,35)}
 else rt.buffUntil=rt.time+20000;
 p[k]--;potCd=rt.time+1200;Settings.sfx('ui');Settings.haptic(10);renderPotions(true)}
function renderPotions(force){const p=potions();for(const k of Object.keys(POT)){const b=$('pot-'+k);if(!b)continue;b.querySelector('small').textContent=p[k];b.disabled=!p[k];b.classList.toggle('empty',!p[k]);if(k==='buff')b.classList.toggle('active',api.runtime.time<(api.runtime.buffUntil||0))}}
// ---------- build DOM ----------
function build(){const f=document.querySelector('.worldFrame');hud=document.createElement('div');hud.id='hud';
 hud.innerHTML=`
 <div id="hudHero" class="hudPanel" role="group" aria-label="Hero status">
  <div class="heroRow"><div class="face"><img id="hudFace" alt=""><b class="lvl" id="hudLvl">1</b></div>
   <div class="heroInfo"><div class="hname" id="hudName"></div>
    <div class="bar hp"><i id="hudHp"></i><span id="hudHpTxt"></span></div>
    <div class="bar mp"><i id="hudMp"></i><span id="hudMpTxt"></span></div></div></div>
  <div class="party" id="hudParty"></div></div>
 <img id="hudLogo" src="${HUD_CONFIG.logo}" alt="Varnethryl" draggable="false">
 <div id="hudMenu" class="hudMenu" role="toolbar" aria-label="Menu">
  <button class="ib" id="hudJournal" type="button" aria-label="Quest journal">${ICON.book}</button>
  <button class="ib" id="hudBag" type="button" aria-label="Inventory">${ICON.bag}</button>
  <button class="ib" id="hudMap" type="button" aria-label="World map">${ICON.compass}</button>
  <button class="ib" id="hudMain" type="button" aria-label="Main menu">${ICON.menu}</button></div>
 <div id="hudMini" class="mini" role="button" tabindex="0" aria-label="Minimap. Tap for world map"><canvas id="hudMiniCv" width="240" height="240"></canvas><svg class="mring" viewBox="0 0 100 100" aria-hidden="true"><circle cx="50" cy="50" r="47.5"/><circle cx="50" cy="50" r="43" class="in"/><path d="M50 1.5l3 6h-6z" class="n"/></svg><em id="hudZone"></em></div>
 <div id="hudQuest" class="hudPanel quest" role="group" aria-label="Quest tracker"><h4 id="hudQTitle"></h4><ul><li id="hudQ1"></li><li id="hudQ2"></li></ul></div>
 <div id="hudChat" class="hudPanel chat" role="group" aria-label="Chat"><div class="tabs" role="tablist"><button class="on" data-ct="general" type="button" role="tab">General</button><button data-ct="party" type="button" role="tab">Party</button><button data-ct="system" type="button" role="tab">System</button></div><div class="log" id="hudLog" aria-live="polite"></div><form class="in" id="hudChatForm" autocomplete="off"><span class="cic">${ICON.chat}</span><input id="hudChatIn" maxlength="120" placeholder="Type a message…" aria-label="Chat message"><button type="submit" aria-label="Send">${ICON.send}</button></form></div>
 <div id="hudPotions" class="pots" role="toolbar" aria-label="Potions">${Object.entries(POT).map(([k,v])=>`<button type="button" class="pt ${v.cls}" id="pot-${k}" aria-label="${v.name}" title="${v.name} (${v.key})">${ICON[v.icon]}<small>0</small><kbd>${v.key}</kbd></button>`).join('')}<button type="button" class="pt bagb" id="hudBag2" aria-label="Inventory">${ICON.bag}</button></div>
 <div id="skillDivider" aria-hidden="true"><i></i><b></b><i></i></div>`;
 f.insertBefore(hud,f.querySelector('.touchControls'));
 // skill number badges under the buttons already exist in index.html (.num); give the divider its own element above.
}
// ---------- layout class (web / land / port), small-screen collapse ----------
function sizeClass(){const w=innerWidth,h=innerHeight,H=document.documentElement,port=h>w,ctl=H.dataset.ctl;
 const mode=port?'port':(w<900||(ctl==='stick'&&h<620))?'land':'web',changed=H.dataset.hud!==mode;H.dataset.hud=mode;
 H.dataset.hudSmall=(mode==='land'&&(h<360||w<640))||(mode==='port'&&(w<360||h<640))?'1':'';
 const s=Settings.get();H.style.setProperty('--hs',s.hudScale);H.style.setProperty('--ho',s.hudOpacity);
 H.classList.toggle('hud-noquest',!s.showQuest);H.classList.toggle('hud-noparty',!s.showParty);H.classList.toggle('hud-nochat',!s.showChat);
 // the divider belongs to the default skill bar; hide it once the player has moved any skill button
 const L=s.layout||{};$('skillDivider')?.classList.toggle('off',['touchAttack','touchSkill','skillHeavy','skillSuper','skillUlt'].some(k=>L[k]));if(changed&&!Settings.isEditing())Settings.applyLayout()}
// ---------- per-frame-ish refresh (called ~5x/s) ----------
let sig={},chatTab='general',chatLocal=[];
const set=(el,t)=>{if(el&&el.textContent!==String(t))el.textContent=t};
export function refresh(){if(!api||!hud)return;const st=api.state,rt=api.runtime,id=st.active,h=api.HEROES[id];
 const fac=factionOf(h.name),[c1,c2]=CREST[fac];hud.style.setProperty('--crest',c1);hud.style.setProperty('--crest2',c2);
 if(sig.hero!==id){sig.hero=id;$('hudFace').src=h.image;$('hudFace').alt=h.name;set($('hudName'),h.name)}
 set($('hudLvl'),api.level(id));
 const max=api.heroMax(id),hp=Math.round(clamp(rt.hp[id]??max,0,max));$('hudHp').style.width=(hp/max*100)+'%';set($('hudHpTxt'),`${api.fmt(hp)} / ${api.fmt(max)}`);
 const ch=Math.floor(api.Controls.chargeOf(id));$('hudMp').style.width=ch+'%';set($('hudMpTxt'),`Focus ${ch} / 100`);
 // party: everyone except the controlled hero; 3 heroes in total in normal play, 4 in boss fights (limited by the guild's party capacity)
 const total=st.zone==='boss'?4:3,others=st.party.filter(p=>p!==id).slice(0,total-1);const ps=others.join(',')+'|'+total;
 if(sig.party!==ps){sig.party=ps;$('hudParty').innerHTML=others.map(p=>{const hh=api.HEROES[p];return `<button type="button" class="pm" data-switch="${p}" aria-label="Switch to ${api.esc(hh.name)}"><img src="${hh.image}" alt=""><span class="pn">${api.esc(hh.name)}</span><b class="pl"></b><i class="pb"><u></u></i></button>`}).join('');hud.classList.toggle('boss',st.zone==='boss')}
 $('hudParty').querySelectorAll('.pm').forEach(b=>{const p=+b.dataset.switch,m=api.heroMax(p);b.querySelector('u').style.width=clamp((rt.hp[p]??m)/m*100,0,100)+'%';set(b.querySelector('.pl'),api.level(p))});
 // quest tracker mirrors the quest card in the adventure side panel
 set($('hudQTitle'),$('questTitle').textContent);set($('hudQ1'),$('questCopy').textContent);const qn=$('questNumbers').textContent;set($('hudQ2'),qn);$('hudQ2').style.display=qn&&/\d/.test(qn)?'':'none';
 const z=api.ZONES.find(z=>z.id===st.zone);set($('hudZone'),z?z.name:'');
 renderPotions();drawMini();renderChat()}
// ---------- minimap ----------
function drawMini(){const cv=$('hudMiniCv');if(!cv||!cv.offsetWidth)return;const c=cv.getContext('2d'),W=cv.width,rt=api.runtime,st=api.state,z=api.ZONES.find(z=>z.id===st.zone);if(!z)return;
 const R=W/2,span=720,k=W/span,ox=rt.x-span/2,oy=rt.y-span/2,X=x=>(x-ox)*k,Y=y=>(y-oy)*k;
 c.save();c.clearRect(0,0,W,W);c.beginPath();c.arc(R,R,R-6,0,7);c.clip();
 const g=c.createRadialGradient(R,R,10,R,R,R);const kind=z.kind;const col=kind==='safe'?['#4f7a4a','#27422d']:kind==='wild'?['#3c6a47','#1c3a2a']:kind==='frost'?['#b9d4e4','#6f90a8']:['#6b6a63','#34383a'];g.addColorStop(0,col[0]);g.addColorStop(1,col[1]);c.fillStyle=g;c.fillRect(0,0,W,W);
 // road band + region edge
 c.fillStyle='rgba(206,178,120,.35)';c.fillRect(0,Y(280),W,(kind==='safe'?80:40)*k);
 c.strokeStyle='rgba(255,255,255,.07)';c.lineWidth=1;for(let x=Math.floor(ox/200)*200;x<ox+span;x+=200){c.beginPath();c.moveTo(X(x),0);c.lineTo(X(x),W);c.stroke()}for(let y=Math.floor(oy/200)*200;y<oy+span;y+=200){c.beginPath();c.moveTo(0,Y(y));c.lineTo(W,Y(y));c.stroke()}
 c.strokeStyle='rgba(0,0,0,.55)';c.lineWidth=6;c.strokeRect(X(0),Y(0),1850*k,1210*k);
 for(const [side] of Object.entries(z.portal||{})){c.fillStyle='#f3cc79';c.fillRect(X(side==='right'?1780:70)-5,Y(210),10,230*k)}
 for(const e of rt.enemy){if(e.hp<=0)continue;c.fillStyle=e.boss?'#ff4a64':'#e0705a';c.beginPath();c.arc(X(e.x),Y(e.y),e.boss?9:5,0,7);c.fill()}
 for(const id in rt.companions){c.fillStyle='#7fd0ff';c.beginPath();c.arc(X(rt.companions[id].x),Y(rt.companions[id].y),4.5,0,7);c.fill()}
 c.translate(R,R);c.rotate((rt.faceA||0)+Math.PI/2);c.fillStyle='#7fe3ff';c.strokeStyle='#04202c';c.lineWidth=2.5;c.beginPath();c.moveTo(0,-13);c.lineTo(9,10);c.lineTo(0,5);c.lineTo(-9,10);c.closePath();c.stroke();c.fill();c.restore()}
// ---------- chat ----------
function renderChat(){const lg=$('hudLog');if(!lg||!lg.offsetParent&&!lg.getClientRects().length)return;const logs=api.state.logs.slice().reverse();
 const rows=chatTab==='system'?logs.map(t=>({k:'sys',t})):chatTab==='party'?chatLocal.filter(m=>m.p).map(m=>({k:'me',t:m.t})):[...logs.slice(-4).map(t=>({k:'sys',t})),...chatLocal.map(m=>({k:'me',t:m.t}))];
 const s=chatTab+JSON.stringify(rows);if(s===sig.chat)return;sig.chat=s;lg.innerHTML=rows.slice(-6).map(r=>`<p class="${r.k}">${r.k==='me'?'<b>You:</b> ':''}${api.esc(r.t)}</p>`).join('')||'<p class="sys">Nothing here yet.</p>';lg.scrollTop=lg.scrollHeight}
// ---------- wiring ----------
export function onTab(tab){const on=tab==='adventure';document.body.classList.toggle('hud-on',on);document.body.classList.remove('menu-open');if(hud)sig.chat=null;if(on)requestAnimationFrame(()=>Settings.applyLayout())}
const mapModal=()=>{const Z=api.ZONES,st=api.state;api.modal(`<span class="eyebrow">WORLD MAP</span><h2>Travel</h2><div class="zoneButtons" id="hudZones">${Z.map(z=>`<button class="${st.zone===z.id?'gold':''}" data-zone="${z.id}">${api.esc(z.name)}${z.kind==='boss'?' ⚠':''}</button>`).join('')}</div><label class="micro" for="hudDiff">Titan Vault difficulty</label><select id="hudDiff" aria-label="Titan Vault difficulty">${[...$('bossDifficulty').options].map(o=>`<option value="${o.value}" ${o.value===st.bossDifficulty?'selected':''}>${api.esc(o.text)}</option>`).join('')}</select><p class="micro">Travel is instant in this prototype.</p>`);
 $('hudZones').addEventListener('click',e=>{if(e.target.closest('[data-zone]'))$('modal').close()});$('hudDiff').onchange=e=>{$('bossDifficulty').value=e.target.value;$('bossDifficulty').dispatchEvent(new Event('change'))}};
export function init(a){api=a;build();onTab('adventure');potions();
 $('hudJournal').onclick=()=>$('questBtn').click();$('hudBag').onclick=$('hudBag2').onclick=()=>api.switchTab('equipment');$('hudMap').onclick=mapModal;
 $('hudMini').onclick=mapModal;$('hudMini').onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();mapModal()}};
 $('hudMain').onclick=()=>document.body.classList.toggle('menu-open');
 document.addEventListener('pointerdown',e=>{if(document.body.classList.contains('menu-open')&&!e.target.closest('.topbar,.bottomNav,#hudMain'))document.body.classList.remove('menu-open')},true);
 $('hudHero').addEventListener('click',e=>{if(!e.target.closest('.pm'))$('hudHero').classList.toggle('open')});
 for(const k of Object.keys(POT))$('pot-'+k).addEventListener('pointerdown',e=>{if(document.querySelector('.worldFrame.editing'))return;e.preventDefault();usePotion(k)});
 $('hudChat').querySelector('.tabs').onclick=e=>{const b=e.target.closest('[data-ct]');if(!b)return;chatTab=b.dataset.ct;$('hudChat').querySelectorAll('.tabs button').forEach(x=>x.classList.toggle('on',x===b));sig.chat=null;renderChat()};
 $('hudChatForm').onsubmit=e=>{e.preventDefault();const i=$('hudChatIn'),t=i.value.trim();if(!t)return;chatLocal.push({t,p:chatTab==='party'});chatLocal=chatLocal.slice(-30);i.value='';sig.chat=null;renderChat()};
 $('hudChatIn').addEventListener('keydown',e=>e.stopPropagation());
 addEventListener('keydown',e=>{if(e.repeat||e.target.tagName==='INPUT'||e.target.tagName==='SELECT'||!api||document.querySelector('.worldFrame.editing')||!document.body.classList.contains('hud-on'))return;
  const k={q:'hp',e:'mp',r:'buff'}[e.key.toLowerCase()];if(k)usePotion(k);if(e.key==='Escape')document.body.classList.remove('menu-open')});
 for(const ev of ['resize','orientationchange','vn-hud','vn-controls'])addEventListener(ev,sizeClass);
 sizeClass();refresh();Settings.applyLayout();setInterval(()=>{if(document.body.classList.contains('hud-on')){sizeClass();refresh()}},200)}
