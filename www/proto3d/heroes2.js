// Darius Umbral and Selene Frostveil: detailed low-poly builds from the boss's character sheets.
import * as THREE from './vendor/three.module.js';

const loadImg = src => new Promise((res, rej) => { const i = new Image(); i.onload = () => res(i); i.onerror = rej; i.src = src; });
const tex = (c, rep) => { const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4; if (rep) { t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(rep[0], rep[1]); } return t; };
const cv = (w, h) => { const c = document.createElement('canvas'); c.width = w; c.height = h; return [c, c.getContext('2d')]; };
const rng = (seed => () => (seed = (seed * 16807) % 2147483647) / 2147483647);

function cross(g, cx, cy, s, col) {   // ornate cross (Umbral emblem): arms with flared ends + diamond centre
  g.save(); g.translate(cx, cy); g.fillStyle = col; g.strokeStyle = col; g.lineWidth = s * 0.07; g.lineCap = 'round';
  g.fillRect(-s * 0.05, -s * 0.5, s * 0.1, s); g.fillRect(-s * 0.32, -s * 0.2, s * 0.64, s * 0.09);
  for (const [dx, dy] of [[0, -0.5], [0, 0.5], [-0.32, -0.155], [0.32, -0.155]]) { g.beginPath(); g.arc(dx * s, dy * s, s * 0.07, 0, 6.3); g.fill(); }
  g.beginPath(); g.moveTo(0, -s * 0.5); g.lineTo(-s * 0.14, -s * 0.38); g.lineTo(s * 0.14, -s * 0.38); g.fill();
  g.beginPath(); g.moveTo(0, s * 0.5); g.lineTo(-s * 0.1, s * 0.34); g.lineTo(s * 0.1, s * 0.34); g.fill();
  g.beginPath(); g.moveTo(0, -s * 0.28); g.lineTo(s * 0.12, -s * 0.15); g.lineTo(0, -s * 0.02); g.lineTo(-s * 0.12, -s * 0.15); g.closePath(); g.stroke();
  g.restore();
}
function snowflake(g, cx, cy, r, col, lw) {
  g.save(); g.translate(cx, cy); g.strokeStyle = col; g.fillStyle = col; g.lineWidth = lw; g.lineCap = 'round';
  for (let i = 0; i < 6; i++) {
    g.save(); g.rotate(i * Math.PI / 3);
    g.beginPath(); g.moveTo(0, 0); g.lineTo(0, -r); g.stroke();
    for (const k of [0.45, 0.7]) { g.beginPath(); g.moveTo(0, -r * k); g.lineTo(-r * 0.22, -r * (k + 0.16)); g.moveTo(0, -r * k); g.lineTo(r * 0.22, -r * (k + 0.16)); g.stroke(); }
    g.beginPath(); g.arc(0, -r, lw * 0.9, 0, 6.3); g.fill(); g.restore();
  }
  g.restore();
}
const band = (g, x, y, w, h, c1 = '#e3bd5a', c2 = '#a8802c') => { const gr = g.createLinearGradient(0, y, 0, y + h); gr.addColorStop(0, c1); gr.addColorStop(1, c2); g.fillStyle = gr; g.fillRect(x, y, w, h); };

