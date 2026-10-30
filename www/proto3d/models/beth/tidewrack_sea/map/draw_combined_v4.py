#!/usr/bin/env python3
"""Beth: combined VARNETHRYL sea, one connected 6 x 6 km sea; regions stream one at a time. North up, metres, origin = Archipelago centre."""
import numpy as np, math
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage
S = 2000; W_M = 6000.0; pm = S / W_M
B = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'; R_ = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
F = ImageFont.truetype(B, 20); f2 = ImageFont.truetype(R_, 17); FT = ImageFont.truetype(B, 34); FR = ImageFont.truetype(B, 28)
def P(x, z): return (S / 2 + x * pm, S / 2 + z * pm)
rng = np.random.default_rng(2)
yy, xx = np.mgrid[0:S, 0:S]; MX = (xx - S / 2) / pm; MZ = (yy - S / 2) / pm
nz = ndimage.gaussian_filter(rng.normal(0, 1, (S, S)), 14); nz /= nz.std()
def fbm(seed, scales=(90, 40, 16, 6), amps=(1.0, 0.55, 0.3, 0.15)):
    r = np.random.default_rng(seed); out = np.zeros((S, S))
    for sc, am in zip(scales, amps):
        g = ndimage.gaussian_filter(r.normal(0, 1, (S, S)), sc); out += am * g / g.std()
    return out
N1 = fbm(11); N2 = fbm(12); N3 = fbm(13)
# domain-warped coordinates -> coves, bays and headlands instead of straight edges
WX = MX + N2 * 110; WZ = MZ + N3 * 110
land_f = np.full((S, S), -1e9)   # signed: >0 = land
def add(f):
    global land_f; land_f = np.maximum(land_f, f)
# mainland NE (existing world) with the sheltered Tidewrack bay
ne = np.minimum(WX - 1850 + 110 * np.sin(WZ / 150.0), -1250 - WZ + 110 * np.sin(WX / 170.0 + 1.0)) + N1 * 120
bay = 260 - np.hypot((MX - 2250) / 1.0, (MZ + 1750) / 1.35) + N1 * 25          # round sheltered bay
mouth = 70 - np.abs((MX - 2000) - (MZ + 1500) * 0.9) + N1 * 10                 # narrow mouth to the SW
mouth = np.where((MX < 2250) & (MX > 1750) & (MZ > -1800) & (MZ < -1150), mouth, -1e9)
ne = np.minimum(ne, -np.maximum(bay, mouth))
add(ne)
# Saltglass mainland (west): big headlands + coves, cliffs on the seaward edge
w = (-2300 - WX) + N1 * 220 + 160 * np.sin(WZ / 230.0) + 90 * np.sin(WZ / 97.0 + 1.0)
# north + south ends of the Saltglass land: natural headlands/coves too (no box clip)
w = np.minimum(w, (WZ + 1650) * 0.9 + N1 * 200 + 120 * np.sin(WX / 140.0) + 60 * np.sin(WX / 53.0 + 2.0))
w = np.minimum(w, (1850 - WZ) * 0.9 + N1 * 200 + 120 * np.sin(WX / 120.0 + 2.0) + 60 * np.sin(WX / 47.0))
add(w)
# islands: irregular (fbm on the radius)
ISL = [(-420, -380, 170), (260, 120, 120), (-560, 420, 110), (420, 640, 70), (0, -40, 40), (-150, 700, 200), (880, -300, 60), (-2150, -800, 120), (-1800, 300, 100), (-1500, -200, 80)]
for x, z, r in ISL: r = r * 1.3; add((1.0 - np.hypot(WX - x, WZ - z) / r) * r + N1 * r * 0.22)
# rivers / inlets: carve thin tapered channels into the land
def river(pts, w0, w1):
    global land_f
    dmin = np.full((S, S), 1e9); tq = np.zeros((S, S)); acc = 0; L = sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))
    for i in range(len(pts) - 1):
        a_ = np.array(pts[i], float); b_ = np.array(pts[i + 1], float); ab = b_ - a_; ll = np.linalg.norm(ab)
        t = np.clip(((MX - a_[0]) * ab[0] + (MZ - a_[1]) * ab[1]) / (ll * ll), 0, 1)
        dd = np.hypot(MX - (a_[0] + ab[0] * t), MZ - (a_[1] + ab[1] * t)); m = dd < dmin; dmin = np.where(m, dd, dmin); tq = np.where(m, (acc + t * ll) / L, tq); acc += ll
    width = w0 + (w1 - w0) * tq
    land_f = np.minimum(land_f, dmin - width + N1 * 4)
