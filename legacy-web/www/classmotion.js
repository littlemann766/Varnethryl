// Varnethryl class + hero motion profiles and class VFX (canvas, procedural). DATA-DRIVEN: edit the tables, not the engine.
// Resolution order for any value: DEFAULT < CLASS_PROFILES[className] < HERO_TWEAKS[heroId].
// Multipliers are relative to the default (1 = neutral). Fields:
//  spd run speed | acc accel/decel | cad stride length (bigger = slower cadence) | bob vertical step bounce | sway lateral weight shift
//  lean lean into motion | turn turn rate | weight 0..1 (settle/footfall, hit-stop, spring stiffness) | hover caster float px
//  idle 'breath'|'sway'|'float'|'ready'|'strum' | fam attack family | atk attack-time scale (<1 faster) | lunge lunge scale
//  fx basic-attack VFX id | tint override colour pair [core,glow] for this hero's VFX | cape cloth sway scale (visual flutter)
import {HEROES} from './data.js';
export const DEFAULT={spd:1,acc:1,cad:1,bob:1,sway:1,lean:1,turn:1,weight:.5,hover:0,idle:'breath',fam:'slash',atk:1,lunge:1,fx:'arc_steel',cape:1,breath:1};
// ---- attack families: shape of wind-up / strike / follow-through (applied in motion.js) ----
// windMul/strikeMul/followMul scale the ACT timing; the rest are pose multipliers.
export const FAMILY={
  slash:   {windMul:1,  strikeMul:1,  followMul:1,  back:.7, fwd:1.9, crouch:.04,rise:0,  squash:0,   lunge:1,   recoil:0, multi:1},
  bash:    {windMul:.9, strikeMul:.9, followMul:1.1,back:.5, fwd:1.5, crouch:.1, rise:0,  squash:.05, lunge:1.4, recoil:0, multi:1, hold:1},
  thrust:  {windMul:.8, strikeMul:.8, followMul:.9, back:.9, fwd:2.4, crouch:.07,rise:0,  squash:0,   lunge:1.5, recoil:0, multi:1},
  overhead:{windMul:1.25,strikeMul:1.1,followMul:1.3,back:1.1,fwd:1.5, crouch:-.06,rise:3.5,squash:.07, lunge:.9, recoil:0, multi:1},
  flurry:  {windMul:.6, strikeMul:2.4,followMul:.8, back:.4, fwd:1.1, crouch:.08,rise:0,  squash:0,   lunge:1.1, recoil:0, multi:4},
  draw:    {windMul:1.3,strikeMul:.8, followMul:1,  back:.6, fwd:-.9, crouch:.02,rise:0,  squash:0,   lunge:-.8, recoil:1, multi:1},
  cast:    {windMul:1.2,strikeMul:1,  followMul:1.2,back:.3, fwd:.7, crouch:-.05,rise:2.5,squash:0,   lunge:.35, recoil:0, multi:1, glow:1},
  strum:   {windMul:.8, strikeMul:1.6,followMul:1,  back:.2, fwd:.4, crouch:.03,rise:0,  squash:0,   lunge:.2, recoil:0, multi:3, pulse:1}};
