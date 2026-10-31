#!/usr/bin/env python3
"""Copy Beth's interior props used by interiors/interior_defs.gd (Medium only by default, --high adds High) into res://interiors/kit.
Never imports in /workspace/godot-art/interiors. Then: godot --headless --import && python3 tools/sync_kit.py --vram"""
import re, shutil, json, sys, glob, os
SRC = "/workspace/godot-art/interiors/"; DST = os.path.join(os.path.dirname(__file__), "../interiors/kit/")
if "--vram" in sys.argv:   # force VRAM compression on textures extracted from the GLBs
    for f in glob.glob(DST + "*.import"):
        if f.endswith(".glb.import"): continue
        t = open(f).read(); t2 = re.sub(r"compress/mode=\d", "compress/mode=2", t); t2 = re.sub(r"process/size_limit=\d+", "process/size_limit=512", t2)
        if t2 != t: open(f, "w").write(t2); print("vram", os.path.basename(f))
    sys.exit()
s = open(os.path.join(os.path.dirname(__file__), "../interiors/interior_defs.gd")).read()
names = set(re.findall(r'\["([a-z][a-z_]+)", \d', s)) | {"ladder", "wall_lantern", "iron_chandelier", "chair", "balcony_railing"}
idx = json.load(open(SRC + "index.json")); names &= set(idx["props"])
os.makedirs(DST, exist_ok=True)
for n in sorted(names):
    for suf in (["", "_lod1"] if "--high" in sys.argv else ["_lod1"]): shutil.copy(SRC + n + suf + ".glb", DST)
# extra props from other kits (Beth's tripo2 set), copied under a kit name
EXTRA = {"castle_model": ("/workspace/godot-art/tripo2/prop_castle_model", {"size_m": [0.6, 0.54, 0.566], "collision_box": {"center": [0, 0.27, 0], "extents": [0.6, 0.54, 0.566]}})}
for n, (src, meta) in EXTRA.items():
    if re.search(r'\["%s", \d' % n, s):
        for suf in (["", "_lod1"] if "--high" in sys.argv else ["_lod1"]): shutil.copy(src + suf + ".glb", DST + n + suf + ".glb")
        idx["props"][n] = dict(meta, name=n); names.add(n)
idx["props"] = {k: v for k, v in idx["props"].items() if k in names}
json.dump(idx, open(DST + "index.json", "w"), indent=1); print(len(names), "props")
