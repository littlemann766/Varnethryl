#!/usr/bin/env python3
"""Validate that all referenced offline assets exist before publishing or building."""
from pathlib import Path
import re, sys, json
root = Path(__file__).resolve().parents[1] / 'www'
js = (root/'sw.js').read_text(encoding='utf-8')
match = re.search(r'const PRECACHE = (\[.*?\]);', js)
if not match:
    sys.exit('ERROR: precache list missing')
missing = [p for p in json.loads(match.group(1)) if not (root / p[2:]).is_file()]
if missing:
    sys.exit('ERROR: missing assets: ' + ', '.join(missing))
assert len(list((root/'assets/heroes').glob('*.webp'))) == 20
assert len(list((root/'assets/sprites').glob('*.png'))) == 20
print('PASS: all precached assets found; 20 character portraits and sprites found')
