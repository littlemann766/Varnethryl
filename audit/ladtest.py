import time
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
  b=p.chromium.launch(args=['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']);pg=b.new_page(viewport={'width':960,'height':540})
  pg.goto('http://localhost:8766/proto3d/index.html');pg.wait_for_function('window.__P&&window.__P.renderer.info.render.frame>3',timeout=180000);time.sleep(3)
  pg.get_by_text('Play Solo').click(timeout=5000);time.sleep(12)
  for spot in [(0,39.2),(260,20)]:
    r=pg.evaluate("""s=>{const P=window.__P;window.__PV_HOOK=()=>{P.state.heroX=s[0];P.state.heroZ=s[1]};return 1}""",list(spot));time.sleep(4)
    a=pg.evaluate("()=>{const P=window.__P;P.renderer.info.autoReset=true;P.renderer.render(P.scene,P.camera);const c=P.renderer.info.render.calls;let n=0;P.scene.traverse(o=>{if(o.name&&o.name.startsWith('ladder-')){o.visible=false;n++}});P.renderer.render(P.scene,P.camera);const c2=P.renderer.info.render.calls;P.scene.traverse(o=>{if(o.name&&o.name.startsWith('ladder-'))o.visible=true});return [c,c2,n,P.renderer.shadowMap.enabled]}")
    print(spot,a)
  b.close()
