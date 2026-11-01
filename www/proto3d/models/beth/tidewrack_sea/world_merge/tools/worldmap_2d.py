"""Stage 10/11 (Beth): world-map top-down in the style of Lucky's 2edf5ff ui/world_map.gd (_build_sea + _draw):
one deep-water background, shallows from each region's shore-distance map, land sand / frost white / ash dark,
the mainland land copy at LAND_AT (1900,300) from main's sea mask (±700), ports (gold) and landings (blue squares).
Usage: worldmap_2d.py <tidewrack root (stage1..4 + landings.json)> <mainland rgba png> <out.png> [shore-map override dir]"""
import sys, json, numpy as np
from PIL import Image, ImageDraw, ImageFont
T, ML, OUT = sys.argv[1:4]
WORLD = (-3200, -3200, 6000, 6400)   # Lucky: widen world_map.gd WORLD to this so the mainland (to x 2600) and the outer islands are not cut; PXM = 5.0; W, H = int(WORLD[2] / PXM), int(WORLD[3] / PXM)
PXM = 5.0; W, H = int(WORLD[2] / PXM), int(WORLD[3] / PXM)
REG = {"A": ([-1200, -1300, 2700, 2600], "stage1/shaders/arch_shore_dist.png"), "B": ([-3000, -1500, 1800, 3200], "stage2/shaders/coast_shore_dist.png"),
       "frost": ([-2400, -3000, 3900, 1500], "stage4/shaders/frost_shore_dist.png"), "ash": ([-1800, 1450, 3300, 1550], "stage4/shaders/ash_shore_dist.png")}
X, Z = np.meshgrid(WORLD[0] + (np.arange(W) + 0.5) * PXM, WORLD[1] + (np.arange(H) + 0.5) * PXM)
def rd(r, x, z):
    dx = np.maximum(np.maximum(r[0] - x, x - (r[0] + r[2])), 0); dz = np.maximum(np.maximum(r[1] - z, z - (r[1] + r[3])), 0)
    ins = np.minimum(np.minimum(x - r[0], r[0] + r[2] - x), np.minimum(z - r[1], r[1] + r[3] - z))
    return np.where((dx > 0) | (dz > 0), np.hypot(dx, dz), -ins)
S = np.full((H, W), 255.0); RID = np.full((H, W), -1)
done = np.zeros((H, W), bool)
for k, (id_, (r, p)) in enumerate(REG.items()):
    m = (rd(r, X, Z) <= 0) & ~done
    im = np.array(Image.open(f'{T}/{p}').convert('L')).astype(float); ih, iw = im.shape
    u = np.clip(((X - r[0]) / r[2] * iw).astype(int), 0, iw - 1); v = np.clip(((Z - r[1]) / r[3] * ih).astype(int), 0, ih - 1)
    S[m] = im[v[m], u[m]]; RID[m] = k; done |= m
if len(sys.argv) > 4:   # unified world shore map (the tw_sea spec): no region rectangle anywhere
    WS = np.array(Image.open(sys.argv[4]).convert('L')).astype(float); n = WS.shape[0]
    S = WS[np.clip(((Z + 3200) / (6400 / n)).astype(int), 0, n - 1), np.clip(((X + 3200) / (6400 / n)).astype(int), 0, n - 1)]
    D = np.stack([rd(r, X, Z) for r, _ in REG.values()]); RID = np.where(RID < 0, D.argmin(0), RID)
DEEP = np.array([0.10, 0.24, 0.40]); SH = np.array([0.16, 0.36, 0.52])
img = np.tile(DEEP, (H, W, 1)); sea = S < 255
t = np.clip(S / 120.0, 0, 1)[..., None]; img = np.where(sea[..., None], SH * (1 - t) + DEEP * t, img)
land = S <= 0.5
img[land] = [0.52, 0.47, 0.33]; img[land & (RID == 2)] = [0.82, 0.86, 0.90]; img[land & (RID == 3)] = [0.30, 0.27, 0.26]
I = Image.fromarray((img * 255).astype(np.uint8)).convert('RGBA')
ml = Image.open(ML).convert('RGBA'); a = (int((1900 - 700 - WORLD[0]) / PXM), int((300 - 700 - WORLD[1]) / PXM)); s = int(1400 / PXM)
I.alpha_composite(ml.resize((s, s), Image.BILINEAR), a)
d = ImageDraw.Draw(I)
try: F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 18); FS = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 14)
except Exception: F = FS = ImageFont.load_default()
w2s = lambda x, z: ((x - WORLD[0]) / PXM, (z - WORLD[1]) / PXM)
LD = json.load(open(f'{T}/landings.json'))
S1 = json.load(open(f'{T}/stage1/meshes/stage1_manifest.json')); S2 = json.load(open(f'{T}/stage2/meshes/stage2_manifest.json')); S4 = json.load(open(f'{T}/stage4/meshes/stage4_manifest.json'))
ports = {'tidewrack': ('Tidewrack pier', (1900 - 425.6, 300 + 392)), 'gullhaven': ('Gullhaven', S1['props']['gullhaven']['anchor']),
         'saltglass': ('Saltglass Landing', S2['props']['saltglass_landing']['anchor']), 'frostreach': ('Frostreach Ice Dock', S4['props']['frostreach_ice_dock']['anchor']),
         'vent': ('Vent Harbour', S4['props']['vent_harbour']['anchor'])}
for k, v in LD.items():
    q = w2s(v['shore'][0], v['shore'][2]); d.rectangle([q[0] - 5, q[1] - 5, q[0] + 5, q[1] + 5], fill='#7fd4ff', outline='black', width=2)
    if k not in ports: d.text((q[0] + 9, q[1] + 6), v.get('name', k), fill='#bfe9ff', font=FS)
for k, (nm, pv) in ports.items():
    q = w2s(pv[0], pv[2]) if len(pv) == 3 else w2s(*pv); d.ellipse([q[0] - 6, q[1] - 6, q[0] + 6, q[1] + 6], fill='#ffd27a'); d.text((q[0] + 9, q[1] - 9), nm, fill='white', font=F)
bg = Image.new('RGBA', (W + 80, H + 110), tuple(int(c * 255) for c in DEEP) + (255,)); bg.alpha_composite(I, (40, 90))
ImageDraw.Draw(bg).text((40, 30), 'WORLD MAP   (Owner: fully revealed)', fill='#f3d98b', font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 30) if F != ImageFont.load_default() else F)
bg.convert('RGB').save(OUT); np.save(OUT + '.land.npy', land); print('map', bg.size)
