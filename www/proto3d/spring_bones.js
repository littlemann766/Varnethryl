// spring_bones.js - tiny runtime cloth / hair / tail secondary-motion module for the VARNETHRYL rigs (three.js, ES module).
// Verlet spring-bone chains driven by body motion. Use alongside baked clips:
//   import {SpringBones} from './spring_bones.js';
//   const sb = new SpringBones(gltf.scene, {clips: gltf.animations});   // finds chains by bone name
//   loop: mixer.update(dt); sb.update(dt);                               // after the mixer
//   sb.enabled = false/true;  sb.reset();  sb.wind.set(x,y,z)
// The baked pose is the *target*: each bone's tail is pulled toward where the animation wants it, with inertia, drag, gravity
// and fixed bone length, then the bone is re-aimed. Collisions: optional sphere colliders via sb.colliders.push({bone,radius,offset}).
import * as THREE from 'three';
export const FAMILIES = [  // regex on bone name -> params. stiff: pull to animated pose (0..1/step), drag: velocity keep (0..1), grav: world units/step^2
  {re:/^cape\d*$/,            stiff:0.10, drag:0.93, grav:0.00030},
  {re:/^quiver\d*$/,          stiff:0.20, drag:0.88, grav:0.00025},
  {re:/^quiver_arrows$/,    stiff:0.14, drag:0.90, grav:0.00020},
  {re:/^cloth_/,              stiff:0.12, drag:0.93, grav:0.00040},
  {re:/^coat\d?_[LR]$/,       stiff:0.16, drag:0.93, grav:0.00030},
  {re:/^hair[LRC]?\d*(_|$)/,        stiff:0.09, drag:0.92, grav:0.00030},
  {re:/^(hood|hood2)$/,       stiff:0.20, drag:0.88, grav:0.00020},
  {re:/^tail\d*$/,            stiff:0.16, drag:0.90, grav:0.00020},
  {re:/^mane\d*$/,            stiff:0.12, drag:0.91, grav:0.00030},
  {re:/^ear\d?_[LR]$/,        stiff:0.22, drag:0.86, grav:0.00015},
  {re:/^(fluke\d?|finHip\d?)_[LR]$/, stiff:0.14, drag:0.92, grav:0.00005},
  {re:/^(scarf|sleeve|belt|pouch|strap|tabard|skirt|wing\d)\w*$/, stiff:0.12, drag:0.90, grav:0.00030},
];
const MAXA=0.85,SMOOTH=0.55,_q3=new THREE.Quaternion(),_v3=new THREE.Vector3(),_v=new THREE.Vector3(),_v2=new THREE.Vector3(),_q=new THREE.Quaternion(),_q2=new THREE.Quaternion(),_m=new THREE.Matrix4();
export class SpringBones {
  constructor(root, opts={}) {
    this.enabled = opts.enabled !== false; this.wind = new THREE.Vector3(); this.colliders = []; this.acc = 0; this.step = 1/60;
    this.families = opts.families || FAMILIES; this.items = []; this.byName = new Map();
    const animated = new Set(); (opts.clips||[]).forEach(c=>c.tracks.forEach(t=>{ if (t.name.endsWith('.quaternion')) animated.add(t.name.slice(0,-11)); }));
    const bones=[]; root.traverse(o=>{ if (o.isBone) bones.push(o); });
    // serpents (body1..N + tail1..N chain): the baked S-wave already carries the whole body head->tail; spring physics on the
    // tail only adds lag/whip ("happy tail" wag), so the tail family is skipped for them.
    const serpent = bones.some(b=>/^body\d+$/.test(b.name));   // body1..N chain = serpent/hydra (neckN optional: Hydrella has multiple heads, no neckN)
    const match = b => { const f=this.families.find(f=>f.re.test(b.name)); return (serpent && f && f.re.source.startsWith('^tail')) ? null : f; };
    root.updateMatrixWorld(true);
    for (const b of bones) {
      const fam = match(b); if (!fam) continue;
      const kids = b.children.filter(c=>c.isBone && match(c));
      let child = kids[0] || null, localDir, len;
      if (child) { localDir = child.position.clone(); len = localDir.length(); localDir.normalize(); }
      else { localDir = (b.position.lengthSq()>1e-9 ? b.position.clone().normalize() : new THREE.Vector3(0,-1,0)); len = Math.max(b.position.length(), 0.08); }
      const it = { bone:b, fam, localDir, len, restQ:b.quaternion.clone(), animated:animated.has(b.name), cur:new THREE.Vector3(), prev:new THREE.Vector3(), depth:0 };
      let p=b; while (p.parent) { it.depth++; p=p.parent; }
      this.items.push(it); this.byName.set(b.name, it);
    }
    this.items.sort((a,b)=>a.depth-b.depth);
    this.reset();
  }
  _target(it, out) { // world position the animation wants for this bone's tail
    const b=it.bone; b.updateWorldMatrix(true,false); _v.copy(it.localDir).multiplyScalar(it.len); return out.copy(_v).applyMatrix4(b.matrixWorld);
  }
  reset() { for (const it of this.items) it.qs=null; for (const it of this.items) { if (!it.animated) it.bone.quaternion.copy(it.restQ); } this.items.forEach(it=>{ this._target(it, it.cur); it.prev.copy(it.cur); }); }
  disable() { this.enabled=false; for (const it of this.items) if (!it.animated) it.bone.quaternion.copy(it.restQ); }
  update(dt) {
    if (!this.enabled) return;
    this.acc += Math.min(dt, 0.1); let n=0;
    for (const it of this.items) it.q0 = it.animated ? it.bone.quaternion.clone() : it.restQ;   // the clip's pose for this frame
    while (this.acc >= this.step && n++<4) { this.acc -= this.step; this._sub(); }
    if (!n) for (const it of this.items) if (it.qs) it.bone.quaternion.copy(it.qs);
  }
  _sub() {
    for (const it of this.items) {
      const b=it.bone;
      b.quaternion.copy(it.q0||it.restQ);
      b.updateWorldMatrix(true,false);
      const head=_v2.setFromMatrixPosition(b.matrixWorld);
      const tgt=this._target(it, new THREE.Vector3());
      const vel=_v.copy(it.cur).sub(it.prev).multiplyScalar(it.fam.drag);
      const next=it.cur.clone().add(vel).addScaledVector(tgt.sub(it.cur),it.fam.stiff);
      next.y -= it.fam.grav; next.addScaledVector(this.wind, 0.0001);
      for (const c of this.colliders) { c.bone.getWorldPosition(_v); if (c.offset) _v.add(c.offset); const d=next.distanceTo(_v); if (d<c.radius) next.sub(_v).multiplyScalar(c.radius/(d||1e-6)).add(_v); }
      // fixed length (world units)
      const sc=b.matrixWorld.getMaxScaleOnAxis(); const L=it.len*sc;
      next.sub(head); const l=next.length()||1e-6; next.multiplyScalar(L/l).add(head);
      it.prev.copy(it.cur); it.cur.copy(next);
      // re-aim bone: world dir -> parent space -> rotation taking localDir to that dir
      _v.copy(next).sub(head).normalize();
      b.parent.getWorldQuaternion(_q).invert(); _v.applyQuaternion(_q);
      // keep the clip's own rotation (roll/twist), add only the physics swing on top, clamp it and low-pass the result (anti-jitter)
      const q0=_q3.copy(b.quaternion); _v3.copy(it.localDir).applyQuaternion(q0);
      _q2.setFromUnitVectors(_v3, _v);
      const ang=2*Math.acos(Math.min(1,Math.abs(_q2.w)));
      if (ang>MAXA) _q2.set(0,0,0,1).slerp(_q2, MAXA/ang);
      _q2.multiply(q0);
      if (!it.qs) it.qs=_q2.clone(); else it.qs.slerp(_q2, SMOOTH);
      b.quaternion.copy(it.qs);
      b.updateWorldMatrix(false,true);
    }
  }
}
