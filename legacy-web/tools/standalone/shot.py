import asyncio,sys
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(args=['--use-gl=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist'])
        pg=await b.new_page(viewport={'width':1000,'height':720})
        errs=[]; pg.on('console',lambda m: errs.append(m.text) if m.type=='error' else None); pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.goto('file:///workspace/varn3d/VARNETHRYL-3D-VIEWER.html?spin=0&yaw=0.5')
        await pg.evaluate('window.__ready'); await pg.wait_for_timeout(800)
        for h in ['Nyx Varrin','Thorne']:
            pass
        await pg.click('text=Selene Frostveil'); await pg.click('text=▶ walk'); await pg.wait_for_timeout(1200)
        st=await pg.evaluate('document.getElementById("status").textContent')
        await pg.screenshot(path='/workspace/shots/varn3d/standalone-viewer.png')
        # all heroes load
        for n in ['Sir Aldric','Dame Seraphine','Brother Thorne']:
            await pg.click(f'button:text-is("{n}")'); await pg.wait_for_timeout(300)
        print('status',st,'final',await pg.evaluate('document.getElementById("status").textContent'),'errors',errs)
        await pg.set_viewport_size({'width':390,'height':780}); await pg.wait_for_timeout(500)
        await pg.screenshot(path='/workspace/shots/varn3d/standalone-viewer-phone.png')
        await b.close()
asyncio.run(main())