river([(-2950, -1200), (-2700, -1050), (-2520, -950), (-2380, -930)], 10, 45)
river([(-2950, 850), (-2750, 700), (-2600, 760), (-2420, 720)], 8, 40)
river([(2950, -2300), (2700, -2150), (2500, -1950), (2400, -1850)], 9, 35)   # river into Tidewrack bay
river([(-2900, -100), (-2600, -140), (-2450, -60)], 14, 70)                   # long inlet (fjord-ish)
land = (land_f > 0).astype(float)
ice = np.zeros((S, S)); ash = np.zeros((S, S))
icef = np.minimum(-2300 - WZ + 120 * np.sin(WX / 180.0), 1600 - WX + 120 * np.sin(WZ / 160.0)) + N1 * 160
for x, z, r in [(-900, -2000, 180), (-200, -1950, 120), (500, -2050, 140), (-1400, -1850, 100), (2500, 0, 90), (2300, -300, 60), (2350, 350, 70)]:
    icef = np.maximum(icef, (1 - np.hypot(WX - x, WZ - z) / r) * r + N1 * r * 0.25)
ice[icef > 0] = 1
ashf = np.full((S, S), -1e9)
for x, z, r in [(300, 2250, 300), (-600, 2050, 160), (1100, 2000, 140), (-1300, 2300, 120)]:
    ashf = np.maximum(ashf, (1 - np.hypot(WX - x, WZ - z) / r) * r + N1 * r * 0.3)
ash[ashf > 0] = 1
# scattered rocks + islets near shores
rr_ = np.random.default_rng(21); shore = ndimage.distance_transform_edt(1 - np.maximum(land, np.maximum(ice, ash))) / pm
cand = np.argwhere((shore > 20) & (shore < 140))
for k in rr_.choice(len(cand), 90, replace=False):
    j, i = cand[k]; r = rr_.uniform(5, 18) if rr_.uniform() < 0.9 else rr_.uniform(25, 45)
    m = np.hypot(MX - MX[j, i], MZ - MZ[j, i]) < r
    (ash if MZ[j, i] > 1700 else ice if MZ[j, i] < -2200 else land)[m] = 1
