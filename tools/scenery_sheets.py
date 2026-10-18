#!/usr/bin/env python3
"""Contact sheets of every scenery variant (all colour sets side by side) + scatter mixes. usage: scenery_sheets.py outdir [port]"""
import sys, subprocess, time, io, json
from pathlib import Path
from playwright.sync_api import sync_playwright
from PIL import Image, ImageDraw
root = Path(__file__).resolve().parents[1] / 'www'; out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True); PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 8931
srv = subprocess.Popen([sys.executable, '-m', 'http.server', str(PORT), '-d', str(root)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
CAT = {'trees': ['oak', 'pine', 'birch', 'cypress', 'apple', 'dead'], 'bushes': ['round', 'hedge', 'spiky', 'reeds', 'mushrooms'], 'flowers': ['daisy', 'tulip', 'lavender', 'bellflower', 'sunflower', 'grass'],
       'rocks': ['boulder', 'stone', 'cluster', 'slab', 'standing'], 'props': ['barrel', 'crate', 'lamp', 'well', 'signpost', 'noticeboard', 'fence', 'bench', 'haybale', 'logs', 'stump', 'cabbages']}
errs = []; info = {}
try:
    with sync_playwright() as p:
        b = p.chromium.launch(args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
        pg = b.new_page(viewport={'width': 1200, 'height': 520}); pg.on('console', lambda m: errs.append(m.text) if m.type in ('error', 'warning') else None); pg.on('pageerror', lambda e: errs.append(str(e)))
        for kind, names in CAT.items():
            tiles = []
            for n in names:
                extra = '&yaw=0.5&pitch=0.28' + ('&dist=9' if n in ('well',) else '')
                pg.goto(f'http://localhost:{PORT}/proto3d/scenery-viewer.html?c={kind}&v={n}&all=1&bare=1{extra}'); pg.wait_for_function('window.__ready', timeout=60000); pg.wait_for_timeout(900)
                im = Image.open(io.BytesIO(pg.screenshot())).convert('RGB'); lab = pg.evaluate('window.__sceneryInfo.label'); info[kind + '/' + n] = lab
                ImageDraw.Draw(im).text((8, 6), lab, fill=(20, 20, 30)); tiles.append(im); im.save(out / f'variant_{kind}_{n}.png')
            for i in range(0, len(tiles), 3):
                chunk = tiles[i:i + 3]; sh = Image.new('RGB', (1200, 520 * len(chunk)))
                for j, t in enumerate(chunk): sh.paste(t, (0, j * 520))
                sh.save(out / f'sheet_{kind}_{i // 3 + 1}.jpg', quality=90)
        for seed in (1, 2, 3):
            for tag, w, h in [('1920x1080', 1920, 1080), ('412x915', 412, 915)]:
                q = b.new_page(viewport={'width': w, 'height': h}); q.goto(f'http://localhost:{PORT}/proto3d/scenery-viewer.html?scatter=1&seed={seed}&bare=1&pitch=0.38&yaw={seed*1.3}&dist=22'); q.wait_for_function('window.__ready', timeout=90000); q.wait_for_timeout(1500)
                q.screenshot(path=str(out / f'scatter_seed{seed}_{tag}.png')); info[f'scatter{seed}'] = q.evaluate('window.__sceneryInfo.label'); q.close()
        b.close()
finally:
    srv.terminate()
print(json.dumps(info, indent=1)); print('errors', errs)
