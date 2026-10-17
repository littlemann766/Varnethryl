// Varnethryl on-screen controls: analog stick (phone/app), D-pad (web only), 5-button skill cluster with cooldown/charge rings.
import * as Settings from './settings.js';
import {resolve,SLOTS,ICONS} from './skills.js';
import * as Motion from './motion.js';
const $=id=>document.getElementById(id);
const clamp=(n,a,b)=>Math.max(a,Math.min(b,n));
export const MODE=Settings.MODE;
export const DEADZONE=.14;
const stick={x:0,y:0,mag:0,active:false,pid:null};
export const input={x:0,y:0,mag:0};          // analog intent, |v|<=1 (post dead-zone, response curve)
export const heroFace={angle:null};            // last intended facing (radians)
let api=null;const cd={},charge={};            // cd[heroId][slot]=readyAt ; charge[heroId]=0..100
const slotBtn={minor:'touchSkill',heavy:'skillHeavy',superHeavy:'skillSuper',ultimate:'skillUlt'};
// ---------- stick ----------
function setupStick(){const base=$('stick'),knob=$('stickKnob'),zone=$('stickZone');if(!base)return;
 const R=()=>base.offsetWidth/2-knob.offsetWidth/2+4;
 const upd=(cx,cy,e)=>{let dx=e.clientX-cx,dy=e.clientY-cy;const r=R(),d=Math.hypot(dx,dy),c=d>r?r/d:1;dx*=c;dy*=c;
  knob.style.transform=`translate(${dx}px,${dy}px)`;let m=Math.hypot(dx,dy)/r;
  if(m<DEADZONE){stick.x=stick.y=stick.mag=0;return}
  m=Math.pow((m-DEADZONE)/(1-DEADZONE),1.15);const a=Math.atan2(dy,dx);stick.x=Math.cos(a)*m;stick.y=Math.sin(a)*m;stick.mag=m;heroFace.angle=a};
 let ctr=null;
 const start=(e,floating)=>{if(stick.active||document.querySelector('.worldFrame.editing'))return;e.preventDefault();
  stick.active=true;stick.pid=e.pointerId;
  if(floating){const f=document.querySelector('.worldFrame').getBoundingClientRect(),w=base.offsetWidth;
   base.style.position='absolute';base.style.right=base.style.bottom='auto';
   base.style.left=clamp(e.clientX-f.left-w/2,6,f.width-w-6)+'px';base.style.top=clamp(e.clientY-f.top-w/2,40,f.height-w-6)+'px'}
  base.classList.add('active');const r=base.getBoundingClientRect();ctr=[r.left+r.width/2,r.top+r.height/2];
  (floating?zone:base).setPointerCapture(e.pointerId);upd(ctr[0],ctr[1],e);Settings.haptic(6)};
 const move=e=>{if(stick.active&&e.pointerId===stick.pid)upd(ctr[0],ctr[1],e)};
 const end=e=>{if(!stick.active||e.pointerId!==stick.pid)return;stick.active=false;stick.x=stick.y=stick.mag=0;knob.style.transform='';base.classList.remove('active');
  if(Settings.get().floatingStick)Settings.applyLayout()};
 for(const t of [base,zone]){t.addEventListener('pointermove',move);t.addEventListener('pointerup',end);t.addEventListener('pointercancel',end);t.addEventListener('lostpointercapture',end)}
 base.addEventListener('pointerdown',e=>start(e,false));
 zone.addEventListener('pointerdown',e=>{if(Settings.get().floatingStick)start(e,true)});
 const sync=()=>{zone.style.display=MODE==='stick'&&Settings.get().floatingStick?'block':'none';base.classList.toggle('floating',Settings.get().floatingStick)};
 sync();window.addEventListener('vn-controls',sync);setInterval(sync,1500)}
// ---------- skills ----------
const heroSkills=()=>{const h=api.HEROES[api.state.active];return resolve(h.id,h.name)};
function cdOf(id){return cd[id]||(cd[id]={})}
function ch(id){return charge[id]??0}
export function addCharge(id,n){charge[id]=clamp(ch(id)+n,0,100)}
const ring=(b,p,ready)=>{b.style.setProperty('--p',clamp(p,0,1).toFixed(3));b.classList.toggle('ready',!!ready)};
function inRange(range){const e=api.runtime.enemy.find(x=>x.id===api.runtime.target&&x.hp>0)||api.nearestEnemy(range);
 if(!e||Math.hypot(e.x-api.runtime.x,e.y-api.runtime.y)>range)return null;return e}
function faceTo(e){if(e){heroFace.angle=Math.atan2(e.y-api.runtime.y,e.x-api.runtime.x);api.runtime.faceA=heroFace.angle}}
function toast(m){api.toast(m)}
let busy=0;
export function basic(){const rt=api.runtime,hero=api.HEROES[api.state.active];if(rt.time<rt.attackUntil||rt.time<busy)return;
 const range=['mage','heal','ranged','support'].includes(hero.style)?255:98,e=inRange(range);
 if(!e){toast('Get closer to an enemy to attack.');return}
 faceTo(e);const d=Motion.act(api.state.active,'basic',rt.time);Settings.sfx('hit');
 const id=api.state.active;busy=rt.time+d.wind+d.strike+60;
 queue(d.wind,()=>{if(api.state.active!==id)return;const t=inRange(range+12);if(t){rt.attackUntil=0;const ok=api.basicAttack(true);if(ok)addCharge(id,5)}})}
const pend=[];function queue(ms,fn){pend.push({at:api.runtime.time+ms,fn})}
export function tick(){const t=api.runtime.time;for(let i=pend.length-1;i>=0;i--)if(t>=pend[i].at){const p=pend.splice(i,1)[0];p.fn()}
 // passive ultimate charge while in combat
 if(api.runtime.enemy.some(e=>e.hp>0)){const id=api.state.active;if(Math.floor(t/1000)!==Math.floor((t-16)/1000))addCharge(id,1.2)}}
