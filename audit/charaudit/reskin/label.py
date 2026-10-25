import bpy,sys,numpy as np
from PIL import Image,ImageDraw
from scipy import ndimage
n=sys.argv[-1]; S=2048
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=f'/workspace/godot-art/characters/{n}.glb')
o=bpy.data.objects[n]; me=o.data; me.calc_loop_triangles()
gn={g.index:g.name for g in o.vertex_groups}
arm=o.parent; mw=arm.matrix_world
def tl(b):
    ch=[c for c in b.children if not c.name.startswith(('coat','cape','hair','eye','jaw','shoulder','thigh'))] or list(b.children)
    return mw@ch[0].head_local if ch else mw@b.head_local
seg={b.name:(mw@b.head_local,tl(b)) for b in arm.data.bones}
from mathutils.geometry import intersect_point_line
SKIP=('coat','cape','hair','eye','jaw','index','middle','ring','pinky','thumb','toe')
segs=[(mw@b.parent.head_local,mw@b.head_local) for b in arm.data.bones if b.parent and not b.name.startswith(SKIP) and (b.head_local-b.parent.head_local).length>1e-3]
def bdist(b,p):
    best=9
    for h,t in segs:
        q,f=intersect_point_line(p,h,t); f=min(max(f,0),1); best=min(best,(p-(h+(t-h)*f)).length)
    return best
def _old(b,p):
    h,t=seg[b]; q,f=intersect_point_line(p,h,t); f=min(max(f,0),1); return (p-(h+(t-h)*f)).length

def reg(b,nrm,z):
    if b.startswith(('head','neck','jaw','eye','hair')): return 1
    if b.startswith(('chest','upperChest','spine2')): return 2 if nrm.y<0.2 else 3
    if b.startswith('shoulder'): return 4
    if b.startswith('upperArm'): return 4
    if b.startswith('foreArm'): return 5
    if b.startswith(('hand','fingers','index','middle','ring','pinky','thumb')): return 6
    if b.startswith(('hips','spine','root')): return 7
    if b.startswith('coat'): return 8
    if b.startswith('cape'): return 9
    if b.startswith('thigh'): return 10
    if b.startswith('shin'): return 11
    if b.startswith(('foot','toe')): return 12
    return 13
uv=me.uv_layers.active.data
L=Image.new('L',(S,S),0); d=ImageDraw.Draw(L)
for t in me.loop_triangles:
    acc={}
    for v in t.vertices:
        for g in me.vertices[v].groups: acc[g.group]=acc.get(g.group,0)+g.weight
    b=gn[max(acc,key=acc.get)] if acc else 'x'
    nrm=o.matrix_world.to_3x3()@t.normal
    r=reg(b,nrm,0)
    c=o.matrix_world@t.center
    if b in seg and r in (2,3,7,8,9,10,11,4) :
        dd=bdist(b,c); thr={2:.17,3:.15,7:.19,8:.0,9:.0,10:.12,11:.10,4:.11}[r]
        pass
    pts=[(uv[l].uv[0]*S,(1-uv[l].uv[1])*S) for l in t.loops]
    d.polygon(pts,fill=r,outline=r)
a=np.array(L)
idx=ndimage.distance_transform_edt(a==0,return_distances=False,return_indices=True)
a=a[tuple(idx)]
np.save(f'lab_{n}.npy',a)
print('LAB',n,np.bincount(a.ravel(),minlength=14))
