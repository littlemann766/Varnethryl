#!/usr/bin/env python3
"""Road network: every building entrance is reachable from the town gate walking ONLY on road surface
(main streets, plaza, side lanes), and nothing (collider) blocks a door or a lane. Grid BFS over road cells that
are free for the hero at ground level. usage: python3 tools/roads_test.py"""
import http.server, threading, functools, os, sys, json
from playwright.sync_api import sync_playwright
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'www')
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a, **k): pass
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Q, directory=ROOT)); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
fails = 0
def chk(n, c, x=''):
    global fails; print(('PASS ' if c else 'FAIL ') + n, x, flush=True); fails += 0 if c else 1
JS = r"""(()=>{const P=__p3d,I=P.roadInfo,R=P.roads,W=I.W,S=0.5,N=Math.ceil(2*W/S),hw=I.ROAD_W/2-0.25;
 const onLane=(x,z)=>{for(const r of R)for(let i=1;i<r.pts.length;i++){const[ax,az]=r.pts[i-1],[bx,bz]=r.pts[i],dx=bx-ax,dz=bz-az,L=dx*dx+dz*dz||1;const t=Math.max(0,Math.min(1,((x-ax)*dx+(z-az)*dz)/L));if(Math.hypot(x-ax-dx*t,z-az-dz*t)<hw)return true}return false};
 const road=(x,z)=>Math.abs(x)<2.5*I.KB-.3||Math.abs(z)<2*I.KB-.3||Math.hypot(x,z)<13*I.PK-.5||onLane(x,z);
 const ix=x=>Math.round((x+W)/S), xi=i=>i*S-W;
 const ok=new Uint8Array(N*N),seen=new Uint8Array(N*N);
 for(let i=0;i<N;i++)for(let j=0;j<N;j++){const x=xi(i),z=xi(j);if(Math.abs(x)<W-1&&Math.abs(z)<W+3&&road(x,z)&&P.free(x,z,0))ok[i*N+j]=1}
 const g=[ix(0),ix(W-2.5)];let q=[g[0]*N+g[1]];const gateOk=!!ok[q[0]];seen[q[0]]=1;
 while(q.length){const nq=[];for(const c of q){const i=(c/N)|0,j=c%N;for(const[di,dj]of[[1,0],[-1,0],[0,1],[0,-1]]){const a=i+di,b=j+dj;if(a<0||b<0||a>=N||b>=N)continue;const k=a*N+b;if(ok[k]&&!seen[k]){seen[k]=1;nq.push(k)}}}q=nq}
 const out=[];
 for(const e of P.enterables){for(const b of(e.parts||[e])){if(!b.toW||!b.insideTest||b.id==='walls'||b.id==='port_dock')continue;
  const r=R.find(q=>q.id===b.id);if(!r){out.push({id:b.id,lane:false});continue}
  const [dx,dz]=r.door;let reach=false;for(let a=-1;a<=1&&!reach;a++)for(let c=-1;c<=1&&!reach;c++){const k=(ix(dx)+a)*N+ix(dz)+c;if(seen[k])reach=true}
  const front=b.footprint?b.footprint.d/2:b.radius/b.K, inn=b.toW(0,front-0.4);
  let walk=true;const e2=r.pts[r.pts.length-1];for(let i=1;i<r.pts.length&&walk;i++){const[ax,az]=r.pts[i-1],[bx,bz]=r.pts[i],n=Math.ceil(Math.hypot(bx-ax,bz-az)/0.25);for(let k=0;k<=n;k++)if(!P.free(ax+(bx-ax)*k/n,az+(bz-az)*k/n,0)){walk=false;break}}
  walk=walk&&Math.hypot(e2[0]-R.gate[0],e2[1]-R.gate[1])<2;
  let bl=null;if(!reach&&!walk)for(let i=1;i<r.pts.length&&!bl;i++){const[ax,az]=r.pts[i-1],[bx,bz]=r.pts[i],n=Math.ceil(Math.hypot(bx-ax,bz-az)/0.5);for(let k=0;k<=n;k++){const x=ax+(bx-ax)*k/n,z=az+(bz-az)*k/n;if(!P.free(x,z,0)){const c=P.colliders.find(c=>c.type==='box'?x>c.minX-.5&&x<c.maxX+.5&&z>c.minZ-.5&&z<c.maxZ+.5:Math.hypot(x-c.x,z-c.z)<c.r+.5);bl=[+x.toFixed(1),+z.toFixed(1),c&&(c.b||c.id||c.type),c&&c.r];break}}}
  out.push({id:b.id,lane:!r.fail,reach:reach||walk,grid:reach,walk,doorFree:P.free(dx,dz,0),pts:r.pts.map(p=>p.map(v=>+v.toFixed(1))),bl})}}
 return JSON.stringify({gateOk,out})})()"""
with sync_playwright() as p:
    b = p.chromium.launch(args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']); pg = b.new_page(viewport={'width': 390, 'height': 844})
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(f'http://127.0.0.1:{port}/proto3d.html?nosave=1'); pg.wait_for_function('window.__p3d && __p3d.frames>5', timeout=180000); pg.wait_for_timeout(1000)
    r = json.loads(pg.evaluate(JS)); out = r['out']
    chk('gate cell is road and free', r['gateOk'])
    chk('every enterable building has a lane', len(out) > 20 and all(o['lane'] for o in out), str([o['id'] for o in out if not o['lane']]) + f' n={len(out)}')
    chk('no door blocked', all(o.get('doorFree') for o in out), str([o['id'] for o in out if not o.get('doorFree')]))
    bad = [o['id'] for o in out if not o.get('reach')]
    chk('every entrance reachable along roads from the gate', not bad, str(bad))
    for o in out:
        if not o.get('reach'): print('   ', o['id'], 'lane', o['pts'], 'blocked at', o['bl'])
    print('INFO lane centre-lines walkable end to end (grid route above is the pass/fail):', sum(1 for o in out if o.get('walk')), '/', len(out), [o['id'] for o in out if not o.get('walk')])
    chk('no page errors', not errs, str(errs[:3])); b.close()
print('FAILS', fails); sys.exit(1 if fails else 0)
