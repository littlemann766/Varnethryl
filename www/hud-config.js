// Varnethryl HUD / world-art config. Swap painted art in here only.
// background.layers: back-to-front parallax layers drawn behind the world entities (the tile ground + trees are skipped
// when at least one layer has loaded). Each layer: {src, speed (0..1 = fraction of the available pan), scale (>=1, cover-fit zoom), y (0..1 vertical anchor)}.
// Example: layers:[{src:'assets/world/sky.webp',speed:.1},{src:'assets/world/mountains.webp',speed:.3},{src:'assets/world/ground.webp',speed:1}]
// Preview with the reference crop: add ?bgdemo=1 to the URL.
export const HUD_CONFIG={
  logo:'assets/hud/wordmark.png',
  background:{layers:[]},
  // Painted parallax zones (see www/world.js). speed: fraction of pan; focus: initial horizontal anchor (0..1).
  zones:{village:{groundTop:.72,
    layers:[{kind:'sky',src:'assets/world/sky.webp',speed:.05},
            {kind:'far',src:'assets/world/far.webp',speed:.12,focus:.62,top:.0,zoom:1.12,minH:.7,
             shimmer:[[.50,.52,.80],[.60,.58,.82],[.73,.66,.85]]}],
    clumps:[{src:'assets/world/mid-left.webp',x:-.02,h:.5,base:.12,speed:.35},{src:'assets/world/mid-left.webp',x:.98,h:.34,base:.1,speed:.5,flip:true}],
    ground:{src:'assets/world/ground.webp',speed:.9},
    fore:{src:'assets/world/fore.webp',speed:1.4,h:.42},
    props:[
     {src:'assets/world/guildhall.webp',x:300,y:262,w:360,noShadow:true,kind:'building'},
     {src:'assets/world/forge.webp',x:772,y:272,w:290,noShadow:true,kind:'building'},
     {src:'assets/world/market.webp',x:1270,y:272,w:310,noShadow:true,kind:'building'},
     {src:'assets/world/oak.webp',x:70,y:520,w:300},{src:'assets/world/oak.webp',x:1640,y:330,w:330},{src:'assets/world/oak.webp',x:1010,y:860,w:290},
     {src:'assets/world/pine.webp',x:200,y:760,w:120},{src:'assets/world/pine.webp',x:1450,y:640,w:130},{src:'assets/world/pine.webp',x:1760,y:910,w:150},{src:'assets/world/pine.webp',x:560,y:1060,w:130},
     {src:'assets/world/arch.webp',x:960,y:480,w:230},{src:'assets/world/arch.webp',x:1560,y:1010,w:210},
     {src:'assets/world/banner.webp',x:130,y:285,w:70,sway:true},{src:'assets/world/banner.webp',x:520,y:290,w:70,sway:true},{src:'assets/world/banner.webp',x:1580,y:300,w:66,sway:true},
     {src:'assets/world/stones.webp',x:700,y:560,w:150},{src:'assets/world/stones.webp',x:330,y:960,w:170},{src:'assets/world/stones.webp',x:1330,y:760,w:140},
     {src:'assets/world/lupine.webp',x:420,y:640,w:130},{src:'assets/world/lupine.webp',x:880,y:1000,w:120},{src:'assets/world/lupine.webp',x:1190,y:560,w:110},{src:'assets/world/lupine.webp',x:1700,y:700,w:130},{src:'assets/world/lupine.webp',x:90,y:1090,w:140}
    ]}},
  demoBackground:{layers:[{src:'assets/hud/bg-demo.png',speed:.6,scale:1.08,y:.5}]}
};
