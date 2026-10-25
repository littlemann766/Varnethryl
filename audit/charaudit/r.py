import bpy,sys,math,os
from mathutils import Vector
f,outp,mode=sys.argv[-3],sys.argv[-2],sys.argv[-1]
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene; sc.render.engine='CYCLES'; sc.cycles.samples=8; sc.cycles.device='CPU'; sc.render.resolution_x=220; sc.render.resolution_y=300; sc.cycles.use_denoising=False
bpy.ops.import_scene.gltf(filepath=f)
arms=[o for o in bpy.data.objects if o.type=='ARMATURE']
w=bpy.data.worlds.new('w'); sc.world=w; w.use_nodes=True; w.node_tree.nodes['Background'].inputs[0].default_value=(0.55,0.6,0.7,1)
bpy.ops.object.light_add(type='SUN',rotation=(math.radians(50),0,math.radians(-30))); bpy.context.object.data.energy=3.5
cam=bpy.data.objects.new('cam',bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera=cam; cam.data.lens=40
mesh=[o for o in bpy.data.objects if o.type=='MESH']
def bbox():
    dg=bpy.context.evaluated_depsgraph_get(); mn=Vector((1e9,)*3); mx=Vector((-1e9,)*3)
    for o in mesh:
        e=o.evaluated_get(dg); m=e.to_mesh()
        for v in m.vertices:
            p=e.matrix_world@v.co; mn=Vector(map(min,mn,p)); mx=Vector(map(max,mx,p))
        e.to_mesh_clear()
    return mn,mx
def setclip(n,fr):
    if not arms: return False
    a=bpy.data.actions.get(n) or next((x for x in bpy.data.actions if x.name.startswith(n)),None)
    if not a: return False
    arm=arms[0]; arm.animation_data_create(); arm.animation_data.action=a
    if getattr(a,'slots',None): arm.animation_data.action_slot=a.slots[0]
    r=a.frame_range; sc.frame_set(int(r[0]+(r[1]-r[0])*fr)); return True
setclip('idle',0)
mn,mx=bbox(); h=mx.z-mn.z; c=(mn+mx)/2; L=max(h,mx.x-mn.x,mx.y-mn.y)
shots=[('idle',0,'front'),('idle',0,'back')]
if mode=='anim': shots+=[('run',0.3,'q'),('run',0.7,'q'),('attack1',0.5,'q'),('attack',0.5,'q')]
done=set()
for cl,fr,v in shots:
    if not setclip(cl,fr) and cl!='idle': continue
    if cl=='attack' and 'attack1' in done: continue
    done.add(cl)
    d=L*1.5
    cam.location={'front':(c.x,c.y-d,c.z+h*0.1),'back':(c.x,c.y+d,c.z+h*0.1),'q':(c.x+d*0.7,c.y-d*0.7,c.z+h*0.1)}[v]
    cam.rotation_euler=(Vector(c)-cam.location).to_track_quat('-Z','Y').to_euler()
    sc.render.filepath=f'{outp}_{cl}{fr}_{v}.png'; bpy.ops.render.render(write_still=True)
print('H',round(h,3),'TEX',[i.name for i in bpy.data.images])
