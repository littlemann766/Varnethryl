import math
from mathutils import Quaternion
LIM={'torso':14,'upperArm':26,'shoulder':7,'pauldron':18,'foreArm':45,'hand':32,'thigh':30,'shin':48,'foot':22,'toe':18,'spine2':10,'chest':10,'upperChest':8,'neck':20,'head':26,'wing':12,'tabard':14,'hips':40}
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
    a2=L*math.tanh(a/L)
    return Quaternion(q.axis,a2)
