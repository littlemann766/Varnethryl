// Procedural "warrior king" sprint for the Mixamo-rigged Owner (native units, model 1.70 tall, faces +Z).
import * as THREE from 'three';
export const P = {
  v: 6.08,        // native ground speed (m/s) = game run speed 9.67 world / mscale 1.592
  T: 0.60,        // full cycle (2 steps) => 200 steps/min
  duty: 0.17,     // stance fraction per foot
  toeFront: 0.27, // toe touchdown, z ahead of hips
  hipY: 0.905,    // hips height at mid-stance
  bounce: 0.05,  // extra hips height at mid-flight
  lean: 9,        // whole-trunk forward lean, deg
  chestUp: 4,     // chest/upper-spine extension back toward upright, deg
  pelvisYaw: 7, chestYaw: 9,
  kneeLiftY: 0.36, kneeLiftZ: 0.36, // swing ankle apex in front (high knee)
  heelKickY: 0.56, heelKickZ: -0.26, // ankle tucked behind under the butt
  armDown: 84, armFwd: 38, armBack: 40, elbowFwd: 74, elbowBack: 62,
  N: 37,
};
const D = Math.PI / 180, X = new THREE.Vector3(1, 0, 0), Y = new THREE.Vector3(0, 1, 0), Zv = new THREE.Vector3(0, 0, 1);
const qa = (ax, deg) => new THREE.Quaternion().setFromAxisAngle(ax, deg * D);
const smooth = (a, b, t) => { t = Math.min(1, Math.max(0, t)); t = t * t * (3 - 2 * t); return a + (b - a) * t; };
// periodic Hermite through keys [phase, value, slope|null]
function curve(keys, ph) {
  const k = keys.slice().sort((a, b) => a[0] - b[0]), n = k.length;
  ph = ((ph % 1) + 1) % 1;
  let i = n - 1; for (let j = 0; j < n; j++) if (k[j][0] <= ph) i = j;
  const a = k[i], b = k[(i + 1) % n], p0 = a[0], p1 = b[0] + (i === n - 1 ? 1 : 0), dp = p1 - p0;
  const pp = ph < p0 ? ph + 1 : ph, t = (pp - p0) / dp;
  const sl = (j) => { const c = k[j]; if (c[2] != null) return c[2]; const pv = k[(j - 1 + n) % n], nx = k[(j + 1) % n]; let d0 = c[0] - pv[0]; if (d0 <= 0) d0 += 1; let d1 = nx[0] - c[0]; if (d1 <= 0) d1 += 1; return (nx[1] - pv[1]) / (d0 + d1); };
  const m0 = sl(i) * dp, m1 = sl((i + 1) % n) * dp, t2 = t * t, t3 = t2 * t;
  return (2 * t3 - 3 * t2 + 1) * a[1] + (t3 - 2 * t2 + t) * m0 + (-2 * t3 + 3 * t2) * b[1] + (t3 - t2) * m1;
}
export const PW = { walk: true, name: 'Walking', v: 2.0, T: 0.857, duty: 0.53, heelFront: 0.30, hipY: 0.895, bounce: 0.018, midSS: 0.29,
  lean: 3, chestUp: 3, pelvisYaw: 5, chestYaw: 6, armDown: 86, armFwd: 22, armBack: 20, elbowFwd: 32, elbowBack: 14, armPh: 0.25,
  curl: [22, 30, 18], N: 41,
  fp: [[0, -16, null], [0.12, 0, 0], [0.30, 0, 0], [0.53, 40, null], [0.62, 30, null], [0.78, 0, null], [0.94, -14, null]],
  swing: [[0.64, 0.25, -0.40], [0.80, 0.20, 0.0], [0.93, 0.17, 0.27]] };
