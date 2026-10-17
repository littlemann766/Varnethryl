/* Varnethryl loading + title screens. Phone/Capacitor: tall poster art; web/desktop: wide banner art.
   The art is clean (no baked-in bar/text); the bar, percentage and tip are real HTML driven by real load progress. */
(() => {
  const L=document.getElementById('brandLoader'),T=document.getElementById('brandTitle'),img=document.getElementById('brandLoaderImg'),go=document.getElementById('brandStart');
  if(!L||!T) return;
  const q=new URLSearchParams(location.search), force=q.get('brandlayout');
  const native=!!(window.Capacitor?.isNativePlatform?.());
  const phone=force?force==='tall':(native||(matchMedia('(pointer:coarse)').matches&&Math.min(screen.width,screen.height)<700));
  L.classList.toggle('wide',!phone);
  const art=phone?'assets/brand/poster.webp':'assets/brand/banner.webp';
  const fill=document.getElementById('blFill'),pct=document.getElementById('blPct'),tipEl=document.getElementById('blTip'),bar=L.querySelector('.bl-bar');
  const out=(el,cb)=>{el.classList.add('brandOut');setTimeout(()=>{el.hidden=true;el.style.display='none';cb&&cb()},620)};
  // ---- real progress: art + DOM(5) + hero/sprite assets (80, counted per file) + window load & service worker ready (15)
  const parts={art:0,dom:0,assets:0,ready:0}, W={art:5,dom:5,assets:75,ready:15};
  const target=()=>Object.keys(parts).reduce((s,k)=>s+W[k]*parts[k],0);
  const list=[];for(let i=0;i<20;i++)list.push(`assets/heroes/${i}.webp`,`assets/sprites/${i}.png`);
  let n=0; const bump=()=>{parts.assets=++n/list.length};
  const fetchOne=u=>new Promise(r=>{const i=new Image();i.onload=i.onerror=()=>{bump();r()};i.src=u});
  const pool=async()=>{const q2=list.slice();await Promise.all(Array.from({length:6},async()=>{while(q2.length)await fetchOne(q2.shift())}))};
  L.style.setProperty('--bl-art','url('+art+')');
  img.onload=img.onerror=()=>{parts.art=1}; img.src=art;
  const domDone=()=>{parts.dom=1};
  if(document.readyState!=='loading')domDone(); else document.addEventListener('DOMContentLoaded',domDone);
  pool();
  const swReady=navigator.serviceWorker&&!native?Promise.race([navigator.serviceWorker.ready.catch(()=>0),new Promise(r=>setTimeout(r,2500))]):Promise.resolve();
  const loadP=document.readyState==='complete'?Promise.resolve():new Promise(r=>addEventListener('load',r,{once:true}));
  Promise.all([loadP,swReady]).then(()=>{parts.ready=1});
  // ---- tips: sync tip ONLY when a real sync is happening (game/backend dispatches varn:sync-start / varn:sync-end)
  const tips=['Mix any heroes you like. Crests are lore, not rules.','Party of 3 in the field, 4 against bosses.','Heavy attacks hit harder. Time your super heavy.','Equip relics to push your heroes further.','Your save lives on this device. Export a backup from Settings.'];
  let syncing=false,ti=Math.floor(Math.random()*tips.length),tipTimer;
  const showTip=()=>{tipEl.textContent=syncing?'Your progress is being synced from the cloud.':tips[ti]};
  addEventListener('varn:sync-start',()=>{syncing=true;showTip()}); addEventListener('varn:sync-end',()=>{syncing=false;showTip()});
  showTip(); tipTimer=setInterval(()=>{if(!syncing){ti=(ti+1)%tips.length;showTip()}},2600);
  // ---- smooth display (never jumps backwards, always eases toward real progress; creeps slowly if a source stalls)
  const t0=Date.now(),min=1400; let shown=0,finished=false,last=performance.now();
  const set=v=>{const p=Math.round(v);fill.style.width=v+'%';pct.textContent='Loading... '+p+'%';bar.setAttribute('aria-valuenow',p)};
  const tick=now=>{
    const dt=Math.min(.1,(now-last)/1000); last=now;
    const t=target(), cap=t>=100?100:Math.min(99,Math.max(t,shown)+ (t<95?0:0)); 
    const gap=cap-shown; if(gap>0) shown=Math.min(cap,shown+Math.max(gap*6*dt,gap>0?18*dt*0.2:0));
    if(Date.now()-t0<min) shown=Math.min(shown,((Date.now()-t0)/min)*100);
    set(shown);
    if(shown>=99.5&&!finished){finished=true;set(100);clearInterval(tipTimer);setTimeout(()=>out(L,()=>{T.hidden=false;T.classList.remove('brandOut');T.style.display='';}),260);return}
    if(!finished) requestAnimationFrame(tick);
  };
  if(q.get('brandpct')!==null){ /* test hook: freeze at a given percent */ const v=+q.get('brandpct');set(v);return}
  requestAnimationFrame(tick);
  setTimeout(()=>{parts.art=parts.dom=parts.assets=parts.ready=1},9000); // hard stop: never trap the player on the loader
  const start=()=>out(T); go.addEventListener('click',start);
  addEventListener('keydown',e=>{if(!T.hidden&&(e.key==='Enter'||e.key===' '))start();});
})();
