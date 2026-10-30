#!/usr/bin/env python3
"""Beth: soft storm-fog border v2 (replaces the single slab ribbon). Per region:
  <pre>_fog_layers.glb   5 stacked soft fog ribbons (UV.x along / UV.y up, COLOR.r = layer 0..1)  -> shaders/fog_layers.gdshader
  <pre>_storm_sky.glb    tall backdrop ribbon outside the border (dark cloud + rain)            -> shaders/storm_sky.gdshader
  <pre>_storm_sea.glb    dark choppy water band from just inside the border outwards              -> shaders/storm_sea.gdshader
  <pre>_storm_col.glb    INVISIBLE blocker: thin boxes on the old wall line (same as before; use as StaticBody collider only)"""
import os, math, numpy as np, trimesh, sys
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'meshes')
REGIONS = {'coast': (-3000, -1500, -1200, 1700), 'arch': (-1200, -1300, 1500, 1300)}
def loop(x0, z0, x1, z1, inset):
    return [(x0 + inset, z0 + inset), (x1 - inset, z0 + inset), (x1 - inset, z1 - inset), (x0 + inset, z1 - inset), (x0 + inset, z0 + inset)]
def dense(pts, step):
    out = []
    for a, b in zip(pts, pts[1:]):
        a = np.array(a, float); b = np.array(b, float); n = max(1, int(np.linalg.norm(b - a) / step))
        for t in np.linspace(0, 1, n, endpoint=False): out.append(a + (b - a) * t)
    out.append(np.array(pts[-1], float)); return out
def ribbon(pts, y0, hgt, layer, step=40, rows=3, wob=0.0, seed=0):
    P = dense(pts, step); acc = [0.0]
    for k in range(1, len(P)): acc.append(acc[-1] + np.linalg.norm(P[k] - P[k - 1]))
    vv, uu, cc, ff = [], [], [], []; R = rows + 1
    for k, p in enumerate(P):
        for r in range(R):
            t = r / rows; w = wob * math.sin(acc[k] / 90.0 + seed) * t
            vv.append((p[0] + w, y0 + hgt * t, p[1] + w * 0.6)); uu.append((acc[k] / 200.0, t)); cc.append((int(layer * 255), 0, 0, 255))
    for k in range(len(P) - 1):
        for r in range(rows):
            i = k * R + r; ff += [(i, i + 1, i + R), (i + 1, i + R + 1, i + R)]
    m = trimesh.Trimesh(vv, ff, process=False); m.visual = trimesh.visual.TextureVisuals(uv=np.array(uu)); return m, np.array(cc, np.uint8)
def band(x0, z0, x1, z1, inner, outer, step=40, rows=6):   # flat water strip between two insets (inner > outer)
    A = dense(loop(x0, z0, x1, z1, inner), step); vv, uu, ff = [], [], []
    acc = [0.0]
    for k in range(1, len(A)): acc.append(acc[-1] + np.linalg.norm(A[k] - A[k - 1]))
    cx, cz = (x0 + x1) / 2, (z0 + z1) / 2; R = rows + 1
    for k, p in enumerate(A):
        d = p - np.array([cx, cz]); dn = np.sign(d) * np.array([abs(d[0]) > abs(d[1]) - 1e-6 or True, True])
        # push outward along the rectangle normal of this edge
        ex = (x1 - x0) / 2 - inner; ez = (z1 - z0) / 2 - inner
        nx = np.clip(d[0] / ex, -1, 1); nz = np.clip(d[1] / ez, -1, 1); nrm = np.array([nx if abs(nx) > 0.999 else 0, nz if abs(nz) > 0.999 else 0]); nrm = nrm / (np.linalg.norm(nrm) + 1e-9)
        for r in range(R):
            t = r / rows; q = p + nrm * (inner - outer) * t; vv.append((q[0], 0.06, q[1])); uu.append((acc[k] / 200.0, t))
    for k in range(len(A) - 1):
        for r in range(rows):
            i = k * R + r; ff += [(i, i + R, i + 1), (i + 1, i + R, i + R + 1)]
    m = trimesh.Trimesh(vv, ff, process=False); m.visual = trimesh.visual.TextureVisuals(uv=np.array(uu)); return m
for pre, (x0, z0, x1, z1) in REGIONS.items():
    parts, cols = [], []
    for k, (ins, hgt) in enumerate([(170, 55), (130, 75), (95, 95), (65, 115), (30, 135)]):   # innermost = faint + low, outer = tall + dense
        m, c = ribbon(loop(x0, z0, x1, z1, ins), -6, hgt, k / 4.0, wob=22, seed=k * 1.7); parts.append(m); cols.append(c)
    fog = trimesh.util.concatenate(parts); col = np.concatenate(cols)
    # store the layer in COLOR_0 (shader reads COLOR.r); UVs kept for the noise
    fog.visual = trimesh.visual.TextureVisuals(uv=np.concatenate([p.visual.uv for p in parts]))
    fogc = fog.copy(); fogc.visual = trimesh.visual.ColorVisuals(fogc, vertex_colors=col)
    # trimesh can't export uv+colour together on one primitive easily -> encode layer in UV2 via a second attribute: use vertex colour mesh and recompute UV in shader from world pos instead
    fogc.export(os.path.join(OUT, f'{pre}_fog_layers.glb'))
    sky, _ = ribbon(loop(x0, z0, x1, z1, -220), -10, 420, 0, step=80, rows=4); sky.export(os.path.join(OUT, f'{pre}_storm_sky.glb'))
    band(x0, z0, x1, z1, 150, -600).export(os.path.join(OUT, f'{pre}_storm_sea.glb'))
    cb = []
    L = loop(x0, z0, x1, z1, 40)
    for a, b in zip(L, L[1:]):
        a = np.array(a, float); b = np.array(b, float); c = (a + b) / 2; d = b - a; Ln = np.linalg.norm(d)
        bx = trimesh.creation.box((Ln + 4, 60, 4) if abs(d[0]) > abs(d[1]) else (4, 60, Ln + 4)); bx.apply_translation((c[0], 20, c[1])); cb.append(bx)
    trimesh.util.concatenate(cb).export(os.path.join(OUT, f'{pre}_storm_col.glb'))
    print(pre, 'fog tris', len(fogc.faces), 'sky', len(sky.faces), 'sea', 'ok')
