#!/usr/bin/env python3
"""Prepare the existing APPROVED Hydra and Tidewrack GLB models for devices
that cannot use the browser DecompressionStream API. Never generate a new
procedural hull or change the artist's original meshes.
The files are derived locally from checked-in gzip assets at build time.
"""
from pathlib import Path
import gzip
root=Path(__file__).resolve().parents[1]/'www'/'proto3d'/'models-new'
for name in ('tidewrack_sailing_ship', 'hydra_restored_mobile'):
    compressed=root/(name+'.glb.gz')
    raw=root/(name+'.glb')
    content=gzip.decompress(compressed.read_bytes())
    if len(content)<128 or content[:4]!=b'glTF':
        raise SystemExit(f'Invalid original compressed GLB: {compressed.name}')
    raw.write_bytes(content)
    print(f'Prepared original {name}: {len(content):,} bytes, GLB valid')
