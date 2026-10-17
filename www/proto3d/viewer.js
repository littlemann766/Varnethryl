import * as THREE from 'three';
import { GLTFLoader } from './vendor/jsm/loaders/GLTFLoader.js';
export const ORDER = ['aldric', 'darius', 'selene', 'seraphine', 'talia', 'finn', 'brynn', 'mirelle', 'nyx', 'vesper', 'thorne', 'orin', 'elira'];
export const LABEL = { aldric: 'Sir Aldric', darius: 'Darius Umbral', selene: 'Selene Frostveil', seraphine: 'Dame Seraphine', talia: 'Talia Stormcall', finn: 'Finn Valecourt', brynn: 'Brynn Cogwright', mirelle: 'Mirelle Thornroot', nyx: 'Nyx Varrin', vesper: 'Vesper Crowe', thorne: 'Brother Thorne', orin: 'Orin Ashlance', elira: 'Lady Elira' };
const qs = new URLSearchParams(location.search);
const R = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true }); R.setPixelRatio(Math.min(devicePixelRatio, 2)); R.setSize(innerWidth, innerHeight); R.shadowMap.enabled = true; R.toneMapping = THREE.ACESFilmicToneMapping; R.outputColorSpace = THREE.SRGBColorSpace; document.body.appendChild(R.domElement);
const scene = new THREE.Scene(); scene.background = new THREE.Color(0x2b2733); scene.fog = new THREE.Fog(0x2b2733, 6, 14);
const cam = new THREE.PerspectiveCamera(32, innerWidth / innerHeight, .1, 50);
scene.add(new THREE.HemisphereLight(0xffffff, 0x6a5a55, 2.2));
const key = new THREE.DirectionalLight(0xfff0d8, 2.6); key.position.set(2.5, 4, 3); key.castShadow = true; key.shadow.mapSize.set(2048, 2048); key.shadow.bias = -0.0008; key.shadow.normalBias = 0.03; Object.assign(key.shadow.camera, { left: -2, right: 2, top: 3, bottom: -1, near: .5, far: 12 }); scene.add(key);
const rim = new THREE.DirectionalLight(0xfff4e8, 2.2); rim.position.set(-3, 3, -4); scene.add(rim); const fill = new THREE.DirectionalLight(0xffffff, 1.2); fill.position.set(-3, 1.5, 3); scene.add(fill);
const floor = new THREE.Mesh(new THREE.CircleGeometry(1.1, 40), new THREE.MeshStandardMaterial({ color: 0x3a3340, roughness: 1 })); floor.rotation.x = -Math.PI / 2; floor.receiveShadow = true; scene.add(floor);
const loader = new GLTFLoader(); let cur, mixer, state = { id: qs.get('c') || 'aldric', anim: qs.get('anim') || 'idle', yaw: +(qs.get('yaw') || 0), spin: qs.get('spin') !== '0', dist: +(qs.get('d') || 3.7) }; const clock = new THREE.Clock();
export function load(id) { return new Promise(res => loader.load('models/' + id + '.glb', g => { if (cur) scene.remove(cur); cur = g.scene; cur.traverse(o => { if (o.isMesh) o.castShadow = true; }); scene.add(cur); window.__clips = g.animations; mixer = new THREE.AnimationMixer(cur); state.id = id; play(state.anim); if (qs.get('tt')) mixer.setTime(+qs.get('tt')); mark(); res(g); })); }
function play(n) { state.anim = n; mixer.stopAllAction(); const cl = (window.__clips || []).find(c => c.name === n); if (cl) mixer.clipAction(cl).play(); mark(); }
const bar = document.getElementById('bar'); function mark() { bar.querySelectorAll('button').forEach(b => b.classList.toggle('on', b.dataset.k === state.id || b.dataset.k === state.anim || (b.dataset.k === 'spin' && state.spin))); }
if (!qs.get('bare')) { for (const id of ORDER) { const b = document.createElement('button'); b.textContent = LABEL[id]; b.dataset.k = id; b.onclick = () => load(id); bar.appendChild(b); }
  for (const a of ['idle', 'walk']) { const b = document.createElement('button'); b.textContent = '▶ ' + a; b.dataset.k = a; b.onclick = () => play(a); bar.appendChild(b); }
  const sp = document.createElement('button'); sp.textContent = '⟳ spin'; sp.dataset.k = 'spin'; sp.onclick = () => { state.spin = !state.spin; mark(); }; bar.appendChild(sp); } else bar.style.display = 'none', document.getElementById('info').style.display = 'none';
let drag = false, lx = 0; R.domElement.onpointerdown = e => { drag = true; lx = e.clientX; state.spin = false; mark(); }; addEventListener('pointerup', () => drag = false); addEventListener('pointermove', e => { if (drag) { state.yaw += (e.clientX - lx) * .01; lx = e.clientX; } });
addEventListener('wheel', e => { state.dist = Math.max(2.2, Math.min(9, state.dist + e.deltaY * .004)); });
addEventListener('resize', () => { R.setSize(innerWidth, innerHeight); cam.aspect = innerWidth / innerHeight; cam.updateProjectionMatrix(); });
function frame() { const dt = clock.getDelta(); if (mixer) mixer.update(qs.get('t') ? 0 : dt); if (state.spin) state.yaw += dt * .6; const d = state.dist; const ly = +(qs.get('ly') || .9); cam.position.set(Math.sin(state.yaw) * d, ly + .3, Math.cos(state.yaw) * d); cam.lookAt(0, ly, 0); R.render(scene, cam); requestAnimationFrame(frame); }
window.__state = state; window.__load = load; window.__play = play; window.__ready = load(state.id).then(() => { frame(); });
