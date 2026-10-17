"""Generate PLAY-VARNETHRYL.html, a self-contained playable HTML preview.

No third-party Python packages needed. Run after modifying the web app to refresh
its source and embedded art. Unlike the PWA/Capacitor build, this preview can open
from the device's local files without a web server.
"""
from pathlib import Path
import base64
import json

root=Path(__file__).resolve().parents[1]
w=root/'www'
html=(w/'index.html').read_text(encoding='utf-8')
import re
html=re.sub(r'<div id="brandLoader".*?</div><div id="brandTitle".*?</button></div>','',html,flags=re.S).replace('<link rel="stylesheet" href="brand.css"/>','').replace('<script src="brand.js"></script>','')  # brand screens need external art; skip in standalone
html=html.replace('<link rel="manifest" href="manifest.webmanifest"/>','').replace('<link rel="apple-touch-icon" href="apple-touch-icon.png"/>','').replace('<script defer src="pwa.js"></script>','<script>'+ (w/'pwa.js').read_text(encoding='utf-8') +'</script>')
html=html.replace('<link rel="stylesheet" href="styles.css"/>','<style>'+(w/'styles.css').read_text(encoding='utf-8')+'</style>')
def embed(kind,n):
 return ['data:image/webp;base64,'+base64.b64encode((w/'assets'/kind/f'{i}.webp').read_bytes()).decode('ascii') for i in range(n)]
assets={'heroes':embed('heroes',20),'weapons':embed('weapons',15),'sprites':['data:image/png;base64,'+base64.b64encode((w/'assets'/'sprites'/f'{i}.png').read_bytes()).decode('ascii') for i in range(20)]}
data=(w/'data.js').read_text(encoding='utf-8').replace('export const','const')
js=(w/'game.js').read_text(encoding='utf-8').replace("import {HEROES,ZONES,TIERS,SUBSTAT_POOL,ABILITIES,WEAPON_ART,ENEMIES} from './data.js';",'')
js=js.replace('assets/weapons/${idx}.webp','${ASSET_URLS.weapons[idx]}').replace('assets/weapons/${WEAPON_ART[it.heroId]}.webp','${ASSET_URLS.weapons[WEAPON_ART[it.heroId]]}')
script='const ASSET_URLS='+json.dumps(assets,separators=(',',':'))+';\n'+data+'\nHEROES.forEach((h,i)=>{h.image=ASSET_URLS.heroes[i];h.sprite=ASSET_URLS.sprites[i]});\n'+js
html=html.replace('<script type="module" src="game.js"></script>','<script type="module">\n'+script.replace('</script>','<\\/script>')+'\n</script>')
p=root/'PLAY-VARNETHRYL.html';p.write_text(html,encoding='utf-8')
print(f'Created {p.name} ({p.stat().st_size:,} bytes)')