export async function makeHeroTextures() {
  const [pur, fur, blue] = await Promise.all([loadImg('proto3d/tex/u-purple.jpg'), loadImg('proto3d/tex/s-fur.jpg'), loadImg('proto3d/tex/s-blue.jpg')]);
  const fill = (g, img, w, h, tint, a = 0.8) => { g.fillStyle = tint; g.fillRect(0, 0, w, h); g.globalAlpha = a; g.fillStyle = g.createPattern(img, 'repeat'); g.fillRect(0, 0, w, h); g.globalAlpha = 1; };
  const T = {};
  const EMB = '#cdb98a';
  { const [c, g] = cv(128, 320); fill(g, pur, 128, 320, '#4a1e78'); band(g, 0, 0, 5, 320, '#c9b27a', '#8c7440'); band(g, 123, 0, 5, 320, '#c9b27a', '#8c7440'); cross(g, 64, 95, 90, EMB); cross(g, 64, 235, 54, EMB); T.uTabard = tex(c); }
  { const [c, g] = cv(256, 400); fill(g, pur, 256, 400, '#4a1e78'); cross(g, 128, 175, 190, EMB); band(g, 0, 0, 6, 400, '#6e5a3a', '#4a3c26'); band(g, 250, 0, 6, 400, '#6e5a3a', '#4a3c26'); T.uCape = tex(c); }
  { const [c, g] = cv(128, 128); fill(g, pur, 128, 128, '#4a1e78', 0.9); T.uCloth = tex(c, [2, 2]); }
  { const [c, g] = cv(256, 400); fill(g, blue, 256, 400, '#1f3f8f', 0.55); snowflake(g, 128, 190, 105, '#e8f2ff', 4); snowflake(g, 55, 340, 28, '#e8f2ff', 2.5); snowflake(g, 200, 330, 28, '#e8f2ff', 2.5);
    band(g, 0, 0, 10, 400, '#f1ead8', '#cfc4a8'); band(g, 246, 0, 10, 400, '#f1ead8', '#cfc4a8'); band(g, 10, 0, 3, 400); band(g, 243, 0, 3, 400); band(g, 0, 384, 256, 16, '#f1ead8', '#cfc4a8'); band(g, 0, 380, 256, 4); T.sCape = tex(c); }
  { const [c, g] = cv(256, 256); fill(g, blue, 256, 256, '#2a4ea8', 0.5); for (let i = 0; i < 4; i++) snowflake(g, 32 + i * 64, 70, 22, '#e8f2ff', 2); for (let i = 0; i < 4; i++) snowflake(g, 64 + i * 64 - 32, 150, 18, '#e8f2ff', 2);
    band(g, 0, 232, 256, 24, '#f1ead8', '#cfc4a8'); band(g, 0, 228, 256, 4); T.sSkirt = tex(c, [3, 1]); }
  { const [c, g] = cv(128, 320); fill(g, fur, 128, 320, '#f4f1ea', 0.35); band(g, 0, 0, 6, 320); band(g, 122, 0, 6, 320); snowflake(g, 64, 90, 40, '#7fa6e6', 3); snowflake(g, 64, 220, 28, '#7fa6e6', 2.5); T.sPanel = tex(c); }
  { const [c, g] = cv(128, 128); fill(g, fur, 128, 128, '#f4f1ea', 0.6); T.sFur = tex(c, [2, 1]); }
  { const [c, g] = cv(128, 160); g.fillStyle = '#1d3b86'; g.fillRect(0, 0, 128, 160); g.strokeStyle = '#d7b050'; g.lineWidth = 6; g.strokeRect(5, 5, 118, 150); snowflake(g, 64, 80, 44, '#e0b64e', 4); T.sBook = tex(c); }
  return T;
}

// ---------- shared kit ----------
function kit(shadowOn = true) {
  const P = (geo, m, x, y, z, parent, o = {}) => { if (parent && !parent.isObject3D) { o = parent; parent = null; } const me = new THREE.Mesh(geo, m); me.position.set(x, y, z); me.castShadow = shadowOn; if (o.s) me.scale.set(...o.s); if (o.r) me.rotation.set(...o.r); (parent || P.body).add(me); return me; };
  const phong = (color, o) => new THREE.MeshPhongMaterial(Object.assign({ color, shininess: 70, specular: 0x555a66 }, o));
  return { P, phong, Sph: (r, w = 10, h = 8) => new THREE.SphereGeometry(r, w, h), Box: (x, y, z) => new THREE.BoxGeometry(x, y, z), Cyl: (a, b, h, s = 10) => new THREE.CylinderGeometry(a, b, h, s), lam: (color, o) => new THREE.MeshLambertMaterial(Object.assign({ color }, o)) };
}

