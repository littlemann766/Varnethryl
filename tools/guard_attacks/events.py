# hit/phase frames per clip from weapon-hand speed (right hand = mace, left hand = shield)
import bpy,sys,json
import numpy as np
a=sys.argv[sys.argv.index('--')+1:]; blend,out,clipsj=a[0],a[1],a[2]
C=json.load(open(clipsj))
bpy.ops.wm.open_mainfile(filepath=blend); sc=bpy.context.scene; sc.render.fps=30
arm=[o for o in sc.objects if o.type=='ARMATURE'][0]; P='mixamorig:'
ev={'fps':30,'units':'frames (0-based) at 30 fps; seconds = frame/30','clips':{}}
for an,cfg in C.items():
    A=bpy.data.actions[an]; arm.animation_data.action=A; L=int(A.frame_range[1])
    side=cfg.get('weapon'); pos={'R':[],'L':[]}
    for f in range(L+1):
        sc.frame_set(f)
        for s,b in (('R','RightHand'),('L','LeftHand')): pos[s].append(np.array(arm.matrix_world@arm.pose.bones[P+b].tail))
    e={'frames':L+1,'duration_s':round((L+1)/30,3),'loop':bool(cfg.get('loop'))}
    if side:
        p=np.array(pos[side]); sp=np.r_[0,np.linalg.norm(np.diff(p,axis=0),axis=1)*30]
        pk=int(np.argmax(sp)); m=sp[pk]
        s0=pk
        while s0>0 and sp[s0-1]>0.3*m: s0-=1
        hit=pk
        while hit<L and sp[hit]>0.5*m: hit+=1
        r0=hit
        while r0<L and sp[r0]>0.25*m: r0+=1
        e.update({'weapon':'mace (right hand)' if side=='R' else 'shield (left hand)','windup':[0,max(0,s0-1)],'swing':[s0,hit],'hit_frame':hit,'hit_time_s':round(hit/30,3),
                  'recovery':[r0,L],'cancel_window_from':r0,'peak_weapon_speed_mps':round(float(m),2),'weapon_speed_mps':[round(float(x),1) for x in sp],'hand_world_pos_at_hit':[round(float(x),3) for x in p[hit]]})
    elif an=='block':
        p=np.array(pos['L']); sp=np.r_[0,np.linalg.norm(np.diff(p,axis=0),axis=1)*30]; pk=int(np.argmax(sp))
        r=pk
        while r<L and sp[r]>0.25*sp[pk]: r+=1
        e.update({'block_active':[r,max(r,L-6)],'raise':[0,r]})
    elif an=='hit':
        e.update({'stagger':[0,L-6],'recover':[L-6,L]})
    ev['clips'][an]=e
json.dump(ev,open(out,'w'),indent=1); print('EV',json.dumps({k:v.get('hit_frame') for k,v in ev['clips'].items()}))
