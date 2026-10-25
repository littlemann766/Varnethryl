import json
from playwright.sync_api import sync_playwright
JS=r"""async()=>{
const T=await import('./townlands.js'),B=await import('./bossregions.js'),F=await import('./frostreach.js'),H=await import('./hobcamps.js');
let s=20261024;const R=()=>{s=(s*1664525+1013904223)>>>0;return s/4294967296};const pick=a=>a[Math.floor(R()*a.length)];
const roadD=(x,z)=>{let best=1e9;for(const r of T.TOWN_MAP_ROADS)for(let i=1;i<r.points.length;i++){const[ax,az]=r.points[i-1],[bx,bz]=r.points[i],dx=bx-ax,dz=bz-az;const t=Math.max(0,Math.min(1,((x-ax)*dx+(z-az)*dz)/(dx*dx+dz*dz||1)));best=Math.min(best,Math.hypot(x-ax-t*dx,z-az-t*dz)-r.width/2);}return best;};
const slope=(h,x,z)=>Math.max(Math.abs(h(x+2,z)-h(x-2,z)),Math.abs(h(x,z+2)-h(x,z-2)))/4;
const taken=[];const free=(x,z,r)=>taken.every(t=>Math.hypot(t[0]-x,t[1]-z)>t[2]+r);
const out={frost_town:[],frost_realm:[],volcano:[],port:[],hobcamps:[]};
const add=(zone,file,x,z,ry,sc,rep,r)=>{out[zone].push({file,position:[+x.toFixed(2),null,+z.toFixed(2)],rotation:[0,+ry.toFixed(3),0],scale:[+sc.toFixed(2),+sc.toFixed(2),+sc.toFixed(2)],replaces:rep});taken.push([x,z,r]);};
const th=(x,z)=>T.townElevation(x,z,560);
// FROST (town-side summit slopes, snow biome)
const FS=B.FROST_SUMMIT;
for(let k=0,n=0;k<20000&&n<170;k++){const a=R()*6.283,d=40+R()*130,x=FS.x+Math.cos(a)*d,z=FS.z+Math.sin(a)*d;
 if(B.terrainBiome(x,z)!=='snow'||roadD(x,z)<6||Math.hypot(x-B.FROST_PORTAL.x,z-B.FROST_PORTAL.z)<34||B.balthrixCorridorDistance(x,z)<22||Math.abs(x)<B.CITY_HALF+10&&Math.abs(z)<B.CITY_HALF+10)continue;
 const sl=slope(th,x,z);const r=R();let f,rad,sc=.8+R()*.6;
 if(r<.42){f='trees/tree_pine_snow.glb';rad=2.2}else if(r<.6){f=pick(['frost/snow_drift_a.glb','frost/snow_drift_b.glb']);rad=2.5}else if(r<.78){f=pick(['frost/ice_rock.glb','frost/snow_rock.glb']);rad=1.6}else if(r<.92){f='frost/ice_spire.glb';rad=1.5}else{f='frost/frozen_pond.glb';rad=5;if(sl>.12)continue}
 if(sl>.6||!free(x,z,rad))continue;add('frost_town',f,x,z,R()*6.283,sc,'(new) adds detail on the bare frost slopes; merged per 64 m chunk',rad);n++;}
// FROST REALM (frostreach.js local coords, cave floor)
const ex=[[-7,155,40],[-7,177,27],[-37,-66,33],[37,-66,33],[91,18,47]];
for(let k=0,n=0;k<20000&&n<80;k++){const x=(R()*2-1)*190,z=(R()*2-1)*190;if(ex.some(e=>Math.hypot(x-e[0],z-e[1])<e[2]))continue;
 const h=(X,Z)=>F.frostElevation(X+2250,Z);if(h(x,z)>14||slope(h,x,z)>.5)continue;const r=R();const f=r<.35?'frost/ice_spire.glb':r<.7?pick(['frost/snow_drift_a.glb','frost/snow_drift_b.glb']):r<.95?'frost/ice_rock.glb':'frost/frozen_pond.glb';
 if(!free(x+5000,z,2.4))continue;add('frost_realm',f,x,z,R()*6.283,.9+R()*.8,'(new) cave-floor dressing; local to frost-realm group',2.4);taken[taken.length-1][0]+=5000;n++;}
// VOLCANO ring (outside lava pools)
const TC=B.TITAN_CENTER;
for(let k=0,n=0;k<20000&&n<150;k++){const a=R()*6.283,d=30+R()*120,x=TC.x+Math.cos(a)*d,z=TC.z+Math.sin(a)*d;
 if(B.onLava(x,z)||B.LAVA_POOLS.some(p=>Math.hypot(x-p.x,z-p.z)<p.r+5)||roadD(x,z)<6||B.balthrixCorridorDistance(x,z)<22||Math.max(Math.abs(x),Math.abs(z))>540)continue;
 if(slope(th,x,z)>.7)continue;const r=R();let f,rad;
 if(r<.25){f='volcano/basalt_columns.glb';rad=2}else if(r<.5){f=pick(['volcano/lavacrust_rock.glb','volcano/basalt_boulder.glb']);rad=1.6}else if(r<.75){f='volcano/ash_tree.glb';rad=1.5}else if(r<.85){f='volcano/steam_vent.glb';rad=2.5}else{f='clusters/cluster_volcano.glb';rad=7}
 if(!free(x,z,rad))continue;add('volcano',f,x,z,R()*6.283,.85+R()*.6,'(new) volcano ring dressing; replaces nothing, merged per chunk',rad);n++;}
// PORT (walled-harbor local coords; land is x>-26; port building near centre)
const P=[];for(let i=0;i<23;i+=2)for(const z of [-24,24])for(const s of [-1,1])P.push(['port/pier_post.glb',-14-i*1.3,z+s*1.8,0,1,'harbor-wooden-mooring-piers edge posts (new)']);
for(const [x,z] of [[-8,-30],[-10,30],[6,-50],[20,-52],[34,-50],[6,52],[20,50],[48,40],[50,-38]])P.push([pick(['port/crate_stack.glb','props/barrel.glb','port/crate_stack.glb']),x,z,R()*6.283,1,'(new) dock dressing']);
for(const [x,z,ry] of [[-6,-40,0],[-6,40,3.14],[30,57,0],[30,-57,3.14]])P.push(['port/net_rack.glb',x,z,ry,1,'(new) net drying racks']);
for(const [x,z] of [[-16,-36],[-16,36]])P.push(['props/lamp_post.glb',x,z,0,1,'(new) dock lamps, no emissive']);
for(const p of P)out.port.push({file:p[0],position:[p[1],p[0].includes('pier_post')?0.0:null,p[2]],rotation:[0,p[3],0],scale:[p[4],p[4],p[4]],replaces:p[5],frame:'walled-harbor local (PORT_CENTER origin)'});
out.port.push({file:'port/ship_galleon.glb',ship:true,mooring:0,position:[-44,-0.28,-25],rotation:[0,.15,0],scale:[1.27,1.27,1.27],replaces:'harbor-three-mast-sailing-ship (buildSailingShip(1.27,true))'});
out.port.push({file:'port/ship_sloop.glb',ship:true,mooring:1,position:[-49,-0.28,24],rotation:[0,-.14,0],scale:[1,1,1],replaces:'harbor-single-mast-sailing-boat (buildSailingShip(1,false))'});
// HOB CAMPS (world coords, same layout as hobcamps.js)
for(const site of H.HOB_CAMPS){const S=(f,dx,dz,ry,sc,rep)=>out.hobcamps.push({file:f,camp:site.id,position:[+(site.x+dx).toFixed(2),null,+(site.z+dz).toFixed(2)],rotation:[0,+ry.toFixed(3),0],scale:[sc,sc,sc],replaces:rep});
 for(let i=0;i<3;i++){const a=i*2*Math.PI/3+.35;S(i===1?'hobcamp/hob_tent2_red.glb':'hobcamp/hob_tent2.glb',Math.cos(a)*8.2,Math.sin(a)*8.2,-a-Math.PI/2,1.5,'tent cone + door plane');}
 for(let i=0;i<10;i++){if(i===1||i===2)continue;const a=i*2*Math.PI/10;for(const o of [-.22,0,.22]){const aa=a+o;S('hobcamp/hob_palisade.glb',Math.cos(aa)*12.6,Math.sin(aa)*12.6,-aa+Math.PI/2,1.0,'palisade stakes');}}
 S('hobcamp/hob_firepit.glb',0,0,0,1.6,'log ring + ember sphere (MeshBasic glow)');for(let i=0;i<3;i++){const a=i*2*Math.PI/3+.3;S('volcano/lavacrust_rock.glb'.replace('volcano/lavacrust_rock','props/barrel'),Math.cos(a+1)*5.5,Math.sin(a+1)*5.5,a,1,'(new)');}
 S('hobcamp/hob_banner.glb',10,-7,.18,1,'pole + flag');S('hobcamp/hob_totem.glb',Math.cos(.95)*13.5,Math.sin(.95)*13.5-0,0,1.2,'(new) gate totem');S('hobcamp/hob_totem.glb',Math.cos(2.2)*13.5,Math.sin(2.2)*13.5,0,1.2,'(new) gate totem');
 S('hobcamp/hob_rack.glb',-4,5,1.2,1,'(new)');S('props/crate.glb',4.5,-4,0.4,1,'(new)');}
return out;}"""
with sync_playwright() as p:
  b=p.chromium.launch();pg=b.new_page();pg.goto('http://localhost:8765/proto3d/bldview.html?b=inn');pg.wait_for_function('window.__ready',timeout=60000);r=pg.evaluate(JS);b.close()
note={'frost_town':'World coords (town map). y=null -> snap to townElevation(x,z). Merged per 64 m chunk with placeZone().',
 'frost_realm':'LOCAL to frost-realm group (origin FROST_REALM cx=2250,cz=0). y=null -> frostElevation(OX+x,OZ+z).',
 'volcano':'World coords. y=null -> townElevation. Lava pools (+5 m), roads, Balthrix corridor avoided.',
 'port':'LOCAL to walled-harbor group (origin PORT_CENTER). Ships: replace the two buildSailingShip() groups at the same mooring; keep animateMooredShip on the parent.',
 'hobcamps':'World coords; same layout/angles as hobcamps.js (open approach at stakes i=1,2 kept).'}
for z,items in r.items():
  json.dump({'zone':z,'note':note[z],'items':items},open(f'/workspace/beth-world/www/proto3d/models/beth/PLACEMENT_{z}.json','w'),indent=0);print(z,len(items))
