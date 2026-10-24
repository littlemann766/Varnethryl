#!/usr/bin/env python3
"""Natural-route stair test: the simulated player starts OUTSIDE the front door, aims straight at the stairs (centre, then the top) with keyboard (8-way) or joystick, like a real player.
usage: python3 tools/stairs_route_test.py  (ONLY=id,id MODE=key|joy|touch|key,joy,touch YAWS=0 PARTY=2 BASE=<live url>)"""
# the test teleports the hero between buildings: companions are placed next to the hero at each start (followers never snap up a floor, and after the
# guild hall they would still be waiting at its door, so a far-away start would only measure the long walk back)
import http.server, threading, functools, os, sys, json, math
from playwright.sync_api import sync_playwright
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'www')
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a, **k): pass
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Q, directory=ROOT)); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
ONLY = os.environ.get('ONLY', '').split(',') if os.environ.get('ONLY') else None
BFS = """([a,g,lv])=>{const S=.3,x0=a[0]-(g.length>2?15:0)+Math.min(0,g[0]-a[0])-8,z0=a[1]-(g.length>2?15:0)+Math.min(0,g[1]-a[1])-8,W=Math.ceil((Math.abs(a[0]-g[0])+(g.length>2?30:16))/S),H=Math.ceil((Math.abs(a[1]-g[1])+(g.length>2?30:16))/S);
const ok=(i,j)=>i>=0&&j>=0&&i<W&&j<H&&__p3d.free(x0+i*S,z0+j*S,lv);const idx=(i,j)=>j*W+i;
let s=null,bd=1e9;for(let i=0;i<W;i++)for(let j=0;j<H;j++){const d=Math.hypot(x0+i*S-a[0],z0+j*S-a[1]);if(d<bd&&d<4&&ok(i,j)){bd=d;s=[i,j];}}
if(!s)return null;const prev=new Map([[idx(...s),-1]]);const q=[s];
for(let h=0;h<q.length;h++){const [i,j]=q[h];for(const [di,dj] of [[1,0],[-1,0],[0,1],[0,-1],[1,1],[1,-1],[-1,1],[-1,-1]]){const ni=i+di,nj=j+dj;if(!prev.has(idx(ni,nj))&&ok(ni,nj)){prev.set(idx(ni,nj),idx(i,j));q.push([ni,nj]);}}}
let e=null,ed=1e9;for(const [i,j] of q){if(g.length>2&&__p3d.onRamp(x0+i*S,z0+j*S,lv))continue;const d=g.length>2?-Math.min(10,Math.hypot(x0+i*S-a[0],z0+j*S-a[1])):Math.hypot(x0+i*S-g[0],z0+j*S-g[1]);if(d<ed){ed=d;e=[i,j];}}
if(!e)return [];const path=[];let c=idx(...e);while(c!==-1){path.push([x0+(c%W)*S,z0+Math.floor(c/W)*S]);c=prev.get(c);}path.reverse();
if(ed>6&&0)return null;const out=[];for(let k=2;k<path.length;k+=2)out.push(path[k]);out.push(path[path.length-1]);return out}"""
MODES = os.environ.get('MODE', 'key,joy').split(','); PARTY = os.environ.get('PARTY', '2'); BASE = os.environ.get('BASE')
YAWS = [float(v) for v in os.environ.get('YAWS', '0').split(',')]; SHOTS = os.environ.get('SHOTS')
THROTTLE = float(os.environ.get('THROTTLE', '0'))   # CPU throttle factor via CDP (4 = 4x slower) to emulate a laggy phone
fails = 0; total = 0
with sync_playwright() as p:
    b = p.chromium.launch(args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']); pg = b.new_page(viewport={'width': 390, 'height': 844}, has_touch=True)
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    cdp = pg.context.new_cdp_session(pg)
    if THROTTLE > 1: cdp.send('Emulation.setCPUThrottlingRate', {'rate': THROTTLE})
    pg.goto(f'{BASE or "http://127.0.0.1:%d" % port}/proto3d.html?party={PARTY}&npcs={1 if PARTY != "0" else 0}'); pg.wait_for_function('window.__p3d && window.__p3d.frames>5', timeout=120000); pg.wait_for_timeout(2500)
    if os.environ.get('HERO'): import heroscale; print('HERO', heroscale.apply(pg, os.environ['HERO']), flush=True); pg.wait_for_timeout(500)   # HERO=pip|phoenix|wren|owner|troll|vaelthryx (sizes from charscale.js)
    if PARTY != '0':   # companions load asynchronously: wait until they exist before the first run (a late spawn would start at the town gate)
        try: pg.wait_for_function("__p3d.bump.crowd.filter(c=>c.kind==='party' && c.root).length>=%d" % int(PARTY), timeout=90000)
        except Exception: print('    warn: companions not all loaded', flush=True)
    info = json.loads(pg.evaluate("JSON.stringify(__p3d.multi.filter(b=>b.id!=='walls'&&!/^(wt|gt)/.test(b.id)).map(b=>({id:b.id,K:b.K,ramps:b.ramps,d:b.footprint?b.footprint.d:2*(b.radius||4)/b.K,round:!b.footprint,r:b.radius/b.K})))"))
    def W(bid, lx, lz): return pg.evaluate("([id,lx,lz])=>__p3d.multi.find(b=>b.id===id).toW(lx,lz)", [bid, lx, lz])
    box = pg.evaluate("(()=>{const r=document.getElementById('stick').getBoundingClientRect();return [r.x+r.width/2,r.y+r.height/2,r.width/2]})()")
    def drive(via, top, mode, l1, y1, secs=22, tag='', near=None):
        held = set(); joy = False; t = 0; trace = []
        try:
            while t < secs * 1000:
                st = pg.evaluate("({x:__p3d.state.heroX,z:__p3d.state.heroZ,lv:__p3d.state.level,y:__p3d.state.heroY,cy:__p3d.state.camYaw})")
                if st['lv'] == l1 and (y1 is None or abs(st['y'] - y1) < .2) and (near is None or math.hypot(st['x'] - near[0], st['z'] - near[1]) < 1.0): return st, t, True
                while via and (math.hypot(via[0][0] - st['x'], via[0][1] - st['z']) < 1.1 or st['lv'] != 0): via = via[1:]
                gx, gz = via[0] if via else top
                dx, dz = gx - st['x'], gz - st['z']; d = math.hypot(dx, dz) or 1; dx /= d; dz /= d
                sy, cy = math.sin(st['cy']), math.cos(st['cy']); ix = dx * cy - dz * sy; iy = -dx * sy - dz * cy
                if mode == 'key':
                    want = set()
                    if iy > .38: want.add('w')
                    if iy < -.38: want.add('s')
                    if ix > .38: want.add('d')
                    if ix < -.38: want.add('a')
                    for k in held - want: pg.keyboard.up(k)
                    for k in want - held: pg.keyboard.down(k)
                    held = want
                else:
                    x, y = box[0] + ix * box[2] * .8, box[1] - iy * box[2] * .8
                    if mode == 'touch':
                        if not joy: cdp.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [{'x': box[0], 'y': box[1], 'id': 1}]}); joy = True
                        cdp.send('Input.dispatchTouchEvent', {'type': 'touchMove', 'touchPoints': [{'x': x, 'y': y, 'id': 1}]})
                    else:
                        if not joy: pg.mouse.move(box[0], box[1]); pg.mouse.down(); joy = True
                        pg.mouse.move(x, y)
                if os.environ.get('TRACE'): print('   ', round(st['x'],2), round(st['z'],2), st['lv'], round(st['y'],2), sorted(held), [round(v,1) for v in (via[0] if via else top)])
                pg.wait_for_timeout(120); t += 120
            return st, t, False
        finally:
            for k in held: pg.keyboard.up(k)
            if joy:
                if mode == 'touch': cdp.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []})
                else: pg.mouse.up()
    FOLL = "(()=>{const f=__p3d.bump.crowd.filter(c=>c.kind==='party');return f.length>0&&f.every(c=>c.level===__p3d.state.level&&Math.abs(c.y-__p3d.state.heroY)<3.2)})()"
    def followers_arrive(tag):
        global fails, total
        if PARTY == '0': return True
        total += 1
        if pg.evaluate("!!(window.__heroOnly && __heroOnly.has(__p3d.state.inside))"):   # playable-characters-only building (guild hall): companions must wait outside instead
            pg.wait_for_timeout(3000); ok = pg.evaluate("__p3d.bump.crowd.filter(c=>c.kind==='party').every(c=>c.level===0 && !__p3d.enterables.some(e=>e.id===__p3d.state.inside && (e.parts?e.parts[0]:e).insideTest(...(e.parts?e.parts[0]:e).toL(c.a.x,c.a.z))))")
            if not ok: print('    companions got into a hero-only building (%s)' % tag, flush=True); fails += 1
            return ok
        try: pg.wait_for_function(FOLL, timeout=45000); return True
        except Exception:
            print('    followers did NOT reach the hero floor (%s):' % tag, pg.evaluate("__p3d.bump.crowd.filter(c=>c.kind==='party').map(c=>[c.level,+c.y.toFixed(1),+c.a.x.toFixed(1),+c.a.z.toFixed(1)])"), 'hero', pg.evaluate("[__p3d.state.level,__p3d.state.heroY]"), flush=True); fails += 1; return False
    print('buildings', len(info), flush=True)
    if os.environ.get('LIST'): print('IDS', ','.join(b['id'] for b in info if any(m['l0'] == 0 for m in b['ramps']))); sys.exit(0)
    for bi in info:
        if ONLY and bi['id'] not in ONLY: continue
        for m in bi['ramps']:
            if m['l0'] != 0 and not os.environ.get('UPPER'): continue
            s, c = math.sin(m['ang']), math.cos(m['ang']); h = m['len'] / 2
            front = bi['r'] + 2.5 if bi['round'] else bi['d'] / 2 + 2.8
            start = W(bi['id'], 0, front); door = W(bi['id'], 0, (bi['r'] - 2.2) if bi['round'] else bi['d'] / 2 - 1.9); via = [door, W(bi['id'], m['cx'], m['cz'])] if os.environ.get('VIA', 'centre') == 'centre' else [door, W(bi['id'], m['cx'] - s * (h + 1.0), m['cz'] - c * (h + 1.0))]; top = W(bi['id'], m['cx'] + s * (h + 1.4), m['cz'] + c * (h + 1.4))
            if m['l0'] != 0:   # upper flights: start on the floor below the foot, walk up, then back down
                start = W(bi['id'], m['cx'] - s * (h - 0.5), m['cz'] - c * (h - 0.5)); via = []
            res = []
            for mode in MODES:
                for yw in YAWS:
                    pg.evaluate("([s,y,l])=>{__p3d.teleport(s[0],s[1],l);__p3d.state.target=null;__p3d.state.camYaw=y;for(const c of __p3d.bump.crowd)if(c.kind==='party'){c.a.x=s[0]+(Math.random()-.5)*1.5;c.a.z=s[1]+(Math.random()-.5)*1.5;c.level=__p3d.state.level;c.y=__p3d.state.heroY||0;c.ti=null;c.lvT=0;c.vxs=c.vzs=0}}", [start, yw, m['l0']]); pg.wait_for_timeout(300)
                    r, ms, ok = drive([list(v) for v in via], top, mode, m['l1'], m['y1']*bi['K']); total += 1
                    if not ok and m['l0'] == 0 and os.environ.get('PATHFIND', '1') == '1':   # a real player walks around furniture: BFS a free path door -> stair and retry
                        wp = pg.evaluate(BFS, [start, via[-1], 0]); print('    bfs', door, via[-1], wp and [[round(a,1),round(b,1)] for a,b in wp], flush=True)
                        if wp:
                            pg.evaluate("([s,y])=>{__p3d.teleport(s[0],s[1],0);__p3d.state.target=null;__p3d.state.camYaw=y;for(const c of __p3d.bump.crowd)if(c.kind==='party'){c.a.x=s[0]+(Math.random()-.5)*1.5;c.a.z=s[1]+(Math.random()-.5)*1.5;c.level=__p3d.state.level;c.y=__p3d.state.heroY||0;c.ti=null;c.lvT=0;c.vxs=c.vzs=0}}", [start, yw]); pg.wait_for_timeout(300)
                            r, ms, ok = drive([list(q) for q in wp], top, mode, m['l1'], m['y1']*bi['K'])
                    fails += 0 if ok else 1
                    if ok and os.environ.get('FOLLOW', '1') == '1' and not followers_arrive('up'): ok = False
                    if ok and os.environ.get('EXIT', '1') == '1':   # and actually walk off the top into the upper room (BFS over the upper floor to the room centre), not stuck on the last step
                        cur = pg.evaluate("[__p3d.state.heroX,__p3d.state.heroZ]"); goal = W(bi['id'], 0, 0); total += 1
                        wp = pg.evaluate(BFS, [cur, goal + [1], m['l1']]); ok3 = bool(wp) and (len(wp) > 0)
                        if ok3:
                            for q in wp:
                                r3, ms3, ok3 = drive([], list(q), mode, m['l1'], None, secs=8, near=list(q))
                                if not ok3: break
                        if not ok3: print('    exit-warn: cannot follow a walk path from the top landing into the upper room', bool(wp), pg.evaluate("[__p3d.state.heroX,__p3d.state.heroZ]"), flush=True)
                        if not ok3 and os.environ.get('EXITSTRICT'): fails += 1; ok = False
                        if True: pg.evaluate("([x,z,l])=>__p3d.teleport(x,z,l)", [cur[0], cur[1], m['l1']]); pg.wait_for_timeout(200)
                    if ok and os.environ.get('DOWN', '1') == '1':   # now turn around at the top and walk back down to the street
                        foot = W(bi['id'], m['cx'] - s * (h + 2.0), m['cz'] - c * (h + 2.0)); total += 1
                        r2, ms2, ok2 = drive([], foot, mode, m['l0'], m['y0']*bi['K']); fails += 0 if ok2 else 1
                        if not ok2: print('    descent stuck at', {k: round(v, 1) if isinstance(v, float) else v for k, v in r2.items()}, flush=True)
                        if ok2 and os.environ.get('FOLLOW', '1') == '1' and not followers_arrive('down'): ok2 = False
                        ok = ok and ok2; ms = (ms, ms2)
                    if not ok: print('    stuck near:', pg.evaluate("([x,z,l])=>__p3d.colliders.filter(c=>(c.lv===undefined||(Array.isArray(c.lv)?c.lv.includes(l):c.lv===l))&&(c.type==='box'?(Math.hypot(Math.max(c.minX,Math.min(x,c.maxX))-x,Math.max(c.minZ,Math.min(z,c.maxZ))-z)<1.1):(Math.hypot(c.x-x,c.z-z)<1.1+c.r))).map(c=>[c.type,c.b,c.minX,c.maxX,c.minZ,c.maxZ,c.x,c.z,c.r,c.lv,c.stair].map(v=>typeof v==='number'?+v.toFixed(2):v))", [r['x'], r['z'], r['lv']]))
                    if SHOTS: pg.screenshot(path=f"{SHOTS}/{bi['id']}_{mode}_{'ok' if ok else 'FAIL'}.png")
                    res.append(f"{mode}@{yw:+.1f}:" + (('OK ' + (('%.1f+%.1fs' % (ms[0]/1000, ms[1]/1000)) if isinstance(ms, tuple) else '%.1fs' % (ms/1000))) if ok else 'FAIL(lv%s y%.1f @%.1f,%.1f)' % (r['lv'], r['y'], r['x'], r['z'])))
            print('PASS' if all('FAIL' not in x for x in res) else 'FAIL', bi['id'], f"{m['l0']}->{m['l1']}", ' '.join(res), flush=True)
    b.close()
print('page errors:', errs[:5]); print(f'FAILS {fails}/{total}'); sys.exit(1 if fails else 0)
