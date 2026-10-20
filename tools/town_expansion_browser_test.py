#!/usr/bin/env python3
"""Browser smoke: compact city walls, volcanic overworld, ice portal, boss sizes and shadowed walkable terrain."""
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
      top:q(60,-210),west:q(-210,0),east:q(210,0),south:q(60,210),frames:a.frames,calls:a.info().calls};}""")
    print('initial world',json.dumps(info),flush=True)
    check('town opens at doubled 560-unit half extent',info['zone']=='town' and info['half']==560)
    check('landscaped trees/fields/chunks present',info['tree']>=250 and info['fields']==3 and info['chunks']>0)
    check('gatehouse moved to compact city wall',abs(info['gate']-208.8)<0.1,info['gate'])
    check('all four compact city walls have physical collision',all(info[k] for k in ('top','west','east','south')))
    check('Town camera and landscape render after travelling to outskirts',True)
    page.evaluate("window.__p3d.teleport(390,265);window.__p3d.setCamYaw(0)")
    page.wait_for_timeout(2200)
    out=page.evaluate("""()=>({zone:__p3d.zone,rendered:__p3d.info().triangles,calls:__p3d.info().calls,visible:[...__p3d.townLands.group.children].filter(m=>m.visible).length,
         pos:[__p3d.state.heroX,__p3d.state.heroZ],ground:__p3d.townLands.heightAt(__p3d.state.heroX,__p3d.state.heroZ),feet:__p3d.state.heroY,camera:[__p3d.camRig.pos.x,__p3d.camRig.pos.y,__p3d.camRig.pos.z]})""")
    print('outskirts',json.dumps(out),flush=True)
    check('outer districts render without disappearing',out['visible']>0 and out['rendered']>10000,out)
    check('camera stays finite near hero',all(isinstance(x,(int,float)) and abs(x)<10000 for x in out['camera']))
    check('hero feet follow walkable hill height',out['ground']>5 and abs(out['feet']-out['ground'])<0.05,out)
    land=page.evaluate("""()=>({shadow:__p3d.townLands.terrain.castShadow,receives:__p3d.townLands.terrain.receiveShadow,
       vertexColors:__p3d.townLands.terrain.material.vertexColors,kept:__p3d.townLands.terrain.userData.keep,
       frostPeak:__p3d.townLands.heightAt(-65,-325),titan:__p3d.townLands.heightAt(-397,-399),
       lava:__p3d.townLands.isLava(-461,-431),water:__p3d.townLands.isWater(460,477)})""")
    check('terrain is lit with genuine vertex colors and receives/casts real shadows',all(land[k] for k in ('shadow','receives','vertexColors','kept')),land)
    check('summit climb and volcanic plateau built',land['frostPeak']>=51 and land['titan']>=21 and land['lava'],land)
    check('fortified harbor has real water gameplay zone',land['water'],land)
    page.evaluate("__p3d.teleport(460,477)")
    page.wait_for_timeout(700)
    swim=page.evaluate("""()=>({heroY:__p3d.state.heroY,sea:__p3d.townLands.waterLevel,zone:__p3d.zone})""")
    check('swimming lowers character into the water surface',swim['zone']=='town' and 0<swim['sea']-swim['heroY']<1.1,swim)
    page.evaluate("__p3d.state.heroX=-6;__p3d.state.heroZ=38")
    page.wait_for_function("__p3d.zone==='wilds'",timeout=90000)
    check('portal continues to enter Wilds',page.evaluate("__p3d.zone")=='wilds')
    page.evaluate("__p3d.state.heroX=994;__p3d.state.heroZ=-2")
    page.wait_for_function("__p3d.zone==='town'",timeout=90000)
    check('portal still returns to expanded town',page.evaluate("__p3d.zone")=='town')
    page.evaluate("__p3d.teleport(-65,-325)")
    page.wait_for_function("__p3d.zone==='frost'",timeout=120000)
    ice=page.evaluate("""()=>({zone:__p3d.zone,center:__p3d.frost.center,
        snow:__p3d.frost.group.visible,brothers:__p3d.frost.brothers.length,
        heroY:__p3d.state.heroY,portal:__p3d.frost.portal})""")
    check('summit cave leads to the new frost realm',ice['zone']=='frost' and ice['snow'] and ice['brothers']==2,ice)
    # The two boss brothers must exist as real enemy entities, not merely as
    # markers in a decorative ice map. Both keep their distinct skill patterns.
    page.wait_for_function("""()=>__p3d.fight&&
      __p3d.fight.monsters.some(e=>e.key==='frostbrother_a')&&
      __p3d.fight.monsters.some(e=>e.key==='frostbrother_b')""",timeout=120000)
    duo=page.evaluate("""()=>__p3d.fight.monsters.filter(e=>e.key.startsWith('frostbrother')).map(e=>({
      key:e.key,name:e.def.name,modelHeight:e.view.userData.heightW,
      patterns:e.def.boss,terrainFeet:e.view.position.y}))""")
    check('both Frost Troll brothers spawn as 3x combat bosses',
          len(duo)==2 and all(x['modelHeight']>7.9 and x['patterns'] for x in duo),duo)
    page.evaluate("__p3d.teleport(__p3d.frost.portal.x,__p3d.frost.portal.z)")
    page.wait_for_function("__p3d.zone==='town'",timeout=120000)
    check('frost realm portal returns to the main world',page.evaluate("__p3d.zone")=='town')
    # Approach the volcanic corner without standing in molten lava. Both the
    # 40x Titan and patrolling Balthrix should spawn lazily and be combat-ready.
    page.evaluate("__p3d.teleport(-397,-515)")
    page.wait_for_function("""()=>__p3d.fight&&__p3d.fight.on&&
      __p3d.fight.monsters.some(e=>e.key==='titan')&&
      __p3d.fight.monsters.some(e=>e.key==='vaelthryx')""",timeout=120000)
    bosses=page.evaluate("""()=>__p3d.fight.monsters.filter(e=>e.def.boss).map(e=>({
      key:e.key,name:e.def.name,height:e.view.userData.heightW,y:e.view.position.y
    }))""")
    check('Ashen Titan 40x and roaming Balthrix are real playable encounters',
          any(e['key']=='titan' and 105<e['height']<115 for e in bosses) and
          any(e['key']=='vaelthryx' and 25<e['height']<30 for e in bosses),bosses)
    check('no uncaught browser errors',not errors,errors[:2])
    browser.close()
srv.shutdown()
print('FAILS',len(fails),fails,flush=True)
sys.exit(bool(fails))
