import * as THREE from 'three';
import {GLTFLoader} from '/proto3d/vendor/jsm/loaders/GLTFLoader.js';
import {buildRun,P,PW} from '/or/gen.js';
window.P=P;
let R,scene,model,mixer,act,ground,cams,bones,G,gtex;
window.setup=async(url)=>{
 R=new THREE.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});R.setSize(1280,540);R.setPixelRatio(1);document.body.appendChild(R.domElement);R.setScissorTest(true);
 scene=new THREE.Scene();scene.background=new THREE.Color(0x8fb4d8);scene.add(new THREE.HemisphereLight(0xffffff,0x556644,1.6));const dl=new THREE.DirectionalLight(0xffffff,2.2);dl.position.set(3,6,4);scene.add(dl);
 const c=document.createElement('canvas');c.width=c.height=256;const x=c.getContext('2d');for(let i=0;i<8;i++)for(let j=0;j<8;j++){x.fillStyle=(i+j)%2?'#6d8a4e':'#88a862';x.fillRect(i*32,j*32,32,32);}x.fillStyle='#fff';x.fillRect(0,0,256,3);
 gtex=new THREE.CanvasTexture(c);gtex.wrapS=gtex.wrapT=THREE.RepeatWrapping;gtex.repeat.set(20,20);gtex.colorSpace=THREE.SRGBColorSpace;
 ground=new THREE.Mesh(new THREE.PlaneGeometry(40,40),new THREE.MeshLambertMaterial({map:gtex}));ground.rotation.x=-Math.PI/2;scene.add(ground); // 2 m tiles (40/20)
 G=await new GLTFLoader().loadAsync(url);model=G.scene;scene.add(model);bones={};model.traverse(o=>{if(o.isBone)bones[o.name]=o;if(o.isMesh)o.frustumCulled=false;});
 const side=new THREE.PerspectiveCamera(30,640/540,.1,100);side.position.set(5.2,1.0,0.1);side.lookAt(0,0.85,0.1);
 const tq=new THREE.PerspectiveCamera(30,640/540,.1,100);tq.position.set(3.4,1.6,3.6);tq.lookAt(0,0.8,0);cams=[side,tq];
 mixer=new THREE.AnimationMixer(model);initHeel();return true;};
window.useClip=(which,timeScale)=>{mixer.stopAllAction();let clip;
 if(which==='old')clip=G.animations.find(c=>c.name==='Running');else if(which==='oldwalk'||which==='walkclip')clip=G.animations.find(c=>c.name==='Walking');else if(which==='newwalk'){clip=buildRun(model,bones,PW).clip;}else{clip=buildRun(model,bones).clip;window.NEWCLIP=clip;}
 act=mixer.clipAction(clip);act.reset().play();act.timeScale=timeScale;return clip.duration;};
window.frame=(t,v)=>{mixer.setTime(t);act.time=(t*act.timeScale)%act.getClip().duration;mixer.update(0);
 gtex.offset.y=(v*t/2)%1; // ground scrolls backward at v (texture repeat 2 m)
 for(let i=0;i<2;i++){R.setViewport(i*640,0,640,540);R.setScissor(i*640,0,640,540);R.render(scene,cams[i]);}
 return R.domElement.toDataURL('image/jpeg',0.92);};
