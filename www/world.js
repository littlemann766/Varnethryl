// Varnethryl painted-world renderer: parallax backdrop, props, ambient effects, shadows and colour grading.
// Config lives in hud-config.js (HUD_CONFIG.zones). Effects honour Settings.reducedMotion() and Settings graphics quality.
import {HUD_CONFIG} from './hud-config.js';
import * as Settings from './settings.js';
const clamp=(n,a,b)=>Math.max(a,Math.min(b,n));
const imgs={};
function load(src){if(!imgs[src]){const i=new Image();i.decoding='async';i.src=src;imgs[src]=i}return imgs[src]}
const ok=src=>{const i=imgs[src];return i&&i.complete&&i.naturalWidth?i:null};
const cfgOf=z=>HUD_CONFIG.zones&&HUD_CONFIG.zones[z];
export const active=z=>!!cfgOf(z);
// ---------- quality ----------
const FX={high:{leaves:34,motes:30,mist:5,shimmer:true,rays:true,sway:true,grade:true},medium:{leaves:14,motes:12,mist:3,shimmer:true,rays:true,sway:false,grade:true},low:{leaves:0,motes:0,mist:0,shimmer:false,rays:false,sway:false,grade:true}};
let autoDrop=0;const LV=['high','medium','low'];
export function quality(){const g=Settings.get().graphics||'auto';if(g!=='auto')return g;
 const small=Math.min(innerWidth,innerHeight)<700||(matchMedia&&matchMedia('(pointer:coarse)').matches);
 return LV[Math.min(2,(small?1:0)+autoDrop)]}
// auto quality: if frames average >24ms for 90 frames in a row, drop one level (Auto mode only)
let acc=0,n=0,last=0;
function watch(now){if(last){const d=now-last;if(d<200){acc+=d;n++;if(n>=90){if((Settings.get().graphics||'auto')==='auto'&&acc/n>24&&autoDrop<2&&quality()!=='low')autoDrop++;acc=0;n=0}}}last=now}
// ---------- cached sprites ----------
const cache={};
function sprite(key,w,h,fn){if(!cache[key]){const c=document.createElement('canvas');c.width=w;c.height=h;fn(c.getContext('2d'),w,h);cache[key]=c}return cache[key]}
const glow=()=>sprite('glow',32,32,(c,w,h)=>{const g=c.createRadialGradient(16,16,0,16,16,16);g.addColorStop(0,'rgba(255,240,170,1)');g.addColorStop(.25,'rgba(255,214,120,.55)');g.addColorStop(1,'rgba(255,200,90,0)');c.fillStyle=g;c.fillRect(0,0,w,h)});
const mistSpr=()=>sprite('mist',320,110,(c,w,h)=>{c.translate(w/2,h/2);c.scale(1,h/w);const g=c.createRadialGradient(0,0,0,0,0,w/2);g.addColorStop(0,'rgba(255,236,206,.55)');g.addColorStop(.6,'rgba(235,222,214,.22)');g.addColorStop(1,'rgba(235,225,220,0)');c.fillStyle=g;c.fillRect(-w/2,-w/2,w,w)});
const shadowSpr=()=>sprite('shadow',64,24,(c,w,h)=>{c.translate(w/2,h/2);c.scale(1,h/w);const g=c.createRadialGradient(0,0,0,0,0,w/2);g.addColorStop(0,'rgba(8,16,10,.55)');g.addColorStop(.6,'rgba(8,16,10,.28)');g.addColorStop(1,'rgba(8,16,10,0)');c.fillStyle=g;c.fillRect(-w/2,-w/2,w,w)});
function raysSpr(){return sprite('rays',640,360,(c,w,h)=>{c.translate(w*.88,-h*.08);for(let i=0;i<9;i++){const a=Math.PI*(.58+i*.062)+Math.sin(i*7.1)*.02,wd=.018+((i*37)%5)*.006,L=h*1.5;const g=c.createLinearGradient(0,0,Math.cos(a)*L,Math.sin(a)*L);g.addColorStop(0,'rgba(255,224,150,.9)');g.addColorStop(1,'rgba(255,210,130,0)');c.fillStyle=g;c.beginPath();c.moveTo(0,0);c.lineTo(Math.cos(a-wd)*L,Math.sin(a-wd)*L);c.lineTo(Math.cos(a+wd)*L,Math.sin(a+wd)*L);c.closePath();c.fill()}})}
let gradeCv=null,gradeKey='';
function gradeSpr(cw,ch,withWarm){const k=cw+'x'+ch+withWarm;if(gradeKey!==k){gradeKey=k;gradeCv=document.createElement('canvas');gradeCv.width=Math.ceil(cw/2);gradeCv.height=Math.ceil(ch/2);const c=gradeCv.getContext('2d'),w=gradeCv.width,h=gradeCv.height;
 if(withWarm){const g=c.createLinearGradient(0,0,w,h);g.addColorStop(0,'rgba(255,196,120,.10)');g.addColorStop(1,'rgba(255,150,80,.14)');c.fillStyle=g;c.fillRect(0,0,w,h)}
 const v=c.createRadialGradient(w/2,h*.5,Math.min(w,h)*.38,w/2,h*.5,Math.max(w,h)*.72);v.addColorStop(0,'rgba(20,10,6,0)');v.addColorStop(1,'rgba(20,10,6,.42)');c.fillStyle=v;c.fillRect(0,0,w,h)}return gradeCv}
