"""Same-camera shot list for before (land3) and after (land4). Heights come from land3 so the cameras match the untouched walk surface."""
import os, sys, json
import numpy as np
import trimesh
sys.path.insert(0, os.path.dirname(__file__))
from smooth_land import LAND3, REG, is_terrain, MAN

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def load_region(region, src_root):
    d, pre = REG[region]
    ms = []
    folder = os.path.join(src_root, d)
    for f in sorted(os.listdir(folder)):
        if not f.endswith(".glb") or f.endswith("_lod1.glb"):
            continue
        b = f[:-4]
        if b.startswith(pre) and is_terrain(b):
            s = trimesh.load(os.path.join(folder, f), force="mesh", process=False)
            ms.append((b, s))
    return ms

def height_grid(ms, cell=4.0):
    cols = []
    for b, s in ms:
        V = np.asarray(s.vertices)
        C = np.asarray(s.visual.vertex_colors)
        m = C[:, 3] > 127 if C.ndim == 2 else np.ones(len(V), bool)
        cols.append(np.concatenate([V[m][:, [0, 2]], V[m][:, 1:2], C[m][:, :3]], 1))
    P = np.concatenate(cols)
    origin = np.floor(P[:, :2].min(0)) - 8
    ij = np.floor((P[:, :2] - origin) / cell).astype(int)
    shape = tuple(ij.max(0) + 2)
    H = np.full(shape, -999, np.float32)
    # colour grid for border hunting
    COL = np.zeros(shape + (3,), np.float64)
    CNT = np.zeros(shape, np.float64)
    np.maximum.at(H, (ij[:, 0], ij[:, 1]), P[:, 2])
    np.add.at(COL, (ij[:, 0], ij[:, 1]), P[:, 3:6])
    np.add.at(CNT, (ij[:, 0], ij[:, 1]), 1)
    return origin, cell, H, COL, CNT

def h_at(origin, cell, H, x, z):
    i = int(np.floor((x - origin[0]) / cell)); j = int(np.floor((z - origin[1]) / cell))
    if i < 0 or j < 0 or i >= H.shape[0] or j >= H.shape[1] or H[i, j] < -100:
        return None
    return float(H[i, j])

def land_near(origin, cell, H, x, z):
    """Component centroids often sit in a bay. Walk outward until a real shore cell."""
    hy = h_at(origin, cell, H, x, z)
    if hy is not None and hy > 0.6:
        return x, z, hy
    for step in (12, 24, 40, 60, 90, 130, 180):
        for dx, dz in ((step, 0), (-step, 0), (0, step), (0, -step), (step, step), (-step, step), (step, -step), (-step, -step)):
            hy = h_at(origin, cell, H, x + dx, z + dz)
            if hy is not None and hy > 0.8:
                return x + dx, z + dz, hy
    return None

