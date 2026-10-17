// VARNETHRYL 3D hero textures: small procedural canvas textures (cloth weave, leather grain, brushed metal, hair strands, faces,
// heraldic decals). Emblems 'lion' and 'fleur' are derived from the boss's Sir Aldric sheet (tex/emb_*.png, see tools/derive_emblems.py).
import * as THREE from 'three';
const cache = {};
const mk = (w, h) => { const c = document.createElement('canvas'); c.width = w; c.height = h; return c; };
const tex = (cv, rep = 1) => { const t = new THREE.CanvasTexture(cv); t.colorSpace = THREE.SRGBColorSpace; t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(rep, rep); t.anisotropy = 4; t.userData.mimeType = 'image/jpeg'; return t; };
let seed = 7; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
export function surface(kind) { // greyscale albedo modulators, tinted by material colour
  if (cache[kind]) return cache[kind]; seed = 7 + kind.length * 13;
  const S = 128, cv = mk(S, S), g = cv.getContext('2d'); g.fillStyle = '#e4e4e4'; g.fillRect(0, 0, S, S);
  if (kind === 'cloth') { for (let y = 0; y < S; y += 2) { g.fillStyle = `rgba(0,0,0,${.08 + rnd() * .06})`; g.fillRect(0, y, S, 1); } for (let x = 0; x < S; x += 2) { g.fillStyle = `rgba(255,255,255,${.06 + rnd() * .07})`; g.fillRect(x, 0, 1, S); }
    for (let i = 0; i < 700; i++) { g.fillStyle = `rgba(${rnd() < .5 ? 0 : 255},${rnd() < .5 ? 0 : 255},0,${rnd() * .06})`; g.fillRect(rnd() * S, rnd() * S, 2 + rnd() * 6, 1); } }
  if (kind === 'leather') { g.fillStyle = '#d8d8d8'; g.fillRect(0, 0, S, S); for (let i = 0; i < 900; i++) { g.fillStyle = `rgba(0,0,0,${rnd() * .16})`; g.beginPath(); g.arc(rnd() * S, rnd() * S, .6 + rnd() * 1.6, 0, 7); g.fill(); }
    for (let i = 0; i < 14; i++) { g.strokeStyle = `rgba(0,0,0,${.05 + rnd() * .1})`; g.lineWidth = 1; g.beginPath(); const y = rnd() * S; g.moveTo(0, y); g.bezierCurveTo(S * .3, y + rnd() * 20 - 10, S * .6, y + rnd() * 20 - 10, S, y + rnd() * 10 - 5); g.stroke(); } }
  if (kind === 'steel') { const gr = g.createLinearGradient(0, 0, S, 0); gr.addColorStop(0, '#f2f2f2'); gr.addColorStop(.35, '#cfcfcf'); gr.addColorStop(.5, '#fafafa'); gr.addColorStop(.8, '#c4c4c4'); gr.addColorStop(1, '#f0f0f0'); g.fillStyle = gr; g.fillRect(0, 0, S, S);
    for (let i = 0; i < 160; i++) { g.strokeStyle = `rgba(${rnd() < .5 ? 0 : 255},${rnd() < .5 ? 0 : 255},0,${rnd() * .12})`; g.lineWidth = rnd() * 1.2; const y = rnd() * S; g.beginPath(); g.moveTo(0, y); g.lineTo(S, y + rnd() * 6 - 3); g.stroke(); }
    for (let i = 0; i < 90; i++) { g.fillStyle = `rgba(40,30,20,${rnd() * .13})`; g.fillRect(rnd() * S, rnd() * S, 1 + rnd() * 3, 1 + rnd() * 3); } }
  if (kind === 'hair') { g.fillStyle = '#d0d0d0'; g.fillRect(0, 0, S, S); for (let x = 0; x < S; x++) { const v = rnd(); g.fillStyle = `rgba(${v < .5 ? 0 : 255},${v < .5 ? 0 : 255},${v < .5 ? 0 : 255},${.07 + rnd() * .18})`; g.fillRect(x, 0, 1 + rnd() * 2, S); } }
  if (kind === 'fur') { g.fillStyle = '#e8e8e8'; g.fillRect(0, 0, S, S); for (let i = 0; i < 1400; i++) { g.strokeStyle = `rgba(${rnd() < .5 ? 80 : 255},${rnd() < .5 ? 80 : 255},${rnd() < .5 ? 80 : 255},${.1 + rnd() * .25})`; g.lineWidth = 1; const x = rnd() * S, y = rnd() * S; g.beginPath(); g.moveTo(x, y); g.lineTo(x + rnd() * 4 - 2, y + 5 + rnd() * 6); g.stroke(); } }
  return cache[kind] = tex(cv, kind === 'steel' ? 1 : 3);
}
// ---- heraldic decals: white-on-alpha shapes, tinted by material colour ----
const shapes = {
  sun(g, S) { g.beginPath(); g.arc(S / 2, S / 2, S * .2, 0, 7); g.fill(); for (let i = 0; i < 16; i++) { const a = i / 16 * Math.PI * 2, r0 = S * .24, r1 = S * (i % 2 ? .36 : .47); g.beginPath(); g.moveTo(S / 2 + Math.sin(a - .12) * r0, S / 2 - Math.cos(a - .12) * r0); g.lineTo(S / 2 + Math.sin(a) * r1, S / 2 - Math.cos(a) * r1); g.lineTo(S / 2 + Math.sin(a + .12) * r0, S / 2 - Math.cos(a + .12) * r0); g.fill(); }
    g.globalCompositeOperation = 'destination-out'; g.fillRect(S * .47, S * .33, S * .06, S * .34); g.fillRect(S * .39, S * .42, S * .22, S * .05); g.globalCompositeOperation = 'source-over'; },
  snow(g, S) { g.lineCap = 'round'; for (let i = 0; i < 3; i++) { g.save(); g.translate(S / 2, S / 2); g.rotate(i * Math.PI / 3); g.lineWidth = S * .05; g.beginPath(); g.moveTo(0, -S * .46); g.lineTo(0, S * .46); g.stroke(); for (const s of [-1, 1]) for (const y of [-.3, .3]) { g.lineWidth = S * .035; g.beginPath(); g.moveTo(0, S * y); g.lineTo(S * .09, S * (y + .09 * s)); g.moveTo(0, S * y); g.lineTo(-S * .09, S * (y + .09 * s)); g.stroke(); } g.restore(); } g.beginPath(); g.arc(S / 2, S / 2, S * .06, 0, 7); g.fill(); },
  gear(g, S) { g.lineWidth = S * .1; g.beginPath(); g.arc(S / 2, S / 2, S * .27, 0, 7); g.stroke(); for (let i = 0; i < 8; i++) { g.save(); g.translate(S / 2, S / 2); g.rotate(i * Math.PI / 4); g.fillRect(-S * .06, -S * .46, S * .12, S * .16); g.restore(); } g.lineWidth = S * .05; for (let i = 0; i < 4; i++) { g.save(); g.translate(S / 2, S / 2); g.rotate(i * Math.PI / 4); g.beginPath(); g.moveTo(0, -S * .24); g.lineTo(0, S * .24); g.stroke(); g.restore(); } g.beginPath(); g.arc(S / 2, S / 2, S * .07, 0, 7); g.fill(); },
  spiral(g, S) { g.lineCap = 'round'; g.lineWidth = S * .06; g.beginPath(); for (let t = 0; t < 4.6 * Math.PI; t += .1) { const r = S * (.03 + t * .03); const x = S / 2 + Math.cos(t) * r, y = S / 2 + Math.sin(t) * r; t ? g.lineTo(x, y) : g.moveTo(x, y); } g.stroke(); for (let i = 0; i < 8; i++) { g.save(); g.translate(S / 2, S / 2); g.rotate(i * Math.PI / 4); g.fillRect(-S * .02, -S * .49, S * .04, S * .08); g.restore(); } },
  cross(g, S) { g.fillRect(S * .45, S * .06, S * .1, S * .88); g.fillRect(S * .22, S * .28, S * .56, S * .09); for (const [x, y] of [[.5, .07], [.5, .93], [.22, .325], [.78, .325]]) { g.beginPath(); g.arc(S * x, S * y, S * .06, 0, 7); g.fill(); } g.beginPath(); g.arc(S / 2, S * .33, S * .08, 0, 7); g.fill(); },
  ornate(g, S) { g.fillRect(S * .46, S * .04, S * .08, S * .92); g.fillRect(S * .18, S * .3, S * .64, S * .07); g.fillRect(S * .3, S * .14, S * .4, S * .06); g.fillRect(S * .36, S * .62, S * .28, S * .05); for (const [x, y] of [[.5, .04], [.5, .96], [.18, .335], [.82, .335], [.3, .17], [.7, .17], [.36, .645], [.64, .645]]) { g.save(); g.translate(S * x, S * y); g.rotate(Math.PI / 4); g.fillRect(-S * .045, -S * .045, S * .09, S * .09); g.restore(); } },
  sprig(g, S) { g.lineCap = 'round'; g.lineWidth = S * .045; g.beginPath(); g.moveTo(S / 2, S * .95); g.lineTo(S / 2, S * .12); g.stroke(); const leaf = (x, y, a, s) => { g.save(); g.translate(x, y); g.rotate(a); g.beginPath(); g.moveTo(0, 0); g.bezierCurveTo(S * .1 * s, -S * .04 * s, S * .12 * s, -S * .2 * s, 0, -S * .27 * s); g.bezierCurveTo(-S * .12 * s, -S * .2 * s, -S * .1 * s, -S * .04 * s, 0, 0); g.fill(); g.restore(); };
    leaf(S / 2, S * .22, 0, 1.0); for (let i = 0; i < 4; i++) for (const k of [-1, 1]) leaf(S / 2, S * (.76 - i * .16), k * (1.0 - i * .05), .85 - i * .09); },
  oak(g, S) { shapes.sprig(g, S); g.beginPath(); g.arc(S * .5, S * .5, 0, 0, 7); },
  shield(g, S) { g.beginPath(); g.moveTo(S * .15, S * .1); g.lineTo(S * .85, S * .1); g.lineTo(S * .85, S * .5); g.quadraticCurveTo(S * .8, S * .8, S * .5, S * .95); g.quadraticCurveTo(S * .2, S * .8, S * .15, S * .5); g.closePath(); g.fill(); },
};
export const IMGS = {};
export async function preload() { // loads the two sheet-derived decals
  await Promise.all(['emb_lion', 'emb_fleur'].map(n => new Promise(res => { const im = new Image(); im.onload = () => { IMGS[n] = im; res(); }; im.onerror = res; im.src = new URL('./tex/' + n + '.png', import.meta.url).href; })));
}
export function decal(type) {
  const k = 'd:' + type; if (cache[k]) return cache[k]; const S = 256, cv = mk(S, S), g = cv.getContext('2d'); g.fillStyle = g.strokeStyle = '#fff';
  const key = { lion: 'emb_lion', fleur: 'emb_fleur' }[type];
  if (key) { if (IMGS[key]) g.drawImage(IMGS[key], 0, 0, S, S); } else (shapes[type] || shapes.cross)(g, S);
  const t = new THREE.CanvasTexture(cv); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4; t.userData.mimeType = 'image/png'; return cache[k] = t;
}
// ---- face texture (equirect: face centred at u=.25, +z) ----
export function faceTex(o) {
  const W = 512, H = 256, cv = mk(W, H), g = cv.getContext('2d'), sk = new THREE.Color(o.skin), hex = c => '#' + c.getHexString();
  g.fillStyle = hex(sk); g.fillRect(0, 0, W, H);
  const lighter = sk.clone().offsetHSL(0, 0, .05), darker = sk.clone().offsetHSL(0, .02, -.1);
  let gr = g.createRadialGradient(128, 122, 6, 128, 128, 70); gr.addColorStop(0, hex(lighter) + 'cc'); gr.addColorStop(1, hex(sk) + '00'); g.fillStyle = gr; g.fillRect(40, 40, 180, 200);
  g.fillStyle = hex(darker) + '66'; g.beginPath(); g.ellipse(128, 164, 20, 7, 0, 0, 7); g.fill(); // under-lip/chin shade
  const cx = 128, ey = 117, ex = 30, e = (k) => {
    const x = cx + k * ex; g.fillStyle = '#f4efe6'; g.beginPath(); g.ellipse(x, ey, 13, 7.5, 0, 0, 7); g.fill();
    g.fillStyle = '#' + new THREE.Color(o.eye).getHexString(); g.beginPath(); g.arc(x + k * -.5, ey, 6.2, 0, 7); g.fill(); g.fillStyle = '#15100c'; g.beginPath(); g.arc(x, ey, 3, 0, 7); g.fill(); g.fillStyle = '#fff'; g.beginPath(); g.arc(x - 2, ey - 2.4, 1.5, 0, 7); g.fill();
    g.strokeStyle = '#1c120c'; g.lineWidth = o.fem ? 3.2 : 2.6; g.beginPath(); g.ellipse(x, ey, 13.5, 7.8, 0, Math.PI * 1.05, Math.PI * 1.95); g.stroke(); // upper lid / lashes
    if (o.fem) { g.lineWidth = 2; g.beginPath(); g.moveTo(x + k * 12, ey - 3); g.lineTo(x + k * 17, ey - 7); g.stroke(); }
    g.strokeStyle = '#' + new THREE.Color(o.hair).multiplyScalar(.8).getHexString(); g.lineWidth = o.fem ? 3 : 4.5; g.lineCap = 'round'; g.beginPath(); g.moveTo(x - k * 14, ey - 15 + (o.fem ? 1 : 0)); g.quadraticCurveTo(x, ey - 20 - (o.brow ?? 0), x + k * 14, ey - 13 + (o.brow ?? 0) * 1.5); g.stroke(); };
  e(-1); e(1);
  g.strokeStyle = hex(darker) + 'aa'; g.lineWidth = 2; g.beginPath(); g.moveTo(cx - 2, ey + 8); g.quadraticCurveTo(cx - 5, ey + 24, cx + 1, ey + 28); g.stroke(); // nose
  g.fillStyle = o.fem ? '#b5535a' : '#a8625a'; g.beginPath(); g.ellipse(cx, 152, o.fem ? 10 : 9, o.fem ? 3.4 : 2.6, 0, 0, 7); g.fill(); g.fillStyle = '#00000033'; g.fillRect(cx - 9, 151.4, 18, 1.2);
  if (o.fem) { g.fillStyle = '#e07a7a22'; for (const k of [-1, 1]) { g.beginPath(); g.ellipse(cx + k * 34, 140, 11, 6, 0, 0, 7); g.fill(); } }
  if (o.scar) { g.strokeStyle = '#8a4a40'; g.lineWidth = 2; g.beginPath(); g.moveTo(cx + 22, ey - 12); g.lineTo(cx + 34, ey + 22); g.stroke(); }
  if (o.beard) { g.fillStyle = '#' + new THREE.Color(o.beard).getHexString() + 'dd'; g.beginPath(); g.moveTo(cx - 40, 140); g.quadraticCurveTo(cx, 128, cx + 40, 140); g.quadraticCurveTo(cx + 36, 196, cx, 206); g.quadraticCurveTo(cx - 36, 196, cx - 40, 140); g.fill(); g.fillStyle = hex(sk); g.beginPath(); g.ellipse(cx, 152, 12, 4.5, 0, 0, 7); g.fill(); g.fillStyle = '#a8625a'; g.beginPath(); g.ellipse(cx, 152, 9, 2.4, 0, 0, 7); g.fill(); }
  const t = new THREE.CanvasTexture(cv); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4; t.userData.mimeType = 'image/png'; return t;
}
