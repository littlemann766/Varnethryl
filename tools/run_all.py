import json,subprocess,os
H=json.load(open('../tools/baked_weapon_rules.json'))
for h in os.environ['HEROES'].split():
    rules=[{"bone":b,"center":c,"radius":r} for b,c,r in H[h]]
    c=rules[0]["center"]
    for suf in ("","_lod1"):
        src=f"{h}_voxel{suf}.glb"
        if not os.path.exists(src): continue
        dst=f"{h}_voxel_noweapon{suf}.glb"
        print(h,suf,flush=True)
        subprocess.run(["../tools/run_one.sh",src,dst,json.dumps(rules),*map(str,c),h+suf])
