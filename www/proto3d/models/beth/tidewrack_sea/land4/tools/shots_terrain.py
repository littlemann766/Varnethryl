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

class Height:
    """Highest terrain triangle at an xz. A cell max of vertices sits under long faces, which put cameras inside cliffs."""
    def __init__(self, region, cell=10.0):
        d, pre = REG[region]
        tris = []
        for f in os.listdir(os.path.join(LAND3, d)):
            b = f[:-4]
            if not (f.endswith(".glb") and b.startswith(pre) and is_terrain(b) and not b.endswith("_lod1") and "scatter" not in b):
                continue
            m = trimesh.load(os.path.join(LAND3, d, f), force="mesh", process=False)
            tris.append(m.vertices[m.faces])
        self.tri = np.concatenate(tris).astype(np.float32)
        xz0 = self.tri[:, :, [0, 2]].min(1)
        xz1 = self.tri[:, :, [0, 2]].max(1)
        self.origin = xz0.min(0) - 1.0
        self.cell = cell
        ij0 = np.floor((xz0 - self.origin) / cell).astype(np.int32)
        ij1 = np.floor((xz1 - self.origin) / cell).astype(np.int32)
        self.shape = (int(ij1[:, 0].max()) + 1, int(ij1[:, 1].max()) + 1)
        buckets = [[] for _ in range(self.shape[0] * self.shape[1])]
        for t in range(len(self.tri)):
            for i in range(int(ij0[t, 0]), int(ij1[t, 0]) + 1):
                row = i * self.shape[1]
                for j in range(int(ij0[t, 1]), int(ij1[t, 1]) + 1):
                    buckets[row + j].append(t)
        self.buckets = [np.asarray(b, np.int32) if b else None for b in buckets]
        print(" height tris", len(self.tri), "cells", self.shape, flush=True)

    def y(self, x, z):
        i = int((x - self.origin[0]) / self.cell)
        j = int((z - self.origin[1]) / self.cell)
        if i < 0 or j < 0 or i >= self.shape[0] or j >= self.shape[1]:
            return None
        idx = self.buckets[i * self.shape[1] + j]
        if idx is None:
            return None
        T = self.tri[idx]
        p0, p1, p2 = T[:, 0], T[:, 1], T[:, 2]
        v0x = p1[:, 0] - p0[:, 0]; v0z = p1[:, 2] - p0[:, 2]
        v1x = p2[:, 0] - p0[:, 0]; v1z = p2[:, 2] - p0[:, 2]
        v2x = x - p0[:, 0]; v2z = z - p0[:, 2]
        dot00 = v0x * v0x + v0z * v0z
        dot01 = v0x * v1x + v0z * v1z
        dot02 = v0x * v2x + v0z * v2z
        dot11 = v1x * v1x + v1z * v1z
        dot12 = v1x * v2x + v1z * v2z
        den = dot00 * dot11 - dot01 * dot01
        ok = np.abs(den) > 1e-6
        inv = np.zeros_like(den)
        inv[ok] = 1.0 / den[ok]
        u = (dot11 * dot02 - dot01 * dot12) * inv
        v = (dot00 * dot12 - dot01 * dot02) * inv
        m = ok & (u >= -0.03) & (v >= -0.03) & (u + v <= 1.03)
        if not np.any(m):
            return None
        h = p0[:, 1] * (1.0 - u - v) + p1[:, 1] * u + p2[:, 1] * v
        return float(h[m].max())

def stand_y(hf, x, z):
    h = hf.y(x, z)
    if h is None or h < 0.45:
        return None
    return h

def los_ok(hf, cam, target):
    cam = np.asarray(cam, float); target = np.asarray(target, float)
    for t in (0.04, 0.1, 0.18, 0.28, 0.4):
        p = cam * (1.0 - t) + target * t
        h = hf.y(p[0], p[2])
        if h is not None and h > p[1] + 1.2:
            return False
    return True

shots = []
def add(region, name, cam, at, fov=50, feet=None):
    gy = float(feet if feet is not None else cam[1] - 1.65)
    # hero stands beside the camera, feet on the ground, so the capsule does not enclose the lens
    shots.append(dict(region=region, name=name, fov=fov, cam=[float(v) for v in cam], at=[float(v) for v in at],
                      hero=[float(cam[0] + 3.6), gy + 0.95, float(cam[2] - 2.8)]))

