#!/usr/bin/env python3
"""Render each GLB (via viewer.html) from front/side/back/3-4 and make a contact sheet vs the character sheet. usage: render_proto3d.py [outdir]"""
import http.server, threading, os, sys, functools, io
from playwright.sync_api import sync_playwright
from PIL import Image, ImageDraw
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'www'); OUT = sys.argv[1] if len(sys.argv) > 1 else '/workspace/shots/varn3d'
os.makedirs(OUT, exist_ok=True)
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a, **k): pass
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Q, directory=ROOT)); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
SH = '/workspace/sheets/'
SHEETS = dict(aldric='aldric', darius='darius', selene='selene', seraphine='x0', talia='x1', finn='x2', brynn='x3', mirelle='x6', nyx='x7', vesper='x8', thorne='x9', orin='orin2', elira='elira', elira_a='elira', rook='rook', wolf='rook', asha='asha', rowan='rowan', kael='kael', cedric='cedric', morwen='morwen', garruk='garruk')
NAMES = dict(aldric='Sir Aldric', darius='Darius Umbral', selene='Selene Frostveil', seraphine='Dame Seraphine', talia='Talia Stormcall', finn='Finn Valecourt', brynn='Brynn Cogwright', mirelle='Mirelle Thornroot', nyx='Nyx Varrin', vesper='Vesper Crowe', thorne='Brother Thorne', orin='Orin Ashlance', elira='Lady Elira', elira_a='Elira (Lucky v2 first try)', rook='Rook Wildbane', wolf='Wolf (Rook companion)', asha='Asha Ironfist', rowan='Rowan Firebrand', kael='Kael Runebinder', cedric='Cedric Vale', morwen='Morwen Blackveil', garruk='Garruk Stonefist')
only = os.environ.get('ONLY', '').split(',') if os.environ.get('ONLY') else list(SHEETS)
W, H = 520, 760
NEW = ('orin2', 'elira', 'elira_a', 'rook', 'asha', 'rowan', 'kael', 'cedric', 'morwen', 'garruk')
def front_crop(k):  # front view crop from sheet (first of four turnarounds)
    sk = SHEETS[k]
    if sk in NEW:
        im = Image.open(SH + sk + '.jpg').convert('RGB'); w, h = im.size
        if k == 'wolf': return im.crop((0, int(h * .30), int(w * .12), int(h * .5)))
        return im.crop((0, int(h * .06), int(w * .30), int(h * .46)))
    im = Image.open(SH + sk + ('.png' if k == 'orin' else '.jpg')).convert('RGB'); w, h = im.size
    y0 = {'aldric': .08, 'darius': .1, 'selene': .11, 'x0': .12, 'x1': .1, 'x2': .1, 'x3': .1, 'x6': .09, 'x7': .1, 'x8': .1, 'x9': .1}[sk]
    y1 = {'aldric': .5, 'darius': .5, 'selene': .5, 'x0': .5, 'x1': .5, 'x2': .5, 'x3': .52, 'x6': .5, 'x7': .5, 'x8': .5, 'x9': .5}[sk]
    return im.crop((0, int(h * y0), int(w * .27), int(h * y1)))
with sync_playwright() as p:
    b = p.chromium.launch(args=['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']); pg = b.new_page(viewport={'width': W, 'height': H})
    pg.on('pageerror', lambda e: print('PAGEERR', e)); pg.on('console', lambda m: print('c:', m.text) if m.type == 'error' else None)
    tiles = {}
    for k in only:
        views = []
        for yaw in (0, 1.57, 3.14, .6):
            pg.goto(f'http://127.0.0.1:{port}/proto3d/viewer.html?c={k}&bare=1&spin=0&t=1&yaw={yaw}'); pg.wait_for_function('window.__ready', timeout=20000); pg.wait_for_timeout(700)
            im = Image.open(io.BytesIO(pg.screenshot())).convert('RGB'); views.append(im); im.save(f'{OUT}/{k}_{["front","side","back","three"][len(views)-1]}.png')
        tiles[k] = views
    b.close()
# contact sheet: per row = sheet front crop | 3D front | 3D 3/4 | 3D back
cw = 300; rows = []
for k in only:
    f = front_crop(k); f = f.resize((int(f.width * 480 / f.height), 480))
    row = Image.new('RGB', (1440, 500), (30, 27, 36)); row.paste(f, (6, 10))
    for i, vi in enumerate((0, 3, 2)):
        v = tiles[k][vi].resize((342, 500)); row.paste(v, (330 + i * 343, 0))
    ImageDraw.Draw(row).text((1100, 12), NAMES[k] + '  (left: sheet front | 3D front, 3/4, back)', fill=(232, 220, 192))
    rows.append(row)
for n in range(0, len(rows), 3):
    sheet = Image.new('RGB', (1440, 500 * len(rows[n:n + 3])), (20, 18, 24))
    for i, r in enumerate(rows[n:n + 3]): sheet.paste(r, (0, i * 500))
    sheet.save(f'{OUT}/contact_{n // 3 + 1 + int(os.environ.get("CONTACT_START", "1")) - 1}.png')
print('done', OUT)