// ---- class profiles ----
export const CLASS_PROFILES={
  Knight:      {spd:.88,acc:.8, cad:1.05,bob:.8, sway:.6,lean:.7, turn:.8, weight:.95,fam:'slash',   atk:1.05,fx:'arc_steel',  idle:'breath'},
  Paladin:     {spd:.92,acc:.85,cad:1.03,bob:.8, sway:.6,lean:.75,turn:.85,weight:.85,fam:'bash',    atk:1.0, fx:'arc_gold',   idle:'breath'},
  Berserker:   {spd:.95,acc:.9, cad:1.1, bob:1.2,sway:1.2,lean:1.3,turn:.9, weight:.95,fam:'overhead',atk:1.12,fx:'arc_blood',  idle:'ready',lunge:1.3},
  'Dark Knight':{spd:.85,acc:.75,cad:1.08,bob:.75,sway:.6,lean:.8,turn:.75,weight:1,  fam:'overhead',atk:1.18,fx:'arc_umbral', idle:'breath',lunge:1.2},
  Spearman:    {spd:.97,acc:.95,cad:1.05,bob:.9, sway:.8,lean:1.0,turn:.95,weight:.7, fam:'thrust',  atk:.95, fx:'line_steel', idle:'ready',lunge:1.3},
  Duelist:     {spd:1.12,acc:1.2,cad:.95,bob:1.1,sway:1.0,lean:1.2,turn:1.2,weight:.3,fam:'thrust',  atk:.82, fx:'line_silver',idle:'ready',lunge:1.4},
  Rogue:       {spd:1.2,acc:1.35,cad:.88,bob:.75,sway:1.1,lean:1.35,turn:1.35,weight:.2,fam:'flurry',atk:.78, fx:'flurry_shadow',idle:'ready'},
  Monk:        {spd:1.22,acc:1.3,cad:.9, bob:1.0,sway:1.0,lean:1.2,turn:1.3,weight:.3,fam:'flurry',  atk:.74, fx:'flurry_gold',idle:'ready'},
  Ranger:      {spd:1.08,acc:1.1,cad:.95,bob:.95,sway:1.0,lean:1.15,turn:1.1,weight:.25,fam:'draw',   atk:.95, fx:'arrow_green',idle:'sway'},
  'Witch Hunter':{spd:1.02,acc:1.0,cad:1.0,bob:.9,sway:.9,lean:1.0,turn:1.0,weight:.45,fam:'draw',  atk:.92, fx:'bolt_blood', idle:'ready'},
  Engineer:    {spd:.97,acc:.95,cad:.95,bob:1.1,sway:.8,lean:.9, turn:.95,weight:.5, fam:'draw',    atk:1.0, fx:'bolt_brass', idle:'sway'},
  Beastmaster: {spd:1.08,acc:1.1,cad:1.0,bob:1.0,sway:1.0,lean:1.15,turn:1.1,weight:.4,fam:'thrust', atk:.95, fx:'line_wild',  idle:'ready'},
  Mage:        {spd:.98,acc:.95,cad:1.0,bob:.5, sway:.7,lean:.4, turn:.9, weight:.2, hover:1.2,fam:'cast',atk:1.0,fx:'orb_fire',  idle:'float'},
  Cryomancer:  {spd:.98,acc:.9, cad:1.05,bob:.3,sway:.7,lean:.35,turn:.9, weight:.15,hover:1.5,fam:'cast',atk:1.05,fx:'shard_frost',idle:'float'},
  Necromancer: {spd:.9, acc:.85,cad:1.05,bob:.35,sway:.8,lean:.4,turn:.85,weight:.2, hover:1.4,fam:'cast',atk:1.1, fx:'wisp_shadow',idle:'float'},
  Runemaster:  {spd:.96,acc:.9, cad:1.0, bob:.5,sway:.7,lean:.4, turn:.9, weight:.25,hover:1.1,fam:'cast',atk:1.0, fx:'glyph_rune', idle:'float'},
  Druid:       {spd:.98,acc:.95,cad:1.0, bob:.7,sway:1.1,lean:.5, turn:.95,weight:.3, hover:.5,fam:'cast', atk:1.0, fx:'orb_leaf',  idle:'sway'},
  Shaman:      {spd:1.0, acc:1.0,cad:1.0, bob:.7,sway:1.2,lean:.55,turn:1.0,weight:.3,hover:.7,fam:'cast', atk:.98,fx:'bolt_storm', idle:'sway'},
  Cleric:      {spd:.92,acc:.85,cad:1.0, bob:.6,sway:.8,lean:.4, turn:.85,weight:.35,hover:.8,fam:'cast', atk:1.1, fx:'rays_holy', idle:'sway'},
  Bard:        {spd:1.05,acc:1.05,cad:.95,bob:1.35,sway:1.35,lean:.8,turn:1.05,weight:.3,fam:'strum',atk:.95,fx:'notes_bard',idle:'strum'}};
