#!/usr/bin/env python3
"""usage: perf_measure.py <wwwdir> <label> ; prints JSON lines. Headless chromium + CDP CPU throttle."""
import sys, json, http.server, threading, functools
from playwright.sync_api import sync_playwright
ROOT, LABEL = sys.argv[1], sys.argv[2]
RUNS = int(sys.argv[3]) if len(sys.argv) > 3 else 1
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a, **k): pass
    def end_headers(self): self.send_header('Cache-Control', 'no-store'); super().end_headers()
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Q, directory=ROOT)); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
INIT = """
window.__m={t0:performance.now(),frames:[],long:[],res:[],firstFrame:null};
new PerformanceObserver(l=>{for(const e of l.getEntries())__m.long.push([Math.round(e.startTime),Math.round(e.duration)])}).observe({entryTypes:['longtask']});
new PerformanceObserver(l=>{for(const e of l.getEntries())if(/\\.glb/.test(e.name))__m.res.push([e.name.split('/').pop(),Math.round(e.startTime),Math.round(e.responseEnd)])}).observe({entryTypes:['resource']});
let last=0;(function f(n){if(last)__m.frames.push([Math.round(n),Math.round((n-last)*10)/10]);last=n;requestAnimationFrame(f)})(0);
"""
def run(b, w, h, mob, thr, q):
    ctx = b.new_context(viewport={'width': w, 'height': h}, device_scale_factor=2.625 if mob else 1, is_mobile=mob, has_touch=mob, service_workers='block')
    pg = ctx.new_page(); pg.on('pageerror', lambda e: print('PE', e, file=sys.stderr)); pg.add_init_script(INIT)
    cdp = ctx.new_cdp_session(pg); cdp.send('Emulation.setCPUThrottlingRate', {'rate': thr})
    pg.goto(f'http://127.0.0.1:{port}/proto3d.html{q}', wait_until='commit')
    import time
    t_s=time.time(); ok=False
    while time.time()-t_s<200:
        time.sleep(0.2)
        try:
            st=pg.evaluate("[!!window.__p3d, window.__p3d&&__p3d.frames, document.readyState, (document.getElementById('diag')||{innerText:''}).innerText.slice(-80)]"); pass
            if st[1]>=1: ok=True; break
        except Exception as e: pass
    if not ok: print('ERR no frame', file=sys.stderr); ctx.close(); return {'error': 'no first frame'}
    ff = pg.evaluate('performance.now()')
    pg.wait_for_timeout(20000)
    r = pg.evaluate("""()=>{const m=__m,p=__p3d,r=p.renderer,i=r.info;
      const fr=m.frames.filter(x=>x[0]>0);
      let tti=null,run=0;for(const [t,d] of fr){ if(t<(window.__ff||0))continue; if(d<100){run++; if(run>=10){tti=t;break}} else run=0}
      const nav=performance.getEntriesByType('navigation')[0];
      return {ff:null,tti,long:m.long,frames:fr,glb:m.res,calls:i.render.calls,tris:i.render.triangles,geos:i.memory.geometries,tex:i.memory.textures,pr:r.getPixelRatio(),size:[r.domElement.width,r.domElement.height],prog:(r.info.programs||[]).length,loaded:p.glbInfo.loaded,marks:window.__p3dMarks||null,failed:p.glbInfo.failed,fps:p.fps,dom:Math.round(nav.domContentLoadedEventEnd)}}""")
    ctx.close()
    fr = r['frames']; d = [x[1] for x in fr if x[0] >= ff]
    firstFrame = next((x[0] for x in fr if x[0] >= 0), None)
    # first real frame time: first rAF where __p3d.frames>=1 observed ~ ff
    # TTI: after ff, first time 10 consecutive frames <100ms
    run = 0; tti = None
    for t, dd in fr:
        if t < ff - 200: continue
        if dd < 100:
            run += 1
            if run >= 10: tti = t; break
        else: run = 0
    win = [x for x in fr if x[0] <= 20000 + 0] ; w20 = [x[1] for x in fr if x[0] <= ff + 20000]
    lt = [l for l in r['long'] if l[0] <= ff + 20000]
    s = sorted(w20)
    return {'label': LABEL, 'viewport': f'{w}x{h}', 'throttle': thr, 'query': q, 'first_frame_ms': round(ff), 'tti_ms': tti,
      'frames_in_20s': len(w20), 'frame_p50': s[len(s)//2] if s else None, 'frame_p95': s[int(len(s)*.95)] if s else None, 'frame_max': s[-1] if s else None,
      'hitches_gt100': sum(1 for x in w20 if x > 100), 'hitches_gt250': sum(1 for x in w20 if x > 250),
      'longtasks_n': len(lt), 'longtasks_sum_ms': sum(l[1] for l in lt), 'longtasks_top': sorted(lt, key=lambda l: -l[1])[:6],
      'glb': r['glb'], 'calls': r['calls'], 'tris': r['tris'], 'geos': r['geos'], 'tex': r['tex'], 'pr': r['pr'], 'canvas': r['size'], 'programs': r['prog'], 'loaded': len(r['loaded']), 'marks': r.get('marks'), 'failed': r['failed']}
with sync_playwright() as p:
    b = p.chromium.launch(args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
    for (w, h, mob) in [(412, 915, True), (1920, 1080, False)]:
        for thr in (4, 6):
            for q in ('', '?party=0&npcs=0'):
                for _ in range(RUNS):
                    print(json.dumps(run(b, w, h, mob, thr, q)), flush=True)
    b.close()
