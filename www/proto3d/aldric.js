// Sir Aldric: detailed low-poly knight built from primitives + decals cropped from the boss's character sheet.
import * as THREE from './vendor/three.module.js';

const loadImg = src => new Promise((res, rej) => { const i = new Image(); i.onload = () => res(i); i.onerror = rej; i.src = src; });

// pull the gold pixels (lion, fleur-de-lis) out of the sheet crop into a transparent canvas, keeping the painted shading
function goldMask(img, sx, sy, sw, sh, clip) {
  const c = document.createElement('canvas'); c.width = sw; c.height = sh;
  const g = c.getContext('2d', { willReadFrequently: true }); g.drawImage(img, sx, sy, sw, sh, 0, 0, sw, sh);
  const d = g.getImageData(0, 0, sw, sh), a = d.data;
  for (let y = 0; y < sh; y++) for (let x = 0; x < sw; x++) {
    const i = (y * sw + x) * 4, r = a[i], b = a[i + 2];
    let al = Math.max(0, Math.min(1, (r - b - 40) / 45));
    if (clip && !clip(x + sx, y + sy)) al = 0;
    a[i + 3] = al * 255;
  }
  g.putImageData(d, 0, 0); return c;
}

export async function makeAldricTextures() {
  const [sheet, cloth] = await Promise.all([loadImg('proto3d/tex/shield.jpg'), loadImg('proto3d/tex/cloth.jpg')]);
  // inner-shield clip so the gold rim of the source is not picked up
  const inner = (x, y) => { const k = Math.max(0, y - 120) * 0.62; return x > 28 + k && x < 176 - k && y > 36 && y < 236; };
  const lion = goldMask(sheet, 0, 0, 256, 352, inner);
  const fleurTop = goldMask(sheet, 66, 0, 58, 46, null), fleurBot = goldMask(sheet, 66, 228, 62, 60, (x, y) => y < 284);
  const lionBox = { sx: 26, sy: 38, sw: 152, sh: 190 };
  const base = (g, w, h) => {
    g.fillStyle = '#23469a'; g.fillRect(0, 0, w, h);
    g.globalAlpha = 0.55; const p = g.createPattern(cloth, 'repeat'); g.fillStyle = p; g.fillRect(0, 0, w, h); g.globalAlpha = 1;
  };
  const tex = c => { const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4; return t; };
  const lionAt = (g, cx, cy, w, flip) => {
    const h = w * lionBox.sh / lionBox.sw; g.save(); g.translate(cx, cy); if (flip) g.scale(-1, 1);
    g.drawImage(lion, lionBox.sx, lionBox.sy, lionBox.sw, lionBox.sh, -w / 2, -h / 2, w, h); g.restore();
  };
  const fleurAt = (g, cx, cy, w, which) => { const im = which ? fleurBot : fleurTop, h = w * im.height / im.width; g.drawImage(im, cx - w / 2, cy - h / 2, w, h); };
  const goldBand = (g, x, y, w, h) => { const gr = g.createLinearGradient(0, y, 0, y + h); gr.addColorStop(0, '#e3bd5a'); gr.addColorStop(1, '#a8802c'); g.fillStyle = gr; g.fillRect(x, y, w, h); };

  // shield face (kite UVs are mapped from the shape bounds)
  const sc = document.createElement('canvas'); sc.width = 256; sc.height = 352; { const g = sc.getContext('2d'); base(g, 256, 352);
    lionAt(g, 128, 170, 150); fleurAt(g, 128, 38, 40, 0); fleurAt(g, 128, 300, 38, 1); }
  // tabard (front): crest + fleur + gold hem
  const tc = document.createElement('canvas'); tc.width = 128; tc.height = 320; { const g = tc.getContext('2d'); base(g, 128, 320);
    goldBand(g, 0, 0, 7, 320); goldBand(g, 121, 0, 7, 320); goldBand(g, 0, 300, 128, 20);
    lionAt(g, 64, 78, 78); fleurAt(g, 64, 215, 46, 1); }
  // cape: lion on the outside (back), fleurs at the hem, gold edge
  const cc = document.createElement('canvas'); cc.width = 256; cc.height = 400; { const g = cc.getContext('2d'); base(g, 256, 400);
    goldBand(g, 0, 0, 8, 400); goldBand(g, 248, 0, 8, 400); goldBand(g, 0, 380, 256, 20);
    lionAt(g, 128, 175, 120); fleurAt(g, 128, 60, 36, 0); fleurAt(g, 40, 330, 30, 1); fleurAt(g, 128, 335, 30, 1); fleurAt(g, 216, 330, 30, 1); }
  // emblem disc (chest / rosette)
  return { shield: tex(sc), tabard: tex(tc), cape: tex(cc), lionCanvas: lion };
}