// ---- per-hero tweaks (id -> tweaks ON TOP of class), tuned to each card: build, armour weight, cloak/hair/robe, weapon size, personality ----
export const HERO_TWEAKS={
  0:{note:'Full plate + tower shield; steady, disciplined',spd:.97,acc:.95,bob:.9,lean:.95,turn:.95,weight:1,atk:1.03,tint:['#dfe9ff','#4f86ff']},
  1:{note:'Light hooded cloak, longbow; quiet, quick on her feet',spd:1.0,cape:1.3,lean:1.05,atk:.96,tint:['#d6ffcf','#4dbb5d']},
  2:{note:'Long white robes, tall staff; serene, unhurried',spd:.97,acc:.95,cad:1.05,sway:1.1,hover:1.0,atk:1.08,cape:1.2,tint:['#fff5c9','#ffd25a']},
  3:{note:'Slim, tattered cloak, twin daggers; predatory',spd:1.05,acc:1.1,bob:.85,lean:1.1,turn:1.15,atk:.94,cape:1.5,tint:['#c9d6e8','#3a2a6a']},
  4:{note:'Flame-red cape, fiery hands; impulsive, showy',spd:1.03,acc:1.05,bob:1.1,hover:1.1,atk:.93,cape:1.4,tint:['#ffe2a0','#ff6a2a']},
  5:{note:'Plate, big sun shield and mace; graceful but guarded',spd:1.0,acc:1.0,bob:.95,lean:1.0,weight:.9,atk:1.0,cape:1.0,tint:['#fff0b8','#ffcf4a']},
  6:{note:'Huge fur-clad bruiser, greataxe; wild, momentum-driven',spd:.98,acc:.9,cad:1.05,bob:1.15,lean:1.15,turn:.9,weight:1,atk:1.12,lunge:1.15,cape:1.2,tint:['#ffb08a','#c3181d']},
  7:{note:'Flowing leaf-green robes and vines; gentle, swaying',spd:1.0,sway:1.2,bob:.9,hover:.7,atk:1.0,cape:1.5,tint:['#e0ffb8','#58b84a']},
  8:{note:'Feathered hat, dandy coat, lute; jaunty showman',spd:1.03,bob:1.15,sway:1.2,lean:1.1,atk:.97,cape:1.3,tint:['#ffe9b0','#c24a6a']},
  9:{note:'Hooded dark robes, skull staff; slow, deliberate, floats',spd:.96,acc:.9,cad:1.05,hover:1.3,atk:1.08,cape:1.5,tint:['#d9ffd0','#7b3fd1']},
  10:{note:'Caped scholar, orbiting runes; poised',spd:.99,hover:1.1,sway:.9,atk:1.0,cape:1.2,tint:['#dff2ff','#4a7cff']},
  11:{note:'Long coat, crossbow and blade; wary, efficient',spd:1.0,lean:1.05,turn:1.05,atk:.95,cape:1.2,tint:['#ffe0dc','#c7243a']},
  12:{note:'Wind-whipped spirit robes and charms; restless',spd:1.03,sway:1.25,hover:1.0,atk:.97,cape:1.8,tint:['#d3fbff','#38c6e8']},
  13:{note:'Plate and banner-spear; disciplined reach fighter',spd:.99,acc:1.0,cad:1.03,bob:.95,lunge:1.1,weight:.85,atk:.98,cape:1.3,tint:['#e6efff','#5a86ff']},
  14:{note:'Ethereal ice gown, glides rather than steps',spd:1.02,bob:.6,hover:1.35,sway:.9,atk:1.03,cape:1.7,tint:['#f0fbff','#8fd8ff']},
  15:{note:'Colossal dark plate and greatsword; slow, crushing',spd:.96,acc:.95,cad:1.1,bob:.9,weight:1,atk:1.12,lunge:1.1,cape:1.1,tint:['#e2c8ff','#8a2be2']},
  16:{note:'Long coat and rapier; flamboyant, precise',spd:1.0,acc:1.0,bob:1.05,lean:1.05,atk:.96,lunge:1.1,cape:1.4,tint:['#ffffff','#c7d4ff']},
  17:{note:'Tool-laden leathers, big backpack, crossbow; tinkerer',spd:1.0,cad:.98,bob:1.05,weight:.55,atk:1.0,cape:.8,tint:['#ffe0a0','#d98a2a']},
  18:{note:'Lithe martial artist in wraps; fastest, lowest stance',spd:1.04,acc:1.05,bob:1.05,lean:1.1,turn:1.1,atk:.96,cape:1.2,tint:['#ffe0b0','#ff8a2a']},
  19:{note:'Spear-hunter with wolf at heel; rugged, alert',spd:1.0,lean:1.05,bob:1.0,atk:.98,cape:1.3,tint:['#f2ffe0','#4f9a3c']}};
const cache={};
export function profileFor(heroId){if(cache[heroId])return cache[heroId];
  const h=HEROES[heroId]||{},c=CLASS_PROFILES[h.className]||{},t=HERO_TWEAKS[heroId]||{},p={...DEFAULT,...c};
  // numeric tweaks multiply on top of class; non-numeric (idle, fam, fx, tint, note) replace
  for(const k in t){if(typeof t[k]==='number'&&typeof p[k]==='number'&&k!=='weight'&&k!=='hover')p[k]=p[k]*t[k];else p[k]=t[k]}
  p.family=FAMILY[p.fam]||FAMILY.slash;p.hero=heroId;return cache[heroId]=p}
