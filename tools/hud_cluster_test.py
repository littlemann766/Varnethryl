#!/usr/bin/env python3
"""1.1.9.4 HUD cluster: layout/overlap/touch targets (portrait + landscape), owner-gated Unholy Destruction through the real controller, non-owner lock. SHOTS=dir for screenshots."""
import http.server, threading, functools, os, sys
from playwright.sync_api import sync_playwright
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'www')
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a, **k): pass
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Q, directory=ROOT)); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
SH = os.environ.get('SHOTS'); bad = 0
def T(n, c):
    global bad; print('PASS' if c else 'FAIL', n); bad += 0 if c else 1
BOXES = """(()=>{const q=s=>[...document.querySelectorAll('#cb '+s)].filter(e=>e.offsetParent!==null||getComputedStyle(e).display!=='none').map(e=>{const r=e.getBoundingClientRect();return {s,x:r.x,y:r.y,w:r.width,h:r.height,t:e.dataset.s||e.dataset.a||''}});return [].concat(q('.sl'),q('.cl button'),q('.vit'),q('.tp'),q('.top button'))})()"""
def overlap(a, b): return a['x'] < b['x']+b['w']-1 and b['x'] < a['x']+a['w']-1 and a['y'] < b['y']+b['h']-1 and b['y'] < a['y']+a['h']-1
with sync_playwright() as p:
    b = p.chromium.launch(args=['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
    errs = []
    for name, vp in (('portrait', {'width':390,'height':844}), ('landscape', {'width':844,'height':390})):
        ctx = b.new_context(viewport=vp, has_touch=True, is_mobile=True); pg = ctx.new_page()
        pg.on('pageerror', lambda e: errs.append(str(e))); pg.on('console', lambda m: errs.append(m.text[:150]) if m.type == 'error' else 0)
        pg.goto(f'http://127.0.0.1:{port}/proto3d.html?nosave=1&party=0&npcs=0', wait_until='commit', timeout=120000); pg.wait_for_function('window.__p3d&&__p3d.frames>5', timeout=120000); pg.wait_for_timeout(1500)
        pg.evaluate("window.__p3d.owner=true; window.__p3d.cheats=window.__p3d.cheats||{}")   # test stand-in for the passphrase-gated owner boot
        pg.evaluate("__p3d.fightToggle()"); pg.wait_for_function("__p3d.fight&&__p3d.fight.on&&__p3d.fight.hasSaber", timeout=60000); pg.wait_for_timeout(1200)
        pg.evaluate("__p3d.fight.cc.god=true; __p3d.fight.cc.clearEnemies()")
        bx = pg.evaluate(BOXES); sl = [x for x in bx if x['s'] == '.sl']
        T(f'{name}: 5 cluster buttons (basic+3+ult)', len(sl) == 5 and len([x for x in sl if x['t'] == '0']) == 1)
        T(f'{name}: touch targets >= 44px', all(min(x['w'], x['h']) >= 44 for x in bx if x['s'] in ('.sl', '.cl button')))
        ov = [(a['s'] + a['t'], c['s'] + c['t']) for i, a in enumerate(bx) for c in bx[i+1:] if overlap(a, c)]
        ov = [o for o in ov if not (o[0].startswith('.tp') or o[1].startswith('.tp'))]
        T(f'{name}: no overlaps among HUD controls {ov}', not ov)
        T(f'{name}: all inside viewport', all(x['x'] >= 0 and x['y'] >= 0 and x['x']+x['w'] <= vp['width'] and x['y']+x['h'] <= vp['height'] for x in bx if x['s'] in ('.sl', '.cl button', '.vit')))
        u = next(x for x in sl if x['t'] == '4'); bs = next(x for x in sl if x['t'] == '0'); T(f'{name}: ultimate sits above basic', u['y']+u['h'] <= bs['y']+bs['h']*0.5 and abs((u['x']+u['w']/2)-(bs['x']+bs['w']/2)) < bs['w'])
        if name == 'portrait':
            T('owner: ult enabled (not locked)', pg.evaluate("!document.querySelector('#cb .sl[data-s=\"4\"]').classList.contains('off')"))
            pg.evaluate("(()=>{const f=__p3d.fight,c=f.cc;f.spawn('wolf',6);f.spawn('raider',12);f.spawn('wolf',60)})()")
            pg.wait_for_function("__p3d.fight.monsters.length>=3", timeout=60000); pg.evaluate("(()=>{const c=__p3d.fight.cc;c.setPlayer(c.p.x,c.p.z,c.p.yaw);const l=c.enemies.filter(e=>e.state!=='defeated').slice(0,3);window.__t=l;l.forEach((e,i)=>{e.x=c.p.x+[6,12,60][i];e.z=c.p.z;e.aggroR=0});c.fury=100;c.cd.reset()})()")
            T('fury bar visible for owner', pg.evaluate("getComputedStyle(document.querySelector('#cb .fy')).display!=='none'"))
            def tap(sel):
                q = pg.evaluate("(s=>{const r=document.querySelector(s).getBoundingClientRect();return [r.x+r.width/2,r.y+r.height/2]})", sel); pg.touchscreen.tap(q[0], q[1])
            pg.evaluate("(()=>{const f=__p3d.fight,c=f.cc,h=c.p;for(const e of c.enemies){if(e.key==='wolf'&&Math.hypot(e.x-h.x,e.z-h.z)>40){e.x=h.x+60;e.z=h.z}}})()")
            tap('#cb .sl[data-s="4"]'); pg.wait_for_timeout(900)
            if SH: pg.screenshot(path=f'{SH}/hud_meteor_fall.png')
            pg.wait_for_timeout(1000)
            if SH: pg.screenshot(path=f'{SH}/hud_meteor_impact.png')
            pg.wait_for_function("__p3d.fight.cc.meteors.length===0", timeout=90000); pg.wait_for_timeout(800); print('fps', pg.evaluate('__p3d.fps'))
            r = pg.evaluate("(()=>{const c=__p3d.fight.cc;return {st:window.__t.map(e=>e.state),kills:c.kills,fury:c.fury,cd:c.cd.left('unholy')}})()"); print(r)
            T('meteor via UI tap: in-range monsters defeated, far one survives', r['st'][0]=='defeated' and r['st'][1]=='defeated' and r['st'][2]!='defeated')
            T('Fury spent + cooldown running', r['fury'] < 100 and r['cd'] > 20)
            pg.evaluate("__p3d.fight.cc.fury=100;__p3d.fight.cc.cd.reset()"); pg.evaluate("__p3d.owner=false"); pg.wait_for_timeout(400)
            T('owner gate off: ult locked in HUD', pg.evaluate("document.querySelector('#cb .sl[data-s=\"4\"]').classList.contains('off')"))
            k0 = pg.evaluate("__p3d.fight.cc.kills"); pg.evaluate("__p3d.fight.spawn('wolf',5)"); pg.wait_for_timeout(300); tap('#cb .sl[data-s="4"]'); pg.wait_for_timeout(2200)
            T('owner gate off: tapping/programmatic ult does nothing', pg.evaluate("__p3d.fight.cc.meteors.length===0&&__p3d.fight.cc.fury===100") and pg.evaluate("__p3d.fight.use('unholy')") is not True)
        if SH: pg.screenshot(path=f'{SH}/hud_{name}.png')
        ctx.close()
    T('no page errors ' + str(errs[:3]), not errs)
    b.close()
print('FAILED' if bad else 'ALL PASS'); sys.exit(1 if bad else 0)
