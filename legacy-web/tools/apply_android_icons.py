#!/usr/bin/env python3
"""Run in CI after `npx cap add android` (before gradle): overlay Varnethryl launcher icons + splash onto android/app/src/main/res."""
import shutil, sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]; src=root/'android-res'; res=root/'android/app/src/main/res'
if not res.is_dir(): sys.exit('android/app/src/main/res missing: run `npx cap add android` first')
for p in list(res.glob('drawable*/splash.*')): p.unlink()          # drop Capacitor default splash at every density/orientation
for p in list(res.glob('mipmap-*/ic_launcher*')):
    if p.suffix in ('.png','.webp'): p.unlink()
n=0
for f in src.rglob('*'):
    if f.is_file() and f.name!='playstore-icon-512.png':
        d=res/f.relative_to(src); d.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(f,d); n+=1
print(f'Applied {n} icon/splash files to {res}')
