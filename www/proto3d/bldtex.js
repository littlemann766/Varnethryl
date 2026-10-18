// Varnethryl 3D buildings: procedural canvas textures (stone, slate, half-timber, floors, banners...). All generated in code;
// the lion crest is the one cut from the boss's sheet (tex/emb_lion.png). Textures tile per TILE metres (see buildings.js uv scaling).
import * as THREE from 'three';
let seed = 11; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
const mk = s => { const c = document.createElement('canvas'); c.width = c.height = s; return c; };
const T = (cv, rep) => { const t = new THREE.CanvasTexture(cv); t.colorSpace = THREE.SRGBColorSpace; t.wrapS = t.wrapT = THREE.RepeatWrapping; t.anisotropy = 4; return t; };
const hsl = (h, s, l) => `hsl(${h},${s}%,${l}%)`;
const noise = (g, S, n, a = .12) => { for (let i = 0; i < n; i++) { g.fillStyle = `rgba(${rnd() < .5 ? 0 : 255},${rnd() < .5 ? 0 : 255},${rnd() < .5 ? 0 : 255},${rnd() * a})`; g.fillRect(rnd() * S, rnd() * S, 1 + rnd() * 3, 1 + rnd() * 3); } };
function stoneBlocks(g, S, rows, hue, sat, lum, mortar = '#4a4a4e') {
  g.fillStyle = mortar; g.fillRect(0, 0, S, S); const rh = S / rows;
  for (let r = 0; r < rows; r++) { let x = -(rnd() * 20); const cols = 3 + (r % 2); const cw = S / cols;
    for (let c = -1; c <= cols; c++) { const off = (r % 2) * cw / 2; const w = cw - 3, l = lum + (rnd() - .5) * 14; g.fillStyle = hsl(hue + (rnd() - .5) * 8, sat, l); g.fillRect(c * cw + off + 1.5, r * rh + 1.5, w, rh - 3);
      g.fillStyle = 'rgba(255,255,255,.07)'; g.fillRect(c * cw + off + 1.5, r * rh + 1.5, w, 2); g.fillStyle = 'rgba(0,0,0,.12)'; g.fillRect(c * cw + off + 1.5, r * rh + rh - 3.5, w, 2); } }
  noise(g, S, 900, .1);
}
const makers = {
  stone(g, S) { stoneBlocks(g, S, 6, 38, 7, 50, '#3c3a38'); for (let i = 0; i < 14; i++) { g.fillStyle = `rgba(70,100,50,${.06 + rnd() * .1})`; g.fillRect(rnd() * S, S * .7 + rnd() * S * .3, 12 + rnd() * 30, 5 + rnd() * 12); } },
  stoneD(g, S) { stoneBlocks(g, S, 6, 30, 6, 34, '#232224'); },
  stoneL(g, S) { stoneBlocks(g, S, 5, 38, 20, 76, '#a39a86'); },       // pale limestone (town hall, temple, library)
  rock(g, S) { g.fillStyle = '#585e58'; g.fillRect(0, 0, S, S); for (let i = 0; i < 70; i++) { g.fillStyle = hsl(100 + rnd() * 40, 10 + rnd() * 18, 22 + rnd() * 20); g.beginPath(); g.ellipse(rnd() * S, rnd() * S, 8 + rnd() * 26, 6 + rnd() * 18, rnd() * 3, 0, 7); g.fill(); } noise(g, S, 800, .12); },
  plaster(g, S) { g.fillStyle = '#e4d6b4'; g.fillRect(0, 0, S, S); noise(g, S, 1400, .07); for (let i = 0; i < 20; i++) { g.fillStyle = `rgba(120,100,70,${rnd() * .06})`; g.fillRect(rnd() * S, rnd() * S, 20 + rnd() * 40, 10 + rnd() * 20); } },
  timber(g, S) { // half-timber panel (1 tile = 2m x 2m): plaster with oak frame + cross brace
    makers.plaster(g, S); g.fillStyle = '#4a3220'; const b = S * .06;
    g.fillRect(0, 0, S, b); g.fillRect(0, S - b, S, b); g.fillRect(0, 0, b, S); g.fillRect(S - b, 0, b, S); g.fillRect(S / 2 - b / 2, 0, b, S);
    g.lineWidth = b * .8; g.strokeStyle = '#4a3220'; g.beginPath(); g.moveTo(b, S - b); g.lineTo(S / 2 - b / 2, b); g.stroke();
    for (let i = 0; i < 160; i++) { g.fillStyle = `rgba(20,10,0,${rnd() * .25})`; g.fillRect(rnd() * S, rnd() * S, 1, 4 + rnd() * 10); } },
  darkWood(g, S) { g.fillStyle = '#2b1f14'; g.fillRect(0, 0, S, S); for (let x = 0; x < S; x += S / 8) { g.fillStyle = hsl(24, 30, 12 + rnd() * 10); g.fillRect(x + 1, 0, S / 8 - 2, S); for (let i = 0; i < 20; i++) { g.fillStyle = `rgba(0,0,0,${rnd() * .3})`; g.fillRect(x + rnd() * S / 8, rnd() * S, 1, 6 + rnd() * 20); } } noise(g, S, 400, .08); },
  wood(g, S) { g.fillStyle = '#6b4a2b'; g.fillRect(0, 0, S, S); for (let y = 0; y < S; y += S / 8) { g.fillStyle = hsl(28, 38, 28 + rnd() * 12); g.fillRect(0, y + 1, S, S / 8 - 2); for (let i = 0; i < 14; i++) { g.fillStyle = `rgba(0,0,0,${rnd() * .22})`; g.fillRect(rnd() * S, y + rnd() * S / 8, 10 + rnd() * 30, 1); } } },
  slate(g, S) { g.fillStyle = '#141c2a'; g.fillRect(0, 0, S, S); const rows = 10, rh = S / rows; for (let r = 0; r < rows; r++) for (let c = -1; c < 9; c++) { const x = c * S / 8 + (r % 2) * S / 16, l = 22 + rnd() * 13; g.fillStyle = hsl(214 + (rnd() - .5) * 10, 20 + rnd() * 12, l); g.beginPath(); g.roundRect(x + 1, r * rh + 1, S / 8 - 2, rh + 4, [0, 0, 5, 5]); g.fill(); g.fillStyle = 'rgba(190,210,255,.10)'; g.fillRect(x + 2, r * rh + 2, S / 8 - 4, 2); g.fillStyle = 'rgba(0,0,0,.45)'; g.fillRect(x + 1, r * rh + rh + 1, S / 8 - 2, 3); if (rnd() < .05) { g.fillStyle = 'rgba(80,120,60,.35)'; g.fillRect(x + 3, r * rh + 4, 12, 6); } } noise(g, S, 700, .08); },
  slateG(g, S) { makers.slate(g, S); g.globalCompositeOperation = 'saturation'; g.fillStyle = '#777'; g.fillRect(0, 0, S, S); g.globalCompositeOperation = 'source-over'; },
  hay(g, S) { g.fillStyle = '#c9a85a'; g.fillRect(0, 0, S, S); for (let i = 0; i < 900; i++) { g.strokeStyle = `hsl(${40 + rnd() * 10},${50 + rnd() * 20}%,${40 + rnd() * 30}%)`; g.beginPath(); const x = rnd() * S, y = rnd() * S; g.moveTo(x, y); g.lineTo(x + rnd() * 14 - 7, y + 10 + rnd() * 8); g.stroke(); } },
  floorPlank(g, S) { g.fillStyle = '#4a3220'; g.fillRect(0, 0, S, S); for (let i = 0; i < 8; i++) { g.fillStyle = hsl(28, 35 + (i % 3) * 5, 30 + rnd() * 14); g.fillRect(0, i * S / 8 + 1, S, S / 8 - 2); for (let j = 0; j < 8; j++) { g.fillStyle = `rgba(0,0,0,${rnd() * .2})`; g.fillRect(rnd() * S, i * S / 8 + 2 + rnd() * 10, 8 + rnd() * 30, 1); } } },
  floorStone(g, S) { stoneBlocks(g, S, 4, 215, 4, 42, '#22232a'); },
  floorTile(g, S) { const n = 4, c = S / n; for (let y = 0; y < n; y++) for (let x = 0; x < n; x++) { g.fillStyle = (x + y) % 2 ? '#d9cfae' : '#2e4a82'; g.fillRect(x * c, y * c, c, c); } noise(g, S, 500, .1); g.strokeStyle = '#0003'; g.strokeRect(0, 0, S, S); },
  sand(g, S) { g.fillStyle = '#d4b878'; g.fillRect(0, 0, S, S); noise(g, S, 2400, .16); g.strokeStyle = 'rgba(150,110,50,.25)'; for (let i = 0; i < 40; i++) { g.beginPath(); g.arc(S / 2, S / 2, 8 + i * 5, 0, 7); g.stroke(); } },
  cobble(g, S) { g.fillStyle = '#6e675d'; g.fillRect(0, 0, S, S); for (let y = 0; y < 8; y++) for (let x = 0; x < 8; x++) { g.fillStyle = hsl(35, 8, 44 + rnd() * 18); g.beginPath(); g.roundRect(x * 32 + (y % 2) * 16 + 1, y * 32 + 1, 29, 29, 6); g.fill(); } },
  pave(g, S) { g.fillStyle = '#8a8478'; g.fillRect(0, 0, S, S); for (let y = 0; y < 4; y++) for (let x = 0; x < 4; x++) { g.fillStyle = hsl(40, 8, 66 + rnd() * 10); g.fillRect(x * 64 + 2, y * 64 + 2, 60, 60); } noise(g, S, 600, .08); },
  carpet(g, S) { g.fillStyle = '#1f3d7a'; g.fillRect(0, 0, S, S); g.fillStyle = '#c9a240'; g.fillRect(S * .08, 0, S * .04, S); g.fillRect(S * .88, 0, S * .04, S); g.fillStyle = '#e0bd5a'; for (let y = 0; y < S; y += 32) { g.beginPath(); g.moveTo(S / 2, y + 4); g.lineTo(S / 2 + 12, y + 16); g.lineTo(S / 2, y + 28); g.lineTo(S / 2 - 12, y + 16); g.fill(); } noise(g, S, 500, .08); },
  rug(g, S) { g.fillStyle = '#7a2a2a'; g.fillRect(0, 0, S, S); g.strokeStyle = '#d0a040'; g.lineWidth = 6; g.strokeRect(10, 10, S - 20, S - 20); g.strokeStyle = '#e8d8a8'; g.lineWidth = 2; g.strokeRect(22, 22, S - 44, S - 44); g.fillStyle = '#2a4a8a'; g.beginPath(); g.moveTo(S / 2, 40); g.lineTo(S - 40, S / 2); g.lineTo(S / 2, S - 40); g.lineTo(40, S / 2); g.fill(); noise(g, S, 600, .08); },
  sigil(g, S) { // blue ritual / arcane floor circle
    g.fillStyle = '#10182c'; g.fillRect(0, 0, S, S); g.strokeStyle = '#4fa0ff'; g.shadowColor = '#4fa0ff'; g.shadowBlur = 6; g.lineWidth = 3;
    for (const r of [.46, .4, .26]) { g.beginPath(); g.arc(S / 2, S / 2, S * r, 0, 7); g.stroke(); }
    g.lineWidth = 2; for (let i = 0; i < 8; i++) { const a = i / 8 * 6.283; g.beginPath(); g.moveTo(S / 2 + Math.cos(a) * S * .26, S / 2 + Math.sin(a) * S * .26); g.lineTo(S / 2 + Math.cos(a + 2.4) * S * .4, S / 2 + Math.sin(a + 2.4) * S * .4); g.stroke(); }
    g.strokeStyle = '#d4af37'; g.shadowColor = '#d4af37'; g.beginPath(); g.arc(S / 2, S / 2, S * .12, 0, 7); g.stroke(); g.shadowBlur = 0; },
  marbleInlay(g, S) { g.fillStyle = '#d8d2c0'; g.fillRect(0, 0, S, S); g.strokeStyle = '#1f3a7a'; g.lineWidth = 8; g.strokeRect(6, 6, S - 12, S - 12); g.strokeStyle = '#c9a240'; g.lineWidth = 3; g.strokeRect(20, 20, S - 40, S - 40); noise(g, S, 600, .08); },
  awning(g, S) { for (let i = 0; i < 8; i++) { g.fillStyle = i % 2 ? '#f2ead0' : '#2a4fa0'; g.fillRect(i * S / 8, 0, S / 8, S); } noise(g, S, 300, .06); },
  glass(g, S) { g.fillStyle = '#ffd98a'; g.fillRect(0, 0, S, S); const gr = g.createLinearGradient(0, 0, 0, S); gr.addColorStop(0, 'rgba(255,170,60,.0)'); gr.addColorStop(1, 'rgba(160,80,10,.45)'); g.fillStyle = gr; g.fillRect(0, 0, S, S); g.strokeStyle = '#2a1c10'; g.lineWidth = 10; g.strokeRect(0, 0, S, S); g.lineWidth = 5; g.beginPath(); g.moveTo(S / 2, 0); g.lineTo(S / 2, S); g.moveTo(0, S / 2); g.lineTo(S, S / 2); g.stroke(); },
  stained(g, S) { g.fillStyle = '#16306e'; g.fillRect(0, 0, S, S); const cols = ['#2a5ac8', '#3a78e8', '#c9a240', '#1a3a90', '#6aa0ff']; for (let i = 0; i < 40; i++) { g.fillStyle = cols[i % 5]; g.beginPath(); g.moveTo(rnd() * S, rnd() * S); g.lineTo(rnd() * S, rnd() * S); g.lineTo(rnd() * S, rnd() * S); g.fill(); } g.strokeStyle = '#d8b850'; g.lineWidth = 6; g.beginPath(); g.arc(S / 2, S * .38, S * .2, 0, 7); g.moveTo(S / 2, S * .1); g.lineTo(S / 2, S); g.stroke(); g.lineWidth = 8; g.strokeRect(0, 0, S, S); },
  door(g, S) { g.fillStyle = '#4a2f1a'; g.fillRect(0, 0, S, S); for (let x = 0; x < S; x += S / 5) { g.fillStyle = `rgba(0,0,0,.35)`; g.fillRect(x, 0, 2, S); } g.fillStyle = '#25272c'; for (const y of [.2, .5, .8]) g.fillRect(0, S * y - 5, S, 10); g.fillStyle = '#c9a240'; g.beginPath(); g.arc(S * .78, S * .52, 6, 0, 7); g.fill(); noise(g, S, 300, .1); },
  iron(g, S) { g.fillStyle = '#26282e'; g.fillRect(0, 0, S, S); g.strokeStyle = '#555a66'; g.lineWidth = 6; for (let x = 0; x <= S; x += S / 5) { g.beginPath(); g.moveTo(x, 0); g.lineTo(x, S); g.stroke(); } for (let y = 0; y <= S; y += S / 6) { g.beginPath(); g.moveTo(0, y); g.lineTo(S, y); g.stroke(); } },
  water(g, S) { const gr = g.createLinearGradient(0, 0, S, S); gr.addColorStop(0, '#2f6fb0'); gr.addColorStop(1, '#1d4a86'); g.fillStyle = gr; g.fillRect(0, 0, S, S); g.strokeStyle = 'rgba(255,255,255,.25)'; for (let i = 0; i < 26; i++) { g.beginPath(); const y = rnd() * S, x = rnd() * S; g.moveTo(x, y); g.quadraticCurveTo(x + 14, y - 5, x + 30, y); g.stroke(); } },
  parchment(g, S) { g.fillStyle = '#e8d8a8'; g.fillRect(0, 0, S, S); noise(g, S, 500, .08); g.fillStyle = '#6a4a2a'; for (let i = 0; i < 14; i++) g.fillRect(20, 24 + i * 16, S - 40 - rnd() * 80, 3); },
  gold(g, S) { const gr = g.createLinearGradient(0, 0, S, S); gr.addColorStop(0, '#f0cd60'); gr.addColorStop(.5, '#b8902c'); gr.addColorStop(1, '#e8c04c'); g.fillStyle = gr; g.fillRect(0, 0, S, S); noise(g, S, 300, .12); },
  books(g, S) { g.fillStyle = '#2a1c10'; g.fillRect(0, 0, S, S); const cols = ['#7a2a2a', '#2a4a8a', '#2f6a4a', '#8a6a2a', '#5a3a6a', '#d8c8a0']; for (let r = 0; r < 4; r++) { let x = 0; while (x < S) { const w = 6 + rnd() * 10, h = S / 4 - 8 - rnd() * 10; g.fillStyle = cols[(rnd() * 6) | 0]; g.fillRect(x, r * S / 4 + S / 4 - 4 - h, w, h); x += w + 1; } g.fillStyle = '#4a3220'; g.fillRect(0, r * S / 4 + S / 4 - 4, S, 4); } },
  grass(g, S) { g.fillStyle = '#5c9a45'; g.fillRect(0, 0, S, S); for (let i = 0; i < 1800; i++) { g.fillStyle = hsl(88 + rnd() * 30, 40 + rnd() * 20, 28 + rnd() * 18); g.fillRect(rnd() * S, rnd() * S, 2, 3); } },
};
const cache = {};
// real-render texture patches cropped from the boss's beauty renders (tex/b_*.jpg, seamless mirrored tiles) blended over the procedural ones
const REAL = { stone: ['b_stone.jpg', .75, 'overlay'], stoneD: ['b_stoneD.jpg', .7, 'overlay'], slate: ['b_slate.jpg', .95, 'overlay'], slateG: ['b_slate.jpg', .7, 'overlay'], door: ['b_door.jpg', 1] };
const USE_REAL = typeof location === 'undefined' || new URLSearchParams(location.search).get('procedural') == null;
export function tex(name) { if (cache[name]) return cache[name]; seed = 11 + name.length * 31; const cv = mk(256), g = cv.getContext('2d'); makers[name](g, 256); const t = cache[name] = T(cv);
  if (USE_REAL && REAL[name]) { const im = new Image(); im.onload = () => { g.save(); g.globalAlpha = REAL[name][1]; if (REAL[name][2]) g.globalCompositeOperation = REAL[name][2]; g.drawImage(im, 0, 0, 256, 256); g.restore(); if (name === 'slateG') { g.globalCompositeOperation = 'saturation'; g.fillStyle = '#777'; g.fillRect(0, 0, 256, 256); g.globalCompositeOperation = 'source-over'; } t.needsUpdate = true; }; im.src = new URL('./tex/' + REAL[name][0], import.meta.url).href; }
  return t; }
