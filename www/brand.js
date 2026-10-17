/* Varnethryl loading + title screens. Phone app/phones: poster; web/desktop: banner. */
(() => {
  const L=document.getElementById('brandLoader'),T=document.getElementById('brandTitle'),img=document.getElementById('brandLoaderImg'),go=document.getElementById('brandStart');
  if(!L||!T) return;
  const native=!!(window.Capacitor?.isNativePlatform?.());
  const phone=native||(matchMedia('(pointer:coarse)').matches&&Math.min(screen.width,screen.height)<700);
  const wide=!phone; L.classList.toggle('wide',wide);
  img.src=wide?'assets/brand/banner.webp':'assets/brand/poster.webp';
  const out=(el,cb)=>{el.classList.add('brandOut');setTimeout(()=>{el.hidden=true;el.style.display='none';cb&&cb()},620)};
  const t0=Date.now(), min=1400;
  let done=false; const finish=()=>{ if(done)return; done=true; setTimeout(()=>out(L,()=>{T.hidden=false;T.classList.remove('brandOut');T.style.display='';}),Math.max(0,min-(Date.now()-t0))); };
  if(document.readyState==='complete') finish(); else addEventListener('load',finish);
  setTimeout(finish,6000);
  const start=()=>out(T); go.addEventListener('click',start);
  addEventListener('keydown',e=>{if(!T.hidden&&(e.key==='Enter'||e.key===' '))start();});
})();
