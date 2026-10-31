// Ensure the offline precache exactly matches assets and uses the current game version.
import assert from 'node:assert/strict';
import { readFileSync, readdirSync, existsSync } from 'node:fs';
import { join, basename } from 'node:path';
const root=new URL('../www/',import.meta.url), pkg=JSON.parse(readFileSync(new URL('../package.json',import.meta.url),'utf8'));
const sw=readFileSync(new URL('sw.js',root),'utf8');
const main=readFileSync(new URL('proto3d/main.js',root),'utf8');
const html=readFileSync(new URL('proto3d.html',root),'utf8');
assert.match(pkg.version,/^\d+\.\d+\.\d+$/,'package version must be semantic');
assert.ok(sw.includes("const CACHE = PREFIX + '"+pkg.version+"'"));
assert.ok(main.includes("const ASSET_V = '"+pkg.version+"'"));
assert.ok(html.includes('id="ver">v'+pkg.version));
const match=sw.match(/const PRECACHE = (\[[\s\S]*?\]);/);
assert.ok(match,'service-worker asset list exists');
const cache=JSON.parse(match[1]);
const excluded=new Set(['viewer.html','viewer.js','export.html','model-viewer.html','scenery-viewer.html','scenery-viewer.js','scenery.js']);
function walk(p,base=''){
 let out=[];for(const ent of readdirSync(p,{withFileTypes:true})){
  if(ent.isDirectory())out.push(...walk(join(p,ent.name),base+ent.name+'/'));
  else if(ent.isFile()&&!ent.name.startsWith('.')&&ent.name!=='sw.js'&&!ent.name.endsWith('.glb')&&!excluded.has(ent.name)){
    out.push('./'+base+ent.name);
  }
 }return out;
}
const expected=walk(new URL('.',root).pathname).sort();
assert.deepEqual(cache,expected,'offline asset list must match disk');
assert.ok(cache.includes('./proto3d/townlands.js')&&cache.includes('./balthrix-scale.html'));
assert.equal(new Set(cache).size,cache.length);
console.log('Offline release '+pkg.version+' verified: '+cache.length+' files; town landscape + comparison viewer are cached.');