export function buildAldric(T, shadowOn = true) {
  const phong = (color, o) => new THREE.MeshPhongMaterial(Object.assign({ color, shininess: 70, specular: 0x555a66, flatShading: false }, o));
  const mat = {
    silver: phong(0xaeb6c4), silverD: phong(0x7c8494), gold: phong(0xd8aa3a, { specular: 0xffe08a, shininess: 90, emissive: 0x2a1c00 }),
    mail: phong(0x3b4048, { shininess: 25 }), leather: new THREE.MeshLambertMaterial({ color: 0x6a4126 }),
    skin: new THREE.MeshLambertMaterial({ color: 0xf0c3a0 }), hair: new THREE.MeshLambertMaterial({ color: 0xd9a84a }),
    blue: new THREE.MeshLambertMaterial({ color: 0x23469a }), gem: new THREE.MeshPhongMaterial({ color: 0x2a62ff, emissive: 0x0d2a90, shininess: 120, specular: 0xffffff }),
    dark: new THREE.MeshLambertMaterial({ color: 0x20232a }), eye: new THREE.MeshBasicMaterial({ color: 0x2a3550 }),
    tabard: new THREE.MeshLambertMaterial({ map: T.tabard, side: THREE.DoubleSide }),
    cape: new THREE.MeshLambertMaterial({ map: T.cape, side: THREE.DoubleSide }),
    shield: new THREE.MeshLambertMaterial({ map: T.shield }),
  };
  const root = new THREE.Group(), body = new THREE.Group(); root.add(body);
  const P = (geo, m, x, y, z, parent, o = {}) => { if (parent && !parent.isObject3D) { o = parent; parent = null; } const me = new THREE.Mesh(geo, m); me.position.set(x, y, z); me.castShadow = shadowOn; me.receiveShadow = false; if (o.s) me.scale.set(...o.s); if (o.r) me.rotation.set(...o.r); (parent || body).add(me); return me; };
  const Sph = (r, w = 10, h = 8) => new THREE.SphereGeometry(r, w, h), Box = (x, y, z) => new THREE.BoxGeometry(x, y, z), Cyl = (a, b, h, s = 10) => new THREE.CylinderGeometry(a, b, h, s);

  // ---- legs: cuisse (silver), gold knee cop, greave, sabaton
  const mkLeg = sx => {
    const pv = new THREE.Group(); pv.position.set(sx * 0.2, 0.98, 0); body.add(pv);
    P(Cyl(0.17, 0.15, 0.5, 9), mat.silver, 0, -0.27, 0, pv);                    // cuisse
    P(Sph(0.16, 9, 7), mat.gold, 0, -0.55, 0.05, pv, { s: [1, 0.85, 0.9] });  // knee cop
    P(Cyl(0.14, 0.11, 0.5, 9), mat.silver, 0, -0.8, 0, pv);                    // greave
    P(Cyl(0.15, 0.15, 0.04, 9), mat.gold, 0, -0.6, 0, pv);
    P(Box(0.24, 0.12, 0.42), mat.silverD, 0, -1.04, 0.08, pv);                 // sabaton
    P(Cyl(0.12, 0.13, 0.03, 9), mat.gold, 0, -1.0, 0, pv);
    return pv;
  };
  const legL = mkLeg(-1), legR = mkLeg(1);
  // ---- torso: mail under plate, breastplate, belt
  P(Cyl(0.34, 0.31, 0.45, 12), mat.mail, 0, 1.12, 0);
  P(Cyl(0.42, 0.33, 0.62, 12), mat.silver, 0, 1.45, 0, { s: [1.0, 1, 0.78] });         // breastplate
  P(new THREE.TorusGeometry(0.4, 0.025, 6, 16), mat.gold, 0, 1.74, 0, { r: [Math.PI / 2, 0, 0], s: [1, 0.8, 1] }); // gorget trim
  P(Cyl(0.34, 0.34, 0.12, 12), mat.leather, 0, 1.06, 0, { s: [1.03, 1, 0.9] });        // belt
  P(Box(0.14, 0.12, 0.05), mat.gold, 0, 1.06, 0.3);                                    // buckle
  // skirt tassets (plate flaps)
  for (const sx of [-1, 1]) P(Box(0.26, 0.28, 0.1), mat.silver, sx * 0.2, 0.92, 0.22, null, { r: [0.15, 0, 0] });
  // straps across chest
  P(Box(0.05, 0.5, 0.04), mat.leather, 0.16, 1.45, 0.3, null, { r: [0, 0, 0.35] });
  // ---- tabard front panel (pivot at belt for swing)
  const tab = new THREE.Group(); tab.position.set(0, 1.78, 0.285); body.add(tab);
  const tabMesh = P(new THREE.PlaneGeometry(0.56, 1.28), mat.tabard, 0, -0.64, 0.0, tab);
  tabMesh.castShadow = false;
  // ---- head: face, blond hair, no helm (matches sheet)
  const head = new THREE.Group(); head.position.set(0, 1.95, 0); body.add(head);
  P(Sph(0.24, 14, 12), mat.skin, 0, 0, 0, head, { s: [0.92, 1.08, 0.98] });
  P(Cyl(0.1, 0.12, 0.14, 8), mat.skin, 0, -0.24, -0.02, body === head ? null : head);
  P(Sph(0.255, 14, 10), mat.hair, 0, 0.07, -0.04, head, { s: [1, 0.85, 1.03] });
  P(Box(0.1, 0.34, 0.14), mat.hair, -0.2, -0.04, -0.02, head); P(Box(0.1, 0.34, 0.14), mat.hair, 0.2, -0.04, -0.02, head);          // hair cap
  P(Box(0.4, 0.12, 0.1), mat.hair, 0, 0.17, 0.15, head, { r: [0.2, 0, 0] });                // fringe
  for (const [x, z, rz] of [[-0.2, 0.0, 0.7], [0.2, 0.0, -0.7], [0.0, -0.22, 0], [-0.12, 0.1, 0.4], [0.12, 0.1, -0.4]]) P(new THREE.ConeGeometry(0.06, 0.14, 5), mat.hair, x, 0.22, z, head, { r: [z < -0.1 ? -0.9 : 0.3, 0, rz] }); // tufts
  for (const sx of [-1, 1]) { P(Sph(0.028, 6, 5), mat.eye, sx * 0.09, 0.02, 0.215, head); P(Box(0.1, 0.02, 0.02), mat.hair, sx * 0.09, 0.09, 0.22, head); }
  P(Box(0.04, 0.08, 0.05), mat.skin, 0, -0.03, 0.235, head);                                  // nose
  // ---- pauldrons: layered plates + gold trim + gold rosette (cape attachment)
  for (const sx of [-1, 1]) {
    const g = new THREE.Group(); g.position.set(sx * 0.5, 1.7, 0); body.add(g); g.rotation.z = -sx * 0.25;
    P(new THREE.SphereGeometry(0.26, 12, 8, 0, 6.283, 0, 1.6), mat.silver, 0, 0, 0, g, { s: [1.05, 0.9, 1] });
    P(new THREE.SphereGeometry(0.3, 12, 8, 0, 6.283, 0, 1.2), mat.silver, 0, -0.1, 0, g, { s: [1.0, 0.8, 1.0] });
    P(new THREE.TorusGeometry(0.28, 0.022, 6, 16), mat.gold, 0, -0.1, 0, g, { r: [Math.PI / 2, 0, 0] });
    P(Cyl(0.07, 0.07, 0.04, 10), mat.gold, sx * 0.0, 0.1, -0.2, g, { r: [Math.PI / 2, 0, 0] });
  }
  // ---- arms (pivot at shoulder): mail sleeve, gold couter, silver vambrace, gauntlet
  const mkArm = sx => {
    const pv = new THREE.Group(); pv.position.set(sx * 0.56, 1.62, 0); body.add(pv);
    P(Cyl(0.1, 0.09, 0.38, 8), mat.mail, 0, -0.22, 0, pv);
    P(Sph(0.1, 8, 6), mat.gold, 0, -0.43, -0.02, pv);
    P(Cyl(0.1, 0.085, 0.36, 8), mat.silver, 0, -0.62, 0, pv);
    P(Cyl(0.105, 0.105, 0.03, 8), mat.gold, 0, -0.46, 0, pv);
    P(Box(0.14, 0.16, 0.16), mat.silverD, 0, -0.87, 0, pv);
    return pv;
  };
  const armL = mkArm(-1), armR = mkArm(1);
  // ---- sword (right hand, point down-forward): steel blade, gold guard, blue gem, leather grip
  const sword = new THREE.Group(); sword.position.set(0, -0.87, 0.04); armR.add(sword); sword.rotation.x = Math.PI - 0.55;
  P(Box(0.075, 1.0, 0.025), mat.silver, 0, 0.62, 0, sword);
  P(new THREE.ConeGeometry(0.053, 0.2, 4), mat.silver, 0, 1.22, 0, sword, { s: [1, 1, 0.35], r: [0, Math.PI / 4, 0] });
  P(Box(0.4, 0.05, 0.07), mat.gold, 0, 0.1, 0, sword);
  for (const sx of [-1, 1]) P(Sph(0.04, 7, 6), mat.gold, sx * 0.2, 0.1, 0, sword);
  P(Cyl(0.03, 0.03, 0.2, 8), mat.leather, 0, -0.03, 0, sword);
  P(Sph(0.045, 8, 6), mat.gold, 0, -0.15, 0, sword);
  P(Sph(0.035, 8, 6), mat.gem, 0, 0.1, 0.045, sword);
  // ---- kite shield (left arm): gold rim + textured face with lion
  const kite = new THREE.Shape(); { const W = 0.36, H = 0.6; kite.moveTo(-W, H); kite.lineTo(W, H); kite.lineTo(W, H * 0.15); kite.quadraticCurveTo(W * 0.7, -H * 0.55, 0, -H); kite.quadraticCurveTo(-W * 0.7, -H * 0.55, -W, H * 0.15); kite.lineTo(-W, H); }
  const rim = new THREE.ExtrudeGeometry(kite, { depth: 0.05, bevelEnabled: true, bevelSize: 0.03, bevelThickness: 0.02, bevelSegments: 1, curveSegments: 8 });
  const faceShape = new THREE.Shape(); { const W = 0.33, H = 0.57; faceShape.moveTo(-W, H); faceShape.lineTo(W, H); faceShape.lineTo(W, H * 0.15); faceShape.quadraticCurveTo(W * 0.7, -H * 0.55, 0, -H); faceShape.quadraticCurveTo(-W * 0.7, -H * 0.55, -W, H * 0.15); faceShape.lineTo(-W, H); }
  const face = new THREE.ShapeGeometry(faceShape, 8);
  { // UV: map shape bounds to the 256x352 face canvas
    const p = face.attributes.position, uv = face.attributes.uv; for (let i = 0; i < p.count; i++) uv.setXY(i, (p.getX(i) + 0.33) / 0.66, (p.getY(i) + 0.57) / 1.14); }
  const shield = new THREE.Group(); shield.position.set(-0.3, -0.5, 0.15); shield.rotation.set(0, -0.3, 0); armL.add(shield);
  P(rim, mat.gold, 0, 0, -0.025, shield);
  P(face, mat.shield, 0, 0, 0.056, shield).castShadow = false;
  P(Sph(0.06, 8, 6), mat.gold, 0, 0.0, 0.07, shield, { s: [1, 1, 0.5] });
  // ---- cape: subdivided plane from shoulders, vertices swayed on the CPU each frame
  const CW = 6, CH = 10, capeGeo = new THREE.PlaneGeometry(1, 1, CW, CH);
  const base = capeGeo.attributes.position.array.slice();
  const cape = new THREE.Mesh(capeGeo, mat.cape); cape.castShadow = shadowOn; body.add(cape);
  cape.position.set(0, 1.78, -0.27);
  const TOP_W = 0.78, BOT_W = 1.3, LEN = 1.75;
  function capeUpdate(t, w, turn) {
    const pos = capeGeo.attributes.position;
    for (let i = 0; i < pos.count; i++) {
      const u = base[i * 3], v = base[i * 3 + 1];            // u in [-.5,.5], v in [-.5,.5]
      const f = 0.5 - v;                                     // 0 at shoulders, 1 at hem
      const width = TOP_W + (BOT_W - TOP_W) * f;
      const x = u * width;
      const sway = Math.sin(t * 6 - f * 3.2 + u * 2) * 0.05 * w + Math.sin(t * 1.7 - f * 2 + u) * 0.025;
      const z = -(0.02 + f * 0.1) - f * f * (0.2 + w * 0.5) * 1.0 + sway * f * 1.6 - u * u * 0.12 * f;
      const y = -f * LEN + Math.abs(u) * 0.05 * f * f;
      pos.setXYZ(i, x + turn * f * f * 0.3, y, z);
    }
    pos.needsUpdate = true; capeGeo.computeVertexNormals();
  }
  capeUpdate(0, 0, 0);
  // gold clasps joining cape to pauldrons + chain
  for (const sx of [-1, 1]) P(Cyl(0.08, 0.08, 0.05, 10), mat.gold, sx * 0.4, 1.76, -0.22, null, { r: [Math.PI / 2, 0, 0] });
  P(new THREE.TorusGeometry(0.4, 0.015, 5, 14, Math.PI), mat.gold, 0, 1.76, -0.2, null, { r: [0, 0, Math.PI] });

  root.userData = { body, legL, legR, armL, armR, cape, head, tab, capeUpdate, sword };
  return root;
}