export const TEX_NAMES = Object.keys(makers);
let bannerTex;
export function bannerTexture() { // deep-blue silk, gold trim, lion crest cut from Sir Aldric's sheet
  if (bannerTex) return bannerTex; const cv = document.createElement('canvas'); cv.width = 128; cv.height = 256; const g = cv.getContext('2d');
  g.fillStyle = '#1f3f86'; g.fillRect(0, 0, 128, 256); g.fillStyle = 'rgba(255,255,255,.06)'; for (let x = 0; x < 128; x += 6) g.fillRect(x, 0, 2, 256);
  g.strokeStyle = '#d4af37'; g.lineWidth = 6; g.strokeRect(5, 5, 118, 236); g.fillStyle = '#d4af37'; g.beginPath(); g.moveTo(0, 246); g.lineTo(128, 246); g.lineTo(128, 256); g.lineTo(64, 238); g.lineTo(0, 256); g.fill();
  bannerTex = new THREE.CanvasTexture(cv); bannerTex.colorSpace = THREE.SRGBColorSpace; bannerTex.anisotropy = 4;
  if (USE_REAL) { const rb = new Image(); rb.onload = () => { g.clearRect(0, 0, 128, 256); g.drawImage(rb, 0, 0, 128, 256); bannerTex.needsUpdate = true; }; rb.src = new URL('./tex/b_banner.png', import.meta.url).href; return bannerTex; }
  const im = new Image(); im.onload = () => { const a = Math.min(100 / im.width, 150 / im.height); const w = im.width * a, h = im.height * a; g.save(); g.fillStyle = '#d9b448'; g.drawImage(im, 64 - w / 2, 100 - h / 2, w, h); g.restore(); bannerTex.needsUpdate = true; }; im.src = new URL('./tex/emb_lion.png', import.meta.url).href;
  return bannerTex;
}
export function signTexture(text, emblem) { // hanging shop sign: dark wood board, gold border, text
  const cv = document.createElement('canvas'); cv.width = 256; cv.height = 128; const g = cv.getContext('2d');
  g.fillStyle = '#2a1c14'; g.fillRect(0, 0, 256, 128); g.strokeStyle = '#d4af37'; g.lineWidth = 6; g.strokeRect(6, 6, 244, 116);
  g.fillStyle = '#e8d8a8'; g.font = 'bold 26px Georgia,serif'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText(text, 128, emblem ? 92 : 64, 230);
  if (emblem) { g.fillStyle = '#d4af37'; g.font = '40px serif'; g.fillText(emblem, 128, 40); }
  const t = new THREE.CanvasTexture(cv); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4; return t;
}
