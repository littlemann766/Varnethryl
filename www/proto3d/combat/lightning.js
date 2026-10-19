/* Owner second ultimate - "Thunderstorm" lightning VFX (visual only; damage is done by CombatController via DamageCalculator).
   Procedural bolts: recursive midpoint displacement with forks that decay; jitter is regenerated ~every 45 ms into pooled Float32 buffers (no per-frame allocation);
   bright white core + coloured glow (two additive LineSegments per bolt + glow Points on the joints); chain arcs between conductive targets with falloff;
   ground scorch + sparks that fall with gravity; screen flash + small shake via the DOM (no extra scene lights, so no shader recompiles). Modular: needs only THREE + scene. */
const MAXSEG = 220, POOL = 7, SPARKS = 160, SCORCH = 6;
export class LightningFX {
  constructor(o) {
    this.T = o.THREE; this.scene = o.scene; this.HS = o.HS || 1.5; this.canvas = o.canvas || null; this.rng = o.rng || Math.random;
    const T = this.T; this.group = new T.Group(); this.group.name = 'lightningFX'; this.group.visible = false; this.scene.add(this.group);
    const mk = (color, op) => new T.LineBasicMaterial({ color, transparent: true, opacity: op, blending: T.AdditiveBlending, depthWrite: false });
    this.bolts = []; for (let i = 0; i < POOL; i++) {
      const pos = new Float32Array(MAXSEG * 6), g = new T.BufferGeometry(); const at = new T.BufferAttribute(pos, 3); at.setUsage(T.DynamicDrawUsage); g.setAttribute('position', at); g.setDrawRange(0, 0);
      const core = new T.LineSegments(g, mk(0xffffff, 1)), glow = new T.LineSegments(g, mk(0x6fb8ff, 0.55)); glow.scale.setScalar(1.0); core.frustumCulled = glow.frustumCulled = false;
      const jp = new Float32Array(MAXSEG * 3), jg = new T.BufferGeometry(); const ja = new T.BufferAttribute(jp, 3); ja.setUsage(T.DynamicDrawUsage); jg.setAttribute('position', ja); jg.setDrawRange(0, 0);
      const halo = new T.Points(jg, new T.PointsMaterial({ color: 0x9fd0ff, size: 0.3 * this.HS, transparent: true, opacity: 0.5, blending: T.AdditiveBlending, depthWrite: false, sizeAttenuation: true })); halo.frustumCulled = false;
      this.group.add(glow, core, halo); core.visible = glow.visible = halo.visible = false;
      this.bolts.push({ core, glow, halo, pos, at, g, jp, ja, jg, n: 0, nj: 0, life: 0, max: 0, a: [0, 0, 0], b: [0, 0, 0], amp: 1, forks: 0, acc: 0, busy: false, delay: 0 });
    }
    const sp = new Float32Array(SPARKS * 3), sg = new T.BufferGeometry(); this.spA = new T.BufferAttribute(sp, 3); this.spA.setUsage(T.DynamicDrawUsage); sg.setAttribute('position', this.spA); sg.setDrawRange(0, SPARKS);
    this.sp = sp; this.sv = new Float32Array(SPARKS * 3); this.sl = new Float32Array(SPARKS); this.sp.fill(-9999);
    this.sparks = new T.Points(sg, new T.PointsMaterial({ color: 0xffe9a0, size: 0.18 * this.HS, transparent: true, opacity: 1, blending: T.AdditiveBlending, depthWrite: false })); this.sparks.frustumCulled = false; this.group.add(this.sparks);
    this.scorch = []; const sgeo = new T.CircleGeometry(1, 20); for (let i = 0; i < SCORCH; i++) { const m = new T.Mesh(sgeo, new T.MeshBasicMaterial({ color: 0x0a0c14, transparent: true, opacity: 0, depthWrite: false })); m.rotation.x = -Math.PI / 2; m.visible = false; this.group.add(m);
      const r = new T.Mesh(new T.RingGeometry(0.6, 1, 24), new T.MeshBasicMaterial({ color: 0xbfe0ff, transparent: true, opacity: 0, blending: T.AdditiveBlending, depthWrite: false, side: T.DoubleSide })); r.rotation.x = -Math.PI / 2; r.visible = false; this.group.add(r); this.scorch.push({ m, r, t: 9, x: 0, z: 0, s: 1 }); }
    this.sIdx = 0; this.scIdx = 0; this.flash = 0; this.shake = 0; this.shT = 0; this.queue = []; this.clock = 0;
    if (typeof document !== 'undefined') { const d = document.createElement('div'); d.style.cssText = 'position:fixed;inset:0;pointer-events:none;z-index:6;background:#cfe6ff;opacity:0;mix-blend-mode:screen'; d.id = 'lightningFlash'; document.body.appendChild(d); this.flashEl = d; }
    this._lastOp = -1; this._lastTf = '';
  }
  r(a = 1) { return (this.rng() - 0.5) * 2 * a; }
  /* recursive midpoint displacement: writes segments into bolt.pos, returns new count. Forks (smaller, decaying) branch off the midpoint with probability p. */
  jag(b, ax, ay, az, bx, by, bz, amp, depth, forkP) {
    if (b.n >= MAXSEG - 2) return;
    if (depth <= 0) { const i = b.n * 6, p = b.pos; p[i] = ax; p[i + 1] = ay; p[i + 2] = az; p[i + 3] = bx; p[i + 4] = by; p[i + 5] = bz; b.n++; return; }
    const mx = (ax + bx) / 2 + this.r(amp), my = (ay + by) / 2 + this.r(amp * 0.6), mz = (az + bz) / 2 + this.r(amp);
    this.jag(b, ax, ay, az, mx, my, mz, amp * 0.55, depth - 1, forkP); this.jag(b, mx, my, mz, bx, by, bz, amp * 0.55, depth - 1, forkP);
    if (depth >= 2 && b.forks < 5 && this.rng() < forkP) {   // fork: heads roughly the same way (gravity-ward / toward the conductor) but sprawls sideways, shorter and thinner
      b.forks++; const dx = bx - ax, dy = by - ay, dz = bz - az, L = 0.55 + this.rng() * 0.35;
      this.jag(b, mx, my, mz, mx + dx * L + this.r(amp * 2.2), my + dy * L - Math.abs(this.r(amp)), mz + dz * L + this.r(amp * 2.2), amp * 0.5, depth - 2, forkP * 0.5);
    }
  }
  rebuild(b) {
    b.n = 0; b.forks = 0; const [ax, ay, az] = b.a, [bx, by, bz] = b.b, L = Math.hypot(bx - ax, by - ay, bz - az);
    this.jag(b, ax, ay, az, bx, by, bz, Math.min(2.4, L * 0.09 * b.amp), L > 12 ? 6 : 5, b.fork);
    b.at.needsUpdate = true; b.g.setDrawRange(0, b.n * 2);
    // glow joints: sample every 3rd segment end
    let k = 0; for (let i = 0; i < b.n && k < MAXSEG; i += 3) { b.jp[k * 3] = b.pos[i * 6 + 3]; b.jp[k * 3 + 1] = b.pos[i * 6 + 4]; b.jp[k * 3 + 2] = b.pos[i * 6 + 5]; k++; }
    b.ja.needsUpdate = true; b.jg.setDrawRange(0, k);
  }
  spawnBolt(a, bx, by, bz, life, amp, fork, delay, str) {
    const b = this.bolts.find(q => !q.busy) || this.bolts.reduce((m, q) => q.life < m.life ? q : m, this.bolts[0]);
    b.busy = true; b.a[0] = a[0]; b.a[1] = a[1]; b.a[2] = a[2]; b.b[0] = bx; b.b[1] = by; b.b[2] = bz; b.life = b.max = life; b.amp = amp; b.fork = fork; b.acc = 99; b.delay = delay || 0; b.str = str || 1;
    b.core.visible = b.glow.visible = b.halo.visible = delay <= 0; if (delay <= 0) this.rebuild(b); return b;
  }
  sparksAt(x, y, z, n, v) { for (let i = 0; i < n; i++) { const k = this.sIdx = (this.sIdx + 1) % SPARKS, a = this.rng() * 6.283, h = this.rng() * v; this.sp[k * 3] = x; this.sp[k * 3 + 1] = y; this.sp[k * 3 + 2] = z; this.sv[k * 3] = Math.cos(a) * h; this.sv[k * 3 + 1] = 2 + this.rng() * v * 1.3; this.sv[k * 3 + 2] = Math.sin(a) * h; this.sl[k] = 0.5 + this.rng() * 0.6; } }
  scorchAt(x, z, s) { const c = this.scorch[this.scIdx = (this.scIdx + 1) % SCORCH]; c.t = 0; c.x = x; c.z = z; c.s = s; c.m.position.set(x, 0.03, z); c.r.position.set(x, 0.05, z); c.m.visible = c.r.visible = true; }
  /* ev: { from:{x,z}, path:[{x,z,y,falloff}], big } - first path point is struck from the sky, the rest are arcs conductor to conductor (decaying) */
  strike(ev) {
    const HS = this.HS, path = ev.path || []; if (!path.length) return; this.group.visible = true; let prev = null, d = 0;
    for (let i = 0; i < path.length; i++) {
      const p = path[i], f = p.falloff === undefined ? 1 : p.falloff, y = p.y === undefined ? 1.1 * HS : p.y;
      if (i === 0) {
        this.spawnBolt([p.x + this.r(3 * HS), 26 * HS, p.z + this.r(3 * HS)], p.x, y, p.z, 0.42, 1.25, 0.55, 0, 1);
        this.spawnBolt([p.x + this.r(2 * HS), 24 * HS, p.z + this.r(2 * HS)], p.x, y, p.z, 0.3, 1.0, 0.35, 0.03, 0.8);   // twin, staggered re-strike
        this.flash = 1; this.shake = 0.9; this.impact(p.x, p.z, 1.6 * f, y);
      } else {
        const dl = d += 0.09; this.spawnBolt([prev.x, (prev.y === undefined ? 1.1 * HS : prev.y), prev.z], p.x, y, p.z, 0.3 * (0.6 + 0.4 * f), 0.8, 0.3, dl, f);
        this.queue.push({ t: this.clock + dl, x: p.x, z: p.z, y, f });
      }
      prev = p;
    }
  }
  impact(x, z, s, y) { this.sparksAt(x, (y || 1) * 0.5, z, 22, 5.5); this.scorchAt(x, z, s * this.HS * 0.45); }
  update(dt) {
    this.clock += dt; if (!this.group.visible) return;
    let live = 0;
    for (const b of this.bolts) {
      if (!b.busy) continue; live++;
      if (b.delay > 0) { b.delay -= dt; if (b.delay > 0) continue; b.core.visible = b.glow.visible = b.halo.visible = true; this.rebuild(b); b.acc = 0; }
      b.life -= dt; if (b.life <= 0) { b.busy = false; b.core.visible = b.glow.visible = b.halo.visible = false; continue; }
      b.acc += dt; if (b.acc > 0.045) { b.acc = 0; this.rebuild(b); }   // per-frame-ish jitter
      const k = b.life / b.max, flick = 0.55 + 0.45 * this.rng(), fade = Math.min(1, k * 2.2);
      b.core.material.opacity = Math.min(1, flick * fade * b.str * 1.2); b.glow.material.opacity = 0.6 * flick * fade * b.str; b.halo.material.opacity = 0.5 * fade * b.str * (0.6 + 0.4 * flick);
    }
    for (let i = this.queue.length - 1; i >= 0; i--) { const q = this.queue[i]; if (q.t <= this.clock) { this.impact(q.x, q.z, 0.8 * q.f, q.y); this.shake = Math.max(this.shake, 0.35 * q.f); this.flash = Math.max(this.flash, 0.35 * q.f); this.queue.splice(i, 1); } }
    let anySp = false; for (let k = 0; k < SPARKS; k++) { if (this.sl[k] <= 0) continue; this.sl[k] -= dt; if (this.sl[k] <= 0) { this.sp[k * 3 + 1] = -9999; continue; } anySp = true;
      this.sv[k * 3 + 1] -= 18 * dt; const i3 = k * 3; this.sp[i3] += this.sv[i3] * dt; this.sp[i3 + 1] += this.sv[i3 + 1] * dt; this.sp[i3 + 2] += this.sv[i3 + 2] * dt;
      if (this.sp[i3 + 1] < 0.03) { this.sp[i3 + 1] = 0.03; this.sv[i3 + 1] *= -0.35; this.sv[i3] *= 0.6; this.sv[i3 + 2] *= 0.6; } }   // gravity, bounce, friction
    if (anySp) this.spA.needsUpdate = true;
    let anySc = false; for (const c of this.scorch) { if (c.t >= 2.2) continue; anySc = true; c.t += dt; const u = c.t / 2.2; if (u >= 1) { c.m.visible = c.r.visible = false; continue; }
      c.m.scale.setScalar(c.s * (0.7 + 0.3 * Math.min(1, c.t * 6))); c.m.material.opacity = 0.55 * (1 - u); c.r.scale.setScalar(c.s * (0.5 + 2.4 * Math.min(1, c.t * 3.5))); c.r.material.opacity = Math.max(0, 0.9 * (1 - c.t * 3)); }
    this.flash = Math.max(0, this.flash - dt * 5.5); this.shake = Math.max(0, this.shake - dt * 3.2); this.shT += dt * 70;
    if (this.flashEl) { const op = +(this.flash * 0.5).toFixed(2); if (op !== this._lastOp) { this.flashEl.style.opacity = op; this._lastOp = op; } }
    if (this.canvas) { const s = this.shake * this.shake * 5, tf = s > 0.05 ? `translate(${(Math.sin(this.shT) * s).toFixed(1)}px,${(Math.cos(this.shT * 1.3) * s).toFixed(1)}px)` : ''; if (tf !== this._lastTf) { this.canvas.style.transform = tf; this._lastTf = tf; } }
    if (!live && !anySp && !anySc && !this.queue.length && this.flash <= 0) this.group.visible = false;
  }
  dispose() { this.scene.remove(this.group); if (this.flashEl) this.flashEl.remove(); if (this.canvas) this.canvas.style.transform = ''; }
}
