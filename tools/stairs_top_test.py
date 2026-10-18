#!/usr/bin/env python3
"""Top-of-stair landing probe: along every flight's axis (and +-0.6 m lateral) from 1 m before the top to 3.5 m past it, at the upper level, report collider/floor blockage."""
import http.server, threading, functools, os, json
from playwright.sync_api import sync_playwright
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'www')
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a, **k): pass
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Q, directory=ROOT)); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
JS = """()=>{const out=[];const P=__p3d;for(const b of P.multi){for(const m of b.ramps){const s=Math.sin(m.ang),c=Math.cos(m.ang);
 for(const v of [0,-.6,.6]){let first=null,why=null;for(let u=m.len/2-1;u<=m.len/2+3.5;u+=.15){
  const lx=m.cx+s*u+c*v,lz=m.cz+c*u-s*v;const [wx,wz]=b.toW(lx,lz);const sf=b.surface(wx,wz,m.l1);
  const ok=P.free(wx,wz,m.l1);if(!ok){first=+(u-m.len/2).toFixed(2);why=sf?'collider':'nofloor';break;}}
  if(first!==null&&first<2.8)out.push({b:b.id,len:m.len,v,past:first,why});}}}return out;}"""
with sync_playwright() as p:
    b = p.chromium.launch(args=['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']); pg = b.new_page(viewport={'width':390,'height':844})
    pg.goto(f'http://127.0.0.1:{port}/proto3d.html?party=0&npcs=0'); pg.wait_for_function('window.__p3d && window.__p3d.frames>3', timeout=90000)
    r = pg.evaluate(JS)
    for x in r: print(x)
    print('blocked probes', len(r)); b.close()
