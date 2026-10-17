// Varnethryl settings + movable on-screen buttons. Additive: stored in localStorage and in save envelope state.settings{}.
const SKEY='varnethryl_settings_v1';
export const DEFAULTS={musicVolume:0.5,sfxVolume:0.8,haptics:true,reducedMotion:null,textSize:'normal',layout:{},updatedAt:0};
const clamp=(n,a,b)=>Math.max(a,Math.min(b,n));
const $=id=>document.getElementById(id);
let S={...DEFAULTS,layout:{}},stateRef=null,onSave=()=>{};
const mq=window.matchMedia?matchMedia('(prefers-reduced-motion: reduce)'):{matches:false};
export const get=()=>S;
export const reducedMotion=()=>S.reducedMotion===null?mq.matches:!!S.reducedMotion;
function sanitize(o){o=o&&typeof o==='object'?o:{};const r={...DEFAULTS,layout:{}};
 if(typeof o.musicVolume==='number')r.musicVolume=clamp(o.musicVolume,0,1);
 if(typeof o.sfxVolume==='number')r.sfxVolume=clamp(o.sfxVolume,0,1);
 if(typeof o.haptics==='boolean')r.haptics=o.haptics;
 if(typeof o.reducedMotion==='boolean')r.reducedMotion=o.reducedMotion;
 if(['normal','large','xlarge'].includes(o.textSize))r.textSize=o.textSize;
 if(o.layout&&typeof o.layout==='object')for(const k of ['dpad','touchSkill','touchAttack']){const p=o.layout[k];if(p&&isFinite(p.x)&&isFinite(p.y))r.layout[k]={x:clamp(+p.x,0,1),y:clamp(+p.y,0,1)}}
 r.updatedAt=+o.updatedAt||0;return r}
function persist(){S.updatedAt=Date.now();try{localStorage.setItem(SKEY,JSON.stringify(S))}catch(e){}
 if(stateRef){stateRef.settings={...(stateRef.settings||{}),...JSON.parse(JSON.stringify(S))};onSave()}}
// Merge local + save-envelope settings; newest updatedAt wins.
export function adopt(state,saveFn){stateRef=state;if(saveFn)onSave=saveFn;let local=null;try{local=JSON.parse(localStorage.getItem(SKEY))}catch(e){}
 const a=sanitize(local),b=sanitize(state.settings);const hasA=!!local,hasB=state.settings&&Object.keys(state.settings).length>0;
 S=hasA&&(!hasB||a.updatedAt>=b.updatedAt)?a:hasB?b:sanitize(null);
 if(hasA||hasB){try{localStorage.setItem(SKEY,JSON.stringify(S))}catch(e){}state.settings={...(state.settings||{}),...JSON.parse(JSON.stringify(S))}}
 apply()}
// ---------- appearance ----------
export function apply(){const h=document.documentElement;h.classList.toggle('reduce-motion',reducedMotion());
 h.classList.remove('ts-large','ts-xlarge');if(S.textSize==='large')h.classList.add('ts-large');if(S.textSize==='xlarge')h.classList.add('ts-xlarge');
 applyLayout();applyMusic()}
// ---------- haptics ----------
export function haptic(ms=8){if(S.haptics&&navigator.vibrate)try{navigator.vibrate(ms)}catch(e){}}
// ---------- audio (synthesized, no assets) ----------
let ac=null,musicGain=null,musicOn=false;
function ctx(){if(!ac){const A=window.AudioContext||window.webkitAudioContext;if(!A)return null;ac=new A()}if(ac.state==='suspended')ac.resume();return ac}
export function sfx(kind='hit'){if(S.sfxVolume<=0)return;const c=ctx();if(!c)return;const t=c.currentTime,o=c.createOscillator(),g=c.createGain();
 const f={hit:[220,90,.12],skill:[420,880,.28],ui:[520,620,.06]}[kind]||[300,200,.1];
 o.type=kind==='skill'?'triangle':'square';o.frequency.setValueAtTime(f[0],t);o.frequency.exponentialRampToValueAtTime(f[1],t+f[2]);
 g.gain.setValueAtTime(.18*S.sfxVolume,t);g.gain.exponentialRampToValueAtTime(.0001,t+f[2]+.04);o.connect(g).connect(c.destination);o.start(t);o.stop(t+f[2]+.06)}