// ---- VFX palette + primitive table. p = primitive; c = [core, glow]; s = size ----
export const VFX={
  arc_steel:{p:'arc',c:['#f2f6ff','#6a8cff'],s:1}, arc_gold:{p:'arc',c:['#fff4c2','#ffc83a'],s:1.05}, arc_blood:{p:'arc',c:['#ffd0c0','#d3202a'],s:1.2},
  arc_umbral:{p:'arc',c:['#f0ddff','#7a2fd0'],s:1.3}, line_steel:{p:'line',c:['#ffffff','#7fa0ff'],s:1}, line_silver:{p:'line',c:['#ffffff','#cfd8ff'],s:.8},
  line_wild:{p:'line',c:['#f3ffe0','#58a840'],s:1}, flurry_shadow:{p:'flurry',c:['#e8e8ff','#4a2aa0'],s:1}, flurry_gold:{p:'flurry',c:['#fff1c8','#ff9a2a'],s:1},
  arrow_green:{p:'proj',k:'arrow',c:['#f4ffe6','#4dbb5d'],s:1}, bolt_blood:{p:'proj',k:'bolt',c:['#ffffff','#d3203a'],s:1}, bolt_brass:{p:'proj',k:'bolt',c:['#fff0c0','#e09a2a'],s:1,sparks:1},
  orb_fire:{p:'proj',k:'orb',c:['#fff2b0','#ff5a1a'],s:1.1}, shard_frost:{p:'proj',k:'shard',c:['#ffffff','#7fd4ff'],s:1}, wisp_shadow:{p:'wisps',c:['#d9ffd0','#6b2fc0'],s:1},
  glyph_rune:{p:'glyph',c:['#e6f0ff','#4a7cff'],s:1}, orb_leaf:{p:'proj',k:'orb',c:['#efffc9','#58b84a'],s:1,leaf:1}, bolt_storm:{p:'proj',k:'bolt',c:['#ffffff','#38c6e8'],s:1.1,zig:1},
  rays_holy:{p:'rays',c:['#fffbe0','#ffd25a'],s:1}, notes_bard:{p:'notes',c:['#fff0d0','#e0508a'],s:1},
  // skill VFX
  ring_bash:{p:'ring',c:['#ffffff','#7fa0ff'],s:1}, ring_gold:{p:'ring',c:['#fff6d0','#ffc83a'],s:1.2}, ring_quake:{p:'ring',c:['#ffe0b0','#a86a2a'],s:1.5,dust:1},
  ring_umbral:{p:'ring',c:['#f0ddff','#7a2fd0'],s:1.5}, ring_blood:{p:'ring',c:['#ffd0c0','#d3202a'],s:1.6},
  arc_big_steel:{p:'arc',c:['#ffffff','#6a8cff'],s:1.7}, arc_big_blood:{p:'arc',c:['#ffd8c8','#d3202a'],s:1.9}, arc_big_umbral:{p:'arc',c:['#f4e6ff','#8a2be2'],s:2},
  line_big:{p:'line',c:['#ffffff','#7fa0ff'],s:1.7}, line_big_wild:{p:'line',c:['#f3ffe0','#58a840'],s:1.7},
  flurry_big_shadow:{p:'flurry',c:['#ffffff','#5a2ad0'],s:1.5}, flurry_big_gold:{p:'flurry',c:['#fff1c8','#ff7a1a'],s:1.5},
  arrow_volley:{p:'proj',k:'arrow',c:['#f4ffe6','#4dbb5d'],s:1.3,n:5}, bolt_big_blood:{p:'proj',k:'bolt',c:['#fff','#d3203a'],s:1.7},
  bolt_net:{p:'proj',k:'orb',c:['#fff0c0','#e09a2a'],s:1.5,sparks:1}, orb_meteor:{p:'proj',k:'orb',c:['#fff2b0','#ff3a0a'],s:2.2,sky:1},
  orb_fire_big:{p:'burst',c:['#fff2b0','#ff5a1a'],s:1.6}, shard_big:{p:'shards',c:['#ffffff','#7fd4ff'],s:1.6}, shards_ring:{p:'shards',c:['#ffffff','#9fe0ff'],s:1.2},
  wisp_big:{p:'wisps',c:['#d9ffd0','#8a2be2'],s:1.6}, glyph_big:{p:'glyph',c:['#ffffff','#4a7cff'],s:1.7}, rays_big:{p:'rays',c:['#fffbe0','#ffd25a'],s:1.6},
  burst_leaf:{p:'burst',c:['#efffc9','#58b84a'],s:1.3,leaf:1}, burst_storm:{p:'burst',c:['#ffffff','#38c6e8'],s:1.5,zig:1},
  notes_big:{p:'notes',c:['#fff0d0','#ffb02a'],s:1.7}, rays_heal:{p:'rays',c:['#e8fff4','#5fe0b0'],s:1.1}, glyph_ward:{p:'glyph',c:['#fff6d0','#ffc83a'],s:1.2},
  burst_holy:{p:'burst',c:['#fffbe0','#ffd25a'],s:1.5}, burst_dark:{p:'burst',c:['#f0ddff','#7a2fd0'],s:1.5}};
