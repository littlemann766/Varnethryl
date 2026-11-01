# Weaponless variant of a voxel hero rig (FIT_AND_HIDE.md "baked_weapon" list).
# Removes whole voxel cells whose dominant bone is hand_X and whose centre is outside the fist keep-sphere,
# drops leftover floating hand cells, and caps the faces that were culled against removed cells.
# usage: blender -b -P strip_baked_weapon.py -- in.glb out.glb '<json list of {bone,center(glTF),radius}>'
import bpy,sys,json,math,bmesh
from collections import defaultdict,Counter
from mathutils import Vector
a=sys.argv[sys.argv.index('--')+1:]; src,out,rules=a[0],a[1],json.loads(a[2])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
sc=bpy.context.scene; sc.render.fps=30; sc.render.fps_base=1
for o in list(bpy.data.objects):
    if o.name.startswith('Icosphere'): bpy.data.objects.remove(o)
arm=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]
ob=max([o for o in bpy.data.objects if o.type=='MESH'],key=lambda o:len(o.data.vertices))
mw=ob.matrix_world; gn={g.index:g.name for g in ob.vertex_groups}
bm=bmesh.new(); bm.from_mesh(ob.data); bm.faces.ensure_lookup_table(); bm.verts.ensure_lookup_table()
dl=bm.verts.layers.deform.active; uvl=bm.loops.layers.uv.active
def dom(v):
    d=v[dl]; return gn[max(d.items(),key=lambda t:t[1])[0]] if d else None
DIRS=[(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)]
def geo(f):
    vs=[v.co for v in f.verts]
    if len(vs)==3:
        e=max([(vs[0],vs[1]),(vs[1],vs[2]),(vs[2],vs[0])],key=lambda t:(t[0]-t[1]).length)
        return (e[0]+e[1])/2,(e[0]-e[1]).length/math.sqrt(2)
    return f.calc_center_median(),math.sqrt(f.calc_area())
def ndir(n):
    i=max(range(3),key=lambda k:abs(n[k])); t=[0,0,0]; t[i]=1 if n[i]>0 else -1; return tuple(t)
cells=defaultdict(lambda:{'f':[],'b':Counter(),'dirs':set()})
fcell={}
for f in bm.faces:
    pc,sz=geo(f); c=pc-f.normal*(sz/2); q=sz*0.2
    k=(round(c.x/q),round(c.y/q),round(c.z/q),round(sz,4))
    d=cells[k]; d['f'].append(f); d['c']=c; d['s']=sz; d['dirs'].add(ndir(f.normal))
    for v in f.verts: d['b'][dom(v)]+=1
    u=f.loops[0][uvl].uv; d.setdefault('uv',Counter())[(round(u.x,4),round(u.y,4))]+=1
    fcell[f.index]=k
def nbk(k,n):
    d=cells[k]; c=d['c']+Vector(n)*d['s']; q=d['s']*0.2
    return (round(c.x/q),round(c.y/q),round(c.z/q),k[3])
cb={k:d['b'].most_common(1)[0][0] for k,d in cells.items()}
rm=set(); report={}
for r in rules:
    cg=r['center']; C=mw.inverted()@Vector((cg[0],-cg[2],cg[1]))
    hand=[k for k in cells if cb[k]==r['bone']]
    gone={k for k in hand if (mw@cells[k]['c']-Vector((cg[0],-cg[2],cg[1]))).length>r['radius']}
    # weapon palette = colours of the cut-off cells that the forearm/glove never uses; strip those colours inside the fist too
    fa='foreArm_'+r['bone'].split('_')[1]
    cuv=lambda k:cells[k]['uv'].most_common(1)[0][0]
    arm_uv={cuv(k) for k in cells if cb[k] in (fa,)}
    wuv={cuv(k) for k in gone}-arm_uv
    gone|={k for k in hand if cuv(k) in wuv}
    keep=[k for k in hand if k not in gone]; ks=set(keep)
    # connected components of remaining hand cells; keep the one(s) touching a non-hand cell or nearest the fist centre
    comp=[];seen=set()
    for k in keep:
        if k in seen: continue
        st=[k];cc=[];seen.add(k)
        while st:
            x=st.pop();cc.append(x)
            for n in DIRS:
                y=nbk(x,n)
                if y in ks and y not in seen: seen.add(y);st.append(y)
        comp.append(cc)
    def attached(cc): return any(nbk(x,n) in cells and cb.get(nbk(x,n))!=r['bone'] for x in cc for n in DIRS)
    big=max(comp,key=len) if comp else []
    for cc in comp:
        if cc is not big and not attached(cc): gone|=set(cc)
    rm|=gone; report[r['bone']]={'hand_cells':len(hand),'removed':len(gone),'kept':len(hand)-len(gone),'components':len(comp),'weapon_colours':len(wuv)}
fd=[f for f in bm.faces if fcell[f.index] in rm]
# drop small floating clusters (any bone) left near the hands
for r in rules:
    cg=r['center']; Cw=Vector((cg[0],-cg[2],cg[1]))
    near={k for k in cells if k not in rm and (mw@cells[k]['c']-Cw).length<0.3}
    seen=set()
    for k in near:
        if k in seen: continue
        st=[k];cc=[];seen.add(k);touch_out=False
        while st:
            x=st.pop();cc.append(x)
            for n in DIRS:
                y=nbk(x,n)
                if y in cells and y not in rm:
                    if y not in near: touch_out=True
                    elif y not in seen: seen.add(y);st.append(y)
        if len(cc)<6 and not touch_out: rm|=set(cc); report.setdefault('floaters',0); report['floaters']+=len(cc)
fd=[f for f in bm.faces if fcell[f.index] in rm]
# cap culled faces of kept cells that faced a removed cell
new=0
for k,d in cells.items():
    if k in rm: continue
    for n in DIRS:
        y=nbk(k,n)
        if y in rm and n not in d['dirs']:
            s=d['s']/2; c=d['c']; N=Vector(n); U=Vector((n[1],n[2],n[0])); V=N.cross(U)
            co=[c+N*s+(U*a+V*b)*s for a,b in ((-1,-1),(1,-1),(1,1),(-1,1))]
            src_v=d['f'][0].verts[0]
            vs=[bm.verts.new(p) for p in co]
            for v in vs:
                for gi,w in src_v[dl].items(): v[dl][gi]=w
            f=bm.faces.new(vs); f.material_index=d['f'][0].material_index; f.smooth=d['f'][0].smooth
            if f.normal.dot(N)<0: f.normal_flip()
            uv=d['f'][0].loops[0][uvl].uv.copy()
            for l in f.loops: l[uvl].uv=uv
            new+=1
bmesh.ops.delete(bm,geom=fd,context='FACES')
lone=[v for v in bm.verts if not v.link_faces]; bmesh.ops.delete(bm,geom=lone,context='VERTS')
bm.to_mesh(ob.data); bm.free(); ob.data.update()
report['caps']=new; report['src_faces']=len(fcell); report['removed_faces']=len(fd)
print('REPORT',json.dumps(report))
bpy.ops.export_scene.gltf(filepath=out,export_format='GLB',export_animation_mode='ACTIONS',export_force_sampling=True)
