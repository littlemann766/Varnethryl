#!/usr/bin/env python3
"""Cut out + normalize enemy art dropped in www/assets/enemies-incoming/ -> www/assets/enemies/<slug>.png + manifest.json."""
import sys, json, re, shutil, pathlib, argparse
from PIL import Image
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import build_hero_sprites as B
ROOT = B.ROOT; INC = ROOT / 'www/assets/enemies-incoming'; OUT = ROOT / 'www/assets/enemies'
DEFAULT_H = {'wild-wolf': 66, 'frost-hound': 72, 'forest-raider': 60, 'ash-skeleton': 62, 'vine-wraith': 66, 'ice-wraith': 62, 'rune-sentinel': 70, 'glacier-brute': 84, 'ashen-titan': 130}  # world px of the (height-limited) figure; wide quadrupeds use a larger value because they are width-limited on the canvas
def dekey(rgba):
    """Remove magenta/pink chroma-key background that rembg leaves in gaps (between limbs, under weapons) and despill the edge."""
    import numpy as np
    from scipy import ndimage as ndi
    a = np.array(rgba).astype(int); r, g, b = a[..., 0], a[..., 1], a[..., 2]
    key = (r - g > 70) & (b - g > 40) & (r > 120)
    key = ndi.binary_dilation(key, iterations=1) & (r - g > 35) & (b - g > 20) | key
    a[..., 3][key] = 0
    edge = ndi.binary_dilation(key, iterations=2) & ~key
    sp = edge & (r - g > 15) & (b - g > 10)
    a[..., 0][sp] = np.minimum(r[sp], g[sp] + 8); a[..., 2][sp] = np.minimum(b[sp], g[sp] + 8)
    return Image.fromarray(a.astype('uint8'))
def slug(p): return re.sub(r'[^a-z0-9]+', '-', p.stem.lower()).strip('-')
def main():
    ap = argparse.ArgumentParser(); ap.add_argument('files', nargs='*'); ap.add_argument('--height', type=float); ap.add_argument('--keep', action='store_true')
    a = ap.parse_args(); OUT.mkdir(exist_ok=True); (INC / 'processed').mkdir(exist_ok=True)
    files = [INC / f if not pathlib.Path(f).exists() else pathlib.Path(f) for f in a.files] or [p for p in sorted(INC.iterdir()) if p.suffix.lower() in ('.png', '.jpg', '.jpeg', '.webp')]
    if not files: print('nothing to ingest in', INC); return
    from rembg import new_session
    sess = new_session('isnet-general-use'); mf = OUT / 'manifest.json'; man = json.loads(mf.read_text()) if mf.exists() else {}
    for p in files:
        s = slug(p); im = Image.open(p).convert('RGB'); im.thumbnail((1600, 1600))
        fig = B.clean(dekey(B.cut(im, sess, (0, 0) + im.size)), fill=False)
        B.place(fig, 256, 256, 6, 242, 244).save(OUT / f'{s}.png', optimize=True)
        e = man.get(s, {}); e['height'] = a.height or e.get('height') or DEFAULT_H.get(s, 62); e['file'] = f'{s}.png'; man[s] = e
        if not a.keep and p.parent == INC: shutil.move(str(p), INC / 'processed' / p.name)
        print('enemy', s, e)
    mf.write_text(json.dumps(man, indent=1, sort_keys=True))
if __name__ == '__main__': main()
