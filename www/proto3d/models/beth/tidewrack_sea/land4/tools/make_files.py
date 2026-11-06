"""File lists for the still renderer. Before = land3 terrain + land3 scatter. After = land4. Props are shared and not modified."""
import os, json, glob
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SEA = os.path.abspath(os.path.join(ROOT, ".."))
LAND3 = os.path.join(SEA, "land3")
REG = {"A": ("stage1/meshes/", "arch_"), "B": ("stage2/meshes/", "coast_"), "frost": ("stage4/meshes/", "frost_"), "ash": ("stage4/meshes/", "ash_")}
SKIP = ("storm", "fog", "ocean", "buoy", "upg_", "hero", "floe", "iceberg", "hidden", "sunken", "coil_joints")

def is_terrain(b):
    return "_tile_" in b or b == "arch_islands" or ("_isl_" in b and not b.endswith("_glow") and not b.endswith("_port"))

def props(region):
    d, pre = REG[region]
    out = []
    src = os.path.join(SEA, d)
    if os.path.isdir(src):
        for f in sorted(os.listdir(src)):
            if not f.endswith(".glb") or f.endswith("_lod1.glb") or f.endswith("_col.glb"):
                continue
            b = f[:-4]
            if is_terrain(b) or any(s in b for s in SKIP):
                continue
            if not b.startswith(pre):
                continue
            out.append(dict(path=os.path.join(src, f), terrain=False))
    # stage5 harbour / glow, same region prefix
    s5 = os.path.join(SEA, "stage5_islands", "meshes", {"A": "A", "B": "B", "frost": "frost", "ash": "ash"}[region])
    if os.path.isdir(s5):
        for f in sorted(os.listdir(s5)):
            if not f.endswith(".glb") or f.endswith("_lod1.glb") or f.endswith("_col.glb"):
                continue
            b = f[:-4]
            if is_terrain(b):
                continue
            out.append(dict(path=os.path.join(s5, f), terrain=False))
    return out

def scat(root, region):
    d, pre = REG[region]
    folder = os.path.join(root, d)
    out = []
    if not os.path.isdir(folder):
        return out
    for f in sorted(os.listdir(folder)):
        if "land_scatter" in f and f.endswith(".glb") and not f.endswith("_lod1.glb") and not f.endswith("_col.glb"):
            out.append(dict(path=os.path.join(folder, f), terrain=False))
    return out

def terr(root, region):
    d, pre = REG[region]
    folder = os.path.join(root, d)
    out = []
    for f in sorted(os.listdir(folder)):
        if not f.endswith(".glb") or f.endswith("_lod1.glb") or f.endswith("_col.glb"):
            continue
        b = f[:-4]
        if b.startswith(pre) and is_terrain(b):
            out.append(dict(path=os.path.join(folder, f), terrain=True))
    return out

def main():
    before, after = {}, {}
    for region in REG:
        before[region] = terr(LAND3, region) + scat(LAND3, region) + props(region)
        after[region] = terr(ROOT, region) + scat(ROOT, region) + props(region)
        print(region, "before", len(before[region]), "after", len(after[region]))
    json.dump(before, open(os.path.join(ROOT, "preview", "files_before.json"), "w"))
    json.dump(after, open(os.path.join(ROOT, "preview", "files_after.json"), "w"))

if __name__ == "__main__":
    main()
