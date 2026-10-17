// Varnethryl HUD / world-art config. Swap painted art in here only.
// background.layers: back-to-front parallax layers drawn behind the world entities (the tile ground + trees are skipped
// when at least one layer has loaded). Each layer: {src, speed (0..1 = fraction of the available pan), scale (>=1, cover-fit zoom), y (0..1 vertical anchor)}.
// Example: layers:[{src:'assets/world/sky.webp',speed:.1},{src:'assets/world/mountains.webp',speed:.3},{src:'assets/world/ground.webp',speed:1}]
// Preview with the reference crop: add ?bgdemo=1 to the URL.
export const HUD_CONFIG={
  logo:'assets/hud/wordmark.png',
  background:{layers:[]},
  demoBackground:{layers:[{src:'assets/hud/bg-demo.png',speed:.6,scale:1.08,y:.5}]}
};
