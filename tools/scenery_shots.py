#!/usr/bin/env python3
"""Screenshots of several village views + draw-call/triangle numbers. usage: scenery_shots.py outdir prefix [port]"""
import sys, subprocess, time, json
from pathlib import Path
from playwright.sync_api import sync_playwright
root = Path(__file__).resolve().parents[1] / 'www'
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True); pre = sys.argv[2]; PORT = int(sys.argv[3]) if len(sys.argv) > 3 else 8911
srv = subprocess.Popen([sys.executable, '-m', 'http.server', str(PORT), '-d', str(root)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
VIEWS = [('gatein', (0, 16, 46), (0, 0, 8), 0, 14), ('plaza', (-14, 7, 27), (0, 1, 9), -9, 14), ('garden', (13, 6, 32), (24, 1, 14), 20, 20), ('west', (-27, 7, 4), (-12, 1, 15), -12, 16), ('guild', (15, 7, 5), (2, 1, -14), 2, -8), ('lamps', (0, 3.5, 33), (0, 2, 12), 0, 20), ('well', (-4.5, 3.2, 24), (-8.5, 1.2, 17.5), -8, 20), ('outer', (21, 9, 21), (35, 2, -20), 14, 12)]
ONLY = sys.argv[5].split(',') if len(sys.argv) > 5 else None
errs = []
EXTRA = sys.argv[4] if len(sys.argv) > 4 else ''
try:
    with sync_playwright() as p:
        b = p.chromium.launch(args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
        for tag, w, h, mob in [('1920x1080', 1920, 1080, False), ('412x915', 412, 915, True)]:
            ctx = b.new_context(viewport={'width': w, 'height': h}, device_scale_factor=1, has_touch=mob, is_mobile=mob, service_workers='block')
            pg = ctx.new_page(); pg.on('console', lambda m: errs.append(m.text) if m.type in ('error', 'warning') else None); pg.on('pageerror', lambda e: errs.append(str(e)))
            pg.goto(f"http://localhost:{PORT}/proto3d.html?party=0&npcs=0&nosave=1{EXTRA}"); pg.wait_for_function('window.__p3d && window.__p3d.frames > 5', timeout=60000); pg.wait_for_timeout(1500)
            print(tag, 'start-view', json.dumps(pg.evaluate('__p3d.info()')), json.dumps(pg.evaluate('window.__sceneryStats ? [__sceneryStats.tris, __sceneryStats.variants] : null')))
            for name, cp, lk, hx, hz in VIEWS:
                if ONLY and name not in ONLY: continue
                pg.evaluate(f'__p3d.freeCam=true;__p3d.teleport({hx},{hz});const c=__p3d.camera;c.position.set({cp[0]},{cp[1]},{cp[2]});c.lookAt({lk[0]},{lk[1]},{lk[2]})'); pg.wait_for_timeout(1500)
                pg.screenshot(path=str(out / f'{pre}_{tag}_{name}.png'))
            ctx.close()
        b.close()
finally:
    srv.terminate()
print('errors', errs)
