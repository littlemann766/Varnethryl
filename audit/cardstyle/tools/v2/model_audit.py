# Geometry audit of every published GLB: base height (sunk/floating), floating islands, LOD ratios, open-hole estimate.
import trimesh, numpy as np, glob, os, json, sys
G='/workspace/godot-art'
def sets():
    out=[]
    for f in sorted(glob.glob(G+'/buildings/*.glb')+glob.glob(G+'/buildings/tripo/*.glb')+glob.glob(G+'/props_street/*.glb')+glob.glob(G+'/interiors/*.glb')+glob.glob(G+'/ships/*.glb')):
        b=os.path.basename(f)
        if any(s in b for s in ('_lod1','_lod2','_col')): continue
        out.append(f)
    return out
def islands(m):
    V=m.vertices.round(3); _,inv=np.unique(V,axis=0,return_inverse=True); F=inv.ravel()[m.faces]
    lab=trimesh.graph.connected_component_labels(trimesh.graph.face_adjacency(F),node_count=len(F))
    boxes=[];
    for l in np.unique(lab):
        P=m.vertices[m.faces[lab==l]].reshape(-1,3); boxes.append((P.min(0),P.max(0),(lab==l).sum()))
    lo=np.array([b[0] for b in boxes]); hi=np.array([b[1] for b in boxes]); fl=[]
    for i,(a,b,n) in enumerate(boxes):
        if a[1]<0.15: continue
        ov=np.all((lo<=b+0.08)&(hi>=a-0.08),axis=1); ov[i]=False
        if not ov.any(): fl.append(dict(faces=int(n),min=a.round(2).tolist(),max=b.round(2).tolist()))
    return len(boxes),fl
rows=[]
for f in sets():
    m=trimesh.load(f,force='mesh',process=False); n=len(m.faces); b=m.bounds
    r=dict(file=os.path.relpath(f,G),tris=n,min_y=round(float(b[0,1]),3),size=np.ptp(b,0).round(2).tolist())
    for k in (1,2):
        lf=f[:-4]+f'_lod{k}.glb'
        if os.path.exists(lf): r[f'lod{k}']=round(len(trimesh.load(lf,force='mesh',process=False).faces)/max(n,1),3)
    r['has_col']=os.path.exists(f[:-4]+'_col.glb')
    r['n_islands'],fl=islands(m); r['floating']=fl[:5]; r['n_floating']=len(fl)
    rows.append(r); print(r['file'],n,r['min_y'],r.get('lod1'),r.get('lod2'),r['n_floating'],flush=True)
json.dump(rows,open('/workspace/beth-world/audit/model_audit/geom_audit.json','w'),indent=1)
