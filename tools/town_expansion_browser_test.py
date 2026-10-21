#!/usr/bin/env python3
"""Browser smoke test: 1120-unit town, walkable mountain terrain, walls, Wilds transition."""
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
      top:q(60,-185),west:q(-185,0),east:q(185,0),south:q(60,185),frames:a.frames,calls:a.info().calls};}""")
    print('initial world',json.dumps(info),flush=True)
    check('town opens at doubled 560-unit half extent',info['zone']=='town' and info['half']==560)
    check('landscaped trees/fields/chunks present',info['tree']>=250 and info['fields']==3 and info['chunks']>0)
    check('gatehouse stays on inner city walls',abs(info['gate']-183.8)<0.1,info['gate'])
    check('four inner city wall sides have collision',all(info[k] for k in ('top','west','east','south')))
    check('Town camera and landscape render after travelling to outskirts',True)
    page.evaluate("window.__p3d.teleport(390,265);window.__p3d.setCamYaw(0)")
    page.wait_for_timeout(2200)
    out=page.evaluate("""()=>({zone:__p3d.zone,rendered:__p3d.info().triangles,calls:__p3d.info().calls,visible:[...__p3d.townLands.group.children].filter(m=>m.visible).length,
         pos:[__p3d.state.heroX,__p3d.state.heroZ],ground:__p3d.townLands.heightAt(__p3d.state.heroX,__p3d.state.heroZ),feet:__p3d.state.heroY,camera:[__p3d.camRig.pos.x,__p3d.camRig.pos.y,__p3d.camRig.pos.z]})""")
    print('outskirts',json.dumps(out),flush=True)
    check('outer districts render without disappearing',out['visible']>0 and out['rendered']>10000,out)
    check('camera stays finite near hero',all(isinstance(x,(int,float)) and abs(x)<10000 for x in out['camera']))
    check('hero feet follow walkable hill height',out['ground']>5 and abs(out['feet']-out['ground'])<0.05,out)
    page.evaluate("__p3d.state.heroX=-6;__p3d.state.heroZ=38")
    page.wait_for_function("__p3d.zone==='wilds'",timeout=90000)
    check('portal continues to enter Wilds',page.evaluate("__p3d.zone")=='wilds')
    page.evaluate("__p3d.state.heroX=994;__p3d.state.heroZ=-2")
    page.wait_for_function("__p3d.zone==='town'",timeout=90000)
    check('portal still returns to expanded town',page.evaluate("__p3d.zone")=='town')
    # The Frost Troll brothers' cave lives at the summit of the north wilderness hill.
    page.wait_for_timeout(1700)
    page.evaluate("__p3d.teleport(0,-345)")
    page.wait_for_function("__p3d.zone==='frost'",timeout=90000)
    ice=page.evaluate("""()=>({zone:__p3d.zone,ground:__p3d.frostRealm.heightAt(__p3d.state.heroX,__p3d.state.heroZ),
           y:__p3d.state.heroY,portal:__p3d.frostRealm.exit,triangles:__p3d.info().triangles,
           bosses:__p3d.fight?.monsters?.map(e=>e.key)||[]})""")
    print('frost realm',json.dumps(ice),flush=True)
    check('frost portal teleports to separate icy map',ice['zone']=='frost' and ice['triangles']>20000,ice)
    check('frost terrain is actual walkable ground',abs(ice['ground']-ice['y'])<.15,ice)
    cave=page.evaluate("""()=>{const a=__p3d,realm=a.frostRealm,c=realm?.cave;
       return {visible:realm?.group.visible,lights:c?.lights?.length,iceMotes:c?.motes?.geometry?.attributes?.position?.count,
       colliders:c?.colliders?.length,sky:a.scene.background?.getHex?.(),fog:a.scene.fog?.color?.getHex?.(),
       litBrothers:c?.lights?.filter(l=>Math.hypot(l.position.x-37,l.position.z+66)<20||
         Math.hypot(l.position.x+37,l.position.z+66)<20).length,
       litExit:c?.lights?.some(l=>Math.hypot(l.position.x+7,l.position.z-177)<20)};}""")
    print('frost cave lighting and physics',json.dumps(cave),flush=True)
    check('Frost Cave is visibly active and ceiling-dark, never outdoor sky',cave['visible'] and cave['sky']==0x0c1422,cave)
    check('both brothers have nearby cave lighting',cave['lights']==5 and cave['litBrothers']>=2,cave)
    check('portal has cave lighting',cave['litExit'],cave)
    check('low-cost airborne ice motes and solid ice collision present',cave['iceMotes']==168 and cave['colliders']>0,cave)
    # Previous screenshots mistakenly showed the full-screen title menu
    # instead of the game. Hide it explicitly for a TRUE scene preview;
    # do not change the user's save or entry behavior in the shipped game.
    page.evaluate("""()=>{document.getElementById('vnMenu').hidden=true;
                         document.body.classList.remove('vn-menu-open');}""")
    check('actual 3D Frost Cave is visible rather than obscured by the title menu',
          page.evaluate("getComputedStyle(document.getElementById('vnMenu')).display==='none'"))
    page.wait_for_timeout(750)
    page.screenshot(path='frost-cave-mobile-test.png')
    # Boss models load asynchronously, but their encounters must become active without input.
    page.wait_for_function("window.__p3d?.fight?.monsters?.some(e=>e.key==='frosttroll_a')&&__p3d.fight.monsters.some(e=>e.key==='frosttroll_b')",timeout=90000)
    check('both Frost Troll brothers spawn together',page.evaluate("['frosttroll_a','frosttroll_b'].every(k=>__p3d.fight.monsters.some(e=>e.key===k))"))
    # Portrait cameras have a narrow HORIZONTAL field of view. Two brothers
    # 74 world units apart cannot both appear from x=2250; the old screenshot
    # showed an empty patch of fog. Frame each boss individually, and require
    # the actual live model to project inside the camera's viewport.
    for key,x in [('frosttroll_a',2213),('frosttroll_b',2287)]:
        page.evaluate("""x=>{__p3d.teleport(x,-21);__p3d.setCamYaw(0);}""",x)
        page.wait_for_timeout(1100)
        projection=page.evaluate("""key=>{
          const a=__p3d,e=a.fight?.monsters?.find(v=>v.key===key);
          if(!e||!e.view)return null;
          const worldY=(e.view.position.y||0)+Math.min(7,(e.heightAbove||12)*.3);
          const p=new a.THREE.Vector3(e.x,worldY,e.z).project(a.camera);
          return {x:p.x,y:p.y,z:p.z,loaded:!!e.view.userData?.glb,
                  visible:e.view.visible,attached:e.view.parent===a.scene,
                  distance:Math.hypot(e.x-a.state.heroX,e.z-a.state.heroZ)};
        }""",key)
        print('boss camera projection',key,projection,flush=True)
        check(f'{key} live model is in the gameplay camera frame',
              projection is not None and projection['visible'] and projection['attached'] and
              abs(projection['x'])<1 and abs(projection['y'])<1 and -1<=projection['z']<=1,
              projection)
        page.screenshot(path=f'frost-cave-{key}-mobile-test.png')
    page.evaluate("__p3d.teleport(2243,177)")
    page.wait_for_function("__p3d.zone==='town'",timeout=90000)
    check('ice gate returns to mountain summit',page.evaluate("__p3d.zone")=='town')
    # The next overhaul zone must render actual 3D basalt and animated lava,
    # and it must cull the entire optional FX batch near the peaceful town.
    page.evaluate("__p3d.teleport(405,-302);__p3d.setCamYaw(0)")
    page.wait_for_function("""()=>{
      const a=__p3d;return Math.hypot(a.camera.position.x-a.state.heroX,
                                         a.camera.position.z-a.state.heroZ)<70;}""",timeout=90000)
    page.wait_for_timeout(1400)
    camera=page.evaluate("""()=>{
      const a=__p3d,c=a.camera,land=a.townLands;
      const d=Math.hypot(c.position.x-a.state.heroX,c.position.z-a.state.heroZ);
      const q=new a.THREE.Vector3(405,land.heightAt(405,-402)+9,-402).project(c);
      return {distance:d,cameraY:c.position.y,heroY:a.state.heroY,
              craterProjection:{x:q.x,y:q.y,z:q.z},
              terrainVisible:land.terrain.visible && land.group.visible};
    }""")
    print('Titan camera preview',json.dumps(camera),flush=True)
    check('post-portal camera snaps back to player and frames volcanic ground',
          camera['distance']<70 and camera['terrainVisible'] and
          abs(camera['craterProjection']['x'])<1 and
          -1<=camera['craterProjection']['z']<=1,camera)
    volcano=page.evaluate("""()=>{
       const a=__p3d,t=a.townLands,v=t?.volcano,m=t?.poolMeshes?.[0]?.material;
       return {zone:a.zone,active:v?.active,visible:v?.group.visible,
         emberCount:v?.embers?.geometry.attributes.position.count,
         basaltCount:v?.shards?.count,lights:v?.glowLights?.length,
         lavaGlow:m?.emissiveIntensity,playerY:a.state.heroY,
         playerX:a.state.heroX,playerZ:a.state.heroZ,
         lavaPools:t?.poolMeshes?.length,
         triangles:a.info()?.triangles};}""")
    print('Titan volcanic atmosphere',json.dumps(volcano),flush=True)
    check('volcano lava has real embers, basalt scenery and two low-cost glowing lights',
          volcano['zone']=='town' and volcano['active'] and volcano['visible'] and
          volcano['emberCount']==128 and volcano['basaltCount']==42 and
          volcano['lights']==2 and volcano['lavaPools']==5,volcano)
    page.screenshot(path='titan-volcano-mobile-test.png')
    # Walking back into the village removes the optional volcano FX batch.
    page.evaluate("__p3d.teleport(0,0)")
    page.wait_for_timeout(600)
    check('town culls remote Titan embers but keeps original lava pools',
          page.evaluate("!__p3d.townLands.volcano.active && !__p3d.townLands.volcano.group.visible"))
    check('no uncaught browser errors',not errors,errors[:2])
    browser.close()
srv.shutdown()
print('FAILS',len(fails),fails,flush=True)
sys.exit(bool(fails))
