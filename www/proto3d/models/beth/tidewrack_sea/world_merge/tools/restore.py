"""Pipeline step 0 (Beth): every terrain mesh this pipeline may change gets its original saved once in the matching
meshes_v2_backup/ dir; on later runs the original is copied back first, so run_all.sh never stacks changes."""
import sys, os, glob, shutil
R = sys.argv[1]; n = 0
files = []
for st, pats in (('stage1', ['arch_islands*.glb']), ('stage2', ['coast_tile_*.glb', 'coast_terrain_col.glb', 'coast_beach_dressing*.glb', 'coast_saltglass_crystals*.glb']),
                 ('stage4', ['frost_tile_*.glb', 'frost_terrain_col.glb', 'ash_tile_*.glb', 'ash_terrain_col.glb', 'frost_ice_floes.glb', 'frost_ice_floes_lod1.glb', 'frost_icicles*.glb',
                             'ash_vents*.glb', 'ash_glow*.glb', 'ash_steam*.glb', 'ash_lava_seams*.glb'])):
    for p in pats: files += glob.glob(f'{R}/{st}/meshes/{p}')
files += [f for f in glob.glob(f'{R}/stage5_islands/meshes/*/*_isl_*.glb') if '_glow' not in f]
for f in sorted(set(files)):
    bdir = os.path.join(os.path.dirname(f), '..', 'meshes_v2_backup') if '/stage5_islands/' not in f else os.path.dirname(f).replace('/meshes/', '/meshes_v2_backup/')
    os.makedirs(bdir, exist_ok=True); b = os.path.join(bdir, os.path.basename(f))
    if os.path.exists(b): shutil.copy(b, f); n += 1
    else: shutil.copy(f, b)
for st, nm in (('stage1', 'arch'), ('stage2', 'coast'), ('stage4', 'frost'), ('stage4', 'ash')):
    p = f'{R}/{st}/shaders/{nm}_shore_dist.png'; b = f'{R}/{st}/shaders_v2_backup/{nm}_shore_dist.png'; os.makedirs(os.path.dirname(b), exist_ok=True)
    if os.path.exists(b): shutil.copy(b, p)
    else: shutil.copy(p, b)
print('restore: originals', len(files), 'restored', n)
