import bpy,sys,math,json,struct,glob,os
from mathutils import Vector,Matrix
files=sorted(glob.glob('/workspace/godot-proto/characters/*_lod1.glb'))+sorted(glob.glob('/workspace/godot-proto/enemies/models/*.glb'))
def gl(f):
    d=open(f,'rb').read(); n=struct.unpack('<I',d[12:16])[0]; return json.loads(d[20:20+n])
out=[]
for f in files:
    name=os.path.basename(f).replace('_lod1.glb','').replace('.glb','')
    j=gl(f); r={'name':name,'file':f}
    sk=j.get('skins',[]); r['anims']=[a.get('name') for a in j.get('animations',[])]
    if not sk: r['bones']=0; out.append(r); continue
    joints=sk[0]['joints']; r['bones']=len(joints)
    ident=0
    for i in joints:
        q=j['nodes'][i].get('rotation',[0,0,0,1])
        if abs(q[3])>0.9999: ident+=1
    r['ident_frac']=ident/len(joints)
    bpy.ops.wm.read_factory_settings(use_empty=True); sc=bpy.context.scene
    bpy.ops.import_scene.gltf(filepath=f)
    arm=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]
    bn=[b.name for b in arm.data.bones]
    def find(k,s):
        c=[b for b in bn if k.lower() in b.lower() and (b.endswith('_'+s) or b.lower().endswith('.'+s.lower()) or ('left' if s=='L' else 'right') in b.lower())]
        return c[0] if c else None
    ua,hd=find('upperarm','L') or find('arm','L'),find('hand','L')
    r['ua'],r['hand']=ua,hd; r['bonenames']=bn[:40]
    def angle():
        if not(ua and hd): return None
        p=arm.pose.bones; a=arm.matrix_world@p[ua].head; b=arm.matrix_world@p[hd].head
        v=(b-a).normalized(); return round(math.degrees(v.angle(Vector((0,0,-1)))))
    r['rest_arm_deg']=angle()
    act=bpy.data.actions.get('run') or next((a for a in bpy.data.actions if 'run' in a.name.lower()),None)
    if act:
        arm.animation_data_create(); arm.animation_data.action=act
        if getattr(act,'slots',None): arm.animation_data.action_slot=act.slots[0]
        fr=act.frame_range; sc.frame_set(int(fr[0]+(fr[1]-fr[0])*0.3))
        r['run_arm_deg']=angle()
        if ua:
            tw=[]
            for b in (ua,find('forearm','L') or find('lowerarm','L'),hd):
                if b:
                    q=arm.pose.bones[b].matrix_basis.to_quaternion(); tw.append(round(math.degrees(q.to_swing_twist('Y')[1])))
            r['run_twist']=tw
            # palm normal: hand bone local X axis (thumb side) world z component => roll
            if not hd: continue_=1
            else:
             M=arm.matrix_world@arm.pose.bones[hd].matrix
             r["palm_up_z"]=round((M.to_3x3()@Vector((0,0,1))).normalized().z,2)
        # render
        sc.render.engine='BLENDER_WORKBENCH'; sc.display.shading.light='STUDIO'; sc.display.shading.color_type='TEXTURE'
        sc.render.resolution_x=240; sc.render.resolution_y=300
        ms=[o for o in bpy.data.objects if o.type=='MESH']
        dg=bpy.context.evaluated_depsgraph_get(); mn=Vector((1e9,)*3); mx=-mn
        for o in ms:
            for c in o.evaluated_get(dg).bound_box:
                p=o.matrix_world@Vector(c); mn=Vector(map(min,mn,p)); mx=Vector(map(max,mx,p))
        cen=(mn+mx)/2; L=max(mx-mn)
        cam=bpy.data.objects.new('c',bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera=cam
        cam.location=cen+Vector((L*1.1,-L*1.9,L*0.3)); cam.rotation_euler=(cen-cam.location).to_track_quat('-Z','Y').to_euler()
        sc.render.filepath=f'/tmp/rig/{name}.png'; bpy.ops.render.render(write_still=True)
    out.append(r)
json.dump(out,open('/tmp/rig/res.json','w'),indent=1)
