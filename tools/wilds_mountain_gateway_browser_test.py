#!/usr/bin/env python3
"""Phone-size live gateway walkthrough: mountain ruins to Wilds and safe return.
   The old town gate and the Frost Troll cave must remain independent. """
import functools,http.server,os,threading
from playwright.sync_api import sync_playwright
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','www'))
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Q,directory=ROOT))
threading.Thread(target=server.serve_forever,daemon=True).start()
with sync_playwright() as p:
    browser=p.chromium.launch(args=['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist'])
    for mode,w,h in [('portrait',412,915),('landscape',800,440)]:
        ctx=browser.new_context(viewport={'width':w,'height':h},has_touch=True,is_mobile=True,service_workers='block')
        page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(f'http://127.0.0.1:{server.server_address[1]}/proto3d.html?nosave=1&npcs=0&party=0',
                  wait_until='commit',timeout=120000)
        page.wait_for_function('window.__p3d && __p3d.frames>14',timeout=120000)
        page.wait_for_function("""()=>!!__p3d.scene.getObjectByName('mountain-wilds-cave-portal')""",timeout=30000)
        geometry=page.evaluate("""()=>{
          const land=__p3d.townLands,ruins=land?.ruinedGateway,
                mountain=__p3d.scene.getObjectByName('mountain-wilds-cave-portal');
          return {terrain:!!land?.terrain,approach:!!land?.brokenSealRoad,
            chamber:!!ruins?.group,rocks:!!ruins?.group.getObjectByName('mountain-cave-rock-shell'),
            arches:ruins?.group.children.filter(x=>x.name==='mountain-portal-arch-lintel').length,
            portal:!!mountain,portalY:mountain?.position.y,
            floorY:land?.heightAt(-315,-284),frost:!!__p3d.scene.getObjectByName('frost-summit-cave')};
        }""")
        assert all(geometry.get(k) for k in ['terrain','approach','chamber','rocks','arches','portal','frost']),geometry
        assert abs(geometry['portalY']-geometry['floorY'])<.01,geometry
        page.wait_for_timeout(1700)
        page.evaluate('__p3d.teleport(-315,-284)')
        page.wait_for_function("__p3d.zone==='wilds'",timeout=55000)
        page.wait_for_function("""()=>!!__p3d.wilds?.ruinedReturn?.group""",timeout=30000)
        wilds=page.evaluate("""()=>{
          const R=__p3d.wilds?.ruinedReturn?.group;
          return {returnGate:!!R,columns:R?.children.filter(x=>x.name==='wilds-ruined-return-pillars').length,
            cx:__p3d.state.heroX,cz:__p3d.state.heroZ};
        }""")
        assert wilds['returnGate'] and wilds['columns']>=6,wilds
        page.screenshot(path=f'mountain-wilds-arrival-{mode}.png')
        page.wait_for_timeout(2200)
        page.evaluate("""()=>{const s=__p3d.state,P=__p3d.wilds.portal;s.heroX=P.x;s.heroZ=P.z;}""")
        page.wait_for_function("__p3d.zone==='town'",timeout=45000)
        returned=page.evaluate('({x:__p3d.state.heroX,z:__p3d.state.heroZ})')
        assert abs(returned['x']+303)<4 and abs(returned['z']+284)<4,returned
        page.screenshot(path=f'mountain-ruin-town-return-{mode}.png')
        # The old city-centre gate is still functional and returns to itself.
        page.wait_for_timeout(2200)
        page.evaluate('__p3d.teleport(-6,38)')
        page.wait_for_function("__p3d.zone==='wilds'",timeout=45000)
        page.wait_for_timeout(2200)
        page.evaluate("""()=>{const P=__p3d.wilds.portal;__p3d.state.heroX=P.x;__p3d.state.heroZ=P.z;}""")
        page.wait_for_function("__p3d.zone==='town'",timeout=45000)
        legacy=page.evaluate('({x:__p3d.state.heroX,z:__p3d.state.heroZ})')
        assert abs(legacy['x']+6)<3 and abs(legacy['z']-42)<3,legacy
        assert not errors,errors[:6]
        print('PASS',mode,'mountain cave→Wilds→mountain, original gate→Wilds→town, Frost summit intact',flush=True)
        ctx.close()
    browser.close()
