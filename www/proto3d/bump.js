/* Varnethryl 3D: character bump / stumble system.
   Pure logic (no THREE import) so it can be unit-tested in node. No blocking collisions: only personal-space
   separation for non-fixed actors plus a shove + stumble when someone runs into someone else.
   Caller each frame: set a.x a.z a.vx a.vz a.yaw (world units, m/s), call sys.update(dt), then apply a.dx/a.dz
   (through its own wall collision), multiply the runner's speed by a.slowMul, and call applyPose() after the mixer. */
/* 1.1.7: bumps were far too frequent. Now: only a real head-on sprint (>= RUN_SPEED and within ~37 deg of the contact normal), never inside a group
   (player + party followers share group 'party'), 8 s per pair, 5 s of quiet for both actors afterwards, and a much softer/shorter reaction (SOFT). */
export const COOLDOWN = 8, QUIET = 5, CONTACT_R = 0.45, RUN_SPEED = 4.5, HEAD_ON = 0.8, SOFT = 0.25, DUR_K = 0.6, MAX_ACTORS = 12;
const DEG = Math.PI / 180, TAU = Math.PI * 2, SHOVE_K = 8;
const fin = (v, d) => (typeof v === 'number' && isFinite(v)) ? v : d;
const clamp = (v, a, b) => v < a ? a : v > b ? b : v;
/* bumped: tilt deg, spin deg, hop m (negative = crouch), flail deg, shake deg, head deg, waves, dur s, pm shove multiplier
   runner: tilt deg (forward), hop m, spin deg, flail deg, head deg, slow fraction, slowDur s, dur s, shove multiplier on the one they hit */
const B = (tilt, spin, hop, flail, dur, o) => Object.assign({ tilt, spin, hop, flail, dur, shake: 0, head: 0, waves: 0.5, pm: 1 }, o);
const R = (tilt, hop, spin, flail, slow, slowDur, dur, o) => Object.assign({ tilt, hop, spin, flail, slow, slowDur, dur, head: 0, shove: 1 }, o);
export const STYLES = {
  aldric:    { str: 9,  b: B(8, 0, 0, 0, 0.5, { shake: 2, waves: 0.5, pm: 0.8 }),            r: R(6, 0, 0, 0, 0.10, 0.3, 0.4) },
  elira:     { str: 4,  b: B(12, 25, 0, 20, 0.6),                                            r: R(8, 0.08, 15, 0, 0.20, 0.4, 0.5) },
  thorne:    { str: 3,  b: B(15, 0, 0, 10, 0.8, { waves: 2 }),                               r: R(6, 0, 0, 0, 0.25, 0.5, 0.6, { head: 20 }) },
  nyx:       { str: 5,  b: B(6, 120, -0.15, 0, 0.5),                                         r: R(20, 0, 0, 0, 0.10, 0.25, 0.4) },
  rowan:     { str: 2,  b: B(25, 0, 0.12, 70, 0.9, { waves: 1.5 }),                          r: R(12, 0, 0, 60, 0.35, 0.6, 0.8) },
  seraphine: { str: 8,  b: B(10, 0, 0, 25, 0.5, { pm: 0.75 }),                               r: R(8, 0, 0, 0, 0.12, 0.3, 0.4, { head: 10 }) },
  garruk:    { str: 10, b: B(6, 0, 0, 0, 0.4, { pm: 0.6 }),                                  r: R(12, 0, 0, 40, 0.05, 0.2, 0.35, { shove: 1.5 }) },
  mirelle:   { str: 3,  b: B(14, 0, 0, 25, 0.9, { waves: 2 }),                               r: R(6, 0.06, 40, 0, 0.20, 0.5, 0.6) },
  cedric:    { str: 4,  b: B(10, 200, 0.10, 30, 0.8),                                        r: R(15, 0.06, 0, 0, 0.20, 0.5, 0.6, { waves: 2 }) },
  morwen:    { str: 2,  b: B(18, 0, 0.05, 30, 0.9, { pm: 1.15 }),                            r: R(14, 0, 0, 0, 0.30, 0.5, 0.6) },
  kael:      { str: 3,  b: B(15, 0, 0.07, -10, 0.7),                                         r: R(10, 0, 0, 40, 0.30, 0.5, 0.6) },
  vesper:    { str: 5,  b: B(8, 60, -0.10, 0, 0.4),                                          r: R(10, 0, 0, 0, 0.08, 0.2, 0.35, { head: 40 }) },
  talia:     { str: 3,  b: B(18, 45, 0.15, 35, 0.7),                                         r: R(12, 0.10, 0, 0, 0.25, 0.4, 0.55) },
  orin:      { str: 7,  b: B(10, 0, 0, 15, 0.5),                                             r: R(15, 0.05, 0, 0, 0.12, 0.3, 0.4) },
  selene:    { str: 2,  b: B(12, 0, 0, 30, 0.7, { pm: 1.3 }),                                r: R(10, 0, 0, 25, 0.20, 0.4, 0.5) },
  darius:    { str: 9,  b: B(7, 0, 0, 0, 0.5, { head: 30, pm: 0.8 }),                        r: R(10, 0, 0, 10, 0.05, 0.2, 0.35) },
  finn:      { str: 5,  b: B(5, 90, 0, 20, 0.5),                                             r: R(10, 0.07, 0, 20, 0.10, 0.25, 0.4) },
  brynn:     { str: 4,  b: B(14, 0, 0, 35, 0.8, { shake: 4, waves: 1 }),                     r: R(20, 0.06, 0, 0, 0.30, 0.5, 0.6) },
  asha:      { str: 7,  b: B(6, 30, 0, 20, 0.4, { pm: 0.8 }),                                r: R(10, 0, 90, 0, 0.08, 0.25, 0.35) },
  rook:      { str: 6,  b: B(15, 0, 0.08, 30, 0.7),                                          r: R(15, 0, 0, 30, 0.20, 0.4, 0.5) },
};
export const DEFAULT_STYLE = { str: 5, b: B(12, 0, 0.05, 15, 0.6), r: R(10, 0.04, 0, 10, 0.15, 0.3, 0.45) };
export function styleFor(id) { return STYLES[id] || DEFAULT_STYLE; }

