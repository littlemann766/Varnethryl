/* Varnethryl custom HUD layout: touch drag + independent scale, portrait/landscape. */
(function(){
'use strict';
const KEY='vn.hud.layout.v1';
const controls=[
 ['#stick','Joystick'],['#runBtn','Walk / Run'],['#jumpBtn','Jump'],
 ['#staminaHud','Stamina'],['#cinderFlyControls','Flight'],
 ...[0,1,2,3,4].map((n)=>['#cb .sl.b'+n,n===0?'Basic Attack':n===4?'Ultimate':'Skill '+n]),
 ...['dodge','block','jump','lock','potion','swap'].map((k)=>['#cb .cl button[data-a="'+k+'"]',k]),
 ['#cb .cx','Combat pad'],['#cb .vn-exp','XP bar'],['#cb .vit','Vitals'],
 ['#cb .tp','Enemy health'],['#cb .top','Combat options']
];
const css=document.createElement('style');css.id='vnHudEditorStyle';
css.textContent=
 '#vnHudEditorPanel{position:fixed;z-index:9000;top:calc(max(8px,env(safe-area-inset-top)) + 51px);left:8px;right:8px;padding:9px;background:linear-gradient(145deg,#2b1837f5,#141324fb);border:2px ridge #c49c61;border-radius:12px;box-shadow:0 8px 22px #000b;color:#fce5be;font:700 11px/1.35 VarnCinzel,Georgia,serif;touch-action:manipulation}'
 +'#vnHudEditorPanel[hidden]{display:none!important}'
 +'#vnHudEditorPanel strong{font-size:14px}#vnHudEditorPanel .hed-row{display:flex;align-items:center;flex-wrap:wrap;gap:5px;margin-top:7px}'
 +'#vnHudEditorPanel .hed-name{flex:1;min-width:110px;color:#f0caff}'
 +'#vnHudEditorPanel button{min-width:38px;min-height:40px;padding:6px 9px;color:#fff0ce;background:linear-gradient(#492c58,#21162c);border:1px solid #b78c50;border-radius:7px;font:700 12px VarnCinzel,Georgia,serif}'
 +'#vnHudEditorPanel button[data-hud-action="save"]{background:linear-gradient(#956c36,#4b2e20);border-color:#f1ca84}'
 +'body.vn-hud-editing{touch-action:none!important}'
 +'body.vn-hud-editing .vn-hud-movable{outline:2px dashed #d2a6f5!important;outline-offset:3px!important;touch-action:none!important}'
 +'body.vn-hud-editing .vn-hud-selected{outline:3px solid #ffdc78!important;outline-offset:4px!important}'
 +'@media(orientation:landscape) and (max-height:470px){#vnHudEditorPanel{top:max(3px,env(safe-area-inset-top));padding:4px}#vnHudEditorPanel .hed-row{margin-top:3px}#vnHudEditorPanel button{min-height:34px}}';
document.head.appendChild(css);
const empty=()=>({portrait:{},landscape:{}});
const clone=x=>JSON.parse(JSON.stringify(x));
const clamp=(n,min,max)=>Math.min(max,Math.max(min,n));
const orient=()=>innerWidth>=innerHeight?'landscape':'portrait';
let saved=empty();
try{const j=JSON.parse(localStorage.getItem(KEY)||'null');if(j&&j.portrait&&j.landscape)saved=j;}catch(e){}
let staged=clone(saved),on=false,chosen=null,drag=null;
const panel=document.createElement('section');panel.id='vnHudEditorPanel';panel.hidden=true;panel.setAttribute('aria-label','Customize game controls');
panel.innerHTML='<strong>✦ Edit HUD</strong><div>Tap and drag a control. Choose − or + to resize. Portrait and landscape save separately.</div>'
 +'<div class="hed-row"><span class="hed-name" id="vnHudEditName">Tap a control</span><button type="button" data-hud-action="smaller" aria-label="Smaller">−</button><button type="button" data-hud-action="larger" aria-label="Larger">+</button><button type="button" data-hud-action="reset">Reset</button></div>'
 +'<div class="hed-row"><button type="button" data-hud-action="resetall">Reset layout</button><button type="button" data-hud-action="cancel">Cancel</button><button type="button" data-hud-action="save">Save HUD ✓</button></div>';
document.body.appendChild(panel);
const nameEl=panel.querySelector('#vnHudEditName');
const items=()=>controls.map(([key,name])=>({key,name,el:document.querySelector(key)})).filter(i=>i.el);
function refresh(){
 const entries=(on?staged:saved)[orient()]||{};
 for(const {key,el} of items()){
  const c=entries[key];
  if(c&&Number.isFinite(c.x)&&Number.isFinite(c.y)&&Number.isFinite(c.s)){
   el.style.setProperty('translate',Math.round(clamp(c.x,-1.5,1.5)*innerWidth)+'px '+Math.round(clamp(c.y,-1.5,1.5)*innerHeight)+'px','important');
   el.style.setProperty('scale',clamp(c.s,.65,1.8).toFixed(2),'important');
  }else{el.style.removeProperty('translate');el.style.removeProperty('scale');}
  el.classList.toggle('vn-hud-movable',on);
  el.classList.toggle('vn-hud-selected',on&&chosen===key);
 }
}
function info(){
 const row=controls.find(x=>x[0]===chosen);
 nameEl.textContent=row?row[1]+' · '+Math.round(100*(staged[orient()][chosen]?.s||1))+'%':'Tap a control';
}
function open(){
 if(on)return;
 document.getElementById('vnQuickMenu')?.setAttribute('hidden','');
 document.getElementById('vnMenuBtn')?.setAttribute('aria-expanded','false');
 staged=clone(saved);chosen=null;drag=null;on=true;panel.hidden=false;
 document.body.classList.add('vn-hud-editing');refresh();info();
}
function close(commit){
 if(!on)return;
 if(commit){saved=clone(staged);try{localStorage.setItem(KEY,JSON.stringify(saved));}catch(e){console.warn('HUD save failed',e);}}
 else staged=clone(saved);
 on=false;drag=null;chosen=null;panel.hidden=true;
 document.body.classList.remove('vn-hud-editing');refresh();
}
function findControl(t){
 if(!(t instanceof Element))return null;
 for(const [key] of controls){const el=document.querySelector(key);if(el&&el.contains(t)&&el.getClientRects().length)return {key,el};}
 return null;
}
document.addEventListener('pointerdown',e=>{
 if(!on||panel.contains(e.target))return;
 const match=findControl(e.target);
 e.preventDefault();e.stopImmediatePropagation();
 if(!match)return;
 chosen=match.key;const c=staged[orient()][chosen]||{x:0,y:0,s:1};
 drag={pointer:e.pointerId,x:e.clientX,y:e.clientY,initialX:c.x,initialY:c.y,
  s:c.s,w:Math.max(1,innerWidth),h:Math.max(1,innerHeight),rect:match.el.getBoundingClientRect()};
 refresh();info();
},true);
document.addEventListener('pointermove',e=>{
 if(!on||panel.contains(e.target))return;
 e.preventDefault();e.stopImmediatePropagation();
 if(!drag||drag.pointer!==e.pointerId)return;
 const d=drag,r=d.rect;
 const dx=clamp(e.clientX-d.x,32-r.right,d.w-r.left-32);
 const dy=clamp(e.clientY-d.y,32-r.bottom,d.h-r.top-32);
 staged[orient()][chosen]={x:d.initialX+dx/d.w,y:d.initialY+dy/d.h,s:d.s};
 refresh();info();
},true);
for(const event of ['pointerup','pointercancel'])document.addEventListener(event,e=>{
 if(!on||panel.contains(e.target))return;
 e.preventDefault();e.stopImmediatePropagation();
 if(drag&&drag.pointer===e.pointerId)drag=null;
},true);
document.addEventListener('click',e=>{
 if(!on||panel.contains(e.target))return;
 e.preventDefault();e.stopImmediatePropagation();
},true);
panel.addEventListener('click',e=>{
 const b=e.target.closest('button[data-hud-action]');if(!b)return;
 const act=b.dataset.hudAction;
 if(act==='save'){close(true);return;}
 if(act==='cancel'){close(false);return;}
 const map=staged[orient()];
 if(act==='resetall'){staged[orient()]={};chosen=null;refresh();info();return;}
 if(!chosen)return;
 if(act==='reset'){delete map[chosen];refresh();info();return;}
 const c=map[chosen]||(map[chosen]={x:0,y:0,s:1});
 c.s=clamp(Math.round((c.s+(act==='larger'?.1:-.1))*100)/100,.65,1.8);
 refresh();info();
});
document.getElementById('vnEditHud')?.addEventListener('click',open);
addEventListener('resize',()=>{drag=null;refresh();info();});
document.addEventListener('keydown',e=>{
 if(on&&e.key==='Escape'){e.preventDefault();e.stopImmediatePropagation();close(false);}
},true);
// Combat HUD is loaded asynchronously when the game is entered. Apply saved
// positions to any new HUD nodes, without watching attribute/style changes.
let queued=false;
new MutationObserver(list=>{
 if(!list.some(m=>m.addedNodes.length||m.removedNodes.length)||queued)return;
 queued=true;
 requestAnimationFrame(()=>{queued=false;refresh();});
}).observe(document.body,{childList:true,subtree:true});
refresh();
window.__vnHudEditor={open,close,refresh,isEditing:()=>on};
})();