// ---------- backdrop ----------
export function preload(zone){const c=cfgOf(zone);if(!c)return;for(const l of c.layers)load(l.src);load(c.ground.src);
 // props, clumps and foreground are lazy: queued once the first layers are requested
 setTimeout(()=>{for(const p of c.props||[])load(p.src);for(const m of c.clumps||[])load(m.src);if(c.fore)load(c.fore.src)},300)}
let vp={gt:0};
export function drawBackdrop(C,cw,ch,camX,camY,zone,now){const c=cfgOf(zone);if(!c)return false;preload(zone);watch(now);
 const sky=ok(c.layers[0].src),far=ok(c.layers[1].src);if(!sky||!far)return false;
 const px=clamp(camX/Math.max(1,1850-cw),0,1),py=clamp(camY/Math.max(1,1210-ch),0,1),gt=ch*(c.groundTop||.7)-py*ch*.05;vp.gt=gt;
 C.imageSmoothingEnabled=true;C.imageSmoothingQuality='medium';
 C.fillStyle='#d9a566';C.fillRect(0,0,cw,gt+20);
 for(const l of c.layers){const im=ok(l.src);if(!im)continue;const asp=im.naturalWidth/im.naturalHeight;let dh,dw;
  if(l.kind==='sky'){dw=Math.max(cw*1.06,gt*1.2*asp);dh=dw/asp;if(dh<gt*1.1){dh=gt*1.1;dw=dh*asp}}
  else{dh=Math.max(cw*(l.zoom||1.1)/asp,ch*(l.minH||.64));dw=dh*asp}
  const x=-(dw-cw)*clamp((l.focus??.5)+(px-.5)*l.speed*2,0,1);
  const y=l.kind==='sky'?-(dh-gt*1.1)*.4:(l.top??.01)*ch-py*ch*(l.vy??.03);
  C.drawImage(im,x,y,dw,dh);
  if(l.shimmer)drawFallShimmer(C,l,x,y,dw,dh,now)}
 for(const m of c.clumps||[]){const im=ok(m.src);if(!im)continue;const h=ch*m.h,w=h*im.naturalWidth/im.naturalHeight,x=m.x*cw-(px-.5)*cw*m.speed-(m.flip?w:0),y=gt+ch*m.base-h;
  if(m.flip){C.save();C.translate(x+w,0);C.scale(-1,1);C.drawImage(im,0,y,w,h);C.restore()}else C.drawImage(im,x,y,w,h)}
 const g=ok(c.ground.src);if(g){const asp=g.naturalWidth/g.naturalHeight,dh=Math.max((ch-gt)/.75,cw*1.3/asp),dw=dh*asp,xoff=-(dw-cw)*clamp(.5+(px-.5)*c.ground.speed,0,1);
  C.drawImage(g,xoff,ch-dh,dw,dh)}
 return true}