export function makeActor(id, opts) {
  const o = opts || {}, st = styleFor(id);
  return {
    id, style: st, group: o.group || null, quiet: 0, str: fin(o.str, st.str), fixed: !!o.fixed,
    x: 0, z: 0, vx: 0, vz: 0, yaw: 0,
    dx: 0, dz: 0, slowMul: 1,
    svx: 0, svz: 0,
    bT: 0, bDur: 0, bTilt: 0, bdx: 0, bdz: 1, bStr: 1,
    rT: 0, rDur: 0, slowT: 0, slowDur: 0, slowAmt: 0,
    px: 0, pz: 0, ptx: 0, ptz: 0, pyaw: 0, phop: 0, pfl: 0, pfr: 0, phead: 0,
    bumps: 0, bumped: 0,
  };
}

export function createBump(opts) {
  const o = opts || {}, cd = fin(o.cooldown, COOLDOWN), cr = fin(o.contactR, CONTACT_R), runSpeed = fin(o.runSpeed, RUN_SPEED);
  const actors = [], timers = new Float32Array(MAX_ACTORS * MAX_ACTORS);
  const sys = {
    actors, cooldown: cd, runSpeed, events: 0, bumpOn: true,
    add(a) { if (actors.length >= MAX_ACTORS) return null; a.idx = actors.length; actors.push(a); return a; },
    remove(a) { const i = actors.indexOf(a); if (i < 0) return; actors.splice(i, 1); actors.forEach((x, k) => { x.idx = k; }); timers.fill(0); },
    pairTimer(a, b) { return timers[Math.min(a.idx, b.idx) * MAX_ACTORS + Math.max(a.idx, b.idx)]; },
    update(dt) {
      dt = clamp(fin(dt, 0), 0, 0.1);
      const n = actors.length;
      for (let i = 0; i < timers.length; i++) if (timers[i] > 0) timers[i] = Math.max(0, timers[i] - dt);
      for (let i = 0; i < n; i++) {
        const a = actors[i];
        a.x = fin(a.x, 0); a.z = fin(a.z, 0); a.vx = fin(a.vx, 0); a.vz = fin(a.vz, 0); a.yaw = fin(a.yaw, 0);
        a.dx = 0; a.dz = 0;
        a.quiet = Math.max(0, a.quiet - dt); a.bT = Math.max(0, a.bT - dt); a.rT = Math.max(0, a.rT - dt); a.slowT = Math.max(0, a.slowT - dt);
      }
      for (let i = 0; i < n; i++) for (let j = i + 1; j < n; j++) {
        const a = actors[i], b = actors[j];
        let nx = b.x - a.x, nz = b.z - a.z, d = Math.sqrt(nx * nx + nz * nz);
        const min = cr * 2;
        if (d >= min) continue;
        if (d < 1e-5) { nx = Math.sin(i * 2.399 + j); nz = Math.cos(i * 2.399 + j); d = 0; } else { nx /= d; nz /= d; }
        /* personal space: fixed actors (the player) are never moved, others split the overlap */
        const over = min - d, step = Math.min(over, 4 * dt + over * 0.15);
        if (a.fixed && b.fixed) { /* nobody moves */ }
        else if (a.fixed) { b.dx += nx * step; b.dz += nz * step; }
        else if (b.fixed) { a.dx -= nx * step; a.dz -= nz * step; }
        else { a.dx -= nx * step * 0.5; a.dz -= nz * step * 0.5; b.dx += nx * step * 0.5; b.dz += nz * step * 0.5; }
        if (!sys.bumpOn) continue;
        const ti = Math.min(a.idx, b.idx) * MAX_ACTORS + Math.max(a.idx, b.idx);
        if (timers[ti] > 0) continue;
        if (a.group && a.group === b.group) continue;      // party members never bump each other
        if (a.quiet > 0 || b.quiet > 0) continue;          // nobody gets bumped repeatedly
        const ra = Math.max(0, a.vx * nx + a.vz * nz), rb = Math.max(0, -(b.vx * nx + b.vz * nz));
        const ma = Math.hypot(a.vx, a.vz), mb = Math.hypot(b.vx, b.vz);
        const oa = ra >= runSpeed && ra >= HEAD_ON * ma, ob = rb >= runSpeed && rb >= HEAD_ON * mb;   // sprint + head-on only
        if (!oa && !ob) continue;
        if (oa && (!ob || ra >= rb)) bump(a, b, nx, nz, ra); else bump(b, a, -nx, -nz, rb);
        timers[ti] = cd; a.quiet = b.quiet = QUIET; sys.events++;
      }
      for (let i = 0; i < n; i++) {
        const a = actors[i], k = Math.exp(-SHOVE_K * dt);
        a.dx += a.svx * dt; a.dz += a.svz * dt; a.svx *= k; a.svz *= k;
        if (Math.abs(a.svx) < 1e-3) a.svx = 0; if (Math.abs(a.svz) < 1e-3) a.svz = 0;
        a.dx = fin(a.dx, 0); a.dz = fin(a.dz, 0);
        a.slowMul = a.slowT > 0 && a.slowDur > 0 ? clamp(1 - a.slowAmt * (a.slowT / a.slowDur), 0.2, 1) : 1;
        pose(a);
      }
    },
    reset() { timers.fill(0); for (const a of actors) a.quiet = 0; for (const a of actors) { a.bT = a.rT = a.slowT = 0; a.svx = a.svz = 0; a.slowMul = 1; pose(a); } },
  };
  return sys;
}