// ---- runtime FX state ----
let FX=[];const SHAKE=[];let HIT=[];
const ang=(a,b)=>Math.atan2(b.y-a.y,b.x-a.x);
// Spawn the VFX for an action. t0 = absolute strike time (the effect starts when the blow lands). target may be null.
export function strikeFx(heroId,kind,vfxId,x,y,tx,ty,t0,opts={}){const p=profileFor(heroId),def=VFX[vfxId||p.fx]||VFX[p.fx];if(!def)return;
  const col=(p.tint&&(!vfxId||vfxId===p.fx||opts.tintAll))?p.tint:def.c,heavy=kind==='heavy'||kind==='super'||kind==='ult';
  const dx=tx-x,dy=ty-y,d=Math.hypot(dx,dy)||1,a=Math.atan2(dy||0,dx||(opts.dir||1));
  const n=def.n||1;for(let i=0;i<n;i++)FX.push({def,c:col,x,y:y-18,tx,ty:ty-14,a,dist:d,t0:t0+i*70,dur:def.p==='proj'?Math.min(520,140+d*1.6):def.p==='ring'||def.p==='glyph'?650:420,kind,s:(def.s||1)*(kind==='ult'?1.5:kind==='super'?1.15:1),seed:Math.random()*100,off:n>1?(i-(n-1)/2)*.12:0,dir:opts.dir||1,id:heroId});
  if(FX.length>60)FX.splice(0,FX.length-60);
  if(heavy){const w=p.weight;HIT.push({at:t0,dur:kind==='ult'?130:kind==='super'?95:60+40*w});SHAKE.push({at:t0,dur:kind==='ult'?420:kind==='super'?300:200,amp:(kind==='ult'?7:kind==='super'?4.5:2.6)*(.7+.6*w),a})}}
export const clearFx=()=>{FX=[];HIT=[];SHAKE.length=0};
// hit-stop: scales sim time briefly at the moment of a heavy impact
export function timeScale(dt,time,reduce){if(reduce)return dt;for(const h of HIT)if(time>=h.at&&time<h.at+h.dur)return dt*.12;return dt}
// camera nudge: decaying shake along the strike direction
export function camera(time,reduce){let x=0,y=0;if(reduce){return{x,y}}
  for(let i=SHAKE.length-1;i>=0;i--){const s=SHAKE[i],e=time-s.at;if(e>s.dur){SHAKE.splice(i,1);continue}if(e<0)continue;const k=Math.exp(-e/(s.dur*.35))*Math.cos(e*.06);x+=Math.cos(s.a)*s.amp*k;y+=Math.sin(s.a)*s.amp*k*.6}
  for(let i=HIT.length-1;i>=0;i--)if(time>HIT[i].at+HIT[i].dur+50)HIT.splice(i,1);
  return{x,y}}
