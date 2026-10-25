import json,time
from playwright.sync_api import sync_playwright
IDS=['windmill','lighthouse','gt0']
with sync_playwright() as p:
  b=p.chromium.launch(args=['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']);pg=b.new_page(viewport={'width':800,'height':600})
  pg.goto('http://localhost:8765/proto3d/bldview.html');pg.wait_for_function('window.__ready',timeout=120000);pg.evaluate('__size(800,600)')
  out={}
  for i in IDS:
    try:
      r=pg.evaluate("""id=>{const s=__sub(id);const calls=__show(id,/windmill|lighthouse|gt0/.test(id)?{dist:42,ty:8}:{});const ri=__rinfo();const g={};
       const THREE_B=(o)=>{let mn=[1e9,1e9,1e9],mx=[-1e9,-1e9,-1e9],n=0,t=0,mats=new Set();o.updateMatrixWorld(true);const inv=s.root.matrixWorld.clone().invert();
        o.traverse(m=>{if(!m.isMesh)return;n++;mats.add(m.material.uuid);const G=m.geometry,P=G.attributes.position;t+=(G.index?G.index.count:P.count)/3;
         const M=m.matrixWorld.clone().premultiply(inv);const e=M.elements;for(let k=0;k<P.count;k+=Math.max(1,P.count>>9)){const x=P.getX(k),y=P.getY(k),z=P.getZ(k);
          const X=e[0]*x+e[4]*y+e[8]*z+e[12],Y=e[1]*x+e[5]*y+e[9]*z+e[13],Z=e[2]*x+e[6]*y+e[10]*z+e[14];mn=[Math.min(mn[0],X),Math.min(mn[1],Y),Math.min(mn[2],Z)];mx=[Math.max(mx[0],X),Math.max(mx[1],Y),Math.max(mx[2],Z)];}});
        return {meshes:n,tris:Math.round(t),mats:mats.size,min:mn.map(v=>+v.toFixed(2)),max:mx.map(v=>+v.toFixed(2))};};
       for(const k in s.G)g[k]=THREE_B(s.G[k]);
       const extra=[];s.root.children.forEach(c=>{if(!Object.values(s.G).includes(c))extra.push(c.type+':'+c.name)});
       return {calls,tris:ri.tri,K:s.K,w:s.w,d:s.d,h:s.h,vh:s.vh,DW:s.DW,radius:s.radius,cx:s.cx,cz:s.cz,rot:s.rot,groups:g,extra,info:__info(id)};}""",i)
      out[i]=r;print(i,r['calls'],r['tris'],r['K'],r['w'],r['d'],r['h'],r['DW'],{k:(v['meshes'],v['tris']) for k,v in r['groups'].items()},r['extra'][:4])
      pg.screenshot(path=f'r2/bld_before_{i}_front.png')
      pg.evaluate("id=>__show(id,/windmill|lighthouse|gt0/.test(id)?{yaw:0.8,dist:42,ty:8}:{yaw:0.8})",i);pg.screenshot(path=f'r2/bld_before_{i}_34.png')
    except Exception as e:print(i,'ERR',str(e)[:200])
  pass;b.close()
