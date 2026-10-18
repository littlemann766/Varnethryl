#!/usr/bin/env python3
"""Phone-size touch test: the hero selector is a scrollable list; swipe to the end, tap the last character."""
import http.server, threading, functools, os
from playwright.sync_api import sync_playwright
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'www')
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a, **k): pass
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Q, directory=ROOT)); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
with sync_playwright() as p:
    b = p.chromium.launch(args=['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
    ctx = b.new_context(viewport={'width':360,'height':640}, has_touch=True, is_mobile=True); pg = ctx.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(f'http://127.0.0.1:{port}/proto3d.html?all=1'); pg.wait_for_function('window.__p3d&&__p3d.frames>5', timeout=90000); pg.wait_for_timeout(2500)
    m = pg.evaluate("(()=>{const h=document.getElementById('heroes'),r=h.getBoundingClientRect();return {n:h.children.length,sh:h.scrollHeight,ch:h.clientHeight,x:r.x+r.width/2,y:r.y+r.height/2,top:r.y,bot:r.bottom}})()"); print(m)
    print('hit', pg.evaluate("(()=>{const e=document.elementFromPoint(%d,%d);return e&&(e.id||e.tagName)})()" % (m['x'],m['y'])))
    cdp = ctx.new_cdp_session(pg)
    for _ in range(5):
        y0=m['y']+120; cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':m['x'],'y':y0}]})
        for k in range(1,13): cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':m['x'],'y':y0-k*20}]}); pg.wait_for_timeout(16)
        cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]}); pg.wait_for_timeout(300)
    st = pg.evaluate("document.getElementById('heroes').scrollTop"); print('scrollTop', st)
    r = pg.evaluate("(()=>{const bs=document.querySelectorAll('#heroes button'),b=bs[bs.length-1],r=b.getBoundingClientRect();return [r.x+r.width/2,r.y+r.height/2,b.title,b.dataset.i,document.elementFromPoint(r.x+r.width/2,r.y+r.height/2)===b]})()"); print(r)
    pg.touchscreen.tap(r[0], r[1]); pg.wait_for_timeout(4000)
    hi = pg.evaluate("__p3d.heroIndex"); print('heroIndex', hi, 'want', r[3], 'errs', errs)
    ok = m['sh'] > m['ch'] and st > 0 and r[4] and str(hi) == r[3] and not errs
    print('PASS' if ok else 'FAIL'); b.close()