// cape: subdivided plane, CPU-swayed. opts: topW, botW, len, jag (tattered hem depth), billow
function makeCape(material, parent, pos, shadowOn, o) {
  const CW = 10, CH = 10, geo = new THREE.PlaneGeometry(1, 1, CW, CH), base = geo.attributes.position.array.slice();
  const R = rng(o.seed || 7), jag = Array.from({ length: CW + 1 }, () => R());
  const m = new THREE.Mesh(geo, material); m.castShadow = shadowOn; m.position.copy(pos); parent.add(m);
  const update = (t, w, turn) => {
    const p = geo.attributes.position;
    for (let i = 0; i < p.count; i++) {
      const u = base[i * 3], v = base[i * 3 + 1], f = 0.5 - v, col = Math.round((u + 0.5) * CW);
      const width = o.topW + (o.botW - o.topW) * f, x = u * width;
      const sway = Math.sin(t * 6 - f * 3.2 + u * 2) * 0.05 * w + Math.sin(t * 1.7 - f * 2 + u) * 0.025;
      let y = -f * o.len; if (o.jag && f > 0.8) y -= (f - 0.8) / 0.2 * o.jag * (jag[col] - 0.4) * 1.0; // ragged hem
      const z = -(0.02 + f * 0.1) - f * f * (0.2 + w * 0.5) + sway * f * 1.6 - u * u * 0.12 * f + (o.billow || 0) * f * Math.sin(t * 1.3 + u * 4) * 0.04;
      p.setXYZ(i, x + turn * f * f * 0.3, y, z);
    }
    p.needsUpdate = true; geo.computeVertexNormals();
  };
  update(0, 0, 0); return update;
}

