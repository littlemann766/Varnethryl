import * as THREE from '../../www/proto3d/vendor/three.module.js';
import { GLTFLoader } from '../../www/proto3d/vendor/jsm/loaders/GLTFLoader.js';
const ORDER = ['aldric','darius','selene','seraphine','talia','finn','brynn','mirelle','nyx','vesper','thorne','orin','elira'];
const LABEL = {aldric:'Sir Aldric',darius:'Darius Umbral',selene:'Selene Frostveil',seraphine:'Dame Seraphine',talia:'Talia Stormcall',finn:'Finn Valecourt',brynn:'Brynn Cogwright',mirelle:'Mirelle Thornroot',nyx:'Nyx Varrin',vesper:'Vesper Crowe',thorne:'Brother Thorne',orin:'Orin Ashlance', elira: 'Lady Elira'};
const qs = new URLSearchParams(location.search);
const R = new THREE.WebGLRenderer({antialias:true, preserveDrawingBuffer:true});
R.setPixelRatio(Math.min(devicePixelRatio,2)); R.setSize(innerWidth,innerHeight);
R.shadowMap.enabled = true; R.toneMapping = THREE.ACESFilmicToneMapping; R.outputColorSpace = THREE.SRGBColorSpace;
document.body.appendChild(R.domElement);
const scene = new THREE.Scene(); scene.background = new THREE.Color(0x2b2733); scene.fog = new THREE.Fog(0x2b2733,7,16);
const cam = new THREE.PerspectiveCamera(32, innerWidth/innerHeight, .1, 50);
scene.add(new THREE.HemisphereLight(0xffffff,0x6a5a55,2.2));
const key = new THREE.DirectionalLight(0xfff0d8,2.6); key.position.set(2.5,4,3); key.castShadow = true; key.shadow.mapSize.set(2048,2048); key.shadow.bias=-0.0008; key.shadow.normalBias=0.03;
Object.assign(key.shadow.camera,{left:-2,right:2,top:3,bottom:-1,near:.5,far:12}); scene.add(key);
const rim = new THREE.DirectionalLight(0xfff4e8,2.2); rim.position.set(-3,3,-4); scene.add(rim);
const fill = new THREE.DirectionalLight(0xffffff,1.2); fill.position.set(-3,1.5,3); scene.add(fill);
const floor = new THREE.Mesh(new THREE.CircleGeometry(1.1,40), new THREE.MeshStandardMaterial({color:0x3a3340,roughness:1}));
floor.rotation.x = -Math.PI/2; floor.receiveShadow = true; scene.add(floor);
const loader = new GLTFLoader(); const cache = {};
const state = {id: qs.get('c')||'aldric', anim: qs.get('anim')||'idle', yaw:+(qs.get('yaw')||0), pitch:.25, spin: qs.get('spin')!=='0', dist:6.4};
let cur, mixer, clips = []; const clock = new THREE.Clock();
function b64(s){const bin=atob(s);const u=new Uint8Array(bin.length);for(let i=0;i<bin.length;i++)u[i]=bin.charCodeAt(i);return u.buffer;}
function parse(id){ if(cache[id]) return cache[id]; return cache[id]=new Promise((res,rej)=>loader.parse(b64(window.__MODELS[id]),'',res,rej)); }
const bar = document.getElementById('heroes'), ctl = document.getElementById('ctl'), status = document.getElementById('status');
function mark(){ document.querySelectorAll('button').forEach(b=>b.classList.toggle('on', b.dataset.k===state.id||b.dataset.k===state.anim||(b.dataset.k==='spin'&&state.spin))); }
async function load(id){
  status.textContent='Loading '+LABEL[id]+'…';
  const g = await parse(id);
  if(cur) scene.remove(cur);
  // fresh instance each time so skeleton state is clean
  const THREEclone = (await import_clone())(g.scene);
  cur = THREEclone; cur.traverse(o=>{if(o.isMesh){o.castShadow=true;o.frustumCulled=false;}}); scene.add(cur); { const bb=new THREE.Box3().setFromObject(cur); state.h=Math.max(1.9,bb.max.y); }
  clips = g.animations; mixer = new THREE.AnimationMixer(cur); state.id=id; play(state.anim);
  status.textContent=LABEL[id]; mark();
}
import { clone as skClone } from '../../www/proto3d/vendor/jsm/utils/SkeletonUtils.js';
function import_clone(){return Promise.resolve(skClone);}
function play(n){ state.anim=n; if(!mixer)return; mixer.stopAllAction(); const cl=clips.find(c=>c.name===n); if(cl) mixer.clipAction(cl).play(); if(qs.get('tt')) mixer.setTime(+qs.get('tt')); mark(); }
for(const id of ORDER){const b=document.createElement('button');b.textContent=LABEL[id];b.dataset.k=id;b.onclick=()=>load(id);bar.appendChild(b);}
for(const a of ['idle','walk']){const b=document.createElement('button');b.textContent='▶ '+a;b.dataset.k=a;b.onclick=()=>play(a);ctl.appendChild(b);}
const sp=document.createElement('button');sp.textContent='⟳ Spin';sp.dataset.k='spin';sp.onclick=()=>{state.spin=!state.spin;mark();};ctl.appendChild(sp);
// pointer: 1 pointer = orbit, 2 = pinch
const ptrs=new Map(); let pd=0;
const cv=R.domElement; cv.style.touchAction='none';
cv.addEventListener('pointerdown',e=>{cv.setPointerCapture(e.pointerId);ptrs.set(e.pointerId,{x:e.clientX,y:e.clientY});state.spin=false;pd=0;mark();});
cv.addEventListener('pointermove',e=>{const p=ptrs.get(e.pointerId);if(!p)return;
  if(ptrs.size===1){state.yaw-=(e.clientX-p.x)*.01;state.pitch=Math.max(-.2,Math.min(1.1,state.pitch+(e.clientY-p.y)*.006));p.x=e.clientX;p.y=e.clientY;}
  else{p.x=e.clientX;p.y=e.clientY;const [a,b]=[...ptrs.values()];const d=Math.hypot(a.x-b.x,a.y-b.y);if(pd)state.dist=Math.max(2,Math.min(11,state.dist*pd/d));pd=d;}});
const up=e=>{ptrs.delete(e.pointerId);pd=0;}; cv.addEventListener('pointerup',up);cv.addEventListener('pointercancel',up);
cv.addEventListener('wheel',e=>{e.preventDefault();state.dist=Math.max(2,Math.min(11,state.dist*(1+e.deltaY*.0015)));},{passive:false});
addEventListener('resize',()=>{R.setSize(innerWidth,innerHeight);cam.aspect=innerWidth/innerHeight;cam.updateProjectionMatrix();});
function frame(){const dt=clock.getDelta(); if(mixer)mixer.update(qs.get('t')?0:dt); if(state.spin)state.yaw+=dt*.6;
  const fit=Math.max(1,(state.h||1.9)/1.75),d=fit*state.dist*(cam.aspect<1?Math.min(1.7,.95/Math.max(.5,cam.aspect)):1),p=state.pitch; cam.position.set(Math.sin(state.yaw)*Math.cos(p)*d,1.05+Math.sin(p)*d,Math.cos(state.yaw)*Math.cos(p)*d); cam.lookAt(0,(1.05+(cam.aspect<1?.35:0))*Math.max(1,fit*.95),0); R.render(scene,cam); requestAnimationFrame(frame);}
window.__state=state; window.__load=load; window.__play=play;
window.__ready=load(state.id).then(frame).catch(e=>{status.textContent='Error: '+e;});