solid = np.maximum(land, np.maximum(ice, ash))
dist = ndimage.distance_transform_edt(1 - solid) / pm
deep = np.clip(dist / 450.0, 0, 1)
img = np.dstack([16 + 46 * (1 - deep), 56 + 100 * (1 - deep), 100 + 85 * (1 - deep)])
shallowm = np.clip(1 - dist / (60 + 50 * (N2 * 0.5 + 0.5)), 0, 1)[..., None]
img = img * (1 - shallowm * 0.7) + np.array([80, 190, 185]) * shallowm * 0.7
# land shading: lowland greens -> uplands, hillshade from fbm
ld = ndimage.distance_transform_edt(solid) / pm
hs = np.gradient(ndimage.gaussian_filter(N1 + ld / 300.0, 2))[0] * 6
sh = np.clip(0.82 + N3 * 0.06 + hs, 0.45, 1.2)[..., None]
lowc = np.array([96, 140, 70]); upc = np.array([70, 102, 56]); upl = np.clip(ld / 500.0, 0, 1)[..., None]
lcol = (lowc * (1 - upl) + upc * upl) * sh
img[land > 0] = lcol[land > 0]
img[ice > 0] = (np.array([226, 238, 246]) * sh)[ice > 0]; img[ash > 0] = (np.array([72, 62, 60]) * sh)[ash > 0]
# coast band: beaches (sandy where the noise says sheltered) vs cliffs (rocky, mostly on the Saltglass coast)
band = (solid > 0) & (ld < 18)
cliffy = ((MX < -2200) & (N2 > -0.4)) | (N2 > 0.9)
img[band & (land > 0) & ~cliffy] = [218, 200, 146]
cl = band & (land > 0) & cliffy & (ld < 12)
img[cl] = (np.array([112, 102, 92]) * sh)[cl]
img[cl & (ld < 5)] = [62, 56, 52]
# surf foam just offshore, broken by noise
foam = (dist > 2) & (dist < 9 + 5 * (N3 > 0)) & (N1 + N3 * 0.5 > -0.6) & (solid == 0)
img[foam] = img[foam] * 0.35 + np.array([240, 248, 250]) * 0.65
foam2 = (dist > 16) & (dist < 20) & (N2 > 0.3) & (solid == 0)
img[foam2] = img[foam2] * 0.6 + np.array([230, 240, 245]) * 0.4
# rivers tint
riv = (land_f <= 0) & (land_f > -60) & (dist < 1) 
im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(im, 'RGBA')
regions = [('A ARCHIPELAGO', (-1200, -1300, 1500, 1300), (255, 205, 60), 'Stage 1: open from the start (first voyage)'),
           ('B SALTGLASS COAST', (-3000, -1500, -1200, 1700), (180, 140, 255), 'Stage 3: unlock = defeat Brinecrown Coil'),
           ('C-N FROST STRAIT', (-3000, -3000, 1500, -1300), (200, 230, 255), 'Stage 4: unlock = Glasswyrm + Frostreach quest'),
           ('C-S ASH STRAIT', (-3000, 1700, 1500, 3000), (255, 140, 80), 'Stage 4: unlock = Volcano quest (Ashen Titan)'),
           ('C FAR STRAIT', (1500, -1300, 3000, 3000), (255, 80, 80), 'Finale: unlock = both straits')]
ov = Image.new('RGBA', (S, S), (0, 0, 0, 0)); do = ImageDraw.Draw(ov)
for name, (x0, z0, x1, z1), c, unlock in regions:
    do.rectangle([*P(x0, z0), *P(x1, z1)], outline=c + (220,), width=3)
oa = np.array(ov); oa[..., 3] = np.where(solid > 0, 0, oa[..., 3]); im.paste(Image.fromarray(oa), (0, 0), Image.fromarray(oa)); d = ImageDraw.Draw(im, 'RGBA')
def land_frac(x0, y0, x1, y1):
    x0, y0, x1, y1 = [int(max(0, min(S - 1, v))) for v in (x0, y0, x1, y1)]
    return solid[y0:y1, x0:x1].mean() if x1 > x0 and y1 > y0 else 1.0
taken = []
# v4: reserve the Sunken Ward box + its label, the wind roses and the legend so nothing lands on them
_sw0 = P(-1520, 150); _sw1 = P(-1080, 650); taken.append((_sw0[0] - 4, _sw0[1] - 4, _sw1[0] + 4, _sw1[1] + 34))
for _x, _z in [(900, 900), (-2000, 1450), (-1900, -2300), (-1800, 2500), (2250, 2400)]:
    _c = P(_x, _z); taken.append((_c[0] - 52, _c[1] - 52, _c[0] + 120, _c[1] + 74))
taken.append((20, S - 200, 520, S))
def busy(r):
    return any(not (r[2] < t[0] or r[0] > t[2] or r[3] < t[1] or r[1] > t[3]) for t in taken)
for name, (x0, z0, x1, z1), c, unlock in regions:
    bx0, by0 = P(x0, z0); bx1, by1 = P(x1, z1); wdt = max(d.textlength(name, font=FR), d.textlength(unlock, font=f2)) + 16
    best = None
    for yy_ in range(int(by0) + 8, int(by1) - 80, 24):
        for xx_ in range(int(bx0) + 8, int(bx1 - wdt) - 4, 24):
            r = (xx_, yy_, xx_ + wdt, yy_ + 66)
            if r[1] < 66 or busy(r): continue
            sc = land_frac(*r) * 10 + ((xx_ - bx0) + (yy_ - by0)) / 4000.0
            if best is None or sc < best[0]: best = (sc, xx_ - 6, yy_ - 6)
    tx, ty = best[1], best[2]; taken.append((tx, ty, tx + wdt + 8, ty + 70))
    d.rectangle([tx + 6, ty + 6, tx + 14 + d.textlength(name, font=FR), ty + 42], fill=(0, 0, 0, 160)); d.text((tx + 10, ty + 8), name, font=FR, fill=c)
    d.rectangle([tx + 6, ty + 44, tx + 14 + d.textlength(unlock, font=f2), ty + 68], fill=(0, 0, 0, 160)); d.text((tx + 10, ty + 46), unlock, font=f2, fill=(255, 255, 255))