export function buildRun(scene, bones, p = P) {
  const b = n => bones['mixamorig' + n];
  scene.updateMatrixWorld(true);
  const bindL = {}, bindW = {}, bindPos = {}; const names = Object.keys(bones);
  for (const n of names) { bindL[n] = bones[n].quaternion.clone(); bindPos[n] = bones[n].position.clone(); bindW[n] = bones[n].getWorldQuaternion(new THREE.Quaternion()); }
  const wp = n => b(n).getWorldPosition(new THREE.Vector3());
  const restW = {}; for (const n of ['Hips', 'LeftUpLeg', 'LeftLeg', 'LeftFoot', 'LeftToeBase', 'RightUpLeg', 'RightLeg', 'RightFoot', 'RightToeBase']) restW[n] = wp(n);
  const L = s => ({ th: restW[s + 'UpLeg'].distanceTo(restW[s + 'Leg']), sh: restW[s + 'Leg'].distanceTo(restW[s + 'Foot']), toe: restW[s + 'ToeBase'].clone().sub(restW[s + 'Foot']), thDir: restW[s + 'Leg'].clone().sub(restW[s + 'UpLeg']).normalize(), shDir: restW[s + 'Foot'].clone().sub(restW[s + 'Leg']).normalize() });
  const LEG = { Left: L('Left'), Right: L('Right') };
  const toeY = restW.LeftToeBase.y;
  const order = []; b('Hips').traverse(o => { if (o.isBone) order.push(o); });
  const FING = []; for (const sd of ['Left', 'Right']) for (const f of ['Index', 'Middle', 'Ring', 'Pinky']) for (let k = 1; k <= 3; k++) FING.push(sd + 'Hand' + f + k);
  const keyN = [...FING, 'Hips', 'Spine', 'Spine1', 'Spine2', 'Neck', 'Head', 'LeftShoulder', 'RightShoulder', 'LeftArm', 'RightArm', 'LeftForeArm', 'RightForeArm', 'LeftHand', 'RightHand', 'LeftUpLeg', 'RightUpLeg', 'LeftLeg', 'RightLeg', 'LeftFoot', 'RightFoot', 'LeftToeBase', 'RightToeBase'];
  const setW = (n, deltaW) => { // bone world rot = deltaW * bindWorld
    const bo = b(n), want = deltaW.clone().multiply(bindW['mixamorig' + n]);
    bo.parent.updateMatrixWorld(true); const pq = bo.parent.getWorldQuaternion(new THREE.Quaternion());
    bo.quaternion.copy(pq.invert().multiply(want)); bo.updateMatrixWorld(true);
  };
  const v = p.v, T = p.T, stanceLen = v * p.duty * T, toeBack = p.toeFront - stanceLen;
  // foot pitch over own-leg phase (0 = touchdown): + = plantarflex (heel up)
  const footPitch = ph => curve(p.fp || [[0, 8, null], [p.duty * 0.45, 0, null], [p.duty, 48, null], [0.32, 60, null], [0.62, 5, null], [0.86, -12, null]], ph);
  const ankleOf = (toe, phi) => toe.clone().sub(LEG.Left.toe.clone().setX(0).applyQuaternion(qa(X, phi)));
  const ALL = order.map(o => o.name);
  const tracks = {}; for (const n of ALL) tracks[n] = [];
  const hipsPos = [];
  const times = [];
  const legSample = (side, ph, hipJoint) => {
    // ph: own-leg phase; returns {ankle, phi}
    const phi = footPitch(ph);
    if (p.walk) {
      const dH = new THREE.Vector3(0, -0.105, -0.06), dB = LEG.Left.toe.clone().setX(0);
      const st = (q) => { const ph_ = footPitch(q), hz = p.heelFront - v * q * T, H = new THREE.Vector3(0, 0.03, hz), Bp = new THREE.Vector3(0, 0.03 + dB.y - dH.y, hz + dB.z - dH.z);
        return { ankle: ph_ < 0 ? H.clone().sub(dH.clone().applyQuaternion(qa(X, ph_))) : Bp.clone().sub(dB.clone().applyQuaternion(qa(X, ph_))), phi: ph_ }; };
      if (ph < p.duty) return { ...st(ph), stance: true };
      const e = 0.002, A0 = st(p.duty).ankle, A0b = st(p.duty - e).ankle, A1 = st(0).ankle, A1b = st(e).ankle; // A1 at next touchdown
      const s0z = (A0.z - A0b.z) / e, s0y = (A0.y - A0b.y) / e, s1z = (A1b.z - A1.z) / e, s1y = (A1b.y - A1.y) / e;
      const kz = [[p.duty, A0.z, s0z], ...p.swing.map(k => [k[0], k[2], null]), [1.0, A1.z, s1z]];
      const ky = [[p.duty, A0.y, s0y], ...p.swing.map(k => [k[0], k[1], null]), [1.0, A1.y, s1y]];
      const ev = (keys) => { let i = 0; while (i < keys.length - 2 && ph > keys[i + 1][0]) i++; const a = keys[i], c = keys[i + 1], dp = c[0] - a[0], t = (ph - a[0]) / dp;
        const sl = j => keys[j][2] != null ? keys[j][2] : (keys[j + 1][1] - keys[j - 1][1]) / (keys[j + 1][0] - keys[j - 1][0]);
        const m0 = sl(i) * dp, m1 = sl(i + 1) * dp, t2 = t * t, t3 = t2 * t; return (2 * t3 - 3 * t2 + 1) * a[1] + (t3 - 2 * t2 + t) * m0 + (-2 * t3 + 3 * t2) * c[1] + (t3 - t2) * m1; };
      return { ankle: new THREE.Vector3(0, ev(ky), ev(kz)), phi, stance: false };
    }
    if (ph < p.duty) { // stance: toe locked to ground, moving back at v relative to body
      const z = p.toeFront - v * ph * T;
      return { ankle: ankleOf(new THREE.Vector3(0, toeY, z), phi), phi, stance: true };
    }
    // swing: ankle body-relative path (y absolute, z rel to hips)
    const A0 = ankleOf(new THREE.Vector3(0, toeY, toeBack), footPitch(p.duty)), A1 = ankleOf(new THREE.Vector3(0, toeY, p.toeFront), footPitch(0));
    const dphi = 0.002, Ap = ankleOf(new THREE.Vector3(0, toeY, toeBack - v * dphi * T), footPitch(p.duty + dphi)); // continue stance slope
    const s0z = (Ap.z - A0.z) / dphi, s0y = (Ap.y - A0.y) / dphi;
    const A1b = ankleOf(new THREE.Vector3(0, toeY, p.toeFront + v * dphi * T), footPitch(1 - dphi));
    const s1z = (A1.z - A1b.z) / dphi, s1y = (A1.y - A1b.y) / dphi;
    const kz = [[p.duty, A0.z, s0z], [0.38, p.heelKickZ, null], [0.66, p.kneeLiftZ, null], [0.86, p.toeFront - 0.02, null], [1.0, A1.z, s1z]];
    const ky = [[p.duty, A0.y, s0y], [0.38, p.heelKickY, null], [0.66, p.kneeLiftY, null], [0.86, A1.y + 0.10, null], [1.0, A1.y, s1y]];
    // non-periodic hermite over [duty,1]
    const ev = (keys) => { let i = 0; while (i < keys.length - 2 && ph > keys[i + 1][0]) i++; const a = keys[i], c = keys[i + 1], dp = c[0] - a[0], t = (ph - a[0]) / dp;
      const sl = j => keys[j][2] != null ? keys[j][2] : (keys[j + 1][1] - keys[j - 1][1]) / (keys[j + 1][0] - keys[j - 1][0]);
      const m0 = sl(i) * dp, m1 = sl(i + 1) * dp, t2 = t * t, t3 = t2 * t; return (2 * t3 - 3 * t2 + 1) * a[1] + (t3 - 2 * t2 + t) * m0 + (-2 * t3 + 3 * t2) * c[1] + (t3 - t2) * m1; };
    return { ankle: new THREE.Vector3(0, ev(ky), ev(kz)), phi, stance: false };
  };
  for (let f = 0; f < p.N; f++) {
    const t = f / (p.N - 1) * T, ph = t / T; times.push(t);
    for (let i = 0; i < order.length; i++) { const n = order[i].name; order[i].quaternion.copy(bindL[n]); order[i].position.copy(bindPos[n]); }
    // hips: lowest at mid-stance of each foot (ph=duty/2 and 0.5+duty/2), peak mid-flight
    const sp = ph - p.duty / 2; const bounceW = 0.5 - 0.5 * Math.cos(4 * Math.PI * sp);
    const hy = p.walk ? p.hipY + p.bounce * Math.cos(4 * Math.PI * (ph - p.midSS)) : p.hipY + p.bounce * bounceW;
    const yawP = p.pelvisYaw * Math.sin(2 * Math.PI * (ph + 0.25 - p.duty / 2)); // left leg forward -> pelvis yawed right-side-forward
    const yawC = -p.chestYaw / p.pelvisYaw * yawP;
    const roll = 3 * Math.sin(4 * Math.PI * sp + Math.PI / 2) * 0;
    const lean = p.lean + (p.walk ? 0.5 : 1.5) * Math.cos(4 * Math.PI * sp);
    // hips world position
    const hb = b('Hips'); hb.parent.updateMatrixWorld(true);
    const wpos = new THREE.Vector3(restW.Hips.x + (p.walk ? 0.018 * Math.sin(2 * Math.PI * (ph - p.midSS + 0.25)) : 0), hy, restW.Hips.z);
    hb.position.copy(hb.parent.worldToLocal(wpos.clone())); hb.updateMatrixWorld(true);
    const Rp = qa(Y, yawP).multiply(qa(X, lean * 0.6));
    setW('Hips', Rp);
    const sY = [yawP + (yawC - yawP) * 0.35, yawP + (yawC - yawP) * 0.7, yawC];
    const sX = [lean * 0.75, lean * 0.85 - p.chestUp * 0.4, lean - p.chestUp];
    ['Spine', 'Spine1', 'Spine2'].forEach((n, i) => setW(n, qa(Y, sY[i]).multiply(qa(X, sX[i]))));
    setW('Neck', qa(Y, yawC * 0.5).multiply(qa(X, lean * 0.3)));
    setW('Head', qa(Y, yawC * 0.1).multiply(qa(X, -2)));
    const Rc = qa(Y, yawC).multiply(qa(X, sX[2]));
    setW('LeftShoulder', Rc.clone()); setW('RightShoulder', Rc.clone());
    for (const [side, sgn, off] of [['Left', 1, 0], ['Right', -1, 0.5]]) {
      const lp = ((ph - off) % 1 + 1) % 1; // own-leg phase
      const hj = b(side + 'UpLeg').getWorldPosition(new THREE.Vector3());
      const s = legSample(side, lp, hj);
      const A = s.ankle.clone(); A.x = hj.x + (side === 'Left' ? 0.01 : -0.01) + (restW[side + 'Foot'].x - restW[side + 'UpLeg'].x) * 0.6;
      // 2-bone IK, knee pole forward
      const Lg = LEG[side], d = A.clone().sub(hj); let dl = d.length(); const maxL = (Lg.th + Lg.sh) * 0.999; if (dl > maxL) { d.setLength(maxL); A.copy(hj).add(d); dl = maxL; }
      const cosA = (Lg.th * Lg.th + dl * dl - Lg.sh * Lg.sh) / (2 * Lg.th * dl), ang = Math.acos(Math.min(1, Math.max(-1, cosA)));
      const dn = d.clone().normalize(); const pole = new THREE.Vector3(0.05 * sgn, 0, 1).applyQuaternion(qa(Y, yawP)); const side_ = new THREE.Vector3().crossVectors(dn, pole).normalize(); const up = new THREE.Vector3().crossVectors(side_, dn).normalize();
      const K = hj.clone().add(dn.clone().multiplyScalar(Math.cos(ang) * Lg.th)).add(up.multiplyScalar(Math.sin(ang) * Lg.th));
      const thigh = K.clone().sub(hj).normalize();
      const Ry = qa(Y, yawP);
      const Rth = new THREE.Quaternion().setFromUnitVectors(Lg.thDir.clone().applyQuaternion(Ry), thigh).multiply(Ry);
      setW(side + 'UpLeg', Rth);
      const shin = A.clone().sub(K).normalize();
      const Rsh = new THREE.Quaternion().setFromUnitVectors(Lg.shDir.clone().applyQuaternion(Rth), shin).multiply(Rth);
      setW(side + 'Leg', Rsh);
      setW(side + 'Foot', qa(Y, yawP * 0.5).multiply(qa(X, s.phi)));
      setW(side + 'ToeBase', qa(Y, yawP * 0.5).multiply(qa(X, s.stance ? Math.min(0, s.phi) : Math.min(s.phi, 20) * 0.3)));
      // arms: opposite to own leg -> arm phase = other leg
      const ap = Math.sin(2 * Math.PI * (lp + (p.armPh ?? 0.30))); // +1 when this leg is forward
      const swing = ap > 0 ? ap * p.armBack : ap * p.armFwd; // this leg fwd -> this arm back (+ = back)
      const elbow = ap > 0 ? p.elbowBack + (p.elbowFwd - p.elbowBack) * 0 : p.elbowBack + (p.elbowFwd - p.elbowBack) * (-ap);
      const Rarm = Rc.clone().multiply(qa(X, swing)).multiply(qa(Zv, -sgn * p.armDown)).multiply(qa(Y, 0)).multiply(qa(Zv, 0));
      const inward = qa(Y, -sgn * 8);
      setW(side + 'Arm', Rc.clone().multiply(inward).multiply(qa(X, swing)).multiply(qa(Zv, -sgn * p.armDown)));
      setW(side + 'ForeArm', Rc.clone().multiply(inward).multiply(qa(X, swing - elbow)).multiply(qa(Zv, -sgn * (p.armDown - 6))).multiply(qa(X, 0)));
      const Rh = Rc.clone().multiply(inward).multiply(qa(X, swing - elbow + 10)).multiply(qa(Zv, -sgn * (p.armDown - 6)));
      setW(side + 'Hand', Rh);
      for (const f of ['Index', 'Middle', 'Ring', 'Pinky']) { let c = 0; (p.curl || [62, 85, 55]).forEach((ang, k) => { c += ang; const n = side + 'Hand' + f + (k + 1); if (b(n)) setW(n, Rh.clone().multiply(qa(Zv, -sgn * c))); }); }
    }
    for (const n of ALL) tracks[n].push(...bones[n].quaternion.toArray());
    hipsPos.push(...b('Hips').position.toArray());
  }
  // restore bind
  for (const o of order) { o.quaternion.copy(bindL[o.name]); o.position.copy(bindPos[o.name]); }
  const kt = [new THREE.VectorKeyframeTrack('mixamorigHips.position', times, hipsPos)];
  for (const n of ALL) kt.push(new THREE.QuaternionKeyframeTrack(n + '.quaternion', times, tracks[n]));
  return { clip: new THREE.AnimationClip(p.name || 'Running', T, kt), raw: { times, hipsPos, tracks } };
}