function startMusic(){if(musicOn)return;const c=ctx();if(!c)return;musicOn=true;musicGain=c.createGain();musicGain.gain.value=0;musicGain.connect(c.destination);
 [110,164.81,220.5].forEach((f,i)=>{const o=c.createOscillator();o.type='sine';o.frequency.value=f;const l=c.createOscillator(),lg=c.createGain();l.frequency.value=.07+i*.03;lg.gain.value=3;l.connect(lg).connect(o.frequency);const g=c.createGain();g.gain.value=.5/(i+1);o.connect(g).connect(musicGain);o.start();l.start()});applyMusic()}
function applyMusic(){if(musicGain)musicGain.gain.setTargetAtTime(.09*S.musicVolume,ac.currentTime,.1)}
export function armAudio(){const go=()=>{if(S.musicVolume>0)startMusic();window.removeEventListener('pointerdown',go)};window.addEventListener('pointerdown',go)}
// ---------- button layout ----------
const IDS=['dpad','touchSkill','touchAttack'];
const el=id=>id==='dpad'?document.querySelector('.dpad'):$(id);
const frame=()=>document.querySelector('.worldFrame');
function safe(){const p=document.createElement('div');p.style.cssText='position:fixed;visibility:hidden;padding:env(safe-area-inset-top) env(safe-area-inset-right) env(safe-area-inset-bottom) env(safe-area-inset-left)';document.body.appendChild(p);const cs=getComputedStyle(p),r={t:parseFloat(cs.paddingTop)||0,r:parseFloat(cs.paddingRight)||0,b:parseFloat(cs.paddingBottom)||0,l:parseFloat(cs.paddingLeft)||0};p.remove();return r}
// Allowed box for an element's top-left inside the frame, honoring device safe areas + a margin, minus the top HUD strip.
function bounds(f,e){const fr=f.getBoundingClientRect(),s=safe(),m=10,hud=40;
 const L=Math.max(m,s.l-fr.left+m),R=Math.max(m,fr.right-(window.innerWidth-s.r)+m),T=Math.max(hud,s.t-fr.top+m),nav=document.querySelector('.bottomNav'),vb=Math.min(window.innerHeight-s.b,nav?nav.getBoundingClientRect().top:1e9),B=Math.max(m,fr.bottom-vb+m);
 return{minX:L,maxX:Math.max(L,fr.width-e.offsetWidth-R),minY:T,maxY:Math.max(T,fr.height-e.offsetHeight-B)}}
function place(id,pos){const e=el(id),f=frame();if(!e||!f)return;const b=bounds(f,e);
 e.style.position='absolute';e.style.right='auto';e.style.bottom='auto';
 e.style.left=clamp(pos.x*f.clientWidth,b.minX,b.maxX)+'px';e.style.top=clamp(pos.y*f.clientHeight,b.minY,b.maxY)+'px'}
export function applyLayout(){const f=frame();if(!f)return;for(const id of IDS){const e=el(id);if(!e)continue;const p=S.layout[id];
 if(p&&f.clientWidth)place(id,p);else{e.style.position=e.style.left=e.style.top=e.style.right=e.style.bottom=''}}}