def main():
    inv = json.load(open(os.path.join(ROOT, "island_inventory.json")))
    shots = []
    for region in REG:
        ms = load_region(region, LAND3)
        origin, cell, H, COL, CNT = height_grid(ms)
        # mountain: highest cell
        iy, ix = np.unravel_index(np.argmax(H), H.shape)
        px = origin[0] + iy * cell + cell / 2
        pz = origin[1] + ix * cell + cell / 2
        py = float(H[iy, ix])
        mx, mz, mh = px + 140, pz + 100, py
        for dist in (100, 160, 240, 340):
            mx, mz = px + dist, pz + dist * 0.7
            mh = h_at(origin, cell, H, mx, mz)
            if mh is None or mh < py * 0.45:
                break
        if mh is None:
            mh = 4.0
        shots.append(dict(region=region, name=f"{region}_mountain", fov=46,
                          cam=[mx, max(mh + 10.0, py * 0.35), mz],
                          at=[px, py * 0.58, pz]))
        # ground close: a gentle inland cell
        flat = np.argwhere((H > 3) & (H < 18))
        if len(flat) == 0:
            flat = np.argwhere(H > 2)
        mid = flat[len(flat) // 3]
        gx = origin[0] + mid[0] * cell; gz = origin[1] + mid[1] * cell; gy = float(H[mid[0], mid[1]])
        shots.append(dict(region=region, name=f"{region}_ground_close", fov=50,
                          cam=[gx - 6.5, gy + 1.7, gz - 4.5],
                          at=[gx + 4, gy + 0.8, gz + 3],
                          hero=[gx, gy, gz]))
        # shore: a cell just above the water with a lower neighbour
        shore_ij = None
        ys, xs = np.nonzero((H > 0.4) & (H < 2.4))
        for i, j in zip(ys[::8], xs[::8]):
            if i + 2 < H.shape[0] and H[i + 2, j] < 0.2:
                shore_ij = (i, j); break
        if shore_ij:
            i, j = shore_ij
            sx = origin[0] + i * cell; sz = origin[1] + j * cell; sy = float(H[i, j])
            shots.append(dict(region=region, name=f"{region}_shore", fov=50,
                              cam=[sx + 14, max(sy, 0.6) + 1.4, sz + 6],
                              at=[sx, sy + 0.6, sz],
                              hero=[sx, sy, sz]))
        # border: high colour variance vs neighbour, on land
        best = None; bestv = 0
        known = CNT > 0
        avg = COL / np.maximum(CNT, 1)[:, :, None]
        for i, j in zip(*np.nonzero(known & (H > 4) & (H < 30))):
            if i + 3 >= avg.shape[0] or j + 3 >= avg.shape[1] or not known[i + 3, j + 3]:
                continue
            dv = np.abs(avg[i, j] - avg[i + 3, j + 3]).sum()
            if dv > bestv:
                bestv = dv; best = (i, j)
            if bestv > 180:
                break
        if best and bestv > 25:
            i, j = best
            bx = origin[0] + i * cell; bz = origin[1] + j * cell; by = float(H[i, j])
            shots.append(dict(region=region, name=f"{region}_border", fov=52,
                              cam=[bx - 10, by + 6, bz - 10],
                              at=[bx + 6, by + 1, bz + 6],
                              hero=[bx, by, bz]))
        # named islands
        for k, I in MAN["islands"].items():
            if I["region"] != region:
                continue
            L = MAN["landings"][k]
            inl = np.array(L["inland"], float); inl = inl / (np.linalg.norm(inl) + 1e-9)
            sh = np.array(L["shore"], float)
            p = np.array([sh[0], sh[2]]) + inl * (28 if k != "saltwatch_keep" else 14)
            hy = h_at(origin, cell, H, p[0], p[1])
            if hy is None:
                hy = float(sh[1])
            cam = p - inl * 7.5
            chy = h_at(origin, cell, H, cam[0], cam[1]) or hy
            shots.append(dict(region=region, name=f"{k}_close", fov=50,
                              cam=[cam[0], max(chy, hy) + 1.65, cam[1]],
                              at=[p[0] + inl[0] * 9, hy + 1.1, p[1] + inl[1] * 9],
                              hero=[p[0], hy, p[1]]))
            # silhouette if the island mesh rises
            mesh = I["files"]["mesh"]
            mp = os.path.join(LAND3, REG[region][0], mesh + ".glb")
            if os.path.exists(mp):
                s = trimesh.load(mp, force="mesh", process=False)
                V = np.asarray(s.vertices)
                peak = V[int(V[:, 1].argmax())]
                if peak[1] > 12:
                    # stand off toward the landing until the camera is on lower ground, so it isn't buried in the cliff
                    d = np.array([sh[0] - peak[0], sh[2] - peak[2]])
                    d = d / (np.linalg.norm(d) + 1e-9)
                    c = np.array([peak[0], peak[2]])
                    ch = peak[1]
                    for dist in (50, 80, 120, 170):
                        c = np.array([peak[0], peak[2]]) + d * dist
                        ch = h_at(origin, cell, H, c[0], c[1])
                        if ch is None or ch < peak[1] * 0.55:
                            break
                    if ch is None:
                        ch = 2.0
                    shots.append(dict(region=region, name=f"{k}_silhouette", fov=42,
                                      cam=[c[0], max(ch + 6.0, 8.0), c[1]],
                                      at=[peak[0], peak[1] * 0.62, peak[2]]))
        # islets not already covered by a named pier
        for rec in inv:
            if rec.get("region") != region or rec.get("kind") != "islet":
                continue
            if rec.get("area_m2", 0) < 2000:
                continue
            c = rec["centroid"]
            hit = land_near(origin, cell, H, c[0], c[1])
            if hit is None:
                continue
            x, z, hy = hit
            shots.append(dict(region=region, name=f"islet_{int(round(c[0]))}_{int(round(c[1]))}", fov=50,
                              cam=[x - 9, hy + 3.2, z - 7],
                              at=[x + 4, hy + 1.0, z + 3],
                              hero=[x, hy, z],
                              note=rec["id"]))
        # smallest skerry in the region, if we have one under 3500 and over 400
        small = [r for r in inv if r.get("region") == region and r.get("kind") == "islet" and 400 <= r.get("area_m2", 0) < 3500]
        if small:
            rec = min(small, key=lambda r: r["area_m2"])
            c = rec["centroid"]
            hit = land_near(origin, cell, H, c[0], c[1])
            if hit is None:
                continue
            x, z, hy = hit
            shots.append(dict(region=region, name=f"skerry_{int(round(c[0]))}_{int(round(c[1]))}", fov=48,
                              cam=[x - 8, hy + 2.4, z - 6],
                              at=[x, hy + 0.8, z],
                              hero=[x, hy, z],
                              note=rec["id"]))
        # lift cameras off the mesh
        for s in shots:
            if s["region"] != region:
                continue
            hh = h_at(origin, cell, H, s["cam"][0], s["cam"][2])
            if hh is not None:
                s["cam"][1] = max(s["cam"][1], hh + 1.5)
    json.dump(shots, open(os.path.join(ROOT, "shots.json"), "w"), indent=1)
    print("shots", len(shots))
    for s in shots:
        print(f"  {s['region']:6} {s['name']}")

if __name__ == "__main__":
    main()