// =====================================================================
export function buildUmbral(T, shadowOn = true) {
  const { P, phong, Sph, Box, Cyl, lam } = kit(shadowOn);
  const M = {
    steel: phong(0x3a3b44, { shininess: 55, specular: 0x777788 }), steelL: phong(0x575a66, { shininess: 60, specular: 0x888899 }),
    gold: phong(0xb99238, { specular: 0xffe08a, shininess: 80, emissive: 0x1c1200 }), leather: lam(0x4a2d1a), mail: phong(0x24262c, { shininess: 20 }),
    skin: lam(0xe6b896), hair: lam(0x2a1d1c), eye: new THREE.MeshBasicMaterial({ color: 0x3a2a3a }), bone: lam(0xd8c9a0),
    tab: lam(0xffffff, { map: T.uTabard, side: THREE.DoubleSide }), cape: lam(0xffffff, { map: T.uCape, side: THREE.DoubleSide }), cloth: lam(0xffffff, { map: T.uCloth, side: THREE.DoubleSide }),
    blade: new THREE.MeshPhongMaterial({ color: 0x1a1426, emissive: 0x5a1fa8, shininess: 100, specular: 0xb080ff }),
    glow: new THREE.MeshBasicMaterial({ color: 0xa855ff, transparent: true, opacity: 0.42, depthWrite: false, blending: THREE.AdditiveBlending }),
    gem: new THREE.MeshBasicMaterial({ color: 0xc27bff }), spike: phong(0x2c2d34, { shininess: 70 }),
  };
  const root = new THREE.Group(), body = new THREE.Group(); root.add(body); P.body = body;
  const mkLeg = sx => {
    const pv = new THREE.Group(); pv.position.set(sx * 0.2, 0.98, 0); body.add(pv);
    P(Cyl(0.17, 0.15, 0.5, 9), M.steel, 0, -0.27, 0, pv); P(Sph(0.16, 9, 7), M.gold, 0, -0.55, 0.06, pv, { s: [1, 0.85, 0.9] });
    P(new THREE.ConeGeometry(0.05, 0.14, 5), M.spike, 0, -0.55, 0.2, pv, { r: [Math.PI / 2, 0, 0] });
    P(Cyl(0.14, 0.11, 0.5, 9), M.steelL, 0, -0.8, 0, pv); P(Box(0.25, 0.13, 0.44), M.steel, 0, -1.04, 0.08, pv);
    return pv;
  };
  const legL = mkLeg(-1), legR = mkLeg(1);
  P(Cyl(0.34, 0.31, 0.45, 12), M.mail, 0, 1.12, 0);
  P(Cyl(0.42, 0.33, 0.62, 12), M.steel, 0, 1.45, 0, { s: [1, 1, 0.8] });
  P(new THREE.TorusGeometry(0.4, 0.025, 6, 16), M.gold, 0, 1.74, 0, { r: [Math.PI / 2, 0, 0], s: [1, 0.8, 1] });
  P(Cyl(0.35, 0.35, 0.13, 12), M.leather, 0, 1.06, 0, { s: [1.03, 1, 0.9] }); P(new THREE.TorusGeometry(0.06, 0.016, 6, 10), M.gold, 0.0, 0.98, 0.31);
  P(Sph(0.065, 8, 6), M.bone, 0.0, 1.07, 0.32, { s: [1, 1.05, 0.7] });                                 // belt skull
  for (const sx of [-1, 1]) P(Box(0.26, 0.3, 0.1), M.steel, sx * 0.2, 0.92, 0.22, { r: [0.15, 0, 0] });
  P(Box(0.05, 0.55, 0.04), M.leather, -0.17, 1.45, 0.3, { r: [0, 0, -0.35] });
  const tab = new THREE.Group(); tab.position.set(0, 1.78, 0.285); body.add(tab);   // tabard with ragged hem
  { const g = new THREE.PlaneGeometry(0.5, 1.3, 6, 8), p = g.attributes.position; const R = rng(5); for (let i = 0; i < p.count; i++) if (p.getY(i) < -0.6) p.setY(i, p.getY(i) - R() * 0.16 * (1 + (p.getY(i) < -0.64 ? 1 : 0))); P(g, M.tab, 0, -0.65, 0, tab).castShadow = false; }
  // head: dark swept hair, no helm
  const head = new THREE.Group(); head.position.set(0, 1.95, 0); body.add(head);
  P(Sph(0.24, 14, 12), M.skin, 0, 0, 0, head, { s: [0.92, 1.08, 0.98] }); P(Cyl(0.1, 0.12, 0.14, 8), M.skin, 0, -0.24, -0.02, head);
  P(Sph(0.255, 14, 10), M.hair, 0, 0.08, -0.05, head, { s: [1, 0.86, 1.05] }); P(Box(0.42, 0.1, 0.12), M.hair, 0, 0.17, 0.15, head, { r: [0.3, 0, 0] });
  for (const [x, z, rx, rz] of [[-0.2, 0.0, 0.2, 0.9], [0.2, 0.0, 0.2, -0.9], [0, -0.22, -1.1, 0], [-0.1, 0.08, 0.5, 0.4], [0.1, 0.1, 0.5, -0.5], [0.0, -0.1, -0.5, 0.0]]) P(new THREE.ConeGeometry(0.07, 0.26, 5), M.hair, x, 0.2, z, head, { r: [rx, 0, rz] });
  for (const sx of [-1, 1]) { P(Sph(0.028, 6, 5), M.eye, sx * 0.09, 0.02, 0.215, head); P(Box(0.1, 0.025, 0.02), M.hair, sx * 0.09, 0.085, 0.222, head, { r: [0, 0, sx * -0.2] }); }
  P(Box(0.04, 0.08, 0.05), M.skin, 0, -0.03, 0.235, head);
  // pauldrons: stacked plates, ring of spikes, gold skull on the left
  for (const sx of [-1, 1]) {
    const g = new THREE.Group(); g.position.set(sx * 0.52, 1.72, 0); g.rotation.z = -sx * 0.3; body.add(g);
    P(new THREE.SphereGeometry(0.28, 12, 8, 0, 6.283, 0, 1.6), M.steel, 0, 0, 0, g, { s: [1.1, 0.9, 1.05] });
    P(new THREE.SphereGeometry(0.33, 12, 8, 0, 6.283, 0, 1.2), M.steelL, 0, -0.1, 0, g, { s: [1.0, 0.8, 1.05] });
    P(new THREE.SphereGeometry(0.37, 12, 8, 0, 6.283, 0, 1.0), M.steel, 0, -0.2, 0, g, { s: [1.0, 0.8, 1.05] });
    P(new THREE.TorusGeometry(0.31, 0.022, 6, 16), M.gold, 0, -0.1, 0, g, { r: [Math.PI / 2, 0, 0] });
    for (let i = 0; i < 5; i++) { const a = -1.2 + i * 0.6; P(new THREE.ConeGeometry(0.055, 0.3, 5), M.spike, Math.sin(a) * 0.26 * sx + sx * 0.08, 0.16 + (i % 2) * 0.03, Math.cos(a) * 0.18, g, { r: [Math.cos(a) * 0.5, 0, -sx * (0.4 + Math.sin(a) * 0.3)] }); }
    P(new THREE.ConeGeometry(0.07, 0.4, 5), M.spike, sx * 0.1, 0.3, 0, g, { r: [0, 0, -sx * 0.2] });
    if (sx < 0) { P(Sph(0.085, 8, 6), M.gold, -0.12, -0.06, 0.26, g, { s: [1, 1.05, 0.7] }); for (const e of [-1, 1]) P(Sph(0.02, 5, 4), M.eye, -0.12 + e * 0.03, -0.04, 0.31, g); }
    P(Cyl(0.07, 0.07, 0.04, 10), M.gold, sx * 0.0, 0.1, -0.25, g, { r: [Math.PI / 2, 0, 0] });
  }
  P(new THREE.TorusGeometry(0.15, 0.015, 5, 10), M.gold, -0.3, 1.45, 0.3, { r: [0.4, 0, 0] });   // hanging chain ring
  const mkArm = sx => {
    const pv = new THREE.Group(); pv.position.set(sx * 0.57, 1.62, 0); body.add(pv);
    P(Cyl(0.1, 0.09, 0.38, 8), M.mail, 0, -0.22, 0, pv); P(Sph(0.11, 8, 6), M.gold, 0, -0.43, -0.02, pv);
    P(new THREE.ConeGeometry(0.04, 0.14, 5), M.spike, 0, -0.43, -0.13, pv, { r: [-Math.PI / 2, 0, 0] });
    P(Cyl(0.105, 0.085, 0.36, 8), M.steelL, 0, -0.62, 0, pv); P(Box(0.14, 0.17, 0.17), M.steel, 0, -0.87, 0, pv);
    return pv;
  };
  const armL = mkArm(-1), armR = mkArm(1);
  // shadow sword: dark blade with purple glow shell, winged spiked guard, purple gem
  const sword = new THREE.Group(); sword.position.set(0, -0.87, 0.04); armR.add(sword); sword.rotation.x = Math.PI - 0.5;
  P(Box(0.12, 1.1, 0.03), M.blade, 0, 0.68, 0, sword); P(new THREE.ConeGeometry(0.085, 0.3, 4), M.blade, 0, 1.38, 0, sword, { s: [1, 1, 0.3], r: [0, Math.PI / 4, 0] });
  P(Box(0.2, 1.25, 0.09), M.glow, 0, 0.72, 0, sword).castShadow = false; P(new THREE.ConeGeometry(0.12, 0.45, 4), M.glow, 0, 1.58, 0, sword, { s: [1, 1, 0.6], r: [0, Math.PI / 4, 0] }).castShadow = false;
  P(Box(0.5, 0.06, 0.08), M.steel, 0, 0.1, 0, sword);
  for (const sx of [-1, 1]) { P(new THREE.ConeGeometry(0.05, 0.28, 4), M.spike, sx * 0.3, 0.16, 0, sword, { r: [0, 0, -sx * 1.2] }); P(new THREE.ConeGeometry(0.035, 0.16, 4), M.spike, sx * 0.14, 0.2, 0, sword); }
  P(Cyl(0.03, 0.03, 0.22, 8), M.leather, 0, -0.04, 0, sword); P(Sph(0.05, 8, 6), M.gold, 0, -0.17, 0, sword); P(Sph(0.04, 8, 6), M.gem, 0, 0.1, 0.05, sword);
  // tattered cloak (purple, cross on back) + cowl collar
  P(Cyl(0.3, 0.42, 0.22, 12), M.cloth, 0, 1.83, -0.03, { s: [1, 1, 0.9] });
  const capeUpdate = makeCape(M.cape, body, new THREE.Vector3(0, 1.8, -0.27), shadowOn, { topW: 0.86, botW: 1.45, len: 1.85, jag: 0.5, seed: 11, billow: 1 });
  for (const sx of [-1, 1]) P(Cyl(0.08, 0.08, 0.05, 10), M.gold, sx * 0.4, 1.76, -0.22, { r: [Math.PI / 2, 0, 0] });
  root.userData = { body, legL, legR, armL, armR, head, tab, capeUpdate, name: 'Darius Umbral', glow: M.glow };
  return root;
}