/* runner a hits bumped b; (nx,nz) is the unit vector a -> b; speed = approach speed */
export function bump(a, b, nx, nz, speed) {
  const rs = a.str, bs = b.str, rst = a.style.r, bst = b.style.b;
  /* sideways: mostly away from the runner, with a sidestep on whichever side b is on */
  const ha = Math.hypot(a.vx, a.vz) || 1, cross = (a.vx / ha) * nz - (a.vz / ha) * nx, side = cross >= 0 ? 1 : -1;
  let sx = nx * 0.6 + (-nz) * side * 0.4, sz = nz * 0.6 + nx * side * 0.4;
  const sl = Math.hypot(sx, sz) || 1; sx /= sl; sz /= sl;
  const power = 0.5 + rs / 10, resist = 0.8 + bs / 20;
  const push = clamp(0.5 * 0.4 * power / resist * bst.pm * rst.shove * clamp(speed / 5, 0.5, 1.2), 0.1, 1.2);
  b.svx += sx * push * SHOVE_K; b.svz += sz * push * SHOVE_K;
  b.bT = b.bDur = bst.dur * DUR_K; b.bTilt = bst.tilt * clamp(0.6 + rs / 10 * 0.8, 0.5, 1.6); b.bdx = sx; b.bdz = sz; b.bStr = clamp(0.6 + rs / 10 * 0.8, 0.5, 1.6); b.bumped++;
  a.rT = a.rDur = rst.dur * DUR_K; a.slowT = a.slowDur = rst.slowDur * DUR_K; a.slowAmt = clamp(rst.slow * 0.4, 0, 0.8); a.bumps++;
}