// ---- drawing (world space, after characters). Painted-feel: additive glow cores over soft coloured bloom. ----
const glow=(C,x,y,r,col,al)=>{const g=C.createRadialGradient(x,y,0,x,y,r);g.addColorStop(0,col);g.addColorStop(1,'rgba(0,0,0,0)');C.globalAlpha=al;C.fillStyle=g;C.beginPath();C.arc(x,y,r,0,7);C.fill();C.globalAlpha=1};
const ease=t=>1-Math.pow(1-t,3);
function drawOne(C,f,t,reduce){const D=f.def,[core,gl]=f.c,e=ease(t),fade=Math.max(0,1-t*t),s=f.s,R=reduce?.6:1;
  C.save();C.globalCompositeOperation='lighter';
  switch(D.p){
  case 'arc':{const r=34*s,a0=f.a-1.3*f.dir*(1-e)-.2,a1=f.a+1.1*f.dir*e;C.translate(f.x+Math.cos(f.a)*8,f.y);C.scale(1,.78);
    for(const [w,col,al] of [[16*s,gl,.35],[8*s,gl,.6],[3.2*s,core,.95]]){C.lineWidth=w*fade+.5;C.strokeStyle=col;C.globalAlpha=al*fade;C.lineCap='round';C.beginPath();C.arc(0,0,r,Math.min(a0,a1),Math.max(a0,a1));C.stroke()}
    glow(C,Math.cos(a1)*r,Math.sin(a1)*r,16*s,core,.6*fade);break}
  case 'line':{const L=(60+60*e)*s,ca=Math.cos(f.a),sa=Math.sin(f.a),x0=f.x+ca*10,y0=f.y+sa*10,x1=x0+ca*L,y1=y0+sa*L*.8;
    for(const [w,col,al] of [[10*s,gl,.35],[4.5*s,gl,.7],[2*s,core,1]]){C.lineWidth=w*fade+.4;C.strokeStyle=col;C.globalAlpha=al*fade;C.lineCap='round';C.beginPath();C.moveTo(x0+ca*L*.35*e,y0+sa*L*.28*e);C.lineTo(x1,y1);C.stroke()}
    glow(C,x1,y1,14*s,core,.7*fade);break}
  case 'flurry':{const n=Math.round(5*Math.min(s,1.5)*R);for(let i=0;i<n;i++){const k=(t*1.6-i*.12);if(k<0||k>1)continue;const aa=f.a+(Math.sin(f.seed+i*2.3))*1.1,rr=18+16*s*(1-k)+i*3,ox=Math.cos(f.a)*20,fk=1-k;
    C.globalAlpha=fk;C.lineCap='round';C.strokeStyle=gl;C.lineWidth=7*fk*s;C.beginPath();C.arc(f.x+ox,f.y,rr,aa-.5,aa+.5);C.stroke();C.strokeStyle=core;C.lineWidth=2.2*fk;C.stroke()}
    glow(C,f.x+Math.cos(f.a)*30,f.y,22*s,gl,.4*fade);break}
  case 'proj':{const k=D.k;let px,py;const sky=D.sky;const fl=Math.min(1,t*1.15),ex=f.tx,ey=f.ty;
    const tr=(u)=>{const bx=f.x+(ex-f.x)*u,by=f.y+(ey-f.y)*u;return sky?[bx+(1-u)*-120*f.dir,by-(1-u)*260]:[bx,by-Math.sin(u*Math.PI)*(k==='arrow'?10:4)+(D.zig?Math.sin(u*40+f.seed)*5*(1-u):0)]};
    const u=Math.min(1,t/.8)+0;[px,py]=tr(Math.min(1,u)+f.off*0);const py2=py+f.off*40*(1-Math.min(1,u));
    const imp=t>.8?(t-.8)/.2:0;
    if(u<1){C.lineCap='round';for(let j=6;j>=1;j--){const [qx,qy]=tr(Math.max(0,u-j*.035));C.globalAlpha=.5*(1-j/7);C.strokeStyle=gl;C.lineWidth=(k==='orb'?9:3.5)*s*(1-j/8);C.beginPath();C.moveTo(qx,qy+f.off*40*(1-u));C.lineTo(px,py2);C.stroke()}
      if(k==='arrow'){const [bx,by]=tr(Math.max(0,u-.03));C.globalAlpha=1;C.strokeStyle=core;C.lineWidth=2;C.beginPath();C.moveTo(bx,by+f.off*40*(1-u));C.lineTo(px,py2);C.stroke();C.fillStyle=core;C.beginPath();const ar=Math.atan2(py2-by,px-bx);C.moveTo(px+Math.cos(ar)*5,py2+Math.sin(ar)*5);C.lineTo(px+Math.cos(ar+2.5)*4,py2+Math.sin(ar+2.5)*4);C.lineTo(px+Math.cos(ar-2.5)*4,py2+Math.sin(ar-2.5)*4);C.fill()}
      else if(k==='shard'){C.fillStyle=core;C.globalAlpha=1;C.save();C.translate(px,py2);C.rotate(Math.atan2(ey-f.y,ex-f.x));C.beginPath();C.moveTo(9*s,0);C.lineTo(-5*s,-3.5*s);C.lineTo(-2*s,0);C.lineTo(-5*s,3.5*s);C.fill();C.restore();glow(C,px,py2,13*s,gl,.6)}
      else{glow(C,px,py2,(k==='orb'?18:11)*s,gl,.8);glow(C,px,py2,(k==='orb'?8:5)*s,core,1)}
      if(D.leaf&&!reduce){C.globalAlpha=.8;C.fillStyle=gl;for(let j=0;j<3;j++){C.fillRect(px-j*7+Math.sin(t*20+j)*3,py2+Math.cos(t*17+j*2)*5,3,2)}}
      if(D.sparks&&!reduce){C.fillStyle=core;for(let j=0;j<4;j++)C.fillRect(px-j*5-Math.random()*4,py2+(Math.random()-.5)*8,2,2)}}
    else{const r=(10+26*imp)*s;glow(C,ex,ey,r,gl,.9*(1-imp));glow(C,ex,ey,r*.45,core,1-imp)}
    break}
  case 'burst':{const r=(18+46*e)*s;glow(C,f.tx,f.ty,r*1.2,gl,.7*fade);const n=Math.round(10*R);for(let i=0;i<n;i++){const a=f.seed+i*6.283/n,rr=r*(.5+.5*((i*7)%3)/2);C.globalAlpha=fade;C.fillStyle=i%2?core:gl;C.fillRect(f.tx+Math.cos(a)*rr-1.5,f.ty+Math.sin(a)*rr*.7-1.5,3,3)}
    if(D.zig){C.strokeStyle=core;C.lineWidth=2;C.globalAlpha=fade;C.beginPath();let zx=f.tx,zy=f.ty-80*(1-e);C.moveTo(zx,zy);for(let i=0;i<6;i++){zx+=(Math.sin(f.seed*(i+1))*9);zy+=(f.ty-zy)/(6-i);C.lineTo(zx,zy)}C.stroke()}
    glow(C,f.tx,f.ty,r*.5,core,.9*fade);break}
  case 'ring':{const cx=f.x+Math.cos(f.a)*30*(D.s>1.2?0:1),cy=f.y+20,r=(14+58*e)*s;C.translate(cx,cy);C.scale(1,.38);
    for(const [w,col,al] of [[14*s,gl,.3],[6*s,gl,.6],[2.4,core,.95]]){C.lineWidth=w*fade+.4;C.strokeStyle=col;C.globalAlpha=al*fade;C.beginPath();C.arc(0,0,r,0,7);C.stroke()}
    if(D.dust&&!reduce){C.globalCompositeOperation='source-over';C.fillStyle='rgba(120,90,60,.5)';for(let i=0;i<10;i++){const a=i*.63+f.seed;C.globalAlpha=.5*fade;C.beginPath();C.arc(Math.cos(a)*r,Math.sin(a)*r,4+e*5,0,7);C.fill()}}break}
  case 'glyph':{const cx=f.tx||f.x,cy=(f.ty||f.y)+26,r=30*s*(.6+.4*e);C.translate(cx,cy);C.scale(1,.4);const al=Math.min(1,t*5)*Math.max(0,1-Math.max(0,t-.6)/.4);
    C.globalAlpha=al;C.strokeStyle=gl;C.lineWidth=5;C.beginPath();C.arc(0,0,r,0,7);C.stroke();C.strokeStyle=core;C.lineWidth=1.6;C.beginPath();C.arc(0,0,r*.78,0,7);C.stroke();
    C.rotate(t*3);for(let i=0;i<6;i++){C.rotate(1.047);C.fillStyle=core;C.fillRect(r*.82-3,-3,6,6);C.strokeStyle=gl;C.strokeRect(r*.55,-4,7,8)}
    C.setTransform(1,0,0,1,0,0);break}
  case 'rays':{const cx=f.tx||f.x,cy=f.ty||f.y,H=120*s*Math.min(1,t*4);const al=Math.max(0,1-Math.max(0,t-.4)/.6);
    for(let i=-3;i<=3;i++){const g=C.createLinearGradient(0,cy-H,0,cy+24);g.addColorStop(0,'rgba(255,255,255,0)');g.addColorStop(.5,gl);g.addColorStop(1,core);C.globalAlpha=al*(.35-Math.abs(i)*.04);C.fillStyle=g;C.fillRect(cx+i*9*s-3,cy-H,6,H+24)}
    glow(C,cx,cy+10,34*s,core,.55*al);break}
  case 'shards':{const cx=f.tx||f.x,cy=f.ty||f.y;for(let i=0;i<8;i++){const a=i*.785+f.seed,rr=(10+48*e)*s;C.globalAlpha=fade;C.fillStyle=i%2?core:gl;C.save();C.translate(cx+Math.cos(a)*rr,cy+Math.sin(a)*rr*.7);C.rotate(a);C.beginPath();C.moveTo(9*s,0);C.lineTo(-4,-3);C.lineTo(-4,3);C.fill();C.restore()}glow(C,cx,cy,28*s,gl,.4*fade);break}
  case 'wisps':{const cx=f.tx||f.x,cy=f.ty||f.y,n=Math.round(6*R);for(let i=0;i<n;i++){const k=Math.min(1,Math.max(0,t*1.3-i*.06)),bx=f.x+(cx-f.x)*k+Math.sin(k*9+i)*14,by=f.y+(cy-f.y)*k-Math.sin(k*3.14)*18+Math.cos(k*7+i)*6;
    C.globalAlpha=Math.sin(Math.min(1,k)*3.14)*.9;glow(C,bx,by,12*s,gl,1);glow(C,bx,by,5*s,core,1)}
    if(t>.7)glow(C,cx,cy,30*s*(t-.7)*3,gl,.5*fade);break}
  case 'notes':{const cx=f.x,cy=f.y;for(let i=0;i<3;i++){const k=Math.max(0,t*1.2-i*.15);if(k>1)continue;C.globalAlpha=(1-k)*.8;C.strokeStyle=i%2?core:gl;C.lineWidth=3;C.save();C.translate(cx,cy+4);C.scale(1,.5);C.beginPath();C.arc(0,0,(12+60*k)*s,0,7);C.stroke();C.restore()}
    if(!reduce)for(let i=0;i<4;i++){const k=Math.min(1,t*1.1),a=f.seed+i*1.6,rr=22+30*k;C.globalAlpha=(1-k);C.fillStyle=core;const nx=cx+Math.cos(a)*rr,ny=cy-8-k*30+Math.sin(a)*10;C.beginPath();C.ellipse(nx,ny,3,2.2,-.4,0,7);C.fill();C.fillRect(nx+2.2,ny-9,1.4,9)}
    break}
  }
  C.restore();C.globalAlpha=1;C.globalCompositeOperation='source-over'}