// =====================================================================
export function buildSelene(T, shadowOn = true) {
  const { P, phong, Sph, Box, Cyl, lam } = kit(shadowOn);
  const M = {
    gold: phong(0xd8aa3a, { specular: 0xffe08a, shininess: 90, emissive: 0x2a1c00 }), leather: lam(0x6a4126), glove: lam(0x2a2c38),
    skin: lam(0xf4d2b8), hair: lam(0xe8c675), eye: new THREE.MeshBasicMaterial({ color: 0x4a78c0 }),
    blue: lam(0x24449a), white: lam(0xf1eee6), silver: phong(0xc8cfdc, { shininess: 80 }),
    fur: lam(0xffffff, { map: T.sFur }), cape: lam(0xffffff, { map: T.sCape, side: THREE.DoubleSide }),
    skirt: lam(0xffffff, { map: T.sSkirt, side: THREE.DoubleSide }), panel: lam(0xffffff, { map: T.sPanel, side: THREE.DoubleSide }),
    crystal: new THREE.MeshPhongMaterial({ color: 0x66b4ff, emissive: 0x2a6ad0, shininess: 120, specular: 0xffffff, transparent: true, opacity: 0.88, flatShading: true }),
    book: lam(0xffffff, { map: T.sBook }), page: lam(0xe9dcb4),
  };
  const root = new THREE.Group(), body = new THREE.Group(); root.add(body); P.body = body;
  const mkLeg = sx => {  // legs mostly hidden by the gown: dark thigh-high boots with gold trim
    const pv = new THREE.Group(); pv.position.set(sx * 0.15, 0.98, 0); body.add(pv);
    P(Cyl(0.12, 0.1, 0.55, 8), M.glove, 0, -0.3, 0, pv); P(Cyl(0.1, 0.085, 0.45, 8), M.silver, 0, -0.78, 0, pv); P(Box(0.17, 0.1, 0.3), M.gold, 0, -1.0, 0.06, pv);
    return pv;
  };
  const legL = mkLeg(-1), legR = mkLeg(1);
  // gown: flared blue skirt, open white-gold front panel, gold hem ring (the "tab" group sways)
  const tab = new THREE.Group(); tab.position.set(0, 1.08, 0); body.add(tab);
  P(new THREE.CylinderGeometry(0.3, 0.78, 1.0, 22, 1, true), M.skirt, 0, -0.5, 0, tab).castShadow = shadowOn;
  P(new THREE.CylinderGeometry(0.72, 0.8, 0.12, 22, 1, true), M.panel, 0, -0.98, 0, tab);
  const pg = new THREE.PlaneGeometry(0.34, 0.98, 1, 6); P(pg, M.panel, 0, -0.5, 0.4, tab, { r: [0.5, 0, 0] });
  P(new THREE.TorusGeometry(0.79, 0.022, 6, 28), M.gold, 0, -1.0, 0, tab, { r: [Math.PI / 2, 0, 0] });
  // bodice
  P(Cyl(0.27, 0.22, 0.5, 12), M.blue, 0, 1.3, 0, { s: [1, 1, 0.82] });
  P(Cyl(0.3, 0.3, 0.14, 12), M.leather, 0, 1.06, 0, { s: [1, 1, 0.85] });
  P(new THREE.TorusGeometry(0.23, 0.02, 6, 14), M.gold, 0, 1.12, 0, { r: [Math.PI / 2, 0, 0], s: [1, 0.85, 1] });
  P(new THREE.OctahedronGeometry(0.075), M.crystal, 0, 1.45, 0.24, { s: [0.8, 1.2, 0.6] });                       // chest ornament
  P(new THREE.TorusGeometry(0.1, 0.015, 5, 10), M.gold, 0, 1.45, 0.235);
  // spellbook on the left hip + belt pouches + hanging crystals
  const book = P(Box(0.26, 0.34, 0.08), M.book, -0.33, 0.98, 0.1, { r: [0, 0.35, 0.1] });
  P(Box(0.02, 0.34, 0.085), M.gold, -0.2, 0.98, 0.12, { r: [0, 0.35, 0.1] }); P(Box(0.22, 0.3, 0.05), M.page, -0.32, 0.98, 0.06, { r: [0, 0.35, 0.1] });
  for (let i = 0; i < 3; i++) P(new THREE.OctahedronGeometry(0.04), M.crystal, 0.3 + i * 0.03, 0.9 - i * 0.07, 0.2, { s: [0.7, 1.4, 0.7] });
  // head with long wavy blonde hair
  const head = new THREE.Group(); head.position.set(0, 1.88, 0); body.add(head);
  P(Sph(0.21, 14, 12), M.skin, 0, 0, 0, head, { s: [0.9, 1.1, 0.98] }); P(Cyl(0.075, 0.09, 0.14, 8), M.skin, 0, -0.22, -0.02, head);
  for (const sx of [-1, 1]) { P(Sph(0.026, 6, 5), M.eye, sx * 0.08, 0.02, 0.195, head); P(Box(0.09, 0.018, 0.02), M.hair, sx * 0.08, 0.075, 0.2, head); }
  P(Box(0.035, 0.07, 0.04), M.skin, 0, -0.03, 0.21, head);
  P(Box(0.07, 0.015, 0.02), new THREE.MeshBasicMaterial({ color: 0xc86a6a }), 0, -0.1, 0.19, head);
  P(Sph(0.235, 14, 10), M.hair, 0, 0.06, -0.04, head, { s: [1, 0.9, 1.03] });
  for (const sx of [-1, 1]) P(Box(0.08, 0.3, 0.1), M.hair, sx * 0.2, -0.1, 0.02, head);                        // face-framing locks
  const hairBack = new THREE.Group(); hairBack.position.z = 0.04; head.add(hairBack);
  { const pts = []; for (let i = 0; i <= 10; i++) pts.push(new THREE.Vector3(Math.sin(i * 0.9) * 0.07, -i * 0.13, -0.2 - i * 0.012));
    for (const [dx, sc] of [[0, 1], [-0.12, 0.8], [0.12, 0.8]]) { const g = new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts.map(p => new THREE.Vector3(p.x + dx, p.y, p.z))), 20, 0.1 * sc, 7); P(g, M.hair, 0, 0, 0, hairBack, { s: [1.3, 1, 0.6] }); } }
  P(new THREE.OctahedronGeometry(0.06), M.crystal, 0.12, 0.22, 0.14, head, { s: [0.8, 1.3, 0.5] });
  // fur collar + gold clasp
  P(new THREE.TorusGeometry(0.28, 0.1, 8, 16), M.fur, 0, 1.68, 0, { r: [Math.PI / 2, 0, 0], s: [1.15, 1, 0.9] });
  for (let i = 0; i < 7; i++) { const a = i / 7 * 6.28; P(Sph(0.1, 7, 6), M.fur, Math.sin(a) * 0.36, 1.66, Math.cos(a) * 0.3, null); }
  for (const sx of [-1, 1]) { P(Sph(0.17, 8, 6), M.fur, sx * 0.5, 1.64, 0, { s: [1, 0.8, 1] }); }
  // arms: blue sleeves with white/gold cuffs, gloves
  const mkArm = sx => {
    const pv = new THREE.Group(); pv.position.set(sx * 0.4, 1.58, 0); body.add(pv);
    P(Cyl(0.075, 0.07, 0.42, 8), M.blue, 0, -0.22, 0, pv); P(Cyl(0.11, 0.085, 0.3, 8), M.white, 0, -0.5, 0, pv); P(new THREE.TorusGeometry(0.095, 0.014, 5, 10), M.gold, 0, -0.64, 0, pv, { r: [Math.PI / 2, 0, 0] });
    P(Cyl(0.065, 0.05, 0.14, 8), M.glove, 0, -0.74, 0, pv); P(Sph(0.065, 7, 6), M.glove, 0, -0.84, 0, pv);
    return pv;
  };
  const armL = mkArm(-1), armR = mkArm(1);
  // staff: gold twisted shaft, crystal cluster with filigree, hanging crystals (held vertically at the right hand)
  const staff = new THREE.Group(); staff.position.set(0.45, 0.0, 0.55); body.add(staff);
  P(Cyl(0.028, 0.032, 2.5, 8), M.gold, 0, 1.2, 0, staff); for (let i = 0; i < 8; i++) P(new THREE.TorusGeometry(0.036, 0.008, 4, 8), M.gold, 0, 0.3 + i * 0.28, 0, staff, { r: [Math.PI / 2, 0, 0] });
  P(Sph(0.06, 8, 6), M.gold, 0, 0.0, 0, staff);
  P(new THREE.OctahedronGeometry(0.17), M.crystal, 0, 2.7, 0, staff, { s: [0.7, 1.9, 0.7] });
  for (const [x, z, h, rz] of [[-0.14, 0, 0.9, 0.6], [0.14, 0, 0.9, -0.6], [0, 0.12, 0.7, 0], [0, -0.12, 0.7, 0]]) P(new THREE.OctahedronGeometry(0.1), M.crystal, x, 2.55, z, staff, { s: [0.6, h * 1.4, 0.6], r: [0, 0, rz] });
  P(new THREE.TorusGeometry(0.17, 0.018, 6, 14), M.gold, 0, 2.38, 0, staff, { r: [Math.PI / 2, 0, 0] });
  for (const sx of [-1, 1]) P(new THREE.TorusGeometry(0.2, 0.014, 5, 12, Math.PI), M.gold, sx * 0.0, 2.55, 0, staff, { r: [0, sx * Math.PI / 2, sx * 1.4] });
  for (let i = 0; i < 4; i++) P(new THREE.OctahedronGeometry(0.045), M.crystal, (i % 2 ? 0.1 : -0.1), 2.25 - i * 0.12, 0.04, staff, { s: [0.7, 1.5, 0.7] });
  // cape: wide, blue outside with snowflake, white-gold edge
  const capeUpdate = makeCape(M.cape, body, new THREE.Vector3(0, 1.72, -0.34), shadowOn, { topW: 0.9, botW: 1.8, len: 1.7, seed: 3, billow: 1.5 });
  for (const sx of [-1, 1]) P(Cyl(0.06, 0.06, 0.04, 10), M.gold, sx * 0.34, 1.7, -0.2, { r: [Math.PI / 2, 0, 0] });
  root.userData = { body, legL, legR, armL, armR, head, tab, capeUpdate, hairBack, staff, armRBase: -0.75, name: 'Selene Frostveil', gown: true };
  return root;
}
