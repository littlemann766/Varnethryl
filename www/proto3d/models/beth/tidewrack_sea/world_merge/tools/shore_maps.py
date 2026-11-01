"""Stage 10/11 (Beth): re-author the Saltglass / Frost / Ash shore-distance maps (R = metres to land, 3 m/px, 255 cap)
from the carved terrain meshes themselves: every tile + POI island mesh of the region is rasterised top-down (max y)
at 3 m, land = y > 0, distance via EDT. Also writes world_merge/world_shore_dist.png (all four regions merged, 5 m/px,
x/z -3200..3200) so the game can look shore distance up without any region rectangle. Originals -> shaders_v2_backup/.
Usage: shore_maps.py <tidewrack_sea dir> [--check]  (--check: rasterise the v2 backups and compare with the authored maps)"""
import sys, os, glob, shutil, numpy as np, trimesh
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
from scipy.ndimage import distance_transform_edt, zoom
R = sys.argv[1]; CHECK = '--check' in sys.argv
REG = {"B": ([-3000, -1500, 1800, 3200], "stage2", "coast_", "B"), "frost": ([-2400, -3000, 3900, 1500], "stage4", "frost_", "frost"),
       "ash": ([-1800, 1450, 3300, 1550], "stage4", "ash_", "ash"), "A": ([-1200, -1300, 2700, 2600], "stage1", "arch_", "A")}
from rast import raster
WORLD = {}
for k, (r, st, pre, isl) in REG.items():
    md = f'{R}/{st}/meshes_v2_backup' if CHECK else f'{R}/{st}/meshes'
    files = sorted(f for f in glob.glob(f'{md}/{pre}tile_x?z?.glb')) + ([f'{md}/arch_islands.glb'] if k == 'A' and os.path.exists(f'{md}/arch_islands.glb') else [])
    if CHECK: files += [f for f in glob.glob(f'{R}/{st}/meshes/{pre}tile_x?z?.glb') + glob.glob(f'{R}/{st}/meshes/arch_islands.glb' if k == 'A' else '/nonexistent') if not os.path.exists(f'{md}/' + os.path.basename(f))]
    sd = f'{R}/stage5_islands/meshes{"_v2_backup" if CHECK else ""}/{isl}'
    isls = sorted(glob.glob(f'{sd}/{pre}isl_*.glb')); isls = [f for f in isls if not any(t in f for t in ('_lod1', '_col', '_glow'))]
    if CHECK: isls += [f for f in glob.glob(f'{R}/stage5_islands/meshes/{isl}/{pre}isl_*.glb') if not any(t in f for t in ('_lod1', '_col', '_glow')) and not os.path.exists(f'{sd}/' + os.path.basename(f))]
    Hm = raster(files + isls, r, 3.0); land = Hm > 0.0
    p = f'{R}/{st}/shaders/{ {"B": "coast", "A": "arch"}.get(k, k)}_shore_dist.png'; bk = f'{R}/{st}/shaders_v2_backup/' + os.path.basename(p)
    os.makedirs(os.path.dirname(bk), exist_ok=True)
    if not os.path.exists(bk): shutil.copy(p, bk)
    old = np.array(Image.open(bk).convert('L')) <= 0
    if CHECK: print(k, 'authored land', int(old.sum()), 'raster land', int(land.sum()), 'agree %.1f%%' % (100 * (old == land[:old.shape[0], :old.shape[1]]).mean())); continue
    d = np.clip(distance_transform_edt(~land) * 3.0, 0, 255); Image.fromarray(d.astype(np.uint8), 'L').save(p)
    np.save(f'{R}/{st}/shaders_v2_backup/{k}_land3m.npy', land); WORLD[k] = (r, land); print(k, 'land px', int(old.sum()), '->', int(land.sum()))
if not CHECK:
    L = np.zeros((2133, 2133), bool)   # 3 m world mask -3200..3200
    for k, (r, m) in WORLD.items():
        i0, j0 = int(round((r[0] + 3200) / 3)), int(round((r[1] + 3200) / 3)); L[j0:j0 + m.shape[0], i0:i0 + m.shape[1]] |= m[:2133 - j0, :2133 - i0]
    np.save(os.environ.get("LAND3M", f"{R}/world_merge/world_land3m.npy"), L)
    d = np.clip(distance_transform_edt(~L) * 3.0, 0, 255); d5 = zoom(d, 3 / 5, order=1)
    Image.fromarray(d5.astype(np.uint8), 'L').save(f'{R}/world_merge/world_shore_dist.png'); print('world map', d5.shape)
