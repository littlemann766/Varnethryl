/* Varnethryl's live north-up topographic chart.
 * Samples real physics terrain, water, road positions and obstacles, never a
 * fixed screenshot. Mobile-friendly cached background; live actor markers. */
import {CITY_HALF,TITAN_CENTER,FROST_SUMMIT,FROST_PORTAL,PORT_CENTER,lavaAmount,onLava} from './bossregions.js';

const P={town:['VARNETHRYL',160,30],wilds:['THE WILDS',160,35],
 frost:['FROST CAVE',155,30],hydra:['HYDRA MIRE',145,25],
 sailing:['TIDEWRACK OCEAN',250,65]};
const custom=new Map();
const W=220,C=110,N=112;
const css=[
 '#vnMiniMap{position:fixed;top:max(90px,calc(env(safe-area-inset-top) + 76px));right:max(9px,env(safe-area-inset-right));width:138px;height:152px;z-index:55;display:block;pointer-events:none;color:#f5e4ba;font:700 10px VarnCinzel,Georgia,serif;text-align:center;text-shadow:0 1px 3px #000}',
 '#vnMiniMap .vn-mini-open{position:relative;display:block;width:138px;height:138px;border:0;background:transparent;cursor:pointer;pointer-events:auto;padding:0;touch-action:manipulation;border-radius:50%;filter:drop-shadow(0 3px 6px #000b)}',
 '#vnMiniMap canvas{position:absolute;left:12%;top:12%;width:76%;height:76%;border-radius:50%}',
 "#vnMiniMap .vn-mini-ring{position:absolute;inset:0;display:block;background:url('assets/hud/minimap-ring.svg') center/contain no-repeat;pointer-events:none}",
 '#vnMiniMap .vn-mini-zone{display:block;margin-top:-2px;letter-spacing:.07em;pointer-events:none}',
 '#vnMiniMap.expanded{width:238px;height:252px}#vnMiniMap.expanded .vn-mini-open{width:238px;height:238px}',
 '#vnMiniMap .vn-mini-controls{display:none;position:absolute;right:100%;top:55px;margin-right:5px;gap:4px;flex-direction:column;pointer-events:auto}',
 '#vnMiniMap.expanded .vn-mini-controls{display:flex}',
 '#vnMiniMap .vn-mini-control{width:38px;height:34px;border:1px solid #d3b17b;border-radius:6px;background:#20243bed;color:#ffe7bb;font:bold 14px Georgia,serif;cursor:pointer;touch-action:manipulation}',
 '#vnMiniMap .vn-mini-control.full{font-size:10px}',
 '#vnMiniMap .vn-mini-detail{display:none;position:absolute;top:100%;right:0;width:230px;color:#ffebbd;background:#1b2538dd;font:10px Georgia,serif}',
 '#vnMiniMap.expanded .vn-mini-detail{display:block}',
 '#vnMiniMap button:focus-visible{outline:2px solid #ffda85}body.vn-menu-open #vnMiniMap{visibility:hidden!important}',
 '@media(orientation:portrait){#vnMiniMap{top:calc(max(12px,env(safe-area-inset-top)) + 58px);width:108px;height:120px}#vnMiniMap .vn-mini-open{width:108px;height:108px}#vnMiniMap.expanded{width:188px;height:202px}#vnMiniMap.expanded .vn-mini-open{width:188px;height:188px}}',
 '@media(orientation:landscape) and (max-height:450px){#vnMiniMap{top:max(54px,calc(env(safe-area-inset-top) + 48px));width:105px;height:115px}#vnMiniMap .vn-mini-open{width:105px;height:105px}#vnMiniMap.expanded{width:162px;height:175px}#vnMiniMap.expanded .vn-mini-open{width:162px;height:162px}}'
].join('');
function landmarks(zone,z){
 const cx=z.cx||0,cz=z.cz||0,h=z.half||560;
 if(zone==='town')return [
  [0,0,'Village','town'],[0,-134.4,'Castle Keep','town'],
  [TITAN_CENTER.x,TITAN_CENTER.z,'Ashen Titan','boss'],
  [FROST_SUMMIT.x,FROST_SUMMIT.z,'Ice Cave','portal'],
  [-315,-284,'Broken Seal','portal'],
  [PORT_CENTER.x,PORT_CENTER.z,'Harbor','port'],[0,CITY_HALF-1.2,'Town Gate','portal']];
 if(zone==='frost')return [[cx-7,cz+177,'Exit','portal'],[cx-37,cz-66,'Frost Troll A','boss'],[cx+37,cz-66,'Frost Troll B','boss'],[cx+91,cz+18,'Frozen Lake','water']];
 if(zone==='hydra')return [[cx,cz-11,'Hydra','boss'],[cx,cz+117,'Exit','portal']];
 if(zone==='wilds')return [[cx-6,cz-2,'Return Ruins','portal'],[cx,cz+85*(h/280),'Standing Stones','ruin']];
 if(zone==='sailing')return [[cx,cz+h-175,'Departure','port']];
 return [];
}
const markerColors={town:'#ead39e',boss:'#ff8064',portal:'#c199fe',port:'#e4b881',water:'#5bcae6',ruin:'#c9b99e',party:'#8fddff'};
function terrainColor(zone,x,z,e,cx,cz){
 if(zone==='sailing'||e.water?.(zone,x,z))return zone==='sailing'?'#25536d':'#316b82';
 const height=e.height?.(zone,x,z)||0,biome=e.biome?.(zone,x,z)||'meadow';
 if(zone==='hydra')return Math.hypot(x-cx,z-cz)<69?'#7b857b':'#53636b';
 if(zone==='frost'){
  if(Math.hypot(x-cx-91,z-cz-18)<45)return '#477f98';
  return height>29?'#617283':height>8?'#7f95a4':'#b2c6cd';
 }
 if(zone==='wilds')return biome==='forest'?'#365d43':biome==='rock'?'#7b817d':biome==='snow'?'#bfccce':'#65855e';
 if(onLava(x,z))return '#d45f35';
 if(lavaAmount(x,z)>.4)return '#594843';
 if(Math.abs(x)<CITY_HALF&&Math.abs(z)<CITY_HALF)return '#827e6b';
 if(Math.hypot(x-FROST_SUMMIT.x,z-FROST_SUMMIT.z)<145)return height>25?'#b4c7ce':'#859c9d';
 if(height>37)return '#99978d';
 if(height>14)return '#73816a';
 return biome==='forest'?'#416648':biome==='rock'?'#7d8077':'#608460';
}
export function createMiniMap(getState,getZone,env={}){
 const style=document.createElement('style');style.textContent=css;document.head.appendChild(style);
 const root=document.createElement('div');root.id='vnMiniMap';root.dataset.mode='live-topdown';
 const button=document.createElement('button');button.type='button';button.className='vn-mini-open';
 button.setAttribute('aria-label','Expand top-down minimap');button.setAttribute('aria-pressed','false');
 const canvas=document.createElement('canvas');canvas.width=canvas.height=W;canvas.setAttribute('aria-label','Live top-down terrain map');
 const ring=document.createElement('i');ring.className='vn-mini-ring';ring.setAttribute('aria-hidden','true');
 const title=document.createElement('span');title.className='vn-mini-zone';
 const controls=document.createElement('div');controls.className='vn-mini-controls';
 const detail=document.createElement('span');detail.className='vn-mini-detail';detail.textContent='NORTH UP · GOLD ARROW = YOU';
 button.append(canvas,ring);root.append(button,title,controls,detail);document.body.appendChild(root);
 const ctx=canvas.getContext('2d',{alpha:false}),bgCanvas=document.createElement('canvas');
 bgCanvas.width=bgCanvas.height=N;
 const bg=bgCanvas.getContext('2d',{alpha:false}),pixels=bg?.createImageData(N,N);
 const parsed=new Map();
 let active='',cfg=null,radius=0,dirty=true,expanded=false,overview=false,last=-1000,lastPaint=-1000,originX=0,originZ=0,paintCount=0,signature='';
 const invalidate=()=>{dirty=true;last=-1000;};
 function configure(){
  const z=getZone()||{name:'town'};
  if(!cfg||z.name!==active||z.half!==cfg.half||z.cx!==cfg.cx||z.cz!==cfg.cz){
   active=z.name||'town';const v=custom.get(active)||P[active]||[active.toUpperCase(),(z.half||560)*.3,35];
   // A full-map circle must accommodate the furthest square corner.
   // A radius of half*1.08 clips entire quadrants near zone corners.
   cfg={cx:z.cx||0,cz:z.cz||0,half:z.half||560,name:active,label:v[0],min:v[2],max:(z.half||560)*Math.SQRT2*1.07,markers:v[3]||[]};
   radius=v[1];overview=false;root.dataset.view='follow';root.dataset.zone=active;invalidate();
  }
 }
 function zoom(action){
  configure();
  if(action==='full'){overview=true;radius=cfg.max;}
  else{overview=false;radius=Math.max(cfg.min,Math.min(cfg.max,radius*(action==='in'?.65:1.5)));}
  root.dataset.view=overview?'full':'follow';invalidate();
 }
 for(const [action,label,aria] of [['in','+','Zoom in'],['out','−','Zoom out'],['full','FULL','Show full map']]){
  const b=document.createElement('button');b.type='button';b.className='vn-mini-control '+action;b.textContent=label;b.setAttribute('aria-label',aria);
  b.addEventListener('click',event=>{event.stopPropagation();zoom(action);update(performance.now());});controls.appendChild(b);
 }
 button.addEventListener('click',()=>{
  expanded=root.classList.toggle('expanded');
  button.setAttribute('aria-pressed',String(expanded));
  button.setAttribute('aria-label',expanded?'Collapse top-down minimap':'Expand top-down minimap');
  invalidate();update(performance.now());
 });
 function raster(state,time){
  if(!pixels)return;
  // The full chart stays fixed on the world centre; local mode follows hero.
  const px=overview?cfg.cx:(state.heroX||0),pz=overview?cfg.cz:(state.heroZ||0),unit=2*radius*1.2/N;
  for(let j=0;j<N;j++)for(let i=0;i<N;i++){
   const x=px+(i+.5-N/2)*unit,z=pz+(j+.5-N/2)*unit;
   const hex=terrainColor(active,x,z,env,cfg.cx,cfg.cz);
   let col=parsed.get(hex);
   if(!col){col=[parseInt(hex.slice(1,3),16),parseInt(hex.slice(3,5),16),parseInt(hex.slice(5,7),16)];parsed.set(hex,col);}
   const k=4*(j*N+i),f=1+.037*Math.sin(x*.078)*Math.cos(z*.075);
   pixels.data[k]=col[0]*f;pixels.data[k+1]=col[1]*f;pixels.data[k+2]=col[2]*f;pixels.data[k+3]=255;
  }
  bg.putImageData(pixels,0,0);originX=px;originZ=pz;lastPaint=time;dirty=false;
  root.dataset.paintCount=String(++paintCount);
 }
 function overlay(s){
  const scale=C/radius,px=overview?cfg.cx:(s.heroX||0),pz=overview?cfg.cz:(s.heroZ||0);
  const at=(x,z)=>[C+(x-px)*scale,C+(z-pz)*scale];
  const onscreen=(p,r=0)=>p[0]>-r&&p[0]<W+r&&p[1]>-r&&p[1]<W+r;
  if(active==='town'){
   for(const road of env.roads?.()||[]){
    ctx.beginPath();(road.points||[]).forEach((p,i)=>{const q=at(p[0],p[1]);i?ctx.lineTo(q[0],q[1]):ctx.moveTo(q[0],q[1]);});
    ctx.strokeStyle=road.color||'#a79d8b';ctx.lineWidth=Math.max(1,(road.width||8)*scale);ctx.lineJoin='round';ctx.lineCap='round';ctx.stroke();
   }
   const p=at(-CITY_HALF,-CITY_HALF);ctx.strokeStyle='#d1c297';ctx.lineWidth=2;
   ctx.strokeRect(p[0],p[1],2*CITY_HALF*scale,2*CITY_HALF*scale);
   for(const b of env.buildings?.()||[]){
    const q=at(b.cx,b.cz);if(!onscreen(q,10))continue;
    const size=Math.max(2,Math.min(15,(b.size||10)*scale));
    ctx.save();ctx.translate(q[0],q[1]);ctx.rotate(-(b.rot||0));
    ctx.fillStyle=/keep|guild|temple|townhall/.test(b.id)?'#b8ab9b':'#856952';
    ctx.fillRect(-size*.5,-size*.5,size,size);ctx.strokeStyle='#40362d';ctx.lineWidth=1;
    ctx.strokeRect(-size*.5,-size*.5,size,size);ctx.restore();
   }
  }
  if(active==='wilds'){
   const lake=env.lake?.();if(lake){
    const p=at(lake.x,lake.z);ctx.fillStyle='#357e9c';
    ctx.beginPath();ctx.arc(p[0],p[1],lake.r*scale,0,Math.PI*2);ctx.fill();}
  }
  if(active!=='sailing'&&scale>.18){
   ctx.fillStyle=active==='frost'?'#586d7f':active==='hydra'?'#565d58':'#455e4b';let count=0;
   for(const o of env.obstacles?.()||[]){
    if(++count>3500)break;
    if(o.type==='circle'){
     const p=at(o.x,o.z),r=(o.r||1)*scale;if(r<.9||!onscreen(p,r))continue;
     ctx.beginPath();ctx.arc(p[0],p[1],Math.min(20,r),0,Math.PI*2);ctx.fill();
    }else if(o.type==='box'){
     const p=at(o.minX,o.minZ),w=(o.maxX-o.minX)*scale,h=(o.maxZ-o.minZ)*scale;
     if(!onscreen(p,Math.max(w,h)))continue;ctx.fillRect(p[0],p[1],w,h);
    }
   }
  }
  if(active==='sailing')for(const island of env.islands?.(overview)||[]){
   const p=at(island.x,island.z),r=(island.r||1)*scale;if(!onscreen(p,r))continue;
   ctx.fillStyle='#637979';ctx.strokeStyle='#c2bfae';ctx.lineWidth=2;
   ctx.beginPath();ctx.arc(p[0],p[1],Math.max(1,r),0,Math.PI*2);ctx.fill();ctx.stroke();
  }
  const markers=[...landmarks(active,cfg),...cfg.markers,...(env.markers?.(active)||[])];
  for(const b of env.bosses?.()||[])if(b&&b.def?.boss&&b.state!=='defeated')markers.push([b.x,b.z,b.def.name||'Boss','boss']);
  for(const c of env.party?.()||[])if(c.kind==='party'&&!(c.down>0))markers.push([c.a?.x,c.a?.z,'Companion','party']);
  for(const mark of markers){
   const [x,z,label,kind]=mark;if(!Number.isFinite(x)||!Number.isFinite(z))continue;
   const p=at(x,z);if(!onscreen(p,6)||Math.hypot(p[0]-C,p[1]-C)>C-9)continue;
   ctx.fillStyle='#18252b';ctx.strokeStyle=markerColors[kind]||'#ecdeb8';ctx.lineWidth=2;
   ctx.beginPath();ctx.arc(p[0],p[1],kind==='boss'?5:4,0,Math.PI*2);ctx.fill();ctx.stroke();
   if(expanded&&kind!=='party'&&scale>.28){ctx.fillStyle='#fff0d5';ctx.font='bold 8px Georgia';ctx.textAlign='center';ctx.fillText(label,p[0],p[1]-8);}
  }
  // A full map keeps the actual player at their world coordinate, not at
  // the map centre. On local follow mode this still sits at canvas centre.
  // North is always up; walking +Z is south, sailing -Z is north.
  const player=at(s.heroX||0,s.heroZ||0);
  ctx.save();ctx.translate(player[0],player[1]);ctx.rotate(active==='sailing'?-(s.yaw||0):Math.PI-(s.yaw||0));
  ctx.beginPath();ctx.moveTo(0,-15);ctx.lineTo(-9,10);ctx.lineTo(0,4);ctx.lineTo(9,10);ctx.closePath();
  ctx.fillStyle='#ffe4a4';ctx.strokeStyle='#39223e';ctx.lineWidth=3;ctx.stroke();ctx.fill();ctx.restore();
  ctx.fillStyle='#fff0ce';ctx.textAlign='center';ctx.font='bold 13px Georgia';ctx.fillText('N',C,17);
  ctx.font='10px Georgia';ctx.fillText((overview?'FULL · ':'')+Math.round(radius*2)+' wu',C,W-9);
 }
 function update(now=0){
  if(!ctx||now-last<180)return;last=now;
  const state=getState()||{};configure();title.textContent=cfg.label;
  const next=active+'|'+cfg.half+'|'+(env.revision?.()||'');
  if(next!==signature){signature=next;dirty=true;}
  if(dirty||(!overview&&(Math.hypot((state.heroX||0)-originX,(state.heroZ||0)-originZ)>radius*.08||now-lastPaint>2400)))raster(state,now);
  ctx.save();ctx.beginPath();ctx.arc(C,C,C-1,0,Math.PI*2);ctx.clip();
  ctx.fillStyle='#314e4b';ctx.fillRect(0,0,W,W);
  const size=W*1.2,scale=C/radius,centreX=overview?cfg.cx:(state.heroX||0),centreZ=overview?cfg.cz:(state.heroZ||0);
  ctx.drawImage(bgCanvas,C-size/2+(originX-centreX)*scale,C-size/2+(originZ-centreZ)*scale,size,size);
  root.dataset.centerX=String(centreX);root.dataset.centerZ=String(centreZ);
  root.dataset.playerX=String(state.heroX||0);root.dataset.playerZ=String(state.heroZ||0);
  root.dataset.radius=String(radius);
  root.dataset.islandCount=active==='sailing'?String((env.islands?.(overview)||[]).length):'0';
  overlay(state);ctx.restore();
 }
 // First draw belongs to the animation frame after all party/zone bindings exist.
 return {root,update,invalidate,registerZone:(name,config)=>{
   if(typeof name!=='string'||!Array.isArray(config)||config.length<3)return false;
   custom.set(name,config);invalidate();return true;
  },get zone(){return active;},get radius(){return radius;},get paintCount(){return paintCount;}};
}