let editing=false;
const SNAP=8;
function snapVal(v,min,max,guides){let best=Math.round(v/SNAP)*SNAP;for(const g of guides)if(Math.abs(v-g)<10)best=g;return clamp(best,min,max)}
function startEdit(){const f=frame();if(!f||editing)return;editing=true;f.classList.add('editing');f.scrollIntoView({block:'center'});
 // freeze current positions as explicit (so defaults become draggable)
 const fr0=f.getBoundingClientRect(),rects={};for(const id of IDS){const e=el(id);if(e&&!S.layout[id]){const r=e.getBoundingClientRect();rects[id]={x:(r.left-fr0.left)/f.clientWidth,y:(r.top-fr0.top)/f.clientHeight}}}
 for(const id in rects)place(id,rects[id]);
 const bar=document.createElement('div');bar.id='layoutBar';bar.innerHTML='<b>Edit layout</b><span>Drag a button to move it</span><button class="gold" id="layoutDone" type="button">Done</button><button id="layoutReset" type="button">Reset</button>';f.appendChild(bar);
 f.insertAdjacentHTML('beforeend','<div id="layoutGuides"></div>');
 $('layoutDone').onclick=stopEdit;$('layoutReset').onclick=()=>{S.layout={};persist();for(const id of IDS){const e=el(id);e.style.position=e.style.left=e.style.top=e.style.right=e.style.bottom=''}
  // re-freeze so buttons stay draggable after reset
  f.classList.remove('editing');$('layoutBar')?.remove();$('layoutGuides')?.remove();editing=false;startEdit();toast('Layout reset to default.')};
  // capture: swallow gameplay input while editing
 for(const id of IDS){const e=el(id);e.classList.add('movable');e.addEventListener('pointerdown',dragStart,true)}
 toast('Edit layout: drag buttons, then tap Done.')}
let drag=null;
function dragStart(e){if(!editing)return;e.stopImmediatePropagation();e.preventDefault();const id=e.currentTarget.id||'dpad',t=e.currentTarget,f=frame(),fr=f.getBoundingClientRect(),r=t.getBoundingClientRect();
 drag={id,t,dx:e.clientX-r.left,dy:e.clientY-r.top};t.setPointerCapture(e.pointerId);t.classList.add('dragging');
 t.addEventListener('pointermove',dragMove);t.addEventListener('pointerup',dragEnd);t.addEventListener('pointercancel',dragEnd)}
function dragMove(e){if(!drag)return;const f=frame(),fr=f.getBoundingClientRect(),t=drag.t,b=bounds(f,t);
 const x=e.clientX-fr.left-drag.dx,y=e.clientY-fr.top-drag.dy;
 const gx=[b.minX,b.maxX,(b.minX+b.maxX)/2],gy=[b.minY,b.maxY,(b.minY+b.maxY)/2];
 const sx=snapVal(x,b.minX,b.maxX,gx),sy=snapVal(y,b.minY,b.maxY,gy);
 t.style.position='absolute';t.style.right=t.style.bottom='auto';t.style.left=sx+'px';t.style.top=sy+'px';
 S.layout[drag.id]={x:sx/f.clientWidth,y:sy/f.clientHeight}}
function dragEnd(e){if(!drag)return;const t=drag.t;t.classList.remove('dragging');t.removeEventListener('pointermove',dragMove);t.removeEventListener('pointerup',dragEnd);t.removeEventListener('pointercancel',dragEnd);drag=null;persist()}
export function stopEdit(){const f=frame();if(!editing)return;editing=false;f.classList.remove('editing');$('layoutBar')?.remove();$('layoutGuides')?.remove();
 for(const id of IDS){const e=el(id);e.classList.remove('movable','dragging');e.removeEventListener('pointerdown',dragStart,true)}persist();toast('Layout saved.')}