x0, z0, x1, z1 = -1520, 150, -1080, 650; d.rectangle([*P(x0, z0), *P(x1, z1)], fill=(120, 255, 220, 50), outline=(120, 255, 220, 230), width=3)
tx, ty = P(x0, z1); d.rectangle([tx, ty + 2, tx + 10 + d.textlength('SUNKEN WARD (dive, Stage 2)', font=f2), ty + 26], fill=(0, 0, 0, 170)); d.text((tx + 4, ty + 4), 'SUNKEN WARD (dive, Stage 2)', font=f2, fill=(120, 255, 220))
for x, z, r in [(130, -420, 150), (-40, 300, 90), (650, 260, 70), (-1700, -500, 160), (-200, -1700, 200), (400, 1800, 150), (2100, 1300, 200)]:
    cx, cy = P(x, z); rr = r * pm; d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=(200, 40, 40, 70), outline=(220, 40, 40, 230), width=3)
d.rectangle([*P(-2995, -2995), *P(2995, 2995)], outline=(220, 40, 40, 255), width=8)
def route(pts, col, w):
    q = [P(*p) for p in pts]
    for a, b in zip(q, q[1:]):
        L = math.dist(a, b); n = max(1, int(L / 18))
        for i in range(0, n, 2):
            t0, t1 = i / n, min(1, (i + 1) / n); d.line([a[0] + (b[0] - a[0]) * t0, a[1] + (b[1] - a[1]) * t0, a[0] + (b[0] - a[0]) * t1, a[1] + (b[1] - a[1]) * t1], fill=col, width=w)
G = (255, 205, 60, 255); Wt = (255, 255, 255, 230); Dv = (120, 255, 220, 255)
route([(2300, -1900), (1500, -1200), (860, -820), (300, -160), (300, 40)], G, 6)
route([(860, -820), (-420, -560)], G, 5); route([(300, 40), (-380, 420), (-150, 650)], G, 5); route([(300, 40), (430, 560)], G, 5)
route([(-420, -560), (-1400, -400), (-2100, -300)], G, 5); route([(-1400, -400), (-1900, 450)], G, 5); route([(-1900, 450), (-1800, 1100)], G, 5)
route([(-2100, -300), (-2330, -300)], Wt, 3); route([(-1900, 450), (-2330, 360)], Wt, 3); route([(-1800, 1100), (-2330, 1100)], Wt, 3)
route([(-1300, 300), (-1300, 520)], Dv, 4)
route([(-420, -560), (-600, -1500), (-900, -1950)], G, 5); route([(-900, -1950), (-1100, -2280)], Wt, 3)
route([(-150, 650), (100, 1600), (-500, 1900)], G, 5)
route([(-600, -1500), (900, -1700), (2000, -900), (2350, 0)], G, 5); route([(100, 1600), (1200, 1650), (2000, 900), (2350, 0)], G, 5)
marks = [(2300, -1900, 'Tidewrack pier (board)', (255, 220, 80)), (-420, -380, 'Gullhaven', (255, 220, 80)), (0, -40, 'Lantern Rock', (255, 255, 255)),
 (130, -420, 'Wreck Reef', (200, 140, 90)), (-150, 700, 'Brinecrown Coil', (255, 60, 60)), (-2080, -130, 'Saltglass Landing', (255, 220, 80)),
 (-2330, -300, 'Echo Grotto', (170, 120, 255)), (-2330, 360, 'Glasswyrm Cavern', (255, 60, 60)), (-2330, 1100, "Smugglers' Throat", (170, 120, 255)),
 (-1300, 300, 'Dive buoy', (120, 255, 220)), (-900, -1950, 'Frostreach Ice Dock', (255, 220, 80)), (-1100, -2280, 'Rimefang Maw (frost cave)', (170, 120, 255)),
 (-500, 1900, 'Vent Harbour', (255, 220, 80)), (300, 2250, 'Cinderreach', (255, 170, 40)), (-560, 420, 'Saltwatch Keep', (255, 255, 255)), (2350, 0, 'Hollowberg', (255, 60, 60))]
