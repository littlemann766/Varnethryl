"""Player-height cameras aimed at real scatter clusters, plus a skyline and a shore per region.
Cameras are shared by the land3 (before) and land4 (after) renders.
"""
import os, sys, json
import numpy as np
import trimesh
sys.path.insert(0, os.path.dirname(__file__))
from smooth_land import ROOT, LAND3, REG, is_terrain

MAN = json.load(open(os.path.join(os.path.dirname(ROOT), "stage5_islands", "stage5_manifest.json")))
pl = json.load(open(os.path.join(ROOT, "placements.json")))
groves = json.load(open(os.path.join(ROOT, "grove_notes.json")))
P = np.array([[p["x"], p["y"], p["z"]] for p in pl])
K = np.array([p["kind"] for p in pl])
R = np.array([p["region"] for p in pl])
TREE = ("pine", "oak", "dead")

def is_tree(k):
    return any(t in k for t in TREE)

def height_grid(region):
    d, pre = REG[region]
    pts = []
    for f in os.listdir(os.path.join(LAND3, d)):
        b = f[:-4]
        if not (f.endswith(".glb") and b.startswith(pre) and is_terrain(b) and not b.endswith("_lod1")):
            continue
        s = trimesh.load(os.path.join(LAND3, d, f), force="mesh", process=False)
        V = np.asarray(s.vertices)
        C = np.asarray(s.visual.vertex_colors)
        m = C[:, 3] > 127
        pts.append(V[m][:, [0, 1, 2]])
    Q = np.concatenate(pts)
    cell = 4.0
    origin = np.floor(Q[:, [0, 2]].min(0)) - 8
    ij = np.floor((Q[:, [0, 2]] - origin) / cell).astype(int)
    H = np.full(tuple(ij.max(0) + 2), -999, np.float32)
    np.maximum.at(H, (ij[:, 0], ij[:, 1]), Q[:, 1])
    return origin, cell, H

def h_at(origin, cell, H, x, z):
    i = int(np.floor((x - origin[0]) / cell)); j = int(np.floor((z - origin[1]) / cell))
    if i < 0 or j < 0 or i >= H.shape[0] or j >= H.shape[1] or H[i, j] < -100:
        return None
    return float(H[i, j])

def eye(origin, cell, H, x, z, fallback):
    hh = h_at(origin, cell, H, x, z)
    base = hh if hh is not None else fallback
    return base + 1.65

shots = []
checks = []

def add(region, name, cam, at, hero=None, fov=48, expect=None):
    s = dict(region=region, name=name, fov=fov, cam=cam, at=at)
    if hero is not None:
        s["hero"] = hero
    shots.append(s)
    if expect:
        checks.append(dict(name=name, **expect))

