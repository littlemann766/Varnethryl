// Varnethryl actor motion: inertia-driven pose from real movement. No fixed-rate bouncing.
// Stride phase advances with DISTANCE travelled, so planted feet never slide; analog speed drives walk/jog/run blend.
import {profileFor,FAMILY} from './classmotion.js';
const clamp=(n,a,b)=>Math.max(a,Math.min(b,n));
const ss=(a,b,x)=>{const t=clamp((x-a)/(b-a),0,1);return t*t*(3-2*t)};
export const MAXV=.18; // px/ms at full run (matches game speed)
// Action timings (ms): wind-up, strike, follow-through; lean (rad), lunge (px), moveMul during each phase.
export const ACT={
  basic:{wind:90, strike:70, follow:230,lean:.14,lunge:5, mm:[.35,.15,.6]},
  minor:{wind:110,strike:80, follow:260,lean:.17,lunge:6, mm:[.3,.12,.55]},
  heavy:{wind:200,strike:110,follow:380,lean:.25,lunge:11,mm:[.2,.05,.4]},
  super:{wind:320,strike:140,follow:520,lean:.33,lunge:16,mm:[.12,.03,.3]},
  ult:  {wind:520,strike:200,follow:800,lean:.42,lunge:24,mm:[.05,.02,.2]}};
const A={};let current=null;
const get=id=>A[id]||(A[id]={prof:profileFor(id),t:-1,x:0,y:0,vx:0,vy:0,speed:0,pspeed:0,phase:0,lean:0,leanV:0,sx:1,sgn:1,settleT:-1e9,settleAmp:0,act:null,pose:null});
// Class-aware action timing: family (slash/bash/thrust/overhead/flurry/draw/cast/strum) and the hero's attack-speed scale
// reshape wind-up / strike / follow-through. fam overrides the class family (skills can pick their own animation).
export function act(id,kind,time,fam){const b=ACT[kind]||ACT.basic,p=profileFor(id),F=FAMILY[fam]||p.family,k=p.atk*(kind==='ult'?1:1);
  const d={...b,wind:b.wind*F.windMul*k,strike:b.strike*F.strikeMul*k,follow:b.follow*F.followMul*k,lunge:b.lunge*p.lunge*Math.abs(F.lunge),fam:fam||p.fam,F,kind};
  const a=get(id);a.act={kind,d,t0:time};current={id,d,t0:time};return d}
// Movement multiplier for the player while an action is in progress (momentum: you can't sprint through a swing).
export function moveMul(time){if(!current)return 1;const {d,t0}=current,e=time-t0;
  if(e<d.wind)return d.mm[0]+(1-d.mm[0])*0;if(e<d.wind+d.strike)return d.mm[1];
  const f=e-d.wind-d.strike;if(f<d.follow)return d.mm[2]+(1-d.mm[2])*ss(0,d.follow,f);current=null;return 1}
