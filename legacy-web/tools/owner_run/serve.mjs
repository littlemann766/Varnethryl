import http from 'node:http';import fs from 'node:fs';import path from 'node:path';
const roots=[['/or/','/workspace/owner-run/'],['/','/workspace/varn-core/www/']];
const mime={'.js':'text/javascript','.mjs':'text/javascript','.html':'text/html','.glb':'model/gltf-binary','.json':'application/json'};
http.createServer((q,r)=>{const u=decodeURIComponent(q.url.split('?')[0]);for(const[p,d]of roots)if(u.startsWith(p)){const f=path.join(d,u.slice(p.length));if(fs.existsSync(f)&&fs.statSync(f).isFile()){r.writeHead(200,{'content-type':mime[path.extname(f)]||'application/octet-stream'});return fs.createReadStream(f).pipe(r);}}r.writeHead(404);r.end();}).listen(8731);
