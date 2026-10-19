// Road/path network: links every building entrance to the two main streets (x=0 / z=0),
// which run to the gate. Pure geometry helpers (no THREE import) so headless tests can reuse them.
// Each door gets a short stub straight out of the door, then an L-shaped lane to the nearest
// main street that avoids every building footprint. All lanes merge into ONE mesh that shares the
// plaza cobble material (mergeStatic folds it into the plaza draw call).
export const ROAD_W = 2.4;

function footprints(builders, extra) {
  const out = [];
  for (const b of builders) {
    if (!b.toW || b.id === 'walls' || b.id === 'port_dock') continue;
    if (b.footprint) {
      const hw = b.footprint.w / 2 + 0.6 / b.K, hd = b.footprint.d / 2 + 0.6 / b.K; let x0 = 1e9, x1 = -1e9, z0 = 1e9, z1 = -1e9;
      for (const [lx, lz] of [[-hw, -hd], [hw, -hd], [-hw, hd], [hw, hd]]) { const [px, pz] = b.toW(lx, lz); x0 = Math.min(x0, px); x1 = Math.max(x1, px); z0 = Math.min(z0, pz); z1 = Math.max(z1, pz); }
      out.push({ t: 'b', x0, x1, z0, z1, id: b.id });
    } else if (b.radius) { const c = b.toW(0, 0); out.push({ t: 'c', x: c[0], z: c[1], r: b.radius + 0.6, id: b.id }); }
  }
  return out.concat(extra || []);
}
function hit(F, x, z, pad) {
  for (const f of F) {
    if (f.t === 'b') { if (x > f.x0 - pad && x < f.x1 + pad && z > f.z0 - pad && z < f.z1 + pad) return true; }
    else if (Math.hypot(x - f.x, z - f.z) < f.r + pad) return true;
  }
  return false;
}
function segClear(F, a, b, pad) {
  const n = Math.max(2, Math.ceil(Math.hypot(b[0] - a[0], b[1] - a[1]) / 0.5));
  for (let i = 0; i <= n; i++) { const t = i / n; if (hit(F, a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, pad)) return false; }
  return true;
}
function ptFree(cols, x, z, m) {
  for (const c of cols) {
    if (c.npcOnly) continue; if (c.lv !== undefined && (Array.isArray(c.lv) ? !c.lv.includes(0) : c.lv !== 0)) continue;
    if (c.type === 'box') { const qx = Math.max(c.minX, Math.min(c.maxX, x)), qz = Math.max(c.minZ, Math.min(c.maxZ, z)); if (Math.hypot(x - qx, z - qz) < m) return false; }
    else if (Math.hypot(x - c.x, z - c.z) < c.r + m) return false;
  }
  return true;
}
function segFree(cols, a, b, m) { const n = Math.max(2, Math.ceil(Math.hypot(b[0] - a[0], b[1] - a[1]) / 0.4)); for (let i = 0; i <= n; i++) { const t = i / n; if (!ptFree(cols, a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, m)) return false; } return true; }
const plen = P => { let s = 0; for (let i = 1; i < P.length; i++) s += Math.hypot(P[i][0] - P[i - 1][0], P[i][1] - P[i - 1][1]); return s; };

