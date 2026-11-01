"""Stage 10 (Beth): irregular ice floes ringing the new Frost island coast (frost_ice_floes_coast.glb + _lod1).
Placed 8-160 m off the carved frost shore, denser close in; none within 70 m of a landing moor/shore point."""
import sys, os, json, numpy as np, trimesh
from scipy.ndimage import distance_transform_edt
R, HA = sys.argv[1], sys.argv[2]
H = np.fromfile(HA, np.float32).reshape(640, 640); land = H > 0
dist = distance_transform_edt(~land) * 10.0
avoid = []
for p in json.load(open(os.environ.get('TW', '/tmp/gv2/tidewrack') + '/landings.json')).values():
    for k in ('shore', 'moor', 'spawn'):
        if k in p: avoid.append((p[k][0], p[k][2]))
avoid += [(-891, -1950), (-988, -1946)]   # ice dock
avoid = np.array(avoid, float)
rng = np.random.default_rng(1112); parts = []; lo = []; l1s = []
for _ in range(60000):
    x = rng.uniform(-2400, 1500); z = rng.uniform(-3000, -1500)
    i, j = int((z + 3200) / 10), int((x + 3200) / 10); d = dist[i, j]
    if land[i, j] or d < 8 or d > 160 or rng.random() > np.exp(-d / 55.0) * 0.16: continue
    if np.min(np.hypot(avoid[:, 0] - x, avoid[:, 1] - z)) < 70: continue
    if any(np.hypot(px - x, pz - z) < pr + r0 for px, pz, pr in parts[-40:] for r0 in [3]): continue
    r = rng.uniform(4, 9 + 14 * np.exp(-d / 40)); n = rng.integers(6, 11)
    a = np.sort(rng.uniform(0, 2 * np.pi, n)); rr = r * rng.uniform(0.55, 1.0, n)
    pts = np.c_[np.cos(a) * rr, np.sin(a) * rr]
    V = np.r_[np.c_[pts[:, 0], np.full(n, 0.25), pts[:, 1]], np.c_[pts[:, 0] * 0.9, np.full(n, -0.45), pts[:, 1] * 0.9]]
    m = trimesh.convex.convex_hull(V); m.apply_translation([x, 0, z])
    sh = rng.uniform(0.9, 1.05); top = m.vertices[:, 1] > -0.1
    col = np.where(top[:, None], np.array([0.86, 0.90, 0.94]) * sh, np.array([0.50, 0.66, 0.80]) * sh)
    m.visual.vertex_colors = np.c_[(np.clip(col, 0, 1) * 255).astype(np.uint8), np.full(len(col), 255, np.uint8)]
    parts.append((x, z, r)); lo.append(m)
    k = max(3, n // 2); V1 = np.r_[np.c_[pts[::2, 0], np.full(len(pts[::2]), 0.25), pts[::2, 1]], [[0, -0.45, 0]]]
    m1 = trimesh.convex.convex_hull(V1); m1.apply_translation([x, 0, z]); c1 = np.array([0.80, 0.86, 0.92]) * sh
    m1.visual.vertex_colors = np.tile(np.r_[(c1 * 255).astype(np.uint8), 255], (len(m1.vertices), 1)); l1s.append(m1)
M = trimesh.util.concatenate(lo); M.export(R + '/stage4/meshes/frost_ice_floes_coast.glb')
l1 = trimesh.util.concatenate(l1s); l1.export(R + '/stage4/meshes/frost_ice_floes_coast_lod1.glb')
print(len(parts), 'floes', len(M.faces), 'tris; lod1', round(100 * len(l1.faces) / len(M.faces), 1), '%')
