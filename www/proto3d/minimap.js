/* Lightweight minimap: actual player coordinates, orientation, zone, and known landmarks.
 * Ornate circular border is only a decorative overlay; the canvas is real-time.
 * Draws at 5 Hz and allocates no THREE meshes, textures, or new draw calls. */
import { CITY_HALF, TITAN_CENTER, FROST_SUMMIT, FROST_PORTAL, PORT_CENTER } from './bossregions.js';

const LANDMARKS=[
 {x:0,z:0,name:'Village',color:'#e8cc8d',zone:'town'},
 {x:FROST_SUMMIT.x,z:FROST_SUMMIT.z,name:'Frost Summit',color:'#b6e5fc',zone:'town'},
 {x:FROST_PORTAL.x,z:FROST_PORTAL.z,name:'Ice Portal',color:'#a1e4ff',zone:'town'},
 {x:TITAN_CENTER.x,z:TITAN_CENTER.z,name:'Ashen Titan',color:'#ff714d',zone:'town'},
 {x:PORT_CENTER.x,z:PORT_CENTER.z,name:'Port',color:'#d9b788',zone:'town'},
];
const css=`
#vnMiniMap{position:fixed;top:max(90px,calc(env(safe-area-inset-top) + 76px));right:max(9px,env(safe-area-inset-right));width:138px;height:152px;z-index:55;display:block;pointer-events:none;color:#f5e4ba;font:700 10px VarnCinzel,Georgia,serif;text-align:center;text-shadow:0 1px 3px #000,0 0 5px #201029}
#vnMiniMap[hidden]{display:none!important}
#vnMiniMap button{position:relative;display:block;width:138px;height:138px;border:0;background:transparent;cursor:pointer;pointer-events:auto;padding:0;touch-action:manipulation;border-radius:50%;filter:drop-shadow(0 3px 6px #000b)}
#vnMiniMap canvas{position:absolute;left:12%;top:12%;width:76%;height:76%;border-radius:50%;background:#211925}
#vnMiniMap .vn-mini-ring{position:absolute;inset:0;display:block;background:url('assets/hud/minimap-ring.svg') center/contain no-repeat;pointer-events:none}
#vnMiniMap .vn-mini-zone{display:block;margin-top:-2px;letter-spacing:.07em;pointer-events:none}
#vnMiniMap button:focus-visible{outline:3px solid #eedba6;outline-offset:0}
#vnMiniMap.expanded{width:238px;height:252px}
#vnMiniMap.expanded button{width:238px;height:238px}
body.vn-menu-open #vnMiniMap{visibility:hidden!important}
@media(orientation:portrait){#vnMiniMap{top:calc(max(12px,env(safe-area-inset-top)) + 58px);width:108px;height:120px}#vnMiniMap button{width:108px;height:108px}#vnMiniMap.expanded{width:188px;height:202px}#vnMiniMap.expanded button{width:188px;height:188px}}
@media(orientation:landscape) and (max-height:450px){#vnMiniMap{top:max(54px,calc(env(safe-area-inset-top) + 48px));width:105px;height:115px}#vnMiniMap button{width:105px;height:105px}#vnMiniMap.expanded{width:162px;height:175px}#vnMiniMap.expanded button{width:162px;height:162px}}
`;

export function createMiniMap(getState,getZone){
 const style=document.createElement('style');style.textContent=css;document.head.appendChild(style);
 const root=document.createElement('div');root.id='vnMiniMap';
 const button=document.createElement('button');button.type='button';button.setAttribute('aria-label','Expand minimap');button.setAttribute('aria-pressed','false');
 const canvas=document.createElement('canvas');canvas.width=canvas.height=220;canvas.setAttribute('aria-hidden','true');
 const ring=document.createElement('i');ring.className='vn-mini-ring';ring.setAttribute('aria-hidden','true');
 const zoneName=document.createElement('span');zoneName.className='vn-mini-zone';
 button.append(canvas,ring);root.append(button,zoneName);document.body.appendChild(root);
 button.addEventListener('click',()=>{
  const expanded=root.classList.toggle('expanded');
  button.setAttribute('aria-pressed',String(expanded));
  button.setAttribute('aria-label',expanded?'Collapse minimap':'Expand minimap');
 });
 const ctx=canvas.getContext('2d',{alpha:false});
 let last=-Infinity;
 function update(now=0){
  if(!ctx||now-last<180)return;last=now;
  const s=getState(),z=getZone(),zone=z?.name||'town',name=zone==='town'?'VARNETHRYL':zone==='frost'?'FROST CAVE':'THE WILDS';
  zoneName.textContent=name;
  const W=220,c=110,R=109,scale=0.51;
  ctx.save();ctx.beginPath();ctx.arc(c,c,R,0,Math.PI*2);ctx.clip();
  ctx.fillStyle=zone==='frost'?'#182536':zone==='wilds'?'#202d22':'#322b22';ctx.fillRect(0,0,W,W);
  // Paper-like terrain grid helps read the direction without pretending to
  // know where exact 3D walls sit. Center stays on the hero's real position.
  const grid=28;
  ctx.lineWidth=1;ctx.strokeStyle=zone==='frost'?'#7296ad32':'#b49a6840';
  for(let x=((-(s.heroX||0)*scale)%grid+grid)%grid;x<W;x+=grid){ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,W);ctx.stroke();}
  for(let y=(((s.heroZ||0)*scale)%grid+grid)%grid;y<W;y+=grid){ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(W,y);ctx.stroke();}
  if(zone==='town'){
   // Draw the existing protected city limits using its real world size.
   const toPx=(x,zz)=>[c+(x-s.heroX)*scale,c+(zz-s.heroZ)*scale];
   const corner=toPx(-CITY_HALF,-CITY_HALF);
   ctx.strokeStyle='#cdb87e';ctx.lineWidth=2;ctx.strokeRect(corner[0],corner[1],2*CITY_HALF*scale,2*CITY_HALF*scale);
  }
  for(const a of LANDMARKS){
   if(a.zone!==zone)continue;
   const x=c+(a.x-s.heroX)*scale,y=c+(a.z-s.heroZ)*scale;
   if(Math.hypot(x-c,y-c)>R-11)continue;
   ctx.fillStyle='#130b1e';ctx.beginPath();ctx.arc(x,y,6,0,Math.PI*2);ctx.fill();
   ctx.strokeStyle=a.color;ctx.lineWidth=2;ctx.beginPath();ctx.arc(x,y,4.2,0,Math.PI*2);ctx.stroke();
  }
  ctx.strokeStyle='#dcc6a1';ctx.lineWidth=1.5;ctx.beginPath();ctx.arc(c,c,26,0,Math.PI*2);ctx.stroke();
  ctx.save();ctx.translate(c,c);ctx.rotate(-(s.yaw||0));
  ctx.beginPath();ctx.moveTo(0,-15);ctx.lineTo(-9,11);ctx.lineTo(0,6);ctx.lineTo(9,11);ctx.closePath();
  ctx.fillStyle='#ffe0a0';ctx.strokeStyle='#3d173d';ctx.lineWidth=3;ctx.stroke();ctx.fill();ctx.restore();
  ctx.font='bold 13px Georgia';ctx.textAlign='center';ctx.fillStyle='#f9debc';ctx.fillText('N',c,16);
  ctx.restore();
 }
 update(0);
 return {root,update};
}
