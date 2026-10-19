/* Wilds auto-respawn: a fixed population of slots. A slot frees when its monster is defeated (respawns after 20-40 s) or recycled for being far away
   (respawns soon). New monsters are placed out of the hero's sight (outside the camera view and >= minDist away), never outside the Wilds, and
   never above the per-biome cap. Pure logic (no THREE / DOM): the host passes zone, biome, free-space and visibility callbacks. */
export const RESPAWN = { max: 9, delay: [20, 40], refill: 1.6, minDist: 22, maxDist: 60, caps: { meadow: 4, forest: 3, rock: 2, snow: 2, shore: 2 },
  kinds: { meadow: ['wolf', 'raider', 'raider'], forest: ['wolf', 'wraith', 'raider'], rock: ['skeleton', 'raider'], snow: ['frosttroll', 'wolf', 'wolf'], shore: ['wraith', 'wolf'] } };
export class Respawner {
  constructor(o = {}) { this.C = Object.assign({}, RESPAWN, o); this.t = 0; this.ready = []; for (let i = 0; i < this.C.max; i++) this.ready.push(0); this.cool = 0; this.log = []; this.rng = o.rng || Math.random; this.pending = 0; }
  /* host: { zone() -> 'wilds'|'town', inWilds(x,z), biome(x,z), free(x,z), visible(x,z), hero:{x,z}, alive(biome) -> count, spawn(key, x, z, biome) } */
  freeSlot(delayed) { const d = delayed ? this.C.delay[0] + (this.C.delay[1] - this.C.delay[0]) * this.rng() : 2; this.ready.push(this.t + d); this.log.push({ freed: this.t, due: this.t + d, delayed: !!delayed }); if (this.log.length > 64) this.log.shift(); }
  pick(host) {
    const C = this.C, h = host.hero;
    for (let k = 0; k < 24; k++) {
      const a = this.rng() * 6.2832, r = C.minDist + (C.maxDist - C.minDist) * this.rng(), x = h.x + Math.cos(a) * r, z = h.z + Math.sin(a) * r;
      if (!host.inWilds(x, z) || !host.free(x, z) || host.visible(x, z)) continue;
      const b = host.biome(x, z), cap = C.caps[b] || 2; if (host.alive(b) >= cap) continue;
      const ks = C.kinds[b] || C.kinds.meadow; return { x, z, b, key: ks[Math.floor(this.rng() * ks.length)] };
    }
    return null;
  }
  update(dt, host) {
    this.t += dt; if (host.zone() !== 'wilds') return 0;   // never in town
    this.cool -= dt; if (this.cool > 0 || this.pending > 0 || !this.ready.length) return 0;
    let bi = -1; for (let i = 0; i < this.ready.length; i++) if (this.ready[i] <= this.t && (bi < 0 || this.ready[i] < this.ready[bi])) bi = i;
    if (bi < 0) return 0;
    const s = this.pick(host); if (!s) { this.cool = 0.5; return 0; }
    this.ready.splice(bi, 1); this.cool = this.C.refill; this.pending++;
    const due = this.log.find(l => !l.used && l.due <= this.t); if (due) { due.used = true; due.at = this.t; due.vis = host.visible(s.x, s.z); due.d = Math.hypot(s.x - host.hero.x, s.z - host.hero.z); due.b = s.b; }
    Promise.resolve(host.spawn(s.key, s.x, s.z, s.b)).then(e => { this.pending--; if (!e) this.ready.push(this.t + 1); }, () => { this.pending--; this.ready.push(this.t + 1); });
    return 1;
  }
}
