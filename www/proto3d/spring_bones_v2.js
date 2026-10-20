// spring_bones_v2.js - cloth-aware secondary motion for the VARNETHRYL rigs (three.js ES module). Superset of spring_bones_sm.js.
//   import {SpringBones, loadClothConfig} from './spring_bones_v2.js';
//   const cfg = await loadClothConfig('./neris_cl.cloth.json');            // optional; without it behaviour == spring_bones_sm.js
//   const sb = new SpringBones(gltf.scene, {clips: gltf.animations, config: cfg});
//   loop: mixer.update(dt); sb.update(dt);          // after the mixer, before render
//   Construct SpringBones while the skeleton is still in its rest pose (right after load, before the first mixer.update).
//   sb.reset() after teleports / clip changes if you want a clean start; sb.enabled=false to freeze.
// Config (per model, *.cloth.json):
//   groups[]   : {name, kind, match:'regex on bone name', enabled:false => rigid (fur/skin/armor/props),
//                 stiffness (pull to the animated pose per 1/60s step, 0..1), damping (velocity kept per step), gravity (units/step^2),
//                 inertia (0..1: how much of the *character's own motion* the cloth lags behind; <1 follows the body more),
//                 maxSwing (rad, per bone; number or array indexed by chain depth), maxChain (rad, cumulative along the chain; stops hems flaring),
//                 maxVel (units/step cap on velocity; stops snaps on stop/start), smooth (0..1 low-pass of the final rotation, 1 = none),
//                 collide (bool), margin (extra clearance), exclude:[collider names]}
//   colliders[]: capsules {name,a,b,ra,rb, pad} between two bone *heads* (radius ra at a, rb at b), world-space, move with the skeleton.
// Backward compatible: sb.colliders (sphere {bone,radius,offset}) still works; old FAMILIES apply to any bone no group matches when no config is given.
import * as THREE from 'three';
export const FAMILIES = [
  {re:/^cape\d*$/,stiff:0.35,drag:0.72,grav:0.00030},{re:/^quiver\d*$/,stiff:0.35,drag:0.72,grav:0.00025},{re:/^quiver_arrows$/,stiff:0.35,drag:0.72,grav:0.00020},
  {re:/^cloth_/,stiff:0.35,drag:0.72,grav:0.00040},{re:/^coat\d?_[LR]$/,stiff:0.35,drag:0.72,grav:0.00030},{re:/^hair[LRC]?\d*(_|$)/,stiff:0.35,drag:0.72,grav:0.00030},
  {re:/^(hood|hood2)$/,stiff:0.35,drag:0.72,grav:0.00020},{re:/^tail\d*$/,stiff:0.45,drag:0.65,grav:0.00020},{re:/^mane\d*$/,stiff:0.35,drag:0.72,grav:0.00030},
  {re:/^ear\d?_[LR]$/,stiff:0.35,drag:0.72,grav:0.00015},{re:/^(fluke\d?|finHip\d?)_[LR]$/,stiff:0.35,drag:0.72,grav:0.00005},
  {re:/^(scarf|sleeve|belt|pouch|strap|tabard|skirt|wing\d)\w*$/,stiff:0.35,drag:0.72,grav:0.00030},
];
export async function loadClothConfig(url){ const r=await fetch(url); if(!r.ok) throw new Error('cloth config '+url+' '+r.status); return r.json(); }
const MAXA=0.28,SMOOTH=0.5;
const _q3=new THREE.Quaternion(),_q4=new THREE.Quaternion(),_v3=new THREE.Vector3(),_v=new THREE.Vector3(),_v2=new THREE.Vector3(),_q=new THREE.Quaternion(),_q2=new THREE.Quaternion();
const _a=new THREE.Vector3(),_b=new THREE.Vector3(),_ab=new THREE.Vector3(),_p=new THREE.Vector3(),_c=new THREE.Vector3();
export class SpringBones {
  constructor(root, opts={}) {
    this.enabled = opts.enabled !== false; this.wind = new THREE.Vector3(); this.colliders = []; this.acc = 0; this.step = 1/60;
    this.config = opts.config || null; this.items = []; this.byName = new Map(); this.capsules = [];
    const cfg = this.config;
    const groups = cfg ? (cfg.groups||[]).map(g=>Object.assign({re:new RegExp(g.match)},g)) : null;
    this.families = opts.families || FAMILIES;
    const animated = new Set(); (opts.clips||[]).forEach(c=>c.tracks.forEach(t=>{ if (t.name.endsWith('.quaternion')) animated.add(t.name.slice(0,-11)); }));
    const bones=[]; root.traverse(o=>{ if (o.isBone) bones.push(o); });
    const serpent = bones.some(b=>/^body\d+$/.test(b.name));
    const legacy = b => { const f=this.families.find(f=>f.re.test(b.name)); if(!f||(serpent&&f.re.source.startsWith('^tail'))) return null;
      return {stiff:f.stiff,drag:f.drag,grav:f.grav,inertia:1,maxSwing:MAXA,maxChain:1e9,maxVel:1e9,maxCollide:0,smooth:SMOOTH,collide:false,margin:0,exclude:[]}; };
    const gp = b => { for (const g of groups) if (g.re.test(b.name)) { if (g.enabled===false) return null;
        const d=(()=>{let n=0,p=b.parent;while(p&&p.isBone&&g.re.test(p.name)){n++;p=p.parent}return n})();
        const ms=Array.isArray(g.maxSwing)?g.maxSwing[Math.min(d,g.maxSwing.length-1)]:(g.maxSwing??MAXA);
        return {stiff:g.stiffness??0.35,drag:g.damping??0.72,grav:g.gravity??0.0003,inertia:g.inertia??1,maxSwing:ms,maxChain:g.maxChain??1e9,maxVel:g.maxVel??1e9,maxCollide:g.maxCollide??0.8,pushRate:g.pushRate??0.7,smooth:g.smooth??SMOOTH,collide:!!g.collide,margin:g.margin??0,exclude:g.exclude||[],group:g.name}; }
      return null; };
    const match = cfg ? gp : legacy;
    root.updateMatrixWorld(true);
    for (const b of bones) {
      const fam = match(b); if (!fam) continue;
      const kids = b.children.filter(c=>c.isBone && match(c));
      let child = kids[0] || null, localDir, len;
      if (child) { localDir = child.position.clone(); len = localDir.length(); localDir.normalize(); }
      else { localDir = (b.position.lengthSq()>1e-9 ? b.position.clone().normalize() : new THREE.Vector3(0,-1,0)); len = Math.max(b.position.length(), 0.08); }
      const it = { bone:b, fam, localDir, len, restQ:b.quaternion.clone(), animated:animated.has(b.name), cur:new THREE.Vector3(), prev:new THREE.Vector3(), lastTgt:new THREE.Vector3(), depth:0, parentItem:null, cum:0 };
      let p=b; while (p.parent) { it.depth++; p=p.parent; }
      this.items.push(it); this.byName.set(b.name, it);
    }
    this.items.sort((a,b)=>a.depth-b.depth);
    for (const it of this.items) { let p=it.bone.parent; while (p && !this.byName.has(p.name)) p=p.parent; it.parentItem = p? this.byName.get(p.name):null; if(it.parentItem&&it.parentItem.bone!==it.bone.parent) it.parentItem=null; }
    if (cfg) for (const c of (cfg.colliders||[])) { const A=bones.find(b=>b.name===c.a),B=bones.find(b=>b.name===c.b); if(A&&B) this.capsules.push({name:c.name||c.a,a:A,b:B,ra:c.ra,rb:c.rb??c.ra,pad:c.pad||0,offA:c.offA?new THREE.Vector3(...c.offA):null,offB:c.offB?new THREE.Vector3(...c.offB):null}); }
    // rest-aware collision radii: never start inside a capsule (shrink per bone/capsule so the rest pose has zero penetration)
    root.updateMatrixWorld(true); this._caps();
    for (const it of this.items) { it.shrink=new Float32Array(this.capsules.length); if(!it.fam.collide) continue; const tail=this._target(it,new THREE.Vector3()); const head=new THREE.Vector3().setFromMatrixPosition(it.bone.matrixWorld); const mid=head.clone().add(tail).multiplyScalar(0.5);
      this.capsules.forEach((c,ci)=>{ let worst=0; for (const P of [tail,mid,head]) { _ab.subVectors(c.pb,c.pa); const t=Math.max(0,Math.min(1,_p.subVectors(P,c.pa).dot(_ab)/(_ab.lengthSq()||1e-9))); _c.copy(c.pa).addScaledVector(_ab,t); const r=c.ra+(c.rb-c.ra)*t+c.pad+it.fam.margin; const d=P.distanceTo(_c); if (d<r) worst=Math.max(worst,r-d+0.004); } it.shrink[ci]=worst; }); }
    this.reset();
  }
  _target(it, out) { const b=it.bone; b.updateWorldMatrix(true,false); _v.copy(it.localDir).multiplyScalar(it.len); return out.copy(_v).applyMatrix4(b.matrixWorld); }
  reset() { this.acc = 0; for (const it of this.items) it.qs=null; for (const it of this.items) { if (!it.animated) it.bone.quaternion.copy(it.restQ); } this.items.forEach(it=>{ this._target(it, it.cur); it.prev.copy(it.cur); it.lastTgt.copy(it.cur); }); }
  disable() { this.enabled=false; for (const it of this.items) if (!it.animated) it.bone.quaternion.copy(it.restQ); }
  update(dt) {
    if (!this.enabled) return;
    this.acc += Math.min(dt, 0.1); let n=0;
    for (const it of this.items) it.q0 = it.animated ? it.bone.quaternion.clone() : it.restQ;
    while (this.acc >= this.step && n++<4) { this.acc -= this.step; this._sub(); }
    // Do not leave the previous frame's simulated cape pose in place when the
    // render frame is shorter than a physics step. The mixer has just restored
    // the authored pose; blend the cached cloth result back in consistently.
    if (!n) for (const it of this.items) if (it.qs) { it.bone.quaternion.copy(it.qs); it.bone.updateWorldMatrix(false,true); }
  }
  _caps() { // world-space capsule endpoints for this step
    for (const c of this.capsules) { c.a.getWorldPosition(c.pa||(c.pa=new THREE.Vector3())); c.b.getWorldPosition(c.pb||(c.pb=new THREE.Vector3()));
      if (c.offA) c.pa.add(c.offA.clone().applyQuaternion(c.a.getWorldQuaternion(_q))); if (c.offB) c.pb.add(c.offB.clone().applyQuaternion(c.b.getWorldQuaternion(_q))); }
  }
  _push(P, fam, shrink) { // push point P out of every capsule; returns true if moved
    let moved=false;
    for (let ci=0; ci<this.capsules.length; ci++) { const c=this.capsules[ci]; if (fam.exclude.length && fam.exclude.includes(c.name)) continue;
      _ab.subVectors(c.pb,c.pa); const l2=_ab.lengthSq()||1e-9; const t=Math.max(0,Math.min(1,_p.subVectors(P,c.pa).dot(_ab)/l2));
      _c.copy(c.pa).addScaledVector(_ab,t); const r=c.ra+(c.rb-c.ra)*t+c.pad+fam.margin-(shrink?shrink[ci]:0); const d=P.distanceTo(_c);
      if (d<r) { if (d<1e-6) _p.set(0,0,1); else _p.subVectors(P,_c).multiplyScalar(1/d); P.addScaledVector(_p,(r-d)*(fam.pushRate??1)); moved=true; } }
    return moved;
  }
  _sub() {
    const hasCaps=this.capsules.length>0; if (hasCaps) this._caps();
    for (const it of this.items) {
      const b=it.bone, f=it.fam;
      b.quaternion.copy(it.q0||it.restQ); b.updateWorldMatrix(true,false);
      const head=_v2.setFromMatrixPosition(b.matrixWorld);
      const tgt=this._target(it, new THREE.Vector3());
      const tdel=tgt.clone().sub(it.lastTgt); it.lastTgt.copy(tgt);
      if (tdel.lengthSq()>1) { it.cur.copy(tgt); it.prev.copy(tgt); } // teleport
      const vel=_v.copy(it.cur).sub(it.prev).multiplyScalar(f.drag);
      if (f.inertia<1) vel.addScaledVector(tdel, 1-f.inertia);
      const vl=vel.length(); if (vl>f.maxVel) vel.multiplyScalar(f.maxVel/vl);
      const next=it.cur.clone().add(vel).addScaledVector(tgt.sub(it.cur),f.stiff);
      next.y -= f.grav; next.addScaledVector(this.wind, 0.0001);
      for (const c of this.colliders) { c.bone.getWorldPosition(_v); if (c.offset) _v.add(c.offset); const d=next.distanceTo(_v); if (d<c.radius) next.sub(_v).multiplyScalar(c.radius/(d||1e-6)).add(_v); }
      const sc=b.matrixWorld.getMaxScaleOnAxis(); const L=it.len*sc;
      const hold=it.hold||(it.hold=new THREE.Quaternion());
      // 1) dynamics only: fixed length, aim, clamp swing (per bone + cumulative along the chain)
      next.sub(head); { const l=next.length()||1e-6; next.multiplyScalar(L/l).add(head); }
      const aim=(pt,limit)=>{ _v.copy(pt).sub(head).normalize(); b.parent.getWorldQuaternion(_q).invert(); _v.applyQuaternion(_q);
        const q0=_q3.copy(it.q0||it.restQ); _v3.copy(it.localDir).applyQuaternion(q0); _q2.setFromUnitVectors(_v3,_v);
        let ang=2*Math.acos(Math.min(1,Math.abs(_q2.w)));
        if (ang>limit) { if (limit<1e-5) _q2.set(0,0,0,1); else _q2.slerpQuaternions(_q4.identity(), _q2, limit/ang); ang=Math.min(ang,limit); }
        _q2.multiply(q0); hold.copy(_q2); return ang; };
      const pc=it.parentItem?it.parentItem.cum:0, lim=Math.max(0,Math.min(f.maxSwing, f.maxChain-pc));
      let ang=aim(next,lim); const dyn=next.clone(); let delta=null;
      // 2) collisions act on the clamped pose and may exceed the dynamic limit (up to maxCollide), so legs/body always win over the swing clamp
      if (hasCaps&&f.collide) {
        b.quaternion.copy(hold); b.updateWorldMatrix(false,false); this._target(it,next); const pre=next.clone();
        for (let k=0;k<2;k++) { _a.copy(head).add(next).multiplyScalar(0.5); const m0=_a.clone(); if (this._push(_a,f,it.shrink)) next.addScaledVector(_a.sub(m0),2); this._push(next,f,it.shrink);
          next.sub(head); const l=next.length()||1e-6; next.multiplyScalar(L/l).add(head); }
        delta=next.clone().sub(pre); ang=aim(next,Math.max(lim,f.maxCollide));
      }
      it.prev.copy(it.cur); it.cur.copy(dyn); if (delta) it.cur.add(delta);
      it.cum=pc+ang;
      if (!it.qs) it.qs=hold.clone(); else it.qs.slerp(hold, f.smooth);
      b.quaternion.copy(it.qs);
      b.updateWorldMatrix(false,true);
    }
  }
}
export default SpringBones;