for x, z, name, c in marks:
    cx, cy = P(x, z); d.ellipse([cx - 10, cy - 10, cx + 10, cy + 10], fill=c + (255,), outline=(0, 0, 0), width=3)
    tw = d.textlength(name, font=F); best = None
    for ox, oy in [(13, -13), (-21 - tw, -13), (-tw / 2, -42), (-tw / 2, 16), (13, -40), (13, 14), (-21 - tw, -40), (-21 - tw, 14), (40, -13), (-50 - tw, -13)]:
        r = (cx + ox, cy + oy, cx + ox + 8 + tw, cy + oy + 26)
        if r[0] < 4 or r[2] > S - 4 or r[1] < 66: continue
        sc = land_frac(*r) + (2.0 if busy(r) else 0.0)
        if best is None or sc < best[0] - 1e-6: best = (sc, r)
    r = best[1]; taken.append(r)
    d.rectangle(list(r), fill=(0, 0, 0, 160)); d.text((r[0] + 4, r[1] + 2), name, font=F, fill=(255, 255, 255))
for x, z, deg, lab in [(900, 900, 225, 'SW trade'), (-2000, 1450, 270, 'onshore W'), (-1900, -2300, 10, 'polar N'), (-1800, 2500, 160, 'hot S'), (2250, 2400, 300, 'strait gusts')]:
    cx, cy = P(x, z); a = math.radians(deg); tip = (cx + math.sin(a) * 38, cy - math.cos(a) * 38); tail = (cx - math.sin(a) * 38, cy + math.cos(a) * 38)
    d.ellipse([cx - 48, cy - 48, cx + 48, cy + 48], fill=(0, 0, 0, 120)); d.line([tail, tip], fill=(255, 255, 255), width=5)
    d.ellipse([tip[0] - 7, tip[1] - 7, tip[0] + 7, tip[1] + 7], fill=(255, 255, 255)); d.text((cx - 48, cy + 52), 'wind: ' + lab, font=f2, fill=(255, 255, 255))
d.rectangle([0, 0, S, 60], fill=(0, 0, 0, 190)); d.text((20, 11), 'VARNETHRYL: the Tidewrack Sea (combined v4, 6 x 6 km; regions stream in one at a time)', font=FT, fill=(255, 230, 160))
leg = [((255, 205, 60), 'galleon sail route'), ((255, 255, 255), 'skiff-only (caves / shallows)'), ((120, 255, 220), 'dive (Sunken Ward)'), ((220, 40, 40), 'no-go reef / zone edge'), ((200, 200, 200), 'region box = streaming cell')]
for i, (c, t) in enumerate(leg): y = S - 190 + i * 28; d.rectangle([24, y - 4, 330, y + 20], fill=(0, 0, 0, 150)); d.rectangle([28, y, 54, y + 16], fill=c); d.text((62, y - 3), t, font=f2, fill=(255, 255, 255))
d.rectangle([24, S - 34, 24 + 1000 * pm, S - 24], fill=(255, 255, 255)); d.text((24 + 1000 * pm + 10, S - 40), '1 km (galleon about 13 m/s)', font=f2, fill=(255, 255, 255))
np.savez_compressed('/workspace/godot-art/ocean_stage1/map/tidewrack_land_v4.npz', land_f=land_f.astype(np.float32), solid=solid.astype(np.uint8), dist_m=dist.astype(np.float32), N1=N1.astype(np.float32), metres_per_px=np.float32(1/pm))
im.save('tidewrack_sea_world_map_v4.jpg', quality=90); print('ok')
