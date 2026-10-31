#!/usr/bin/env python3
"""Phone-size touch test: the hero selector is a scrollable list; swipe to the end, tap the last character."""
import http.server, threading, functools, os
from playwright.sync_api import sync_playwright
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'www')
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a, **k): pass
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Q, directory=ROOT)); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
SH = os.environ.get('SHOTS')
with sync_playwright() as p:
    b = p.chromium.launch(args=['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
    ok = True
    for name, vw, vh in (('portrait', 360, 640), ('landscape', 640, 360)):
        ctx = b.new_context(viewport={'width':vw,'height':vh}, has_touch=True, is_mobile=True); pg = ctx.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.goto(f'http://127.0.0.1:{port}/proto3d.html?nosave=1'); pg.wait_for_function('window.__p3d&&__p3d.frames>5', timeout=90000); pg.wait_for_timeout(2500)
        R = lambda sel: pg.evaluate("(s)=>{const e=document.querySelector(s);if(!e)return null;const r=e.getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2,w:r.width,h:r.height,t:r.y,b:r.bottom,l:r.x,r:r.right,vis:getComputedStyle(e).display!=='none'}}", sel)
        listVis = lambda: pg.evaluate("getComputedStyle(document.getElementById('hlist')).display!=='none'")
        closed0 = not listVis(); c = R('#hcur'); print(name, 'closed at start', closed0, 'cur', c)
        if SH: pg.screenshot(path=f'{SH}/sel_{name}_closed.png')
        pg.touchscreen.tap(c['x'], c['y']); pg.wait_for_timeout(500)
        opened = listVis(); l = R('#hlist'); print(name, 'open', opened, 'list', l)
        inview = l['t'] >= 0 and l['b'] <= vh and l['r'] <= vw
        sc = pg.evaluate("(()=>{const h=document.getElementById('hlist');return [h.scrollHeight,h.clientHeight]})()"); print('scroll', sc, 'rows', pg.evaluate("document.querySelectorAll('#hlist .row').length"))
        if SH: pg.screenshot(path=f'{SH}/sel_{name}_open.png')
        cdp = ctx.new_cdp_session(pg)
        for _ in range(40):
            y0 = l['y'] + 40; cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':l['x'],'y':y0}]})
            for k in range(1,13): cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':l['x'],'y':y0-k*15}]}); pg.wait_for_timeout(16)
            cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]}); pg.wait_for_timeout(200)
        st = pg.evaluate("document.getElementById('hlist').scrollTop"); print('scrollTop', st)
        r = pg.evaluate("(()=>{const bs=document.querySelectorAll('#hlist button[data-i]'),b=bs[bs.length-1],r=b.getBoundingClientRect();return [r.x+r.width/2,r.y+r.height/2,b.title,b.dataset.i,document.elementFromPoint(r.x+r.width/2,r.y+r.height/2)===b]})()"); print(r)
        if SH: pg.screenshot(path=f'{SH}/sel_{name}_scrolled.png')
        pg.touchscreen.tap(r[0], r[1]); pg.wait_for_timeout(4000)
        hi = pg.evaluate("__p3d.heroIndex"); shut = not listVis(); print('heroIndex', hi, 'want', r[3], 'closed after pick', shut)
        # variant switches: pick Darius, then Old
        pg.touchscreen.tap(c['x'], c['y']); pg.wait_for_timeout(300)
        d = pg.evaluate("(()=>{const b=[...document.querySelectorAll('#hlist button[data-i]')].find(b=>b.title==='Darius Umbral');b.scrollIntoView({block:'center'});const r=b.getBoundingClientRect();return [r.x+r.width/2,r.y+r.height/2]})()")
        pg.touchscreen.tap(d[0], d[1]); pg.wait_for_timeout(3000)
        chips = pg.evaluate("[...document.querySelectorAll('#hvars button')].map(b=>b.textContent)"); print('darius chips', chips)
        vk = lambda: pg.evaluate("(()=>{const h=__p3d.hero;return h&&h.userData&&(h.userData.blocky?'blocky':h.userData.glb?'glb':'none')})()")
        k0 = vk(); old = R('#hvars button[data-m="glb"]')
        pg.touchscreen.tap(old['x'], old['y']); pg.wait_for_timeout(7000); k1 = vk(); print('variant blocky->old', k0, k1)
        if SH: pg.screenshot(path=f'{SH}/sel_{name}_variant.png')
        bl = R('#hvars button[data-m="blocky"]'); pg.touchscreen.tap(bl['x'], bl['y']); pg.wait_for_timeout(3000); k2 = vk(); print('back', k2)
        good = closed0 and opened and inview and sc[0] > sc[1] and st > 0 and r[4] and str(hi) == r[3] and shut and 'Blocky' in chips and 'Old' in chips and k0 == 'blocky' and k1 == 'glb' and k2 == 'blocky' and not errs
        print(name, 'PASS' if good else 'FAIL', errs); ok = ok and good; ctx.close()
    print('PASS' if ok else 'FAIL'); b.close()
