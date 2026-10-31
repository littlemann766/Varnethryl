// Painted in-world sprites: loads the cut-out art once and bakes lit variants (right-facing + mirrored) with a subtle rim light
// matching the scene (warm sun from the upper right, cool bounce from the ground) so they sit inside the painted backdrop.
// Heroes: assets/sprites/N.png (186x250, feet at bottom).  Enemies: assets/enemies/<slug>.png + manifest.json (256x256).
const cache=new Map();
const slug=n=>String(n).toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'');
function bake(img,w,h,{rim='255,214,150',dir=1,strength=1,flip=false,white=false}={}){
 const c=document.createElement('canvas');c.width=w;c.height=h;const x=c.getContext('2d');
 x.imageSmoothingEnabled=true;x.imageSmoothingQuality='high';
 // stepwise downscale keeps the painted detail crisp
 let src=img;while(src.width/2>w){const t=document.createElement('canvas');t.width=Math.ceil(src.width/2);t.height=Math.ceil(src.height/2);const tx=t.getContext('2d');tx.imageSmoothingQuality='high';tx.drawImage(src,0,0,t.width,t.height);src=t}
 x.save();if(flip){x.translate(w,0);x.scale(-1,1)}x.drawImage(src,0,0,w,h);x.restore();
 if(white){x.globalCompositeOperation='source-in';x.fillStyle='#fff';x.fillRect(0,0,w,h);return c}
 // ambient grade: warm top, cool/dark toward the feet (ground occlusion)
 x.globalCompositeOperation='source-atop';
 let g=x.createLinearGradient(0,0,0,h);g.addColorStop(0,`rgba(255,226,170,${.07*strength})`);g.addColorStop(.55,'rgba(0,0,0,0)');g.addColorStop(1,`rgba(8,16,12,${.22*strength})`);x.fillStyle=g;x.fillRect(0,0,w,h);
 // rim light: alpha minus alpha shifted away from the light, tinted, blurred a touch; on the lit (right) side regardless of mirror
 const sh=Math.max(1.5,w/62),m=document.createElement('canvas');m.width=w;m.height=h;const mx=m.getContext('2d');
 mx.drawImage(c,0,0);mx.globalCompositeOperation='destination-out';mx.drawImage(c,-dir*sh,sh*.6);
 mx.globalCompositeOperation='source-in';mx.fillStyle=`rgba(${rim},${.85*strength})`;mx.fillRect(0,0,w,h);
 const b=document.createElement('canvas');b.width=w;b.height=h;const bx=b.getContext('2d');bx.filter=`blur(${Math.max(.5,w/150)}px)`;bx.drawImage(m,0,0);
 x.globalCompositeOperation='source-atop';x.drawImage(b,0,0);x.globalAlpha=.5;x.drawImage(m,0,0);x.globalAlpha=1;x.globalCompositeOperation='source-over';
 return c}
function entry(key,url,w,h,opt){let e=cache.get(key);if(e)return e;e={ready:false,r:null,l:null,wl:null};cache.set(key,e);
 const img=new Image();img.decoding='async';img.onload=()=>{e.r=bake(img,w,h,opt);e.l=bake(img,w,h,{...opt,flip:true});e.wr=null;e.img=img;e.w=w;e.h=h;e.opt=opt;e.ready=true};img.onerror=()=>{e.failed=true};img.src=url;return e}
// ---- heroes: draw rect in world units is 52x70; bake at 2x for dpr2 screens
export function hero(id){return entry('h'+id,`assets/sprites/${id}.png`,104,140,{strength:1})}
// ---- enemies
let manifest=null,mfLoading=false;
function loadManifest(){if(manifest||mfLoading)return;mfLoading=true;fetch('assets/enemies/manifest.json').then(r=>r.ok?r.json():{}).then(j=>{manifest=j}).catch(()=>{manifest={}})}
export function enemy(name){loadManifest();if(!manifest)return null;let s=slug(name).replace(/^(standard|veteran|elite|mythic)-/,'').replace(/^the-/,''),m=manifest[s];if(!m)return null;
 const e=entry('e'+s,`assets/enemies/${m.file}`,m.height>90?192:128,m.height>90?192:128,{rim:'190,215,255',strength:.9});e.height=m.height;e.faces=m.faces||'right';return e}
// white silhouette for hit flash (lazy)
export function flash(e,left){if(!e.ready)return null;const k=left?'fl':'fr';if(!e[k])e[k]=bake(e.img,e.w,e.h,{flip:left,white:true});return e[k]}
// class-coloured silhouette aura (cast charge-up); cached per colour
export function aura(e,left,col){const k='au'+(left?'l':'r')+col;if(!e[k]){const w=e.w,h=e.h,c=document.createElement('canvas');c.width=w;c.height=h;const x=c.getContext('2d');x.filter=`blur(${Math.max(2,w/22)}px)`;x.drawImage(left?e.l:e.r,0,0);x.filter='none';x.globalCompositeOperation='source-in';x.fillStyle=col;x.fillRect(0,0,w,h);e[k]=c}return e[k]}
export const variant=(e,left)=>left?e.l:e.r;
export function preload(ids,enemyNames){ids.forEach(hero);(enemyNames||[]).forEach(enemy)}