export function drawFx(C,time,reduce){if(!FX.length)return;FX=FX.filter(f=>time<f.t0+f.dur+60);
  for(const f of FX){const t=(time-f.t0)/f.dur;if(t<0||t>1)continue;C.save();drawOne(C,f,t,reduce);C.restore()}}
export const fxCount=()=>FX.length;
// Charge-up glow on a caster's hand/staff during wind-up (drawn in hero local space by game.js)
export function chargeGlow(C,P,heroId,reduce){const p=profileFor(heroId);if(!p.family.glow||P.stage!=='wind'&&P.stage!=='strike')return;
  const k=P.stage==='wind'?P.stageP:1-P.stageP*.6,col=(p.tint||(VFX[p.fx]||VFX.orb_fire).c);C.save();C.globalCompositeOperation='lighter';
  glow(C,14*P.sgn,-24-P.dy*0,(8+16*k)*(reduce?.7:1),col[1],.8*k);glow(C,14*P.sgn,-24,(3+7*k),col[0],.9*k);C.restore()}
// Weapon-trail overlay for melee wind-up (faint arc following the swing); drawn in hero local space
export function weaponTrail(C,P,heroId,reduce){const p=profileFor(heroId);if(P.stage!=='strike'||reduce||p.family.glow||p.fam==='draw'||p.fam==='strum')return;
  const col=p.tint||(VFX[p.fx]||VFX.arc_steel).c,k=P.stageP;C.save();C.globalCompositeOperation='lighter';C.globalAlpha=(1-k)*.5;C.strokeStyle=col[1];C.lineWidth=4;C.lineCap='round';
  C.scale(P.sgn||1,1);C.beginPath();C.arc(6,-20,26,-1.6,-1.6+2.4*k);C.stroke();C.restore()}