export const profile=profileFor;export const maxSpeed=id=>MAXV*profileFor(id).spd;
export const strikeAt=kind=>{const d=ACT[kind]||ACT.basic;return d.wind};
export const isActing=time=>current&&time-current.t0<current.d.wind+current.d.strike+current.d.follow;
// Update + return pose. faceHint: optional angle (rad) of intent so turn-in-place works at rest.
export function pose(id,x,y,time,faceHint,reduce){const a=get(id);
  if(a.t<0||Math.hypot(x-a.x,y-a.y)>220){a.x=x;a.y=y;a.t=time;a.pose=null;a.vx=a.vy=0}
  const dt=time-a.t;
  if(dt>0){const k=Math.min(dt,60);
    const rvx=(x-a.x)/k,rvy=(y-a.y)/k,f=1-Math.exp(-k/45);const pvx=a.vx;
    a.vx+= (rvx-a.vx)*f;a.vy+=(rvy-a.vy)*f;a.x=x;a.y=y;a.t=time;
    a.pspeed=a.speed;a.speed=Math.hypot(a.vx,a.vy);
    const ax=(a.vx-pvx)/k;
    // Stop recovery: small settle when a run is cut short.
    if(a.pspeed>.09&&a.speed<.05&&time-a.settleT>400){a.settleT=time;a.settleAmp=clamp(a.pspeed/MAXV,.3,1)}
    // stride: distance-driven so feet are planted; step length grows with speed.
    if(a.speed>.012){const Ls=(24+a.speed*80)*a.prof.cad;a.phase+=a.speed*k/Ls}else a.phase+=((Math.round(a.phase/2)*2-a.phase)*(1-Math.exp(-k/120)));
    // lean spring: leans into velocity & acceleration (into the turn), settles with damping.
    const PF=a.prof,lm=PF.lean*(reduce?.5:1),target=clamp((a.vx*1.5+ax*80)*lm,-.28*lm,.28*lm),w=.012*(1.15-.3*PF.weight),z=.75+.1*PF.weight;
    a.leanV+=(-w*w*(a.lean-target)-2*z*w*a.leanV)*k;a.lean+=a.leanV*k;
    // facing / turn-in-place: horizontal yaw eased through a pivot instead of snapping.
    let face=faceHint;if(face==null&&a.speed>.02)face=Math.atan2(a.vy,a.vx);
    if(face!=null){const c=Math.cos(face);if(c>.2)a.sgn=1;else if(c<-.2)a.sgn=-1}
    const rate=.011*k*a.prof.turn;a.sx+=clamp(a.sgn-a.sx,-rate,rate);
  }
  const PF=a.prof,sp=a.speed,run=ss(.07,.16,sp),walk=ss(.004,.05,sp),gait=walk;
  // weight shift: lateral sway follows which foot is loaded; idle breathing/shift when standing.
  let dx=Math.cos(Math.PI*a.phase)*(.6+1.6*run)*walk*PF.sway*(reduce?.3:1)+Math.sin(time*.0011)*.5*(1-walk)*(PF.idle==='sway'||PF.idle==='strum'?1.8:1);
  // vertical: body rises mid-step, lowest at foot plant (two bumps per stride, amplitude from speed)
  let dy=-Math.abs(Math.sin(Math.PI*a.phase))*(.8+2.7*run)*walk*PF.bob*(reduce?.3:1);
  let sy=1,lean=a.lean,sxm=1;
  // stop settle
  const se=time-a.settleT;if(se>=0&&se<520){const e=Math.exp(-se/170)*Math.sin(Math.PI*clamp(se/260,0,1.6)*1.0);dy+=a.settleAmp*3*e*(.4+PF.weight);sy-=a.settleAmp*.035*e*(.4+PF.weight*1.2);lean-=a.settleAmp*.05*e*a.sgn}
  // idle breathing
  sy+=Math.sin(time*.0021)*.006*PF.breath*(1-walk)*(PF.idle==='ready'?1.7:PF.weight>.8?1.3:1);
  // idle style: casters float/hover (lifted, slower bob), bards bounce to a beat, rangers/clerics sway; hover grows a little with speed-independent lift
  let hover=0;if(PF.hover){const hv=PF.hover*(reduce?.4:1);hover=hv*(3+1.2*Math.sin(time*.0027+a.phase*.3));dy-=hover}
  if(PF.idle==='strum'&&!reduce){const b=Math.max(0,Math.sin(time*.0065));dy-=b*1.1*(1-walk);sy+=b*.012*(1-walk)}
  if(PF.idle==='ready'&&!reduce)dx+=Math.sin(time*.0042)*.7*(1-walk);
  // actions: wind-up (pull back, coil) -> strike (lunge) -> follow-through (decay with momentum)
  let lunge=0,stage=null,stageP=0,sxm2=1;if(a.act){const {d,t0}=a.act,e=time-t0,tot=d.wind+d.strike+d.follow,F=d.F,rf=reduce?.5:1;
    if(e>=tot)a.act=null;else{const s=a.sgn,lg=d.lunge*Math.sign(F.lunge||1);
      if(e<d.wind){const p=ss(0,d.wind,e);stage='wind';stageP=p;lean+=-s*d.lean*F.back*p*rf;dy+=(1.5*p)-F.rise*p*rf;sy-=F.crouch*p;lunge=-s*lg*.25*p;if(F.squash)sxm2=1+F.squash*p}
      else if(e<d.wind+d.strike){const p=(e-d.wind)/d.strike,q=p*p*(3-2*p);stage='strike';stageP=p;
        let fw=F.fwd;if(F.multi>1){const w=Math.sin(p*Math.PI*F.multi);fw=F.fwd*(.35+.65*Math.abs(w));dx+=w*1.4*s}
        lean+=s*d.lean*(-F.back+(F.back+fw)*q)*rf;lunge=s*lg*(-.25+1.25*q)*(F.multi>1?.7:1);sy+=.03*q-(F.squash?F.squash*q*.9:0);dy-=(1*q)-(F.rise*(1-q)*rf);if(F.squash)sxm2=1+F.squash*(1-q);
        if(F.pulse)sy+=Math.sin(p*Math.PI*F.multi*2)*.02}
      else{const p=(e-d.wind-d.strike)/d.follow,q=1-Math.pow(1-p,3);stage='follow';stageP=p;lean+=s*d.lean*(F.fwd>0?1.2:-.6)*(1-q)*rf;lunge=s*lg*(1-q);dy+=.4*Math.sin(Math.PI*p)+(F.rise?F.rise*(1-q)*.4*rf:0);if(F.recoil)sy-=.025*(1-q)}
    }}
  const P={sx:(Math.abs(a.sx)<.28?.28*Math.sign(a.sx||1):a.sx)*sxm*sxm2,hover,stage,stageP,fam:a.act?a.act.d.fam:null,actKind:a.act?a.act.kind:null,sy,lean,dx:dx+lunge,dy,speed:sp,gait,run,phase:a.phase,vx:a.vx,vy:a.vy,sgn:a.sgn,
    gaitName:sp<.012?'idle':sp<.07?'walk':sp<.13?'jog':'run',pivot:Math.abs(a.sx-a.sgn)>.15};
  a.pose=P;return P}
// Planted foot contacts in world space relative to the body: each foot is stationary while in stance.
export function feet(P,id){const a=A[id];if(!a)return[];const Ls=(24+P.speed*80)*(a.prof?a.prof.cad:1),out=[];
  const h=Math.atan2(a.vy,a.vx),ux=Math.cos(h),uy=Math.sin(h);
  for(let k=0;k<2;k++){let s=((a.phase+k)%2+2)%2,off,lift=0;
    if(s<1)off=Ls/2*(1-2*s);else{const t=s-1;off=-Ls/2+Ls*(t*t*(3-2*t));lift=Math.sin(Math.PI*t)}
    const side=(k?1:-1)*4.5;if(P.speed<.012){out.push({x:side*.8,y:0,lift:0});continue}
    out.push({x:ux*off-uy*side*.3,y:uy*off*.4+side*.35,lift})}
  return out}
