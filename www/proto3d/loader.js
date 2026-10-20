/* 7-second medieval startup sequence. Video is optional: it is supplied in
   Varnethryl-Assets.zip and may be installed at assets/brand/varnethryl-loader.mp4.
   If the video is absent or unsupported, the animated Varnethryl crest appears.
   The screen remains until the 3D engine has painted its first frames. */
(function(){
  const box=document.getElementById('load'), video=document.getElementById('vnLoadingFilm');
  const badge=document.getElementById('vnLoadFallback'),label=document.getElementById('loadMsg');
  if(!box)return;
  const begin=performance.now();
  const stages=[
    'Opening the gates of Varnethryl…',
    'Preparing the kingdom…',
    'Loading textures and materials…',
    'Forging terrain and distant mountains…',
    'Awakening the inhabitants…',
    'Preparing character rigs and animations…',
    'Synchronizing combat and skills…',
    'Your adventure awaits…'
  ];
  let engineReady=false,done=false,stage=0,videoReady=false;
  if(video) video.hidden=true; // prevent black video placeholder while media is unavailable
  if(video){
    const fallback=()=>{video.hidden=true;videoReady=false;if(badge)badge.hidden=false;};
    video.addEventListener('error',fallback);
    video.addEventListener('canplay',()=>{
      if(videoReady)return;
      video.play().then(()=>{videoReady=true;video.hidden=false;if(badge)badge.hidden=true;}).catch(fallback);
    });
    if(video.readyState>=3)video.dispatchEvent(new Event('canplay'));
  }
  const tick=setInterval(()=>{
    if(done)return;
    const elapsed=performance.now()-begin;
    stage=Math.min(stages.length-1,Math.floor(elapsed/860));
    if(label)label.textContent=engineReady?'Entering Varnethryl…':stages[stage];
    const progress=document.getElementById('vnLoadProgress');
    if(progress)progress.style.width=(engineReady?100:Math.min(96,Math.max(8,(elapsed/7000)*88))).toFixed(0)+'%';
    // Do not hold a ready player for the full film; startup duration follows the engine.
    if(engineReady)finish();
  },120);
  function finish(){
    if(done)return;done=true;clearInterval(tick);box.style.opacity='0';
    box.style.pointerEvents='none';
    if(video){try{video.pause()}catch(e){}}
    setTimeout(()=>box.remove(),480);
  }
  window.__vnFinishLoading=()=>{engineReady=true;if(label)label.textContent='Entering Varnethryl…';finish();};
  // If loading freezes, the error panel remains accessible; never fake ready.
  addEventListener('error',()=>{if(label&&!engineReady)label.textContent='The kingdom is still loading. Check 3D status if it does not open.';});
})();