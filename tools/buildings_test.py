#!/usr/bin/env python3
"""Walk-in / solid-wall test for every 3D building. Usage: python3 tools/buildings_test.py   (prints PASS/FAIL per building; exit 1 on failure)"""
import http.server, threading, functools, os, sys, json
from playwright.sync_api import sync_playwright
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'www')
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a, **k): pass
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Q, directory=ROOT)); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
JS_INFO = """(()=>{const out=[];for(const e of __p3d.enterables){const ps=e.parts?e.parts:[e];for(const b of ps){if(!b.toW||b.id==='walls'||b.id==='port_dock')continue;
 const r=b.radius&&!b.footprint?b.radius:0;const d=b.footprint?b.footprint.d:b.d,w=b.footprint?b.footprint.w:b.w;
 out.push({id:b.id,round:!b.footprint,w:w,d:d,r:b.radius/b.K,hasIn:!!b.insideTest,iw:b.iw,id_:b.id_,rot:b.rot,cx:b.cx,cz:b.cz,name:b.name})}}return JSON.stringify(out)})()"""
def run(pg, fn, args): return pg.evaluate(fn, args)
fails = 0
with sync_playwright() as p:
    b = p.chromium.launch(args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']); pg = b.new_page(viewport={'width': 390, 'height': 844})
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e))); pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
    pg.goto(f'http://127.0.0.1:{port}/proto3d.html?party=0&npcs=0'); pg.wait_for_function('window.__p3d && window.__p3d.frames>5', timeout=90000); pg.wait_for_timeout(800)
    infos = json.loads(pg.evaluate(JS_INFO))
    ONLY = os.environ.get('ONLY', '').split(',') if os.environ.get('ONLY') else None
    for bi in infos:
        if ONLY and bi['id'] not in ONLY: continue
        # v1.5.33: some doors are portals (the colosseum entrance opens the PvP coliseum map); always restart each building in the town zone
        if pg.evaluate('__p3d.zone') != 'town':
            pg.evaluate("__p3d.setZone('town')"); pg.wait_for_function("__p3d.zone==='town' && !__p3d.zonePending", timeout=60000); pg.wait_for_timeout(800)
        # local -> world helper executed in page
        def W(lx, lz): return pg.evaluate("([id,lx,lz])=>{for(const e of __p3d.enterables){for(const b of (e.parts||[e])){if(b.id===id)return b.toW(lx,lz)}}}", [bi['id'], lx, lz])
        def walk(src, dst, ms):
            pg.evaluate("([s,t])=>{__p3d.teleport(s[0],s[1]);__p3d.state.target={x:t[0],z:t[1]};}", [src, dst])
            for _ in range(int(ms / 500)):
                pg.wait_for_timeout(500)
                if pg.evaluate('__p3d.state.target===null'): break
            return pg.evaluate("({x:__p3d.state.heroX,z:__p3d.state.heroZ,ins:__p3d.state.inside})")
        front = (bi['r'] if bi['round'] else bi['d'] / 2)
        if bi['id'] == 'gatehouse':
            # v1.5.33 walks (not runs) by default at ~1.5 m/s in headless, and the gate is 27 m deep at its new scale: allow 30 s
            s = W(0, front + 0); a = W(0, 8); c = W(0, -8); r = walk(a, c, int(os.environ.get('GATE_MS', 30000))); ok = abs(r['x'] - c[0]) < 2 and abs(r['z'] - c[1]) < 2
            # a solid wall: walk at the tower for the same time; the hero must never get past the wall line (old check passed trivially when the walk was slow)
            a2 = W(7.0, 8); c2 = W(7.0, -8); mid2 = W(7.0, 0); r2 = walk(a2, c2, int(os.environ.get('GATE_MS', 30000))); ok2 = (r2['z'] - mid2[1]) * (a2[1] - mid2[1]) > 0
            print('PASS' if ok and ok2 else 'FAIL', 'gatehouse walk-through', ok, 'tower solid', ok2, '' if ok else ('stopped at %s, wanted %s' % ({k: (round(v, 1) if isinstance(v, float) else v) for k, v in r.items()}, [round(q, 1) for q in c]))); fails += 0 if ok and ok2 else 1; continue
        if not bi['hasIn']: continue
        if bi['id'].startswith(('wt','gt')): front = 4.4
        inner = (0.5 if bi['id'].startswith(('wt','gt')) else bi['r'] - 3.0) if bi['round'] else (bi['id_'] - 1.4)
        if bi['id']=='colosseum': inner = 0
        out_ = W(0, front + 3.5); tgt = W(0, inner)
        if bi['id'] == 'colosseum':   # v1.5.33 design: the town colosseum entrance is the portal to the PvP coliseum map
            r = walk(out_, tgt, 9000); z = pg.evaluate('__p3d.zone'); ok = z == 'coliseum' or r['ins'] == 'colosseum'; fails += 0 if ok else 1
            print('PASS' if ok else 'FAIL', f"colosseum    portal-to-coliseum zone={z} ins={r['ins']} ({bi['name']})"); continue
        r = walk(out_, tgt, 9000); walked_in = r['ins'] is not None and (bi['id']!='colosseum' or True) and (r['ins'] == bi['id'] or r['ins'] == 'port' or r['ins'].startswith('wt') or r['ins'].startswith('gt'))
        # solid: approach the side wall, should not get inside
        side = W((bi['r'] if bi['round'] else bi['w'] / 2) + 3, 0); mid = W(0, 0)
        r2 = walk(side, mid, 6000); solid = r2['ins'] is None or (r2['ins'] != bi['id'] and not (bi['id'] == 'port' and r2['ins'] == 'port'))
        if bi['id'].startswith('gt'):  # gate towers are mirrored: probe from the outer (town-wall) side only
            side2 = W(-((bi['r']) + 3), 0)
            if abs(side2[0]) > abs(side[0]): side = side2
            r2 = walk(side, mid, 6000); solid = r2['ins'] is None
        if os.environ.get('DBG'): print('  dbg', bi['id'], r, 'target', tgt, 'start', out_)
        ok = walked_in and solid; fails += 0 if ok else 1
        print('PASS' if ok else 'FAIL', f"{bi['id']:12s} walk-in={walked_in} walls-solid={solid} ({bi['name']})")
    b.close()
print('page errors:', errs[:5]); print('FAILS', fails); sys.exit(1 if fails else 0)
