import numpy as np,json,struct
from PIL import Image
exec(open('an.py').read().split('R=skin')[0])  # reuse loader
z=np.load('an.npz');m=np.array(Image.open('titan_lava_mask.png'))[...,0]/255.
S=m.shape[0];vm=m[np.clip((UV[:,1]*S).astype(int),0,S-1),np.clip((UV[:,0]*S).astype(int),0,S-1)]
jn=[N[i]['name'] for i in joints];dom=J[np.arange(len(J)),W.argmax(1)];wmax=W.max(1)
want={'head':'drip_neck','chest':'drip_chest','spine2':'drip_waist','hips':'drip_hips',
'shoulder_L':'drip_shoulder_L','shoulder_R':'drip_shoulder_R','upperArm_L':'drip_elbow_L','upperArm_R':'drip_elbow_R',
'foreArm_L':'drip_wrist_L','foreArm_R':'drip_wrist_R','hand_L':'drip_hand_L','hand_R':'drip_hand_R',
'thigh_L':'drip_knee_L','thigh_R':'drip_knee_R','shin_L':'drip_ankle_L','shin_R':'drip_ankle_R'}
out=[]
for bn,name in want.items():
    k=jn.index(bn);sel=(dom==k)&(vm>0.5)
    if sel.sum()<5: sel=(dom==k)
    if sel.sum()<5: sel=((J==k)&(W>0.2)).any(1)
    print(bn,sel.sum())
    pts=P[sel];
    # bone-specific end: elbow/knee/wrist = farthest along bone child direction -> use lowest-weighted (blend) verts
    if name.split('_')[1] in('elbow','knee','wrist','ankle'):
        s2=sel&(wmax<0.75)
        if s2.sum()>5: pts=P[s2]
    # pick lowest-hanging cluster: bottom 15% by Y
    pp=pts[pts[:,1]<=np.percentile(pts[:,1],15)];c=pp.mean(0)
    loc=(IBM[k]@np.r_[c,1])[:3]
    out.append({'name':name,'bone':bn,'offset':[round(float(x),4) for x in loc],'rest_pos_model':[round(float(x),4) for x in c],'emit_dir':'down (world -Y)','vein_density':round(float(vm[sel].mean()),3)})
json.dump({'note':'Offsets are in bone-local space at bind pose, model units (pre 1.3362 instance scale). Attach a BoneAttachment3D to the bone, add a child Node3D at offset; emit along world -Y.','points':out},open('titan_drip_points.json','w'),indent=1)
for o in out:print(o['name'],o['offset'],o['vein_density'])