// foot-slide: world toe z velocity during ground contact (body moving +v)
window.measure=(v,dur)=>{const out={};const N=400;for(const s of ['Left','Right']){let rows=[];for(let i=0;i<=N;i++){const t=dur*i/N;mixer.setTime(0);act.time=t;mixer.update(0);model.updateMatrixWorld(true);const p=bones['mixamorig'+s+'ToeBase'].getWorldPosition(new THREE.Vector3());rows.push([t,p.y,p.z+v*t/act.timeScale*act.timeScale]);} out[s]=rows;}return out;};
window.ready=true;
window.frameNoRender=(t)=>{act.time=(t*act.timeScale)%act.getClip().duration;mixer.update(0);model.updateMatrixWorld(true);};
window.toe=(s)=>bones['mixamorig'+s+'ToeBase'].getWorldPosition(new THREE.Vector3()).toArray();
window.toeB=(n)=>bones['mixamorig'+n].getWorldPosition(new THREE.Vector3()).toArray();
window.getRaw=(w)=>{const {raw}=buildRun(model,bones,w?PW:P);return {...raw,P:w?PW:P};};
window.heel=(s)=>{const f=bones['mixamorig'+s+'Foot'];if(!window.HL)window.HL={};if(!HL[s]){model.updateMatrixWorld(true);}return null};
// heel contact point: bind ankle + (0,-0.105,-0.06) expressed in foot-bone local space (computed at bind, before any clip)
window.initHeel=()=>{window.HL={};model.updateMatrixWorld(true);for(const s of ['Left','Right']){const f=bones['mixamorig'+s+'Foot'];const w=f.getWorldPosition(new THREE.Vector3()).add(new THREE.Vector3(0,-0.105,-0.06));HL[s]=f.worldToLocal(w.clone());}};
window.contact=(s)=>{const h=bones['mixamorig'+s+'Foot'].localToWorld(HL[s].clone());const t=bones['mixamorig'+s+'ToeBase'].getWorldPosition(new THREE.Vector3());return h.y<t.y?h.toArray():t.toArray();};
// game-faithful sequence: walk-mode speed for 2.5 s, then run toggled; speed smoothed like locoAnim (alpha 11/s)
let SQ=null;
window.seqInit=(mode)=>{mixer.stopAllAction();const W=mixer.clipAction(G.animations.find(c=>c.name==='Walking')),Rn=mixer.clipAction(G.animations.find(c=>c.name==='Running'));W.reset().play();Rn.reset().play();
 SQ={mode,W,Rn,v:mode==='old'?3.04:2.0,ph:0,tW:0,tR:0,dist:0};return true;};
window.seqFrame=(t,dt)=>{const s=SQ,old=s.mode==='old';const target=t<2.5?(old?3.04:2.0):6.08;s.v+=(target-s.v)*(1-Math.exp(-dt*11));const v=s.v;s.dist+=v*dt;
 const Sw=old?1.486:2.0,Sr=old?2.28:(window.SR||6.08),cl=x=>Math.max(.5,Math.min(2.4,x));const m=Math.max(0,Math.min(1,(v-Sw)/(Sr-Sw)));
 s.W.setEffectiveWeight(1-m);s.Rn.setEffectiveWeight(m);const tw=cl(v/Sw),tr=cl(v/Sr);
 if(old){s.tW+=dt*tw;s.tR+=dt*tr;s.W.time=s.tW%s.W.getClip().duration;s.Rn.time=s.tR%s.Rn.getClip().duration;}
 else{s.ph=(s.ph+dt*((1-m)*tw/s.W.getClip().duration+m*tr/s.Rn.getClip().duration))%1;s.W.time=s.ph*s.W.getClip().duration;s.Rn.time=s.ph*s.Rn.getClip().duration;}
 s.W.timeScale=0;s.Rn.timeScale=0;mixer.update(0);gtex.offset.y=(s.dist/2)%1;
 for(let i=0;i<2;i++){R.setViewport(i*640,0,640,540);R.setScissor(i*640,0,640,540);R.render(scene,cams[i]);}
 return [R.domElement.toDataURL('image/jpeg',0.92),+v.toFixed(2),+m.toFixed(2)];};
// resample the ORIGINAL Running clip so phase 0 = left toe touchdown (matches the walk clip for phase-synced blending)
window.shiftedOldRun=()=>{const c=G.animations.find(c=>c.name==='Running'),D=c.duration;mixer.stopAllAction();const a=mixer.clipAction(c);a.reset().play();
 const N=200,ys=[];for(let i=0;i<N;i++){a.time=D*i/N;mixer.update(0);model.updateMatrixWorld(true);ys.push(bones.mixamorigLeftToeBase.getWorldPosition(new THREE.Vector3()).y);}
 const ymin=Math.min(...ys);let td=0;for(let i=0;i<N;i++){const p=(i-1+N)%N;if(ys[i]<ymin+0.012&&ys[p]>=ymin+0.012){td=i/N;break;}}
 const F=41,times=[],hipsPos=[],tracks={};const names=Object.keys(bones);names.forEach(n=>tracks[n]=[]);
 for(let f=0;f<F;f++){const t=f/(F-1)*D;times.push(t);a.time=((t/D+td)%1)*D;mixer.update(0);names.forEach(n=>tracks[n].push(...bones[n].quaternion.toArray()));hipsPos.push(...bones.mixamorigHips.position.toArray());}
 a.stop();return {times,hipsPos,tracks,td,P:{v:0,T:D}};};
