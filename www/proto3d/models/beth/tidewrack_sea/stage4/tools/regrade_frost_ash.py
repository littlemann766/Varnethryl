"""Terrain pass fix 8b (Beth): vertex-colour regrade of the frost and ash strait tiles (base + lod1).
Frost: snow capped at 0.80 albedo (no blow-out), steep faces go to shaded glacier blue, and a soft noise breakup with smooth normals (less blocky).
Ash: flat uniform grey becomes warm ash sand on the flats and dark basalt on the slopes, with low-frequency breakup and sparse ember-red tint on low steep rock.
Originals are copied to ../meshes_v1_backup/. Usage: python3 regrade_frost_ash.py <meshes_dir>"""
import sys, os, glob, shutil, numpy as np, trimesh
D = sys.argv[1]; BK = os.path.join(D, '..', 'meshes_v1_backup'); os.makedirs(BK, exist_ok=True)
# NOTE: an existing <name>_v1_backup.glb is treated as the source; delete it first if the live file changed after that backup was made (fix 8a lod1s).
def ss(a, b, x): t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
def noise(p, f): return (np.sin(p[:, 0] * f + 1.7) * np.cos(p[:, 2] * f * 1.13 - 0.4) + 0.5 * np.sin((p[:, 0] - p[:, 2]) * f * 2.3 + p[:, 1] * f)) / 1.5
def grade(g, kind, xf):
    P = trimesh.transform_points(g.vertices, xf); N = g.vertex_normals; ny = np.abs(N[:, 1]); st = 1 - ny
    c = g.visual.vertex_colors[:, :3].astype(float) / 255; L = c.mean(1, keepdims=True)
    n1 = noise(P, 0.045)[:, None]; n2 = noise(P, 0.21)[:, None]
    if kind == 'frost':
        snow = np.minimum(c, 0.80) * (0.80 / np.maximum(L, 0.80))
        snow = snow * (1 + 0.05 * n1 + 0.03 * n2) + np.array([-0.03, -0.01, 0.02])
        ice = np.array([0.42, 0.56, 0.70]) * (0.85 + 0.12 * n1)
        rock = np.array([0.30, 0.32, 0.36])
        out = snow * (1 - ss(0.35, 0.75, st)[:, None]) + ice * ss(0.35, 0.75, st)[:, None]
        out = np.where((L < 0.45), c * 0.9 + rock * 0.1, out)   # keep existing dark rock/beach
    else:
        sand = np.array([0.52, 0.43, 0.34]) * (0.9 + 0.12 * n1 + 0.05 * n2); basalt = np.array([0.12, 0.11, 0.12]) * (0.9 + 0.15 * n2)
        out = sand * (1 - ss(0.22, 0.5, st)[:, None]) + basalt * ss(0.22, 0.5, st)[:, None]
        ember = (st > 0.55) & (P[:, 1] < 6) & (n2[:, 0] > 0.55)
        out[ember] = out[ember] * 0.6 + np.array([0.45, 0.14, 0.05]) * 0.4
        out = np.where((L > 0.6) | (L < 0.08), c, out)          # keep any bright/very dark authored accents
    g.visual.vertex_colors = np.c_[(np.clip(out, 0, 1) * 255).astype(np.uint8), g.visual.vertex_colors[:, 3]]
for f in sorted(glob.glob(os.path.join(D, 'frost_tile_*.glb')) + glob.glob(os.path.join(D, 'ash_tile_*.glb'))):
    if 'backup' in f: continue
    b = os.path.join(BK, os.path.basename(f).replace('.glb', '_v1_backup.glb'))
    if not os.path.exists(b): shutil.copy(f, b)
    s = trimesh.load(b, force='scene'); kind = 'frost' if 'frost_' in os.path.basename(f) else 'ash'
    for node in s.graph.nodes_geometry:
        xf, gname = s.graph[node]; grade(s.geometry[gname], kind, xf)
    s.export(f); print('regraded', os.path.basename(f))
