#!/bin/bash
# Builds /workspace/varn3d/VARNETHRYL-3D-VIEWER.html (self-contained, file:// safe)
set -e; cd "$(dirname "$0")"; ROOT=../..; ESB=${ESBUILD:-/tmp/esb/node_modules/.bin/esbuild}
$ESB entry.js --bundle --minify --alias:three=$ROOT/www/proto3d/vendor/three.module.js --format=iife --target=es2020 --outfile=/tmp/viewer.bundle.js --log-level=warning
python3 - <<PY
import base64,json
R='$ROOT'; ids='aldric darius selene seraphine talia finn brynn mirelle nyx vesper thorne orin'.split()
m={i:base64.b64encode(open(f'{R}/www/proto3d/models/{i}.glb','rb').read()).decode() for i in ids}
css="""html,body{margin:0;height:100%;background:#17151c;color:#e8dcc0;font:14px system-ui,sans-serif;overflow:hidden;overscroll-behavior:none}
#ui{position:fixed;left:0;right:0;top:0;padding:8px;background:#000a;z-index:2;display:flex;flex-direction:column;gap:6px}
#heroes,#ctl{display:flex;flex-wrap:wrap;gap:6px}
button{background:#2a2433;color:#e8dcc0;border:1px solid #6a5a3a;border-radius:8px;padding:9px 12px;font-size:14px;cursor:pointer;touch-action:manipulation}
button.on{background:#8a6f2f;color:#fff}#status{font-weight:600;margin-left:auto;align-self:center}
@media(max-width:600px){button{padding:6px 8px;font-size:12px}#ui{gap:4px;padding:6px}#heroes,#ctl{gap:4px}}
#info{position:fixed;left:10px;bottom:8px;opacity:.6;font-size:12px;pointer-events:none}canvas{display:block;position:fixed;inset:0}"""
html=f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no"><title>VARNETHRYL 3D hero prototypes</title><style>{css}</style></head><body>
<div id="ui"><div id="heroes"></div><div id="ctl"><span id="status">Loading…</span></div></div>
<div id="info">drag = orbit · pinch / wheel = zoom · rough prototypes</div>
<script>window.__MODELS={json.dumps(m)};</script>
<script>{open('/tmp/viewer.bundle.js').read().replace('</script','<\\\\/script')}</script></body></html>'''
open(R+'/VARNETHRYL-3D-VIEWER.html','w').write(html)
PY
ls -la $ROOT/VARNETHRYL-3D-VIEWER.html
