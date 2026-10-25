import * as THREE from 'three';
import {GLTFLoader} from '/proto3d/vendor/jsm/loaders/GLTFLoader.js';
import {buildRun,P} from '/or/gen.js';
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
 mixer=new THREE.AnimationMixer(model);return true;};
window.useClip=(which,timeScale)=>{mixer.stopAllAction();let clip;
 if(which==='old')clip=G.animations.find(c=>c.name==='Running');else{clip=buildRun(model,bones).clip;window.NEWCLIP=clip;}
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
window.getRaw=()=>{const {raw}=buildRun(model,bones);return {...raw,P};};
