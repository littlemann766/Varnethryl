#!/usr/bin/env python3
"""Beth: regenerate the v4 frost (ice) + ash land fields exactly as draw_combined_v4.py does (same seeds), without drawing.
Adds one lava spit off Cinderreach so the ash channel is a narrow strait. Output: ../map/straits_fields.npz"""
import numpy as np, math, os
from scipy import ndimage
SRC = '/workspace/beth-world/www/proto3d/models/beth/tidewrack_sea/map/draw_combined_v4.py'
src = open(SRC).read().split('\n')
a = next(i for i, l in enumerate(src) if l.startswith('S = 2000'))
b = next(i for i, l in enumerate(src) if l.startswith('solid = np.maximum'))
code = '\n'.join(l for l in src[a:b + 1] if not l.startswith(('B = ', 'F = ImageFont')))
g = {'np': np, 'math': math, 'ndimage': ndimage}; exec(code, g)
S, pm, MX, MZ, N1 = g['S'], g['pm'], g['MX'], g['MZ'], g['N1']
ice, ash, land = g['ice'], g['ash'], g['land']
# narrow the ash strait: a lava spit from Cinderreach reaching west towards Vent Harbour isle (leaves a ~140 m channel)
ax, az, bx, bz = 120, 2130, -70, 2075
abx, abz = bx - ax, bz - az; t = np.clip(((MX - ax) * abx + (MZ - az) * abz) / (abx * abx + abz * abz), 0, 1)
dd = np.hypot(MX - (ax + abx * t), MZ - (az + abz * t)); spit = (dd < (52 - 30 * t) + N1 * 16 + 10 * np.sin(MX / 23.0)) & (MZ > 1700)
ash = np.maximum(ash, spit.astype(float))
# Rimefang Narrows: an ice-cliff gorge joining the Frostreach bay to the eastern inlet (so the frost side has a real through-strait)
def carve(pts, w):
    dmin = np.full(MX.shape, 1e9)
    for (ax_, az_), (bx_, bz_) in zip(pts, pts[1:]):
        abx_, abz_ = bx_ - ax_, bz_ - az_; t_ = np.clip(((MX - ax_) * abx_ + (MZ - az_) * abz_) / (abx_ * abx_ + abz_ * abz_), 0, 1)
        dmin = np.minimum(dmin, np.hypot(MX - (ax_ + abx_ * t_), MZ - (az_ + abz_ * t_)))
    return dmin < w + N1 * 10
cut = carve([(-220, -2430), (60, -2395), (330, -2370), (580, -2300)], 42) | carve([(440, -2210), (300, -2120), (262, -1990), (275, -1860)], 32)
ice = np.where(cut, 0, ice); land = np.where(cut, 0, land)
ice = ice * (MZ < -1300); ash = ash * (MZ > 1300)
def sdf(m):
    m = m > 0; return np.where(m, ndimage.distance_transform_edt(m), -ndimage.distance_transform_edt(~m)) / pm
any_ = np.maximum(np.maximum(ice, ash), land)
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'map', 'straits_fields.npz')
np.savez_compressed(OUT, ice_f=sdf(ice).astype(np.float32), ash_f=sdf(ash).astype(np.float32), solid=(any_ > 0).astype(np.uint8),
                    dist_m=np.clip(-sdf(any_), 0, None).astype(np.float32), N1=N1.astype(np.float32), metres_per_px=np.float32(1 / pm))
print('ok', ice.sum(), ash.sum())
