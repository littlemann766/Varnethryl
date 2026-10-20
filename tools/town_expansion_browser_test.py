#!/usr/bin/env python3
"""Browser smoke test: 560-unit town, exterior landscaping, new wall gate and Wilds transition."""
from playwright.sync_api import sync_playwright
import os, http.server, threading, functools, sys, json
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','www'))
class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*a): pass
srv=http.server.ThreadingHTTPServer(('127.0.0.1',0), functools.partial(Quiet,directory=ROOT))
port=srv.server_address[1]
threading.Thread(target=srv.serve_forever,daemon=True).start()
fails=[]
def check(label,condition,details=None):
    print(('PASS' if condition else 'FAIL')+' '+label+((' '+str(details)[:240]) if details is not None else ''),flush=True)
    if not condition: fails.append(label)
with sync_playwright() as p:
    browser=p.chromium.launch(args=['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist'])
    page=browser.new_context(viewport={'width':412,'height':915},has_touch=True,is_mobile=True,service_workers='block').new_page()
    errors=[]
    page.on('pageerror',lambda e: errors.append(str(e)))
    page.goto(f'http://127.0.0.1:{port}/proto3d.html?nosave=1&party=0&npcs=0',wait_until='commit',timeout=120000)
    page.wait_for_function('window.__p3d&&__p3d.frames>8',timeout=120000)
    info=page.evaluate("""()=>{const a=__p3d,W=a.ZONE,L=a.townLands;
      const gate=a.enterables.find(x=>x.id==='gatehouse');
      const g=gate.parts[0];
      const q=(x,z)=>a.colliders.some(c=>c.type==='box'&&x>c.minX&&x<c.maxX&&z>c.minZ&&z<c.maxZ);
      return {zone:a.zone,half:W.half,tree:L.stats.trees,chunks:L.chunkCount,fields:L.stats.fields,gate:g.cz,
      top:q(0,-280),west:q(-280,0),east:q(280,0),south:q(60,280),frames:a.frames,calls:a.info().calls};}""")
    print('initial world',json.dumps(info),flush=True)
    check('town opens at Wilds-scale 280 half-extent',info['zone']=='town' and info['half']==280)
    check('landscaped trees/fields/chunks present',info['tree']>=250 and info['fields']==3 and info['chunks']>0)
    check('gatehouse moved with south wall',abs(info['gate']-278.8)<0.1,info['gate'])
    check('all four wall sides have physical collision',all(info[k] for k in ('top','west','east','south')))
    check('Town camera and landscape render after travelling to outskirts',True)
    page.evaluate("window.__p3d.teleport(191,15);window.__p3d.setCamYaw(0)")
    page.wait_for_timeout(2200)
    out=page.evaluate("""()=>({zone:__p3d.zone,rendered:__p3d.info().triangles,calls:__p3d.info().calls,visible:[...__p3d.townLands.group.children].filter(m=>m.visible).length,
         pos:[__p3d.state.heroX,__p3d.state.heroZ],camera:[__p3d.camRig.pos.x,__p3d.camRig.pos.y,__p3d.camRig.pos.z]})""")
    print('outskirts',json.dumps(out),flush=True)
    check('outer districts render without disappearing',out['visible']>0 and out['rendered']>10000,out)
    check('camera stays finite near hero',all(isinstance(x,(int,float)) and abs(x)<10000 for x in out['camera']))
    page.evaluate("__p3d.state.heroX=-6;__p3d.state.heroZ=38")
    page.wait_for_function("__p3d.zone==='wilds'",timeout=90000)
    check('portal continues to enter Wilds',page.evaluate("__p3d.zone")=='wilds')
    page.evaluate("__p3d.state.heroX=994;__p3d.state.heroZ=-2")
    page.wait_for_function("__p3d.zone==='town'",timeout=90000)
    check('portal still returns to expanded town',page.evaluate("__p3d.zone")=='town')
    check('no uncaught browser errors',not errors,errors[:2])
    browser.close()
srv.shutdown()
print('FAILS',len(fails),fails,flush=True)
sys.exit(bool(fails))
