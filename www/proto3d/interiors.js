// Walk-in buildings: hollow walls with a real door gap, furnished interior, roof/walls cut away when the hero is inside.
import * as THREE from './vendor/three.module.js';

const plank = (() => { let t; return () => t || (t = (() => { const c = document.createElement('canvas'); c.width = c.height = 128; const g = c.getContext('2d'); for (let i = 0; i < 8; i++) { g.fillStyle = `hsl(28,${35 + (i % 3) * 5}%,${34 + (i * 7) % 12}%)`; g.fillRect(0, i * 16, 128, 15); g.fillStyle = '#0003'; g.fillRect(0, i * 16 + 15, 128, 1); } const x = new THREE.CanvasTexture(c); x.colorSpace = THREE.SRGBColorSpace; x.wrapS = x.wrapT = THREE.RepeatWrapping; return x; })()); })();

export function makeEnterable(ctx, c) {
  const { scene, mats, colliders } = ctx, { id, cx, cz, w, d, h } = c, T = 0.4, DW = 2.0;
  const L = (color, o) => new THREE.MeshLambertMaterial(Object.assign({ color }, o));
  const I = {
    wood: L(0x6b4a2b), woodD: L(0x4a3220), rug: L(0x8a2a2a), rug2: L(0x2a4a8a), stone: L(0x7d828b), fire: new THREE.MeshBasicMaterial({ color: 0xff8a2a }),
    iron: L(0x3a3d44), metal: L(0x9aa0aa), cloth: L(0x2c4fa0), white: L(0xe8e2d0), gold: L(0xd8aa3a, { emissive: 0x302000 }), bottle: L(0x4a9a6a), red: L(0xb5452f),
  };
  const group = new THREE.Group(); group.position.set(cx, 0, cz); scene.add(group);
  const ms = []; // all meshes get keep so the static merge ignores them
  const add = (geo, m, x, y, z, parent, shadow = true) => { const me = new THREE.Mesh(geo, m); me.position.set(x, y, z); me.castShadow = shadow; me.receiveShadow = true; me.userData.keep = true; (parent || group).add(me); return me; };
  const col = (lx, lz, bw, bd) => colliders.push({ type: 'box', minX: cx + lx - bw / 2, maxX: cx + lx + bw / 2, minZ: cz + lz - bd / 2, maxZ: cz + lz + bd / 2, interior: id });
  const ccol = (lx, lz, r) => colliders.push({ type: 'circle', x: cx + lx, z: cz + lz, r, interior: id });
  const B = (x, y, z) => new THREE.BoxGeometry(x, y, z), Cy = (a, b, hh, s = 12) => new THREE.CylinderGeometry(a, b, hh, s);

  // walls (own material so it can go see-through)
  const wallMat = (c.wall || mats.wall).clone(); const walls = new THREE.Group(); group.add(walls);
  const wall = (bw, bh, bd, x, y, z) => { const m = add(B(bw, bh, bd), wallMat, x, y, z, walls); ms.push(m); return m; };
  wall(w, h, T, 0, h / 2, -d / 2 + T / 2); col(0, -d / 2 + T / 2, w, T);
  wall(T, h, d, -w / 2 + T / 2, h / 2, 0); col(-w / 2 + T / 2, 0, T, d);
  wall(T, h, d, w / 2 - T / 2, h / 2, 0); col(w / 2 - T / 2, 0, T, d);
  const fw = (w - DW) / 2;
  for (const sx of [-1, 1]) { wall(fw, h, T, sx * (DW / 2 + fw / 2), h / 2, d / 2 - T / 2); col(sx * (DW / 2 + fw / 2), d / 2 - T / 2, fw, T); }
  wall(DW, h - 2.4, T, 0, 2.4 + (h - 2.4) / 2, d / 2 - T / 2);                        // lintel (no collider: door is open)
  const frameG = new THREE.Group(); group.add(frameG);
  for (const sx of [-1, 1]) add(B(0.2, 2.4, 0.5), mats.wood, sx * (DW / 2 + 0.1), 1.2, d / 2 - T / 2, frameG);   // door frame (hidden while inside)
  add(B(DW + 0.4, 0.2, 0.5), mats.wood, 0, 2.5, d / 2 - T / 2, frameG);
  add(B(DW + 0.6, 0.12, 0.9), mats.stoneD || I.stone, 0, 0.06, d / 2 + 0.2, group);   // doorstep
  const leaf = add(B(1.0, 2.3, 0.1), mats.door, -DW / 2 + 0.05, 1.15, d / 2 - T - 0.5, group); leaf.rotation.y = Math.PI / 2;  // open door
  for (const sx of [-1, 1]) add(B(1, 1, 0.12), mats.glass, sx * (DW / 2 + fw / 2), h * 0.58, d / 2 + 0.02, group, false);
  for (const sx of [-1, 1]) add(B(0.28, h, 0.28), mats.wood, sx * (w / 2), h / 2, d / 2, group);
  if (c.sign) { add(B(1.7, 0.7, 0.1), mats.gold, 0, h * 0.86, d / 2 + 0.2, group); }
  // floor + rug
  const fm = L(0xffffff, { map: plank().clone() }); fm.map.repeat.set(w / 3, d / 3); fm.map.needsUpdate = true;
  add(B(w - T * 2, 0.06, d - T * 2), fm, 0, 0.03, 0, group, false);
  add(B(Math.min(4, w - 3), 0.02, Math.min(3, d - 3)), c.rug2 ? I.rug2 : I.rug, 0, 0.07, 0.5, group, false);
  // roof (hidden when inside)
  const roofG = new THREE.Group(); group.add(roofG); const rh = c.roofH || 3.4;
  const roof = add(new THREE.ConeGeometry(1, rh, 4), c.roof || mats.roofR, 0, h + rh / 2, 0, roofG); roof.rotation.y = Math.PI / 4; roof.scale.set(w * 0.78, 1, d * 0.78);
  add(B(0.9, 2.6, 0.9), mats.stoneD, w * 0.25, h + 1.6, -d * 0.2, roofG);

  // ---------- furniture ----------
  const iw = w / 2 - T, id_ = d / 2 - T;
  const table = (x, z, r = 0.6) => { add(Cy(r, r, 0.08, 14), I.wood, x, 0.85, z); add(Cy(0.08, 0.1, 0.8, 8), I.woodD, x, 0.42, z); ccol(x, z, r + 0.1); for (const a of [0, 2.1, 4.2]) { add(Cy(0.18, 0.18, 0.4, 8), I.woodD, x + Math.cos(a) * (r + 0.5), 0.2, z + Math.sin(a) * (r + 0.5)); } add(Cy(0.08, 0.08, 0.16, 6), I.bottle, x + 0.2, 0.97, z); };
  const barrel = (x, z) => { add(Cy(0.38, 0.38, 0.85, 10), I.wood, x, 0.43, z); add(Cy(0.4, 0.4, 0.06, 10), I.iron, x, 0.3, z); add(Cy(0.4, 0.4, 0.06, 10), I.iron, x, 0.6, z); ccol(x, z, 0.45); };
  const box = (bw, bh, bd, x, z, m = I.wood, y0 = 0) => { add(B(bw, bh, bd), m, x, y0 + bh / 2, z); col(x, z, bw, bd); };
  const hearth = (x, z, rot) => { // rot: wall side -1 left wall, 1 right, 0 back
    const g = new THREE.Group(); g.position.set(x, 0, z); g.rotation.y = rot; group.add(g);
    add(B(1.9, 2.4, 0.8), I.stone, 0, 1.2, 0, g); add(B(1.0, 0.9, 0.5), I.fire, 0, 0.6, 0.18, g, false); add(B(0.5, 0.3, 0.3), I.red, 0.1, 0.3, 0.2, g, false); add(B(0.5, 1.4, 0.8), I.stone, 0, 3.0 - 0.1, -0.1, g);
    if (rot === 0) col(x, z, 1.9, 0.8); else col(x, z, 0.8, 1.9);
  };
  const bed = (x, z) => { box(1.2, 0.45, 2.2, x, z, I.woodD); add(B(1.1, 0.2, 2.0), I.white, x, 0.55, z); add(B(1.1, 0.12, 1.2), I.cloth, x, 0.68, z + 0.45); add(B(0.9, 0.15, 0.4), I.white, x, 0.7, z - 0.8); };
  const shelf = (x, z, sw = 2.2) => { box(sw, 2.2, 0.45, x, z, I.woodD); for (let i = 0; i < 3; i++) for (let j = 0; j < 4; j++) add(Cy(0.07, 0.07, 0.2, 6), [I.bottle, I.red, I.cloth, I.gold][(i + j) % 4], x - sw / 2 + 0.3 + j * (sw - 0.6) / 3, 0.55 + i * 0.6 + 0.1, z + 0.1, group, false); };
  const banner = (x, z, ry = 0) => { const m = add(B(1.1, 2.2, 0.06), I.cloth, x, h * 0.62, z); m.rotation.y = ry; add(B(0.5, 0.5, 0.07), I.gold, x, h * 0.62, z + (ry ? 0 : 0.01)).rotation.y = ry; };
  if (c.interior === 'inn') {
    box(3.6, 1.0, 0.8, 1.8, -id_ + 1.2, I.woodD); add(B(3.8, 0.1, 1.0), I.wood, 1.8, 1.05, -id_ + 1.2); shelf(1.8, -id_ + 0.35, 3.0);
    for (let i = 0; i < 3; i++) add(Cy(0.1, 0.1, 0.16, 8), I.metal, 0.6 + i * 0.7, 1.18, -id_ + 1.2);
    table(-1.8, 0.4); table(-0.6, 2.0); barrel(iw - 0.5, -0.4); barrel(iw - 0.5, 0.6); hearth(-iw + 0.4, -0.8, Math.PI / 2); banner(-0.6, -id_ + 0.2);
  } else if (c.interior === 'smith') {
    box(1.6, 1.0, 1.2, iw - 1.2, -id_ + 0.8, I.stone); add(B(1.1, 0.12, 0.8), I.fire, iw - 1.2, 1.02, -id_ + 0.8, group, false); add(B(0.5, 1.8, 0.5), I.stone, iw - 1.2, 1.9, -id_ + 0.5);
    box(0.7, 0.55, 0.45, -0.3, 0.2, I.iron); add(B(1.1, 0.22, 0.4), I.iron, -0.3, 0.66, 0.2); add(new THREE.ConeGeometry(0.14, 0.35, 6), I.iron, 0.4, 0.66, 0.2, group).rotation.z = -Math.PI / 2;
    for (let i = 0; i < 5; i++) add(B(0.06, 1.5, 0.06), I.metal, -iw + 1.2 + i * 0.6, 1.5, -id_ + 0.3, group, false).rotation.z = 0.05 * (i - 2);
    box(2.2, 0.9, 0.7, -1.2, -id_ + 0.6, I.woodD); barrel(-iw + 0.5, 1.4); barrel(-iw + 1.1, 1.8); barrel(iw - 0.5, 1.8);
  } else if (c.interior === 'hall') {
    box(5.6, 0.9, 1.1, 0, -0.3, I.wood); for (const sx of [-1, 1]) for (const sz of [-1, 1]) add(Cy(0.2, 0.2, 0.5, 8), I.woodD, sx * 1.6, 0.25, -0.3 + sz * 1.0);
    box(0.9, 1.8, 0.8, 0, -id_ + 0.7, I.woodD); add(B(0.8, 0.3, 0.7), I.red, 0, 0.95, -id_ + 0.7);
    banner(-3.8, -id_ + 0.2); banner(3.8, -id_ + 0.2); banner(-1.9, -id_ + 0.2); banner(1.9, -id_ + 0.2);
    hearth(iw - 0.4, 0.8, -Math.PI / 2); barrel(-iw + 0.6, id_ - 0.6);
  } else { // house
    bed(-iw + 1.0, -id_ + 1.3); table(1.0, 0.2, 0.55); hearth(0, -id_ + 0.4, 0); shelf(iw - 0.5, 0.3, 1.8);
  }

  // cutaway: roof off + walls see-through + walls stop casting shadows while the hero is inside
  let inside = false;
  const setInside = v => {
    inside = v; roofG.visible = !v; frameG.visible = !v; wallMat.transparent = v; wallMat.opacity = v ? 0.22 : 1; wallMat.depthWrite = !v; wallMat.needsUpdate = true;
    for (const m of ms) m.castShadow = !v;
  };
  return {
    id, group, get inside() { return inside; },
    update(hx, hz) { const v = Math.abs(hx - cx) < w / 2 - T * 0.5 && Math.abs(hz - cz) < d / 2 - T * 0.5; if (v !== inside) setInside(v); return v; },
    door: { x: cx, z: cz + d / 2 },
  };
}