function drawFallShimmer(C,l,x,y,dw,dh,now){const f=FX[quality()];if(!f.shimmer||Settings.reducedMotion())return;
 C.save();C.globalCompositeOperation='lighter';
 for(const [fx,fy0,fy1] of l.shimmer){const X=x+fx*dw,Y0=y+fy0*dh,Y1=y+fy1*dh;for(let i=0;i<7;i++){const t=(now*.0006*(1+i*.13)+i*.37)%1,Y=Y0+(Y1-Y0)*t,a=Math.sin(t*Math.PI)*.35;C.fillStyle=`rgba(255,255,255,${a})`;C.fillRect(X-1.5+Math.sin(now*.003+i)*1.5,Y,2.5,Math.max(8,(Y1-Y0)*.12))}}
 C.restore()}
// ---------- world-space props (called inside the camera transform) ----------
export function drawProps(C,zone,camX,camY,cw,ch,playerY,pass){const c=cfgOf(zone);if(!c)return;C.imageSmoothingEnabled=true;
 for(const p of c.props||[]){const im=ok(p.src);if(!im)continue;const front=p.y>playerY;if((pass==='front')!==front)continue;
  const w=p.w,h=w*im.naturalHeight/im.naturalWidth,x=p.x-w/2,y=p.y-h;if(x+w<camX-20||x>camX+cw+20||y+h<camY-20||y>camY+ch+20)continue;
  if(!p.noShadow)C.drawImage(shadowSpr(),p.x-w*.45,p.y-h*.04,w*.9,Math.max(8,h*.12));
  let sway=0;if(p.sway&&FX[quality()].sway&&!Settings.reducedMotion())sway=Math.sin(performance.now()*.0012+p.x)*.012;
  if(sway){C.save();C.translate(p.x,p.y);C.rotate(sway);C.drawImage(im,-w/2,-h,w,h);C.restore()}else C.drawImage(im,x,y,w,h)}}