export function useSkill(slot){const rt=api.runtime,id=api.state.active,hero=api.HEROES[id],sk=heroSkills()[slot],c=cdOf(id);
 if(slot==='ultimate'){if(ch(id)<(sk.charge||100)){toast(`Ultimate charging (${Math.floor(ch(id))}%).`);return}}
 else if(rt.time<(c[slot]||0)){toast(`${sk.name} recharging (${Math.ceil((c[slot]-rt.time)/1000)}s).`);return}
 const heal=hero.style==='heal'||hero.style==='support';let tgt=null;
 if(!heal){tgt=inRange(sk.range);if(!tgt){toast('Move within range of an enemy.');return}faceTo(tgt)}
 const d=Motion.act(id,sk.act,rt.time);Settings.sfx('skill');Settings.haptic(slot==='ultimate'?40:slot==='superHeavy'?25:14);
 if(slot==='ultimate')charge[id]=0;else c[slot]=rt.time+sk.cd+d.wind;
 // lunge momentum: push the hero forward a little as the strike lands (keeps motion continuous with locomotion)
 queue(d.wind,()=>{if(api.state.active!==id)return;
  if(heal){for(const p of api.state.party){const n=Math.round(api.combinedStats(id).attack*sk.mult*.6);rt.hp[p]=Math.min(api.heroMax(p),(rt.hp[p]||0)+n);api.logDamage(rt.x,rt.y-50,`+${api.fmt(n)}`,'#75efd1')}}
  else{const t=rt.enemy.find(x=>x.id===(tgt&&tgt.id)&&x.hp>0)||inRange(sk.range+20);if(t){api.hitEnemy(t,id,sk.mult);
    if(sk.splash)for(const e of rt.enemy)if(e!==t&&e.hp>0&&Math.hypot(e.x-t.x,e.y-t.y)<sk.splash)api.hitEnemy(e,id,sk.mult*.45)}}
  const lunge=Motion.ACT[sk.act]?.lunge||6,a=heroFace.angle??0;rt.vkick={x:Math.cos(a)*lunge*.012,y:Math.sin(a)*lunge*.012};
  if(slot!=='ultimate')addCharge(id,slot==='minor'?8:slot==='heavy'?14:22);
  api.log(`${hero.name} used ${sk.name}!`)})}
// ---------- HUD refresh (rings) ----------
export function refresh(){if(!api)return;const rt=api.runtime,id=api.state.active,sk=heroSkills(),c=cdOf(id);
 for(const s of SLOTS){const b=$(slotBtn[s]);if(!b)continue;const k=sk[s];
  if(b.dataset.sk!==k.name+(k.icon||'')){b.dataset.sk=k.name+(k.icon||'');b.querySelector('.ico').innerHTML=/^</.test(k.icon||'')?k.icon:`<img src="${k.icon}" alt="">`;b.querySelector('small').textContent=k.name;b.setAttribute('aria-label',k.name)}
  if(s==='ultimate'){const p=ch(id)/(k.charge||100);b.style.setProperty('--c',clamp(p,0,1).toFixed(3));b.classList.toggle('ready',p>=1);b.classList.remove('cooling')}
  else{const rem=Math.max(0,(c[s]||0)-rt.time),p=k.cd?rem/(k.cd||1):0;ring(b,p,false);b.classList.toggle('cooling',rem>0);b.dataset.cd=rem>0?Math.ceil(rem/1000):''}}
 const a=$('touchAttack');if(a){const rem=Math.max(0,rt.attackUntil-rt.time);ring(a,rem/1020,false);a.classList.toggle('cooling',rem>60)}}
// ---------- keyboard (desktop) ----------
const KEYS={j:()=>basic(),k:()=>useSkill('minor'),l:()=>useSkill('heavy'),u:()=>useSkill('superHeavy'),i:()=>useSkill('ultimate')};
export function init(a){api=a;
 const fast=(el,fn)=>el&&el.addEventListener('pointerdown',e=>{if(document.querySelector('.worldFrame.editing'))return;e.preventDefault();fn();a.renderTarget()});
 fast($('touchAttack'),basic);for(const s of SLOTS)fast($(slotBtn[s]),()=>useSkill(s));
 addEventListener('keydown',e=>{if(e.repeat||e.target.tagName==='INPUT'||e.target.tagName==='SELECT'||!a.inAdventure())return;const f=KEYS[e.key.length===1?e.key.toLowerCase():''];if(f){e.preventDefault();f()}});
 setupStick()}
// Combined analog intent for this frame: stick wins, else digital keys/D-pad, else tap-to-walk target.
export function readInput(keys,walkTarget,x,y){let ix=0,iy=0;
 for(const k of keys){if(k==='ArrowLeft'||k==='a')ix--;if(k==='ArrowRight'||k==='d')ix++;if(k==='ArrowUp'||k==='w')iy--;if(k==='ArrowDown'||k==='s')iy++}
 let m=0;if(stick.mag>0){ix=stick.x;iy=stick.y;m=stick.mag}
 else if(ix||iy){const d=Math.hypot(ix,iy);ix/=d;iy/=d;m=1}
 else if(walkTarget){const d=Math.hypot(walkTarget.x-x,walkTarget.y-y);if(d>12){ix=(walkTarget.x-x)/d;iy=(walkTarget.y-y)/d;m=d<60?.35+.4*(d/60):.75}}
 input.x=ix;input.y=iy;input.mag=m;if(m>0)heroFace.angle=Math.atan2(iy,ix);return input}