for region in REG:
    print("cameras", region, flush=True)
    o, c, H, COL, CNT = grid(region)
    hf = Height(region)
    # GROUND: inland, gentle, and the look point is still on land. Eye height is the real surface, not the cell average.
    best_g = None
    step = 4
    for i, j in np.argwhere((H[1:-1, 1:-1] > 3.2) & (H[1:-1, 1:-1] < 16.0)):
        i, j = int(i) + 1, int(j) + 1
        if (i + j) % step:
            continue
        h = float(H[i, j])
        nbr = [float(H[i + di, j + dj]) for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1))]
        if min(nbr) < 2.0 or max(abs(v - h) for v in nbr) > 2.0:
            continue
        land = 0
        for di in range(-4, 5):
            for dj in range(-4, 5):
                if H[i + di, j + dj] > 2.0:
                    land += 1
        if best_g is None or land > best_g[0]:
            best_g = (land, i, j, h)
    if best_g:
        _, i, j, h = best_g
        gx = o[0] + i * c; gz = o[1] + j * c
        gy = stand_y(hf, gx, gz) or h
        look = None
        for di, dj in ((2, 1), (1, 2), (-2, 1), (2, -1), (1, 0), (0, 1)):
            lx, lz = gx + di * 4.0, gz + dj * 4.0
            lh = stand_y(hf, lx, lz)
            if lh is not None and abs(lh - gy) < 2.4:
                look = (lx, min(lh, gy) + 0.35, lz)
                break
        if look is None:
            look = (gx + 6.0, gy + 0.2, gz + 4.0)
        add(region, f"{region}_ground", [gx, gy + 1.65, gz], look, fov=52, feet=gy)
    # SKYLINE: stand where the surface is well below the crest and the ray to the crest is not inside rock
    iy, ix = np.unravel_index(np.argmax(H), H.shape)
    px = o[0] + iy * c; pz = o[1] + ix * c; py = float(H[iy, ix])
    best = None
    for ang in np.linspace(0, 6.2, 20):
        for dist in (200, 320, 480, 700):
            cx, cz = px + np.cos(ang) * dist, pz + np.sin(ang) * dist
            ch = stand_y(hf, cx, cz)
            if ch is None:
                cam_y, ch = 8.0, 0.4
            else:
                if ch > py * 0.34:
                    continue
                cam_y = ch + 6.0
            cam = np.array([cx, cam_y, cz])
            at = np.array([px, py * 0.72, pz])
            if not los_ok(hf, cam, at):
                continue
            score = (py - ch) + dist * 0.02
            if best is None or score > best[0]:
                best = (score, cam, at, ch)
    if best is None:
        # last resort: far side, camera lifted to the local surface so the frame cannot be inside the body
        cx, cz = px + 640.0, pz + 80.0
        ch = stand_y(hf, cx, cz) or 2.0
        best = (0, np.array([cx, max(ch, 2.0) + 14.0, cz]), np.array([px, py * 0.7, pz]), ch)
    _, cam, at, ch = best
    add(region, f"{region}_skyline", cam, at, fov=34, feet=ch)
    # COAST: bank under the camera, water in the lower frame
    ys, xs = np.nonzero((H > 1.2) & (H < 8.0))
    shore = None
    for i, j in zip(ys[::4], xs[::4]):
        for di, dj in ((3, 0), (-3, 0), (0, 3), (0, -3)):
            ii, jj = i + di, j + dj
            if 0 <= ii < H.shape[0] and 0 <= jj < H.shape[1] and H[ii, jj] < 0.25 and H[i, j] > 1.2:
                shore = (int(i), int(j), di, dj)
                break
        if shore:
            break
    if shore:
        i, j, di, dj = shore
        sx = o[0] + i * c; sz = o[1] + j * c
        ix2, iz2 = sx - di * c * 0.55, sz - dj * c * 0.55
        hy = stand_y(hf, ix2, iz2)
        if hy is None:
            hy = float(H[i, j])
        add(region, f"{region}_coast", [ix2, hy + 1.6, iz2], [sx + di * c * 0.2, 0.4, sz + dj * c * 0.2], fov=56, feet=hy)
    for k, I in MAN["islands"].items():
        if I["region"] != region:
            continue
        L = MAN["landings"][k]
        inl = np.array(L["inland"], float); inl /= np.linalg.norm(inl) + 1e-9
        sh = np.array([L["shore"][0], L["shore"][2]])
        perp = np.array([-inl[1], inl[0]])
        pos = sh + inl * 48.0
        hy = None
        for side in (0.0, 22.0, -22.0, 44.0, -44.0):
            pos = sh + inl * 48.0 + perp * side
            for _ in range(18):
                h0 = stand_y(hf, pos[0], pos[1])
                if h0 is not None and 2.0 < h0 < 28.0:
                    ring = []
                    for ang in np.linspace(0.0, 6.0, 8):
                        hh = stand_y(hf, pos[0] + np.cos(ang) * 12.0, pos[1] + np.sin(ang) * 12.0)
                        if hh is not None:
                            ring.append(hh)
                    # Reject a quay pressed against a cliff. A hillside stays inside this band.
                    if len(ring) >= 5 and max(ring) < h0 + 9.0 and min(ring) > h0 - 6.0:
                        hy = h0
                        break
                pos = pos + inl * 10.0
            if hy is not None:
                break
        if hy is None:
            pos = sh + inl * 90.0
            hy = stand_y(hf, pos[0], pos[1])
            if hy is None:
                pos = sh + inl * 24.0
                hy = stand_y(hf, pos[0], pos[1]) or (float(L["shore"][1]) + 1.5)
        look = pos + inl * 6.0
        lh = stand_y(hf, look[0], look[1])
        if lh is None or abs(lh - hy) > 2.5:
            look = pos
            lh = hy
        cam = pos - inl * 9.0
        cy = stand_y(hf, cam[0], cam[1])
        if cy is None or abs(cy - hy) > 3.0:
            cam = pos - inl * 4.0
            cy = stand_y(hf, cam[0], cam[1]) or hy
        add(region, f"{k}_ground", [cam[0], cy + 1.7, cam[1]], [look[0], min(lh, cy) + 0.4, look[1]], fov=50, feet=cy)
        sea = sh - inl * 10.0
        bank = sh + inl * 5.0
        by = stand_y(hf, bank[0], bank[1])
        if by is None:
            by = max(hy, 1.2)
        add(region, f"{k}_coast", [bank[0], by + 1.65, bank[1]], [sea[0], 0.35, sea[1]], fov=50, feet=by)
        mf = os.path.join(LAND3, REG[region][0], I["files"]["mesh"] + ".glb")
        if not os.path.exists(mf):
            continue
        s = trimesh.load(mf, force="mesh", process=False)
        V = np.asarray(s.vertices)
        peak = V[int(V[:, 1].argmax())]
        if peak[1] < 14:
            continue
        base = np.array([sh[0] - peak[0], sh[1] - peak[2]])
        base /= np.linalg.norm(base) + 1e-9
        picked = None
        for turn in np.linspace(-0.9, 0.9, 7):
            d = np.array([base[0] * np.cos(turn) - base[1] * np.sin(turn), base[0] * np.sin(turn) + base[1] * np.cos(turn)])
            for dist in (140, 220, 340, 520):
                cx, cz = peak[0] + d[0] * dist, peak[2] + d[1] * dist
                ch = stand_y(hf, cx, cz)
                if ch is None:
                    cam_y, ch = 8.0, 0.5
                else:
                    if ch > peak[1] * 0.36:
                        continue
                    cam_y = ch + 6.0
                cam = np.array([cx, cam_y, cz])
                at = np.array([peak[0], peak[1] * 0.68, peak[2]])
                if not los_ok(hf, cam, at):
                    continue
                score = peak[1] - ch
                if picked is None or score > picked[0]:
                    picked = (score, cam, at, ch)
        if picked is None:
            cx, cz = peak[0] + base[0] * 480.0, peak[2] + base[1] * 480.0
            ch = stand_y(hf, cx, cz)
            cam_y = 8.0 if ch is None else max(ch + 8.0, 6.0)
            picked = (0, np.array([cx, cam_y, cz]), np.array([peak[0], peak[1] * 0.66, peak[2]]), 0.5 if ch is None else ch)
        _, cam, at, ch = picked
        add(region, f"{k}_skyline", cam, at, fov=32, feet=ch)

json.dump(shots, open(os.path.join(ROOT, "shots_terrain.json"), "w"), indent=1)
print("terrain shots", len(shots))
for s in shots:
    print(f"  {s['region']:6} {s['name']}")
