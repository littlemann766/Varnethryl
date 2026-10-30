import bpy,sys,numpy as np,collections
a=sys.argv[sys.argv.index('--')+1:]; bpy.ops.wm.open_mainfile(filepath=a[0])
arm=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]
ob=[o for o in bpy.data.objects if o.type=='MESH' and o.parent==arm and len(o.data.vertices)>1000][0]
me=ob.data; n=len(me.vertices); co=np.array([ob.matrix_world@v.co for v in me.vertices])
gn={g.index:g.name for g in ob.vertex_groups}; gi=np.array([max(v.groups,key=lambda g:g.weight).group if v.groups else -1 for v in me.vertices])
nm=np.array([gn.get(g,'') for g in gi])
def isa(s): return any(t in s.lower() for t in ('upperarm','forearm','hand','index','middle','ring','pinky','thumb','weapon'))
def isl(s): return any(t in s.lower() for t in ('thigh','shin','foot','toe'))
A=np.array([isa(s) for s in nm]); L=np.array([isl(s) for s in nm]); S=0.018
legs=set(map(tuple,np.floor(co[L]/S).astype(int)))
hit=np.array([A[i] and tuple(np.floor(co[i]/S).astype(int)) in legs for i in range(n)])
H=co[:,2].max()-co[:,2].min()
for g in set(nm[hit]):
  m=hit&(nm==g); t=(nm==g)
  print(g,'hit',m.sum(),'of',t.sum(),'z/H %.2f-%.2f'%((co[m,2].min()-co[:,2].min())/H,(co[m,2].max()-co[:,2].min())/H),'grp z/H %.2f-%.2f'%((co[t,2].min()-co[:,2].min())/H,(co[t,2].max()-co[:,2].min())/H),'x %.2f..%.2f'%(co[m,0].min(),co[m,0].max()))
# which leg bones
lc=collections.Counter()
LI=np.where(L)[0]; cells={}
for i in LI: cells.setdefault(tuple(np.floor(co[i]/S).astype(int)),nm[i])
for i in np.where(hit)[0]: lc[cells[tuple(np.floor(co[i]/S).astype(int))]]+=1
print('legbones',lc.most_common(6))
for g in ('thigh_L','thigh_R','hips','shin_L'):
  t=nm==g
  if t.any(): print(g,t.sum(),'x %.2f..%.2f'%(co[t,0].min(),co[t,0].max()),'z/H %.2f-%.2f'%((co[t,2].min()-co[:,2].min())/H,(co[t,2].max()-co[:,2].min())/H), 'x>0.25 count',(np.abs(co[t,0])>0.25).sum())
print('H',H, 'bone heads', {b.name:tuple(round(x,2) for x in (arm.matrix_world@b.head_local)) for b in arm.data.bones if b.name in('thigh_L','shin_L','foreArm_L','hand_L')})
