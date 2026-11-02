import os
G='/workspace/godot-voxel/tidewrack/'
REG={'A':('stage1/meshes/','arch_'),'B':('stage2/meshes/','coast_'),'frost':('stage4/meshes/','frost_'),'ash':('stage4/meshes/','ash_')}
SKIP={"arch_storm_wall","arch_fog_bank","frost_iceberg_a","frost_iceberg_b","frost_iceberg_c","coast_echo_grotto","coast_glasswyrm_cavern","coast_smugglers_throat"}
def files(r):
    d,p=REG[r]; out=[]
    for f in sorted(os.listdir(G+d)):
        if not f.endswith('.glb') or not f.startswith(p): continue
        b=f[:-4]
        if b.endswith('_lod1') or b.endswith('_col') or b in SKIP: continue
        if any(k in b for k in ['_fog_layers','_storm_','_sunken_ward','_hidden_spots']): continue
        out.append(d+f)
    return out
def is_terrain(b):
    return '_tile_' in b or b in ('arch_islands',) or ('_isl_' in b and not b.endswith('_glow') and not b.endswith('_port'))