export const isEditing=()=>editing;
export function enterEditLayout(switchTab){switchTab('adventure');requestAnimationFrame(()=>requestAnimationFrame(startEdit))}
let toast=m=>{};
// ---------- Settings screen ----------
export function render(host,{toastFn,switchTab,resetAdventure}){toast=toastFn;const pct=v=>Math.round(v*100);
 host.innerHTML=`<div class="pageHead"><span class="eyebrow">PREFERENCES</span><h1>⚙ Settings</h1><p>Saved on this device and with your guild save, so they follow you when you sync.</p></div>
 <div class="settingsGrid">
 <article class="panel"><span class="eyebrow">SOUND</span>
  <label class="setRow" for="setMusic"><span>Music volume <b id="setMusicV">${pct(S.musicVolume)}%</b></span><input type="range" id="setMusic" min="0" max="100" value="${pct(S.musicVolume)}"></label>
  <label class="setRow" for="setSfx"><span>Sound effects volume <b id="setSfxV">${pct(S.sfxVolume)}%</b></span><input type="range" id="setSfx" min="0" max="100" value="${pct(S.sfxVolume)}"></label></article>
 <article class="panel"><span class="eyebrow">COMFORT</span>
  <div class="setRow toggle"><span>Haptics / vibration<small>Short buzz when you tap attack or skill.</small></span><button type="button" class="switch" id="setHaptics" role="switch" aria-checked="${S.haptics}" aria-label="Haptics"><i></i></button></div>
  <div class="setRow toggle"><span>Reduced motion<small>${S.reducedMotion===null?'Following your device setting.':'Turns off animations and fades.'}</small></span><button type="button" class="switch" id="setMotion" role="switch" aria-checked="${reducedMotion()}" aria-label="Reduced motion"><i></i></button></div>
  <div class="setRow"><span>Text size</span><div class="seg" id="setText" role="group" aria-label="Text size">${[['normal','Normal'],['large','Large'],['xlarge','Extra large']].map(([v,l])=>`<button type="button" data-ts="${v}" class="${S.textSize===v?'selected':''}">${l}</button>`).join('')}</div></div></article>
 <article class="panel"><span class="eyebrow">CONTROLS</span><h2>Button layout</h2><p class="micro">Move the D-pad, Skill and Attack buttons wherever your thumbs reach. They snap to a grid and stay inside the safe screen area.</p>
  <div class="quickButtons"><button class="gold" id="setEditLayout" type="button">✥ Edit button layout</button><button id="setResetLayout" type="button">Reset layout</button></div></article>
 <article class="panel"><span class="eyebrow">EXPERIMENTAL</span><h2>3D prototype</h2><p class="micro">A small 3D village with a 3D knight, to test how a 3D Varnethryl would run on your phone. Separate from the game; use the Game link to come back.</p>
  <div class="quickButtons"><a class="gold" href="proto3d.html" style="display:inline-block;padding:10px 14px;border-radius:10px;text-decoration:none">Open 3D prototype</a></div></article>
 <article class="panel"><span class="eyebrow">RESET</span><h2>Defaults</h2><p class="micro">Resets sound, comfort and layout only. Your progress is not touched.</p>
  <div class="quickButtons"><button class="danger" id="setResetAll" type="button">Reset settings</button></div></article></div>`;
 const rerender=()=>render(host,{toastFn,switchTab,resetAdventure});
 $('setMusic').oninput=e=>{S.musicVolume=e.target.value/100;$('setMusicV').textContent=e.target.value+'%';if(S.musicVolume>0)startMusic();applyMusic()};$('setMusic').onchange=persist;
 $('setSfx').oninput=e=>{S.sfxVolume=e.target.value/100;$('setSfxV').textContent=e.target.value+'%'};$('setSfx').onchange=()=>{persist();sfx('ui')};
 $('setHaptics').onclick=()=>{S.haptics=!S.haptics;persist();rerender();if(S.haptics)haptic(30)};
 $('setMotion').onclick=()=>{S.reducedMotion=!reducedMotion();persist();apply();rerender()};
 $('setText').onclick=e=>{const b=e.target.closest('[data-ts]');if(!b)return;S.textSize=b.dataset.ts;persist();apply();rerender()};
 $('setEditLayout').onclick=()=>enterEditLayout(switchTab);
 $('setResetLayout').onclick=()=>{S.layout={};persist();applyLayout();toast('Button layout reset to default.')};
 $('setResetAll').onclick=()=>{S={...DEFAULTS,layout:{}};persist();apply();rerender();toast('Settings reset to defaults.')}}
window.addEventListener('resize',()=>{if(!editing)applyLayout();else for(const id of IDS)if(S.layout[id])place(id,S.layout[id])});
window.addEventListener('orientationchange',()=>setTimeout(applyLayout,250));
