// Standalone viewer for the 3D buildings: ?b=<id>&mode=ext|int|fp&yaw=&pitch=&dist=  (also window.__show for scripted renders)
import * as THREE from 'three';
import { buildVillage, BUILDING_DEFS } from './buildings.js';
const q = new URLSearchParams(location.search);
const renderer = new THREE.WebGLRenderer({ canvas: document.getElementById('c'), antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(1); renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFShadowMap;
const scene = new THREE.Scene(); scene.background = new THREE.Color(q.get('bg') || 0xcfe2ee); scene.fog = new THREE.Fog(0xdde8ee, 70, 160);
scene.add(new THREE.HemisphereLight(0xcfe6ff, 0x6a7a4a, 1.25)); const sun = new THREE.DirectionalLight(0xfff0d0, 2.2); sun.castShadow = true; sun.shadow.mapSize.set(2048, 2048);
Object.assign(sun.shadow.camera, { left: -30, right: 30, top: 30, bottom: -30, near: 1, far: 120 }); sun.shadow.bias = -.0006; sun.shadow.normalBias = .03; scene.add(sun, sun.target);
const ground = new THREE.Mesh(new THREE.PlaneGeometry(400, 400), new THREE.MeshLambertMaterial({ color: 0x5c9a45 })); ground.rotation.x = -Math.PI / 2; ground.receiveShadow = true; scene.add(ground);
const camera = new THREE.PerspectiveCamera(46, 1, .3, 300);
const colliders = []; const ctx = { scene, colliders };
const id = q.get('b'); const list = buildVillage(ctx, id ? id.split(',') : null);
function find(i) { return list.find(b => b.id === i || (b.parts && b.parts.some(p => p.id === i))); }
let curRoot = null;
function sub(b) { return b.parts ? b.parts.find(p => p.id !== 'port_dock' && p.insideTest) || b.parts[0] : b; }
window.__list = list.map(b => b.id); window.__colliders = colliders;
function place(w, h) { renderer.setSize(w, h, false); camera.aspect = w / h; camera.updateProjectionMatrix(); }
window.__size = place;
window.__show = (bid, o = {}) => {
  const b = find(bid), s = sub(b), cx = s.cx, cz = s.cz, rot = s.rot || 0, r = s.radius || Math.max(s.w || 10, s.d || 10);
  list.forEach(x => (x.parts || [x]).forEach(p => { p.root.visible = (p === s) || (x === b); }));
  const inside = !!o.inside; const lp = o.at || [0, 0]; const [wx, wz] = s.toW(lp[0], lp[1]);
  const [ox, oz] = s.toW(0, r + 8); (b.parts || [b]).forEach(p => p.update(inside ? wx : ox, inside ? wz : oz, .016));
  if (o.tick) for (let i = 0; i < o.tick; i++) (b.parts || [b]).forEach(p => p.tick && p.tick(.1));
  const yaw = (o.yaw || 0) + rot, pitch = o.pitch === undefined ? .35 : o.pitch, dist = (o.dist || Math.max(r * 2.9, (s.h || 6) * 2.0));
  const tx = o.target ? s.toW(o.target[0], o.target[1]) : [cx, cz], ty = o.ty === undefined ? (s.h || 6) * .45 : o.ty;
  camera.position.set(tx[0] + Math.sin(yaw) * Math.cos(pitch) * dist, ty + Math.sin(pitch) * dist, tx[1] + Math.cos(yaw) * Math.cos(pitch) * dist); camera.lookAt(tx[0], ty, tx[1]);
  sun.position.set(cx - 18, 30, cz + 14); sun.target.position.set(cx, 0, cz); Object.assign(sun.shadow.camera, { left: -r - 8, right: r + 8, top: r + 8, bottom: -r - 8 }); sun.shadow.camera.updateProjectionMatrix();
  renderer.render(scene, camera); return renderer.info.render.calls;
};
window.__info = bid => { const b = find(bid); let tris = 0, calls = 0, meshes = 0; (b.parts || [b]).forEach(p => p.root.traverse(o => { if (o.isMesh) { meshes++; tris += (o.geometry.index ? o.geometry.index.count : o.geometry.attributes.position.count) / 3; } })); return { meshes, tris: Math.round(tris) }; };
window.__r = bid => { const s = sub(find(bid)); return s.radius || Math.max(s.w || 10, s.d || 10); };
window.__dbg = () => ({ cam: camera.position.toArray(), ch: scene.children.map(c => [c.type, c.visible, c.position.toArray().map(v => +v.toFixed(1))]) });
window.__root = bid => sub(find(bid)).root;
window.__rinfo = () => ({ tri: renderer.info.render.triangles, calls: renderer.info.render.calls, rv: __list.map(i => __root(i).visible), pos: __root('inn').getWorldPosition(new THREE.Vector3()).toArray() });
window.__ready = true;
