#!/usr/bin/env python3
"""Inside view: entering a building fades its roof out (and back in on exit), hides upper floors above the hero's floor, and fades only the walls
between the camera and the hero; draw calls at spawn unchanged; companions still follow. Saves inside screenshots.
usage: python3 tools/inside_view_test.py [outdir]"""
import http.server, threading, functools, os, sys, json
from playwright.sync_api import sync_playwright
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'www')
OUT = sys.argv[1] if len(sys.argv) > 1 else None
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a, **k): pass
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Q, directory=ROOT)); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
fails = 0
def chk(n, c, x=''):
    global fails; print(('PASS ' if c else 'FAIL ') + n, x, flush=True); fails += 0 if c else 1
IDS = os.environ.get('ONLY', 'inn,smithy,townhall,library,bakery,keep,observatory').split(',')
B = "(id=>{for(const e of __p3d.enterables)for(const b of(e.parts||[e]))if(b.id===id)return b})"
with sync_playwright() as p:
    b = p.chromium.launch(args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']); pg = b.new_page(viewport={'width': 390, 'height': 844})
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(f'http://127.0.0.1:{port}/proto3d.html?nosave=1&party=2&npcs=1'); pg.wait_for_function('window.__p3d && __p3d.frames>5', timeout=180000); pg.wait_for_timeout(2000)
    calls0 = pg.evaluate("new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(()=>r(__p3d.renderer.info.render.calls))))")
    for bid in IDS:
        info = pg.evaluate("(id)=>{const b=" + B + "(id);if(!b||!b.viewState)return null;const f=b.footprint?b.footprint.d/2:b.radius/b.K;return {out:b.toW(0,f+4),inn:b.toW(0,0),rot:b.rot,vs:b.viewState()}}", bid)
        if not info: chk(bid + ' found', False); continue
        def tp(pt, wait):
            pg.evaluate("([p,r])=>{__p3d.teleport(p[0],p[1],0);__p3d.state.camYaw=r}", [pt, info['rot']]); pg.wait_for_timeout(wait)
            return pg.evaluate("(id)=>{const b=" + B + "(id),v=b.viewState(),c=b.ctx.cam.position,[x,z]=b.toL(c.x,c.z);v.cam=[x,z];v.beyondFront=b.footprint?z>b.id_-.25:Math.hypot(x,z)>b.iw*.7&&Math.abs(Math.atan2(x,z))<1.25;v.ext=b.extRanges?b.extRanges.every(r=>{const a=r.mesh.geometry.attributes.position.array;for(let i=r.start*3;i<(r.start+r.count)*3;i++)if(a[i]!==0)return true;return false}):null;return v}", bid)
        o = tp(info['out'], 1500)
        chk(bid + ' outside: roof shown, not inside', o['roofShown'] is not False and not o['inside'] and o['roofGroupVisible'], str(o))
        v = tp(info['inn'], 2500)
        upHidden = all(not vis for l, vis in v['up'].items() if int(l) > 0)
        chk(bid + ' inside: roof hidden (faded out), upper floors above hero hidden', v['inside'] and v['roofShown'] is not True and not v['roofGroupVisible'] and not v['fading'] and upHidden, str(v))
        s = v['sides']; camSide = 'f'
        chk(bid + ' inside: wall between camera and hero faded (only if the camera is beyond it), far wall opaque', (s.get(camSide, 1) < .5) == v['beyondFront'] and s.get('b', 1) > .95, str(s) + ' cam ' + str([round(q, 1) for q in v['cam']]))
        chk(bid + ' inside: exterior dressing hidden', v['ext'] in (False, None), str(v['ext']))
        if OUT: pg.wait_for_timeout(1500); os.makedirs(OUT, exist_ok=True); pg.screenshot(path=os.path.join(OUT, f'inside_{bid}.png'))
        o2 = tp(info['out'], 2500)
        chk(bid + ' exit: roof + exterior restored', o2['roofShown'] is not False and not o2['inside'] and o2['roofGroupVisible'] and not o2['fading'] and o2['ext'] in (True, None), str(o2))
    info = pg.evaluate("(id)=>{const b=" + B + "(id);return {out:b.toW(0,b.footprint.d/2+3),inn:b.toW(0,b.footprint.d/2-2.5)}}", 'inn')
    pg.evaluate("([p])=>{__p3d.teleport(p[0],p[1],0);for(const r of __p3d.bump.crowd)if(r.kind==='party'){r.a.x=p[0]+(Math.random()-.5);r.a.z=p[1]+1;r.level=0;r.y=0;r.ti=null}}", [info['out']]); pg.wait_for_timeout(1500)
    pg.evaluate("([p])=>__p3d.teleport(p[0],p[1],0)", [info['inn']]); pg.wait_for_timeout(9000)
    d = pg.evaluate("__p3d.bump.crowd.filter(r=>r.kind==='party').map(r=>+Math.hypot(r.a.x-__p3d.state.heroX,r.a.z-__p3d.state.heroZ).toFixed(1))")
    chk('companions follow the hero into the inn (inside view on)', len(d) > 0 and all(x < 6 for x in d), str(d))
    pg.evaluate("__p3d.teleport(0, %s, 0)" % "__p3d.roadInfo.PK*14"); pg.wait_for_timeout(2500)
    calls1 = pg.evaluate("new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(()=>r(__p3d.renderer.info.render.calls))))")
    chk('draw calls back to spawn level after visiting buildings', calls1 <= calls0 + 2, f'{calls0} -> {calls1}')
    chk('no page errors', not errs, str(errs[:3])); b.close()
print('FAILS', fails); sys.exit(1 if fails else 0)
