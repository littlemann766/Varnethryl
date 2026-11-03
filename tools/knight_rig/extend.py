# v4: extend plate rims at joints (rigid, same part/bone, mirrored UVs) so neighbours overlap; rest-hidden
import bpy,sys,json,math,numpy as np,bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree
G=sys.argv[-1]; OUT=f'/tmp/kr/{G}'; EXT=float(__import__('os').environ.get('EXTL','0.03'))
bpy.ops.wm.open_mainfile(filepath=f'{OUT}/stage3.blend')
ARM=bpy.data.objects['knight_rig']; fig=bpy.data.objects[f'knight_{G}']; me=fig.data
BH={b.name:np.array(b.head_local) for b in ARM.data.bones}; PAR={b.name:(b.parent.name if b.parent else None) for b in ARM.data.bones}
KIDS={}
for b,p in PAR.items():
    if p: KIDS.setdefault(p,[]).append(b)
gn=[g.name for g in fig.vertex_groups]
JOINTB=('pauldron','shoulder','upperArm','elbow','foreArm','hand','neck','upperChest','chest','spine2','hips','tasset','thigh','knee','shin','foot')
bm=bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
dl=bm.verts.layers.deform.active; uvl=bm.loops.layers.uv.active
pl=bm.verts.layers.int.get('part'); bll=bm.verts.layers.int.get('blended')
orig_tree=BVHTree.FromBMesh(bm)
def vb(v):
    d=v[dl]; 
    if not d: return None,0
    k=max(d.keys(),key=lambda x:d[x]); return gn[k],d[k]
def joints(b):
    J=[BH[b]]+[BH[c] for c in KIDS.get(b,[]) if not c.startswith(('wing','tabard'))]
    return J
DIRS=np.array([[math.cos(math.radians(e))*math.cos(math.radians(a)),math.cos(math.radians(e))*math.sin(math.radians(a)),math.sin(math.radians(e))] for e in (-15,0,20,40,60) for a in range(0,360,20)])
def visible(p,n):
    for d in DIRS[DIRS@n>0.2]:
        o=Vector(p)+Vector(d)*0.0005; hidden=False
        for _ in range(6):
            h=orig_tree.ray_cast(o,Vector(d),3.0)
            if h[0] is None: break
            if (h[0]-Vector(p)).length>0.008: hidden=True; break
            o=h[0]+Vector(d)*0.0005
        if not hidden: return True
    return False
bnd=[e for e in bm.edges if len(e.link_faces)==1]
print('boundary edges',len(bnd))
newv={}; stats={'edges_ext':0,'verts_ext':0,'shrunk':0,'dropped':0}
cand={}
for e in bnd:
    f=e.link_faces[0]; a,b=e.verts
    ba,wa=vb(a); bb,wb=vb(b)
    if ba is None or ba!=bb or wa<0.999 or wb<0.999 or not ba.startswith(JOINTB): continue
    c=f.calc_center_median(); m=(a.co+b.co)/2; ed=(b.co-a.co); n=f.normal
    out=ed.cross(n).normalized()
    if out.dot(m-c)<0: out=-out
    J=joints(ba); mp=np.array(m)
    dj=[np.linalg.norm(j-mp) for j in J]; k=int(np.argmin(dj))
    if dj[k]>0.14: continue
    u=(J[k]-mp)/max(dj[k],1e-9)
    if np.dot(np.array(out),u)<0.25: continue
    for v in (a,b): cand.setdefault(v.index,[]).append((np.array(out),f))
# per boundary vertex: extension direction = mean outward; length EXT, shrink while visible in rest
for vi,L in cand.items():
    v=bm.verts[vi]; d=np.mean([x for x,_ in L],0); d/=max(np.linalg.norm(d),1e-9)
    p0=np.array(v.co); n=np.array(L[0][1].normal); l=EXT; ok=False
    for it in range(4):
        p=p0+d*l
        if all(not visible(p0+d*l*t,n) and not visible(p0+d*l*t,-n) for t in (0.12,0.35,0.65,1.0)): ok=True; break
        l*=0.5; stats['shrunk']+=1
    if not ok: stats['dropped']+=1; continue
    newv[vi]=(p,l,d,L[0][1])
# build quads
made=0
nvmap={}
OV={vi:bm.verts[vi] for vi in newv}
for vi,(p,l,d,f) in newv.items():
    v=OV[vi]; nv=bm.verts.new(Vector(p)); nv[dl].clear()
    for k,w in v[dl].items(): nv[dl][k]=w
    if pl: nv[pl]=v[pl]
    if bll: nv[bll]=0
    nvmap[vi]=nv
bm.verts.ensure_lookup_table()
DUP={}; ORIG={}
def dup(v):
    if v.index not in DUP:
        n=bm.verts.new(v.co.copy()); n[dl].clear()
        for k,w in v[dl].items(): n[dl][k]=w
        if pl: n[pl]=v[pl]
        if bll: n[bll]=0
        bm.verts.index_update(); DUP[v.index]=n; ORIG[n.index]=v
    return DUP[v.index]
def uv_of(v,f):
    for lp in f.loops:
        if lp.vert==v: return lp[uvl].uv.copy()
def uvjac(f):
    ls=f.loops[:3]; P=np.array([np.array(x.vert.co) for x in ls]); U=np.array([np.array(x[uvl].uv) for x in ls])
    E=np.array([P[1]-P[0],P[2]-P[0]]).T; D=np.array([U[1]-U[0],U[2]-U[0]]).T
    return D@np.linalg.pinv(E)
for e in bnd:
    a,b=e.verts
    if a.index in nvmap and b.index in nvmap:
        f=e.link_faces[0]
        # winding consistent with neighbour face
        lp=[l for l in f.loops if l.vert==a][0]; order=(b,a) if lp.link_loop_next.vert==b else (a,b)
        x,y=order
        x2=dup(x); y2=dup(y)
        try: nf=bm.faces.new((x2,y2,nvmap[y.index],nvmap[x.index]))
        except ValueError: continue
        nf.material_index=f.material_index; nf.smooth=f.smooth
        Jf=uvjac(f)
        for l in nf.loops:
            if l.vert in (DUP.get(a.index),DUP.get(b.index)): l[uvl].uv=uv_of(ORIG[l.vert.index],f)
            else:
                src=[s for s in (a,b) if nvmap[s.index]==l.vert][0]
                off=np.array(l.vert.co)-np.array(src.co)
                l[uvl].uv=uv_of(src,f)-Vector(Jf@off)   # mirrored back into the plate's own UV island (reuses his texels)
        made+=1
stats['edges_ext']=made; stats['verts_ext']=len(nvmap); stats['ext_len_m']=EXT
bm.to_mesh(me); bm.free(); me.update()
print('EXTEND',stats)
r=json.load(open(OUT+'/bind3_report.json')); r['rim_extension']=stats; json.dump(r,open(OUT+'/bind3_report.json','w'),indent=1)
bpy.ops.wm.save_as_mainfile(filepath=f'{OUT}/stage4.blend')
