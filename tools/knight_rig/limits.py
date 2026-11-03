import os
import math
from mathutils import Quaternion
LIM5={'torso':14,'upperArm':26,'shoulder':7,'pauldron':18,'foreArm':45,'hand':32,'thigh':30,'shin':48,'foot':22,'toe':18,'spine2':10,'chest':10,'upperChest':8,'neck':20,'head':26,'wing':12,'tabard':14,'hips':40}
def lim_for(b):
    for k,v in LIM.items():
        if b.startswith(k): return math.radians(v)
    return None
def soft(q,b):
    L=lim_for(b)
    if L is None: return q
    q=Quaternion(q).normalized()
    if q.w<0: q=-q
    a=q.angle
    if a<1e-6: return q
    if os.environ.get('LIMSET','6')=='6':
        K=0.75*L; a2=a if a<K else K+(L-K)*math.tanh((a-K)/(L-K))
    else: a2=L*math.tanh(a/L)
    return Quaternion(q.axis,a2)

import os
LIM6={'torso':35,'upperArm':170,'shoulder':30,'pauldron':60,'foreArm':115,'hand':50,'thigh':85,'shin':120,'foot':50,'toe':20,'spine2':20,'chest':20,'upperChest':15,'neck':25,'head':30,'wing':28,'tabard':28,'hips':180}
LIM=LIM6 if os.environ.get('LIMSET','6')=='6' else LIM5
