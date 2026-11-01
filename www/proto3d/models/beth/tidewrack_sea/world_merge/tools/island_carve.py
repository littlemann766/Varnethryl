"""Stage 10 (Beth, user decision): Saltglass (B) and Frost become big islands fully inside open sea.
Land is pulled back from every rectangle edge (B also from the ash overlap notch) along an fbm-wobbled inset,
so the coast gets coves and headlands; inland mountains fall smoothly to a -16 m sea floor over ~200 m.
A small shore-band noise also breaks any straight interior coast runs (stage 11).
Library: carve(region, x, z, h) -> new h. CLI: island_carve.py H <in.f32> <out.f32> | island_carve.py MESH <glb> ..."""
import sys, os, numpy as np
RECT = {'B': (-3000, -1500, -1200, 1700), 'frost': (-2400, -3000, 1500, -1500), 'ash': (-1800, 1450, 1500, 3000)}
INSET = {'B': (230, 80, 150, 330, 45, 110), 'frost': (170, 150, 60, 360, 70, 150), 'ash': (55, 30, 25, 110, 30, 70)}   # base, amp, min, max, in, out
ASH = (-1800, 1450, 1500, 3000)
rng = np.random.default_rng(1110)
def _oct(n):
    th = rng.uniform(0, np.pi, n); ph = rng.uniform(0, 2 * np.pi, n); return np.c_[np.cos(th), np.sin(th)], ph
OCT = [(_oct(7), wl) for wl in (900, 420, 190, 85, 38)]
def fbm(x, z, o0=0, o1=5):
    s = 0; a = 1; t = 0
    for (dirs, ph), wl in OCT[o0:o1]:
        k = 2 * np.pi / wl; v = sum(np.sin(k * (dirs[i, 0] * x + dirs[i, 1] * z) + ph[i]) for i in range(len(ph))) / np.sqrt(len(ph))
        s = s + a * v; t += a; a *= 0.55
    return s / t
def smin(a, b, k=140.0): return -k * np.logaddexp(-a / k, -b / k)
def rect_in(r, x, z):   # inside distance to the rect edges (rounded corners)
    return smin(smin(x - r[0], r[2] - x), smin(z - r[1], r[3] - z))
def rect_out(r, x, z):
    dx = np.maximum(np.maximum(r[0] - x, x - r[2]), 0); dz = np.maximum(np.maximum(r[1] - z, z - r[3]), 0)
    ins = np.minimum(np.minimum(x - r[0], r[2] - x), np.minimum(z - r[1], r[3] - z))
    return np.where((dx > 0) | (dz > 0), np.hypot(dx, dz), -ins)
def edge_d(reg, x, z):
    d = rect_in(RECT[reg], x, z)
    if reg == 'B': d = smin(d, rect_out(ASH, x, z) + 40.0)
    return d
def ss(a, b, x): t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
def carve(reg, x, z, h):
    x = np.asarray(x, float); z = np.asarray(z, float); h = np.asarray(h, float)
    n = fbm(x, z)                                  # -1..1-ish
    b, a, lo, hi, ti, to = INSET[reg]
    inset = np.clip(b + a * n + 30 * fbm(x + 777, z - 333, 2, 5), lo, hi)
    d = edge_d(reg, x, z)
    s = ss(inset - ti, inset + to, d)
    out = np.minimum(h, s * h + (1 - s) * -16.0)
    if reg == 'B':   # west spine: low hills tie the Saltglass pieces into one island (the port bay keeps a ~280 m west mouth)
        w = ss(inset - 10, inset + 40, d) * (1 - ss(inset + 170, inset + 240, x + 3000)) * (1 - np.exp(-((z - 110) / 150.0) ** 4))
        hill = 2.5 + 7.0 * ss(inset, inset + 120, d) + 6.0 * np.clip(fbm(x + 50, z - 70, 1, 5) + 0.3, 0, 1)
        out = np.maximum(out, w * hill + (1 - w) * -16.0)
    band = np.exp(-(out / 7.0) ** 2) * (1 - ss(inset + 140, inset + 210, d))                 # shore band wobble: breaks straight runs
    out = out + band * 6.0 * fbm(x - 1234, z + 99, 3, 5)
    return out, s
if __name__ == '__main__':
    if sys.argv[1] == 'H':
        H = np.fromfile(sys.argv[2], np.float32).reshape(640, 640).astype(float)
        c = -3200 + 5 + 10 * np.arange(640); X, Z = np.meshgrid(c, c)
        H2 = H.copy()
        for reg in RECT:
            r = RECT[reg]; m = (X >= r[0]) & (X <= r[2]) & (Z >= r[1]) & (Z <= r[3])
            if reg == 'B': m &= ~((X >= ASH[0]) & (Z >= ASH[1]))
            if reg == 'frost': m &= ~((X <= -1200) & (Z >= -1500))
            if reg == 'ash': m &= (X < -1450) | (Z < 1650)
            H2[m] = np.minimum(H2[m], carve(reg, X[m], Z[m], H[m])[0]) if reg == 'ash' else carve(reg, X[m], Z[m], H[m])[0]
        H2.astype(np.float32).tofile(sys.argv[3]); print('H carved', (H > 0).sum(), '->', (H2 > 0).sum(), 'land cells')
