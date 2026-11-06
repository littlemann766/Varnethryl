"""Terrain-only cameras. No scatter in frame on purpose: these shots are the ground, the slope and the waterline.
Same cameras for land3 and land4. Hero is kept small and off to the side so it does not hide the surface.
"""
import os, sys, json
import numpy as np
import trimesh
sys.path.insert(0, os.path.dirname(__file__))
from smooth_land import ROOT, LAND3, REG, is_terrain

MAN = json.load(open(os.path.join(os.path.dirname(ROOT), "stage5_islands", "stage5_manifest.json")))

def grid(region):
    d, pre = REG[region]
    pts = []
    for f in os.listdir(os.path.join(LAND3, d)):
        b = f[:-4]
        if not (f.endswith(".glb") and b.startswith(pre) and is_terrain(b) and not b.endswith("_lod1") and "scatter" not in b):
            continue
        s = trimesh.load(os.path.join(LAND3, d, f), force="mesh", process=False)
        V = np.asarray(s.vertices); C = np.asarray(s.visual.vertex_colors)
        m = C[:, 3] > 127
        pts.append(np.concatenate([V[m][:, [0, 2]], V[m][:, 1:2], C[m][:, :3].astype(np.float32)], 1))
    Q = np.concatenate(pts)
    cell = 6.0
    origin = np.floor(Q[:, :2].min(0)) - 12
    ij = np.floor((Q[:, :2] - origin) / cell).astype(int)
    shape = tuple(ij.max(0) + 2)
    H = np.full(shape, -999, np.float32)
    COL = np.zeros(shape + (3,), np.float64)
    CNT = np.zeros(shape, np.float64)
    np.maximum.at(H, (ij[:, 0], ij[:, 1]), Q[:, 2])
    np.add.at(COL, (ij[:, 0], ij[:, 1]), Q[:, 3:6])
    np.add.at(CNT, (ij[:, 0], ij[:, 1]), 1)
    return origin, cell, H, COL, CNT

def h_at(o, c, H, x, z):
    i = int((x - o[0]) / c); j = int((z - o[1]) / c)
    if i < 1 or j < 1 or i >= H.shape[0] - 1 or j >= H.shape[1] - 1 or H[i, j] < -100:
        return None
    return float(H[i, j])

shots = []
def add(region, name, cam, at, fov=50):
    # hero a few metres to the side, not in the middle of the ground
    shots.append(dict(region=region, name=name, fov=fov, cam=[float(v) for v in cam], at=[float(v) for v in at],
                      hero=[float(cam[0] + 2.2), float(cam[1] - 1.65), float(cam[2] + 1.4)]))

for region in REG:
    o, c, H, COL, CNT = grid(region)
    # GROUND close-up: a gentle inland cell, camera at eye height looking a few metres down the slope
    flat = np.argwhere((H > 2.5) & (H < 25))
    if len(flat) == 0:
        flat = np.argwhere(H > 1.5)
    mid = flat[len(flat) // 2]
    gx = o[0] + mid[0] * c; gz = o[1] + mid[1] * c; gy = float(H[mid[0], mid[1]])
    add(region, f"{region}_ground", [gx, gy + 1.55, gz], [gx + 3.2, gy + 0.15, gz + 2.4], fov=55)
    # SKYLINE: crest, camera low and far so the face and the sky both show
    iy, ix = np.unravel_index(np.argmax(H), H.shape)
    px = o[0] + iy * c; pz = o[1] + ix * c; py = float(H[iy, ix])
    best = None
    for ang in np.linspace(0, 6.2, 16):
        for dist in (160, 240, 320):
            cx, cz = px + np.cos(ang) * dist, pz + np.sin(ang) * dist
            ch = h_at(o, c, H, cx, cz)
            if ch is None:
                ch = 1.0
            if ch > py * 0.5:
                continue
            score = py - ch
            if best is None or score > best[0]:
                best = (score, cx, cz, ch)
    if best:
        _, cx, cz, ch = best
        add(region, f"{region}_skyline", [cx, ch + 8.0, cz], [px, py * 0.62, pz], fov=36)
    # COAST: stand on the bank, waterline in the lower half, cliff rock if the drop is steep
    ys, xs = np.nonzero((H > 0.8) & (H < 6.0))
    shore = None
    for i, j in zip(ys[::5], xs[::5]):
        for di, dj in ((3, 0), (-3, 0), (0, 3), (0, -3)):
            ii, jj = i + di, j + dj
            if 0 <= ii < H.shape[0] and 0 <= jj < H.shape[1] and H[ii, jj] < 0.2:
                shore = (i, j, di, dj)
                break
        if shore:
            break
    if shore:
        i, j, di, dj = shore
        sx = o[0] + i * c; sz = o[1] + j * c; sy = float(H[i, j])
        # step inland, opposite the water
        # stand close on the bank and look down at the lip so rock, grass and water share the frame
        ix2, iz2 = sx - di * c * 0.45, sz - dj * c * 0.45
        hy = h_at(o, c, H, ix2, iz2) or sy
        add(region, f"{region}_coast", [ix2, hy + 1.45, iz2], [sx + di * c * 0.15, 0.35, sz + dj * c * 0.15], fov=58)
    # every playable island: ground close on its own mesh, plus skyline if it rises, plus coast if it meets the sea
    for k, I in MAN["islands"].items():
        if I["region"] != region:
            continue
        L = MAN["landings"][k]
        inl = np.array(L["inland"], float); inl /= np.linalg.norm(inl) + 1e-9
        sh = np.array([L["shore"][0], L["shore"][2]])
        p = sh + inl * (22 if k != "saltwatch_keep" else 12)
        hy = h_at(o, c, H, p[0], p[1])
        if hy is None:
            hy = float(L["shore"][1])
        cam = p - inl * 5.5
        cy = h_at(o, c, H, cam[0], cam[1]) or hy
        add(region, f"{k}_ground", [cam[0], max(cy, hy) + 1.55, cam[1]], [p[0] + inl[0] * 3.5, hy + 0.2, p[1] + inl[1] * 3.5], fov=55)
        # coast at the landing shore, looking seaward
        sea = sh - inl * 8
        add(region, f"{k}_coast", [sh[0] + inl[0] * 6, hy + 1.7, sh[1] + inl[1] * 6],
            [sea[0], 0.4, sea[1]], fov=52)
        mesh = os.path.join(LAND3, REG[region][0], I["files"]["mesh"] + ".glb")
        if os.path.exists(mesh):
            s = trimesh.load(mesh, force="mesh", process=False)
            V = np.asarray(s.vertices)
            peak = V[int(V[:, 1].argmax())]
            if peak[1] > 14:
                d = np.array([sh[0] - peak[0], sh[1] - peak[2]])
                d /= np.linalg.norm(d) + 1e-9
                cam = np.array([peak[0], peak[2]]) + d * 90
                ch = h_at(o, c, H, cam[0], cam[1])
                if ch is None or ch > peak[1] * 0.6:
                    cam = np.array([peak[0], peak[2]]) + d * 150
                    ch = h_at(o, c, H, cam[0], cam[1]) or 2
                add(region, f"{k}_skyline", [cam[0], max(ch + 6, 4), cam[1]], [peak[0], peak[1] * 0.55, peak[2]], fov=34)

json.dump(shots, open(os.path.join(ROOT, "shots_terrain.json"), "w"), indent=1)
print("terrain shots", len(shots))
for s in shots:
    print(f"  {s['region']:6} {s['name']}")