export function shadow(C,x,y,r=24){C.drawImage(shadowSpr(),x-r*1.15,y+3,r*2.3,r*.85)}
// ---------- screen-space effects ----------
const parts={leaves:[],motes:[],seed:1};
const rnd=()=>{parts.seed=(parts.seed*16807)%2147483647;return parts.seed/2147483647};
function spawnLeaf(cw,ch,anywhere){return {x:rnd()*cw*1.2-cw*.1,y:anywhere?rnd()*ch:-20,vx:10+rnd()*22,vy:14+rnd()*20,r:rnd()*6.28,vr:(rnd()-.5)*2.5,s:3+rnd()*3.5,ph:rnd()*6.28,petal:rnd()<.5}}
function spawnMote(cw,ch){return {x:rnd()*cw,y:ch*(.3+rnd()*.7),ph:rnd()*6.28,sp:.2+rnd()*.5,s:6+rnd()*9}}
let lastT=0;
export function drawFx(C,zone,cw,ch,camX,camY,now){const c=cfgOf(zone);if(!c)return;const q=quality(),f=FX[q],rm=Settings.reducedMotion();
 const dt=Math.min(50,now-lastT||16)/1000;lastT=now;
 C.save();
 if(f.rays){C.globalCompositeOperation='lighter';const sway=rm?0:Math.sin(now*.00035)*.04;C.globalAlpha=.30+sway;C.drawImage(raysSpr(),0,0,cw,ch*.9);if(f.sway&&!rm){C.globalAlpha=.16-sway;C.save();C.translate(cw,0);C.scale(-.6,1);C.drawImage(raysSpr(),cw*.6,0,cw*.75,ch*.8);C.restore()}C.globalAlpha=1;C.globalCompositeOperation='source-over'}
 const gt=vp.gt||ch*.7;
 if(f.mist){const m=mistSpr();for(let i=0;i<f.mist;i++){const w=cw*(.5+((i*37)%7)/12),h=w*.34,sp=rm?0:(6+i*3.5),x=((i*cw*.31+now*.001*sp)%(cw+w))-w*.6-(camX*.05%cw);C.globalAlpha=.55-(i%3)*.08;C.drawImage(m,x,gt-h*.55+((i*53)%40)-20,w,h)}C.globalAlpha=1}
 else{const g=C.createLinearGradient(0,gt-ch*.08,0,gt+ch*.05);g.addColorStop(0,'rgba(240,225,205,0)');g.addColorStop(.5,'rgba(240,225,205,.22)');g.addColorStop(1,'rgba(240,225,205,0)');C.fillStyle=g;C.fillRect(0,gt-ch*.08,cw,ch*.13)}
 if(!rm&&f.leaves){while(parts.leaves.length<f.leaves)parts.leaves.push(spawnLeaf(cw,ch,true));parts.leaves.length=f.leaves;
  for(const p of parts.leaves){p.x+=(p.vx+Math.sin(now*.0015+p.ph)*14)*dt;p.y+=p.vy*dt;p.r+=p.vr*dt;if(p.y>ch+10||p.x>cw+20)Object.assign(p,spawnLeaf(cw,ch,false));
   C.save();C.translate(p.x,p.y);C.rotate(p.r);C.scale(1,.55+.45*Math.abs(Math.sin(p.r*1.3)));C.fillStyle=p.petal?'#f0d6e4cc':'#c9a24acc';C.beginPath();C.ellipse(0,0,p.s,p.s*.5,0,0,6.3);C.fill();C.restore()}}
 if(!rm&&f.motes){while(parts.motes.length<f.motes)parts.motes.push(spawnMote(cw,ch));parts.motes.length=f.motes;const gl=glow();C.globalCompositeOperation='lighter';
  for(const p of parts.motes){const t=now*.001*p.sp+p.ph,x=p.x+Math.sin(t*1.3)*26-(camX*.12%cw),y=p.y+Math.cos(t)*16-(now*.004*p.sp%30),a=.35+.55*Math.max(0,Math.sin(t*2.1));C.globalAlpha=a;C.drawImage(gl,((x%cw)+cw)%cw-p.s/2,y-p.s/2,p.s,p.s)}C.globalAlpha=1;C.globalCompositeOperation='source-over'}
 C.drawImage(gradeSpr(cw,ch,f.grade),0,0,cw,ch);
 C.restore()}
export function drawPond(C,x,y,w,h,now){if(!FX[quality()].shimmer||Settings.reducedMotion())return;C.save();C.globalCompositeOperation='lighter';
 for(let i=0;i<9;i++){const t=(now*.0004+i*.21)%1,px=x+((i*47)%w),py=y+((i*29+t*h)%h);C.fillStyle=`rgba(255,244,210,${Math.sin(t*Math.PI)*.55})`;C.fillRect(px,py,6+(i%3)*4,1.6)}C.restore()}
// ---------- foreground (after entities, screen space, fastest parallax) ----------
export function drawFore(C,zone,cw,ch,camX,camY,now){const c=cfgOf(zone);if(!c||!c.fore)return;const im=ok(c.fore.src);if(!im)return;
 const px=clamp(camX/Math.max(1,1850-cw),0,1),asp=im.naturalWidth/im.naturalHeight,h=ch*(c.fore.h||.5),w=Math.max(cw*1.18,h*asp),
 sway=(FX[quality()].sway&&!Settings.reducedMotion())?Math.sin(now*.0009)*3:0;
 const x=-(w-cw)*clamp(.5+(px-.5)*c.fore.speed,0,1)+sway;
 C.save();C.imageSmoothingEnabled=true;C.drawImage(im,x,ch-h+ch*.04,w,h);C.restore()}