/* pose in the actor's local frame: ptx pitch (+ = forward), ptz roll, pyaw yaw offset, phop y offset, pfl/pfr arm swing (rad), phead head yaw (rad) */
function pose(a) {
  let tx = 0, tz = 0, yaw = 0, hop = 0, fl = 0, fr = 0, head = 0;
  if (a.bT > 0 && a.bDur > 0) {
    const s = a.style.b, p = 1 - a.bT / a.bDur, env = Math.sin(Math.PI * p), wob = Math.sin(TAU * s.waves * p) * (1 - p);
    const sy = Math.sin(a.yaw), cy = Math.cos(a.yaw), fw = a.bdx * sy + a.bdz * cy, rt = a.bdx * cy - a.bdz * sy;
    const L = (a.bTilt || 0) * DEG * wob;
    tx += L * fw; tz -= L * rt;
    yaw += s.spin * DEG * env * (rt >= 0 ? 1 : -1);
    hop += s.hop * env;
    const fw2 = Math.sin(TAU * 3 * p) * (1 - p) * s.flail * DEG;
    fl += fw2; fr -= fw2; head += s.head * DEG * env * (rt >= 0 ? 1 : -1);
    if (s.shake) tz += Math.sin(TAU * 4 * p) * (1 - p) * s.shake * DEG;
  }
  if (a.rT > 0 && a.rDur > 0) {
    const s = a.style.r, p = 1 - a.rT / a.rDur, env = Math.sin(Math.PI * p);
    tx += s.tilt * DEG * env; hop += s.hop * env; yaw += s.spin * DEG * env;
    const f = Math.sin(TAU * 2 * p) * (1 - p) * s.flail * DEG; fl += f; fr += f * 0.7; head += s.head * DEG * env;
    tz += Math.sin(TAU * 2 * p) * (1 - p) * 6 * DEG;
  }
  a.ptx = fin(tx * SOFT, 0); a.ptz = fin(tz * SOFT, 0); a.pyaw = fin(yaw * SOFT, 0); a.phop = fin(hop * SOFT, 0); a.pfl = fin(fl * SOFT, 0); a.pfr = fin(fr * SOFT, 0); a.phead = fin(head * SOFT, 0);
}

/* ---- applying to a model (works with mergeRigidParts: the nodes are the skeleton bones, so offsets show on the skinned mesh) ---- */
const NODE_NAMES = ['upperArm_L', 'upperArm_R', 'head'];
export function findNodes(root) {
  const out = { root, list: [], q: [] };
  if (!root) return out;
  root.traverse(o => { if (o.name && NODE_NAMES.indexOf(o.name) >= 0 && !o.isMesh && !out[o.name]) out[o.name] = o; });
  for (const n of NODE_NAMES) if (out[n]) { out.list.push(out[n]); out.q.push({ x: 0, y: 0, z: 0, w: 1 }); }
  out.dirty = false;
  return out;
}
/* call BEFORE mixer.update (applyPose runs AFTER it) (or any animation write) so offsets never accumulate on nodes the clips do not drive */
export function restoreNodes(nd) {
  if (!nd || !nd.dirty) return;
  for (let i = 0; i < nd.list.length; i++) { const q = nd.list[i].quaternion, s = nd.q[i]; q.x = s.x; q.y = s.y; q.z = s.z; q.w = s.w; }
  nd.dirty = false;
}
function rotAxis(q, saved, ax, ang) {
  saved.x = q.x; saved.y = q.y; saved.z = q.z; saved.w = q.w;
  const h = ang * 0.5, s = Math.sin(h), c = Math.cos(h), ox = ax === 0 ? s : 0, oy = ax === 1 ? s : 0, oz = ax === 2 ? s : 0;
  const x = q.x, y = q.y, z = q.z, w = q.w;
  q.x = x * c + w * ox + y * oz - z * oy; q.y = y * c + w * oy + z * ox - x * oz; q.z = z * c + w * oz + x * oy - y * ox; q.w = w * c - x * ox - y * oy - z * oz;
}
/* root: the hero group (rotation.order must be 'YXZ'); baseY/yaw are what the caller already set */
export function applyPose(a, root, nd, yaw, baseY = 0) {
  if (!root) return;
  if (root.rotation.order !== 'YXZ') root.rotation.order = 'YXZ';
  root.rotation.x = a.ptx; root.rotation.z = a.ptz; root.rotation.y = fin(yaw, 0) + a.pyaw; root.position.y = baseY + fin(a.phop, 0);
  if (!nd || !nd.list.length) return;
  if (a.pfl === 0 && a.pfr === 0 && a.phead === 0) return;
  nd.dirty = true;
  for (let i = 0; i < nd.list.length; i++) {
    const n = nd.list[i], nm = n.name;
    if (nm === 'upperArm_L') rotAxis(n.quaternion, nd.q[i], 0, a.pfl);
    else if (nm === 'upperArm_R') rotAxis(n.quaternion, nd.q[i], 0, a.pfr);
    else if (nm === 'head') rotAxis(n.quaternion, nd.q[i], 1, a.phead);
  }
}
