#!/usr/bin/env python3
"""Varnethryl interactive sea and Hydra tests: mobile and desktop."""
import os,sys,threading,http.server,functools,traceback
from pathlib import Path
from playwright.sync_api import sync_playwright
BASE=Path(__file__).resolve().parent.parent/'www'
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
s=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=BASE))
threading.Thread(target=s.serve_forever,daemon=True).start()
URL=f'http://127.0.0.1:{s.server_address[1]}/proto3d.html?party=2&npcs=0&nosave=1'
fails=0
def check(label,ok,detail=''):
 global fails
 print(('PASS ' if ok else 'FAIL ')+label+(' '+str(detail)[:400] if not ok else ''),flush=True)
 if not ok:fails+=1
with sync_playwright() as pw:
 b=pw.chromium.launch(args=['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist'])
 for w,h,mob in [(412,915,True),(1280,800,False)]:
  tag='mobile' if mob else 'desktop'
  party_count=2 if mob else 3  # Verify the full ship manifest on desktop.
  page_url=URL.replace('party=2',f'party={party_count}')
  ctx=b.new_context(viewport={'width':w,'height':h},is_mobile=mob,has_touch=mob,service_workers='block')
  pg=ctx.new_page()
  errs=[];failedAssets=[]
  pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.on('console',lambda m:errs.append(m.text) if m.type=='error' else None)
  pg.on('response',lambda r:failedAssets.append((r.status,r.url)) if r.status>=400 and any(t in r.url for t in ['hydra_restored','tidewrack_sailing','water-realms']) else None)
  try:
   pg.goto(page_url,wait_until='domcontentloaded',timeout=60000)
   pg.wait_for_function('window.__p3d && __p3d.frames>5',timeout=120000)
   pg.evaluate("document.getElementById('vnEnter')?.click()")
   check(tag+' town boots',pg.evaluate("__p3d.zone==='town'"))
   check(tag+' cheats locked initially',pg.evaluate("!document.getElementById('ownerPanel') && !__p3d.cheats"))
   check(tag+' three map buttons',pg.evaluate("['vnTravelHydra','vnTravelSail','vnTravelTown'].every(id=>!!document.getElementById(id))"))
   pg.evaluate("document.getElementById('vnTravelHydra').click()")
   pg.wait_for_function("__p3d.zone==='hydra'",timeout=30000)
   check(tag+' Mire terrain created',pg.evaluate("!!__p3d.scene.getObjectByName('walkable-hydra-ground')"))
   pg.wait_for_function("!!__p3d.scene.getObjectByName('hydra-unrigged-5-head')?.children?.length",timeout=35000)
   check(tag+' real Hydra model present',pg.evaluate("__p3d.scene.getObjectByName('hydra-unrigged-5-head').children.length>0"))
   pg.wait_for_function("!!__p3d.fight?.monsters?.find(e=>e.key==='hydra')",timeout=30000)
   check(tag+' Hydra boss has health',pg.evaluate("__p3d.fight.monsters.find(e=>e.key==='hydra').max>10000"))
   pg.screenshot(path=f'/tmp/marine-{tag}-hydra.png')
   # The player moves using the same controls used in the normal kingdom.
   a=pg.evaluate("[__p3d.state.heroX,__p3d.state.heroZ]")
   pg.keyboard.down('w');pg.wait_for_timeout(900);pg.keyboard.up('w')
   c=pg.evaluate("[__p3d.state.heroX,__p3d.state.heroZ]")
   check(tag+' Hydra walking works',sum((x-y)**2 for x,y in zip(a,c))>0.02,(a,c))
   pg.evaluate("document.getElementById('vnTravelSail').click()")
   pg.wait_for_function("__p3d.zone==='sailing'",timeout=35000)
   check(tag+' 9x9 km size',pg.evaluate("Math.abs(__p3d.ZONE.half-6390)<1"))
   pg.wait_for_function("!!__p3d.scene.getObjectByName('user-supplied-sailing-ship')",timeout=35000)
   check(tag+' approved ship GLB visible',pg.evaluate("!!__p3d.scene.getObjectByName('user-supplied-sailing-ship')?.visible"))
   check(tag+' real water mesh',pg.evaluate("!!__p3d.scene.getObjectByName('sailing-water-window')"))
   check(tag+' shipboard combat safely disarmed',pg.evaluate("__p3d.fight && !__p3d.fight.on"))
   # Passengers must genuinely board: verify the real model roots occupy the
   # deck in ship-local coordinates, not world-space water to either side.
   pg.wait_for_function("""(count)=>{
     const c=__p3d.bump.crowd.filter(r=>r.kind==='party');
     return __p3d.hero.visible && c.length===count && c.every(r=>r.root?.visible);
   }""",arg=party_count,timeout=35000)
   deck_js="""(()=>{
     const p=__p3d,ship=p.scene.getObjectByName('player-sailing-ship');
     ship.updateMatrixWorld(true);
     const slots=[[0,2.35,-3],[-1.28,1.95,-.65],[1.28,1.95,-.65],[0,1.95,2.4]];
     const roots=[p.hero,...p.bump.crowd.filter(r=>r.kind==='party').map(r=>r.root)];
     const local=roots.map(o=>ship.worldToLocal(o.getWorldPosition(new p.THREE.Vector3())));
     return {near:local.every((v,i)=>v.distanceTo(new p.THREE.Vector3(...slots[i]))<.65),
             visible:roots.every(o=>o.visible),coords:local.map(v=>v.toArray())};
   })()"""
   metrics=pg.evaluate("""(()=>{
     const p=__p3d,T=p.THREE,s=p.scene.getObjectByName('player-sailing-ship');
     const items=[s,s.getObjectByName('user-supplied-sailing-ship'),p.hero,...p.bump.crowd.filter(r=>r.kind==='party').map(r=>r.root)];
     return items.map(o=>{if(!o)return null;const box=new T.Box3().setFromObject(o),v=new T.Vector3(),v2=new T.Vector3();return {name:o.name,scale:o.scale.toArray(),size:box.getSize(v).toArray().map(n=>+n.toFixed(2)),center:box.getCenter(v2).toArray().map(n=>+n.toFixed(2)),pos:o.getWorldPosition(new T.Vector3()).toArray().map(n=>+n.toFixed(2))};});
   })()""")
   print('CREW_BOUNDS',tag,metrics,flush=True)
   aboard=pg.evaluate(deck_js)
   check(tag+' hero and companions stand ON deck',aboard['near'] and aboard['visible'],aboard)
   check(tag+' rendered character sizes fit the galleon',
     all(m and 1.1 <= m['size'][1] <= 3.6 for m in metrics[2:]),metrics)
   check(tag+' all '+str(party_count)+' companions aboard',
     pg.evaluate("(count)=>__p3d.bump.crowd.filter(r=>r.kind==='party'&&r.root?.visible).length===count",party_count))

   a=pg.evaluate("[__p3d.state.heroX,__p3d.state.heroZ,__p3d.state.yaw]")
   pg.keyboard.down('w');pg.wait_for_timeout(1700);pg.keyboard.up('w')
   c=pg.evaluate("[__p3d.state.heroX,__p3d.state.heroZ,__p3d.state.yaw]")
   check(tag+' sails forward',sum((c[i]-a[i])**2 for i in [0,1])>0.04,(a,c)) # software-rendered desktop may advance only a few simulation ticks during asset loading
   pg.keyboard.down('w');pg.keyboard.down('a');pg.wait_for_timeout(1500)
   pg.keyboard.up('a');pg.keyboard.up('w')
   y=pg.evaluate("__p3d.state.yaw")
   check(tag+' rudder steers',abs(y-c[2])>0.02,(y,c[2]))
   check(tag+' port rudder turns the bow LEFT',y-c[2]>0.02,(y,c[2]))
   pg.keyboard.down('w');pg.keyboard.down('d');pg.wait_for_timeout(1500)
   pg.keyboard.up('d');pg.keyboard.up('w')
   right_yaw=pg.evaluate("__p3d.state.yaw")
   check(tag+' starboard rudder turns the bow RIGHT',right_yaw-y < -0.02,(right_yaw,y))
   deck_after=pg.evaluate(deck_js)
   check(tag+' crew follows the vessel while steering',deck_after['near'] and deck_after['visible'],deck_after)

   check(tag+' streaming tiles bounded',pg.evaluate("__p3d.scene.getObjectByName('tidewrack-open-ocean').children.filter(x=>x.name.startsWith('ocean-island-tile-')).length<=25"))
   pg.screenshot(path=f'/tmp/marine-{tag}-sailing.png')
   pg.evaluate("document.getElementById('vnTravelTown').click()")
   pg.wait_for_function("__p3d.zone==='town'",timeout=35000)
   check(tag+' town restored, no ghost ocean',pg.evaluate("!__p3d.scene.getObjectByName('tidewrack-open-ocean')&&__p3d.hero.visible"))
   check(tag+' companions returned to walking world',pg.evaluate("__p3d.bump.crowd.filter(r=>r.kind==='party').every(r=>r.root?.visible && Math.hypot(r.a.x-__p3d.state.heroX,r.a.z-__p3d.state.heroZ)<18)"))
   check(tag+' mobile walking HUD restored',pg.evaluate("!document.body.classList.contains('vn-sailing-zone')"))
   pg.wait_for_function("__p3d.fight && __p3d.fight.on && __p3d.fight.auto",timeout=15000)
   check(tag+' hero combat and abilities restored after disembarking',
     pg.evaluate("__p3d.fight.on && __p3d.fight.auto"))
   # Switching before asynchronous GLB imports settle must not resurrect a
   # retired Hydra or ship in the town scene. Repeat without awaiting models.
   for button,zone in [('vnTravelHydra','hydra'),('vnTravelSail','sailing'),('vnTravelTown','town')]:
    pg.evaluate(f"document.getElementById('{button}').click()")
    pg.wait_for_function(f"__p3d.zone==='{zone}'",timeout=35000)
   pg.wait_for_timeout(1500)
   check(tag+' rapid map changes leave no ghost marine zones',pg.evaluate("!__p3d.scene.getObjectByName('hydra-mire-zone') && !__p3d.scene.getObjectByName('tidewrack-open-ocean') && __p3d.hero.visible"))
   # Simulate double-taps / overlapping owner travel while models are still
   # streaming. All three requests arrive in the *same* event-loop turn.
   # Their completion must leave exactly the last requested map loaded.
   pg.evaluate("""()=>{
     for(const id of ['vnTravelHydra','vnTravelSail','vnTravelTown'])
       document.getElementById(id).click();
   }""")
   pg.wait_for_function("""()=>{
     const p=window.__p3d;
     return p?.zonePending===0 && p.zone==='town'
       && !p.scene.getObjectByName('hydra-mire-zone')
       && !p.scene.getObjectByName('tidewrack-open-ocean');
   }""",timeout=90000)
   check(tag+' simultaneous travel requests serialize and return to town',
     pg.evaluate("__p3d.zonePending===0 && __p3d.zone==='town' && __p3d.hero.visible"))
   check(tag+' no missing marine assets',not failedAssets,failedAssets[:5])
   major=[e for e in errs if any(t in e for t in ['Uncaught','hydra_restored','tidewrack_sailing','TypeError','GLB','camRig.look.set','camRig.lookTarget','is not a function'])]
   check(tag+' no runtime errors for marine gameplay',not major,major[:5])
  except Exception as e:
   fails+=1;print('FAIL '+tag+' exception:',str(e),flush=True)
   try: print('STATE:',pg.evaluate("({zone:__p3d?.zone,frames:__p3d?.frames,diag:document.getElementById('diag')?.innerText?.slice(-1200)})"),flush=True)
   except Exception: pass
   try:pg.screenshot(path=f'/tmp/marine-{tag}-failure.png')
   except Exception:pass
   traceback.print_exc()
  finally:
   print('CONSOLE '+tag,errs[:6],flush=True)
   ctx.close()
 b.close()
print('Marine gameplay checks:',fails,'failed',flush=True)
sys.exit(1 if fails else 0)