for region in REG:
    origin, cell, H = height_grid(region)
    # skyline: highest cell, camera far enough and low enough that the crest crosses open sky
    iy, ix = np.unravel_index(np.argmax(H), H.shape)
    px = float(origin[0] + iy * cell + cell / 2)
    pz = float(origin[1] + ix * cell + cell / 2)
    py = float(H[iy, ix])
    best = None
    for ang in np.linspace(0, 6.0, 12):
        for dist in (180, 260, 340):
            cx, cz = px + np.cos(ang) * dist, pz + np.sin(ang) * dist
            ch = h_at(origin, cell, H, cx, cz)
            if ch is None:
                ch = 2.0
            # want to stand well below the crest
            if ch > py * 0.55:
                continue
            score = (py - ch) + dist * 0.01
            if best is None or score > best[0]:
                best = (score, cx, cz, ch)
    if best:
        _, cx, cz, ch = best
        add(region, f"{region}_skyline",
            [cx, max(ch + 6.0, py * 0.22), cz],
            [px, py * 0.72, pz], fov=38)
    # shore: a cell just above water with open water beside it, camera on land looking along the lip
    ys, xs = np.nonzero((H > 0.6) & (H < 2.2))
    shore = None
    for i, j in zip(ys[::6], xs[::6]):
        if i + 3 < H.shape[0] and H[i + 3, j] < 0.15:
            shore = (i, j); break
    if shore:
        i, j = shore
        sx = float(origin[0] + i * cell); sz = float(origin[1] + j * cell); sy = float(H[i, j])
        # stand 6 m inland (opposite the water step) 
        add(region, f"{region}_shore",
            [sx - 6, sy + 1.65, sz],
            [sx + 4, sy * 0.4, sz],
            hero=[sx - 1.5, sy, sz], fov=52)
    # named islands: aim at the grove spot if it actually holds trees, else the densest tree clump near the pier
    for k, I in MAN["islands"].items():
        if I["region"] != region:
            continue
        g = next((n for n in groves if n.get("id") == k and n.get("spot")), None)
        m = R == region
        center = None
        if g:
            s = np.array(g["spot"])
            d = np.hypot(P[m, 0] - s[0], P[m, 2] - s[2])
            trees = np.nonzero(m)[0][d < 14]
            ntrees = sum(is_tree(K[i]) for i in trees)
            if ntrees >= 3:
                center = P[trees].mean(0)
        if center is None:
            ph = np.array(I["pier_head"], float)
            d = np.hypot(P[:, 0] - ph[0], P[:, 2] - ph[2])
            near = np.nonzero((R == region) & (d < 180))[0]
            trees = [i for i in near if is_tree(K[i])]
            if len(trees) >= 3:
                # densest tree
                TT = P[trees]
                best_i, best_n = trees[0], -1
                for i, t in enumerate(TT):
                    n = np.sum(np.hypot(TT[:, 0] - t[0], TT[:, 2] - t[2]) < 12)
                    if n > best_n:
                        best_n, best_i = n, trees[i]
                center = P[best_i]
        if center is None:
            continue
        # stand 7 m from the cluster, eye height, look into the trunks
        ang = 0.6
        camx = float(center[0] + np.cos(ang) * 7.5)
        camz = float(center[2] + np.sin(ang) * 7.5)
        cy = eye(origin, cell, H, camx, camz, float(center[1]))
        add(region, f"{k}_grove",
            [camx, cy, camz],
            [float(center[0]), float(center[1]) + 1.5, float(center[2])],
            hero=[camx - np.cos(ang) * 1.2, cy - 1.65, camz - np.sin(ang) * 1.2],
            fov=46,
            expect=dict(x=float(center[0]), z=float(center[2]), radius=14, min_trees=3))
    # islets that received a grove or rocks: one close view each if the spot has anything within 12 m
    for n in groves:
        if n.get("kind") not in ("islet_grove", "bare_rock") or not n.get("spot"):
            continue
        if not str(n["id"]).startswith(region) and not str(n["id"]).startswith(region + "_"):
            # ids are like A_islet_... frost_islet_...
            if not str(n["id"]).startswith({"A": "A_", "B": "B_", "frost": "frost_", "ash": "ash_"}[region]):
                continue
        s = np.array(n["spot"])
        d = np.hypot(P[:, 0] - s[0], P[:, 2] - s[2])
        if (d < 12).sum() < 2 and n["kind"] == "islet_grove":
            continue
        camx, camz = float(s[0] + 6.5), float(s[2] + 4.5)
        cy = eye(origin, cell, H, camx, camz, float(s[1]))
        tag = "rocks" if n["kind"] == "bare_rock" else "grove"
        add(region, f"{n['id']}_{tag}",
            [camx, cy, camz],
            [float(s[0]), float(s[1]) + 1.0, float(s[2])],
            hero=[camx - 1.2, cy - 1.65, camz - 0.8],
            fov=50)

# lift any camera that ended up under the land
for s in shots:
    # region height grids already discarded; a small safety uses the look height
    if s["cam"][1] < s["at"][1] - 8:
        s["cam"][1] = s["at"][1] + 2

json.dump(shots, open(os.path.join(ROOT, "shots_evidence.json"), "w"), indent=1)
json.dump(checks, open(os.path.join(ROOT, "view_expect.json"), "w"), indent=1)
print("evidence shots", len(shots))
for s in shots:
    print(f"  {s['region']:6} {s['name']}")
