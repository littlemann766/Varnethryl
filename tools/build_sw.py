#!/usr/bin/env python3
"""Regenerate the PRECACHE list + CACHE name in www/sw.js from every file under www/ (except sw.js).
Usage: python3 tools/build_sw.py"""
from pathlib import Path
import json,re
root=Path(__file__).resolve().parents[1]; w=root/'www'
ver=json.loads((root/'package.json').read_text())['version']
files=sorted('./'+p.relative_to(w).as_posix() for p in w.rglob('*') if p.is_file() and p.name!='sw.js' and p.suffix!='.glb' and not p.name.startswith('.'))
s=(w/'sw.js').read_text(encoding='utf-8')
s=re.sub(r'^/\* Varnethryl v[^\n]*\*/',f'/* Varnethryl v{ver}: complete offline asset precache for installation (GLB models are cached lazily at runtime). */',s,count=1)
s=re.sub(r"const CACHE = PREFIX \+ '[^']*';",f"const CACHE = PREFIX + '{ver}';",s)
s=re.sub(r'const PRECACHE = \[.*?\];','const PRECACHE = '+json.dumps(files).replace('\\','\\\\')+';',s,count=1,flags=re.S)
(w/'sw.js').write_text(s,encoding='utf-8'); print(f'sw.js: {len(files)} files, cache {ver}')