// Grid planner (1 m): rasterise ground-level colliders + building footprints (inflated for clearance), Dijkstra from the
// gate (main streets / plaza cost 1, open grass 2, so lanes join the streets early and share), then trace each door back.
// returns [{id, door:[x,z], pts:[[x,z]...]}] (one polyline per lane: door stub, then the traced route off the streets)
export function planRoads(builders, o) {
  let this_gate = null;
  const W = o.world, S = 1, R = W + 30, N = Math.ceil(2 * R / S), infl = 1.1;
  const ix = v => Math.max(0, Math.min(N - 1, Math.round((v + R) / S))), xv = i => i * S - R;
  const blk = new Uint8Array(N * N), F = footprints(builders, o.obstacles);
  const mark = (x0, x1, z0, z1, test) => { for (let i = ix(x0); i <= ix(x1); i++) for (let j = ix(z0); j <= ix(z1); j++) if (!test || test(xv(i), xv(j))) blk[i * N + j] = 1; };
  for (const c of o.colliders || []) {
    if (c.npcOnly) continue; if (c.lv !== undefined && (Array.isArray(c.lv) ? !c.lv.includes(0) : c.lv !== 0)) continue;
    if (c.type === 'box') mark(c.minX - infl, c.maxX + infl, c.minZ - infl, c.maxZ + infl);
    else { const r = c.r + infl; mark(c.x - r, c.x + r, c.z - r, c.z + r, (x, z) => Math.hypot(x - c.x, z - c.z) < r); }
  }
  for (const f of F) { if (f.t === 'b') mark(f.x0, f.x1, f.z0, f.z1); else mark(f.x - f.r, f.x + f.r, f.z - f.r, f.z + f.r, (x, z) => Math.hypot(x - f.x, z - f.z) < f.r); }
  const onMain = (x, z) => Math.abs(x) < o.mainX || Math.abs(z) < o.mainZ || Math.hypot(x, z) < o.plazaR;
  const cost = new Float32Array(N * N).fill(1e9), par = new Int32Array(N * N).fill(-1);
  // binary heap
  const hk = [], hv = []; const push = (k, v) => { hk.push(k); hv.push(v); let i = hk.length - 1; while (i) { const p = (i - 1) >> 1; if (hv[p] <= hv[i]) break; [hk[p], hk[i]] = [hk[i], hk[p]]; [hv[p], hv[i]] = [hv[i], hv[p]]; i = p; } };
  const pop = () => { const k = hk[0], lk = hk.pop(), lv = hv.pop(); if (hk.length) { hk[0] = lk; hv[0] = lv; let i = 0; for (;;) { const l = 2 * i + 1, r = l + 1; let m = i; if (l < hk.length && hv[l] < hv[m]) m = l; if (r < hk.length && hv[r] < hv[m]) m = r; if (m === i) break; [hk[m], hk[i]] = [hk[i], hk[m]]; [hv[m], hv[i]] = [hv[i], hv[m]]; i = m; } } return k; };
  let g0 = ix(0) * N + ix(o.gate[1]); for (let t = 0; t < 30 && blk[g0]; t++) g0 = ix(0) * N + ix(o.gate[1] - t); cost[g0] = 0; push(g0, 0); this_gate = [xv((g0 / N) | 0), xv(g0 % N)];
  const D8 = [[1, 0, 1], [-1, 0, 1], [0, 1, 1], [0, -1, 1], [1, 1, 1.42], [1, -1, 1.42], [-1, 1, 1.42], [-1, -1, 1.42]];
  while (hk.length) {
    const c = pop(), ci = (c / N) | 0, cj = c % N, cc = cost[c];
    for (const [di, dj, w] of D8) {
      const a = ci + di, b = cj + dj; if (a < 0 || b < 0 || a >= N || b >= N) continue; const k = a * N + b; if (blk[k]) continue;
      if (di && dj && (blk[(ci + di) * N + cj] || blk[ci * N + cj + dj])) continue;
      const nc = cc + w * (onMain(xv(a), xv(b)) ? 1 : 2); if (nc < cost[k]) { cost[k] = nc; par[k] = c; push(k, nc); }
    }
  }
  const roads = []; roads.gate = this_gate; roads.blockedFrac = blk.reduce((a, v) => a + v, 0) / blk.length;
  for (const b of builders) {
    if (!b.toW || !b.insideTest || b.id === 'walls' || b.id === 'port_dock') continue;
    const front = b.footprint ? b.footprint.d / 2 : b.radius / b.K;
    const d = b.toW(0, front + 0.9 / b.K), A = b.toW(0, front + 3.2 / b.K);
    let st = -1, best = 1e9;   // nearest reachable cell to the stub end
    for (let a = -4; a <= 4; a++) for (let c = -4; c <= 4; c++) { const i = ix(A[0]) + a, j = ix(A[1]) + c; if (i < 0 || j < 0 || i >= N || j >= N) continue; const k = i * N + j; if (cost[k] < 1e9) { const dd = Math.hypot(xv(i) - A[0], xv(j) - A[1]); if (dd < best) { best = dd; st = k; } } }
    let stub = [d, A];
    if (st < 0 && b.footprint) {   // door opens onto a narrow strip (e.g. port tavern on the dock): run along the facade to a corner
      for (const sx of [1, -1]) {
        const C = b.toW(sx * (b.footprint.w / 2 + 2.2 / b.K), front + 0.9 / b.K);
        if (!segFree(o.colliders, d, C, 0.42)) continue;
        for (let a = -4; a <= 4; a++) for (let c = -4; c <= 4; c++) { const i = ix(C[0]) + a, j = ix(C[1]) + c; if (i < 0 || j < 0 || i >= N || j >= N) continue; const k = i * N + j; if (cost[k] < 1e9 && segFree(o.colliders, C, [xv(i), xv(j)], 0.42)) { const dd = Math.hypot(xv(i) - C[0], xv(j) - C[1]); if (dd < best) { best = dd; st = k; stub = [d, C]; } } }
        if (st >= 0) break;
      }
    }
    if (st < 0) { roads.push({ id: b.id, door: d, pts: [d, A], fail: true }); continue; }
    const pts = stub.slice(); let k = st;
    while (k >= 0) { const x = xv((k / N) | 0), z = xv(k % N); pts.push([x, z]); k = par[k]; }
    // collapse collinear runs
    const out = [pts[0]];
    for (let i = 1; i < pts.length; i++) {
      if (out.length >= 2 && i < pts.length) { const p = out[out.length - 2], q = out[out.length - 1], r = pts[i]; const cr = (q[0] - p[0]) * (r[1] - q[1]) - (q[1] - p[1]) * (r[0] - q[0]); if (Math.abs(cr) < 1e-6 && out.length > 2) { out[out.length - 1] = r; continue; } }
      out.push(pts[i]);
    }
    roads.push({ id: b.id, door: d, pts: out });
  }
  return roads;
}
export function nearRoad(roads, x, z, m) {
  for (const r of roads) for (let i = 1; i < r.pts.length; i++) {
    const [ax, az] = r.pts[i - 1], [bx, bz] = r.pts[i], dx = bx - ax, dz = bz - az, L = dx * dx + dz * dz || 1;
    const t = Math.max(0, Math.min(1, ((x - ax) * dx + (z - az) * dz) / L));
    if (Math.hypot(x - ax - dx * t, z - az - dz * t) < ROAD_W / 2 + m) return true;
  }
  return false;
}
// flat ribbon geometry (positions/uvs/indices) for all lanes; uv in world units / uvScale
export function roadGeometry(roads, uvScale, y) {
  const pos = [], uv = [], idx = []; const h = ROAD_W / 2;
  const quad = (x0, z0, x1, z1) => { const n = pos.length / 3; for (const [x, z] of [[x0, z0], [x1, z0], [x1, z1], [x0, z1]]) { pos.push(x, y, z); uv.push(x / uvScale + 0.5, -z / uvScale + 0.5); } idx.push(n, n + 2, n + 1, n, n + 3, n + 2); };
  for (const r of roads) for (let i = 1; i < r.pts.length; i++) {
    const [ax, az] = r.pts[i - 1], [bx, bz] = r.pts[i];
    if (Math.abs(ax - bx) < 1e-3 || Math.abs(az - bz) < 1e-3) quad(Math.min(ax, bx) - h, Math.min(az, bz) - h, Math.max(ax, bx) + h, Math.max(az, bz) + h);
    else { // diagonal door stub (rotated building): oriented strip
      const L = Math.hypot(bx - ax, bz - az), nx = -(bz - az) / L * h, nz = (bx - ax) / L * h, n = pos.length / 3;
      for (const [x, z] of [[ax + nx, az + nz], [bx + nx, bz + nz], [bx - nx, bz - nz], [ax - nx, az - nz]]) { pos.push(x, y, z); uv.push(x / uvScale + 0.5, -z / uvScale + 0.5); }
      const up = (pos[3 * n + 5] - pos[3 * n + 2]) * (pos[3 * n + 6] - pos[3 * n]) - (pos[3 * n + 3] - pos[3 * n]) * (pos[3 * n + 8] - pos[3 * n + 2]) > 0;
      if (up) idx.push(n, n + 2, n + 1, n, n + 3, n + 2); else idx.push(n, n + 1, n + 2, n, n + 2, n + 3);
    }
  }
  return { pos, uv, idx };
}
