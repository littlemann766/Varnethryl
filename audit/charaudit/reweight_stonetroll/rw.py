import sys
from g import *
def ss(x): x=np.clip(x,0,1); return x*x*(3-2*x)
def run(src,dst):
    g=G(src); p=g.j['meshes'][0]['primitives'][0]['attributes']
    names=[g.j['nodes'][i]['name'] for i in g.j['skins'][0]['joints']]; ix={n:i for i,n in enumerate(names)}
    P,_=g.view(p['POSITION']); J,_=g.view(p['JOINTS_0']); W,_=g.view(p['WEIGHTS_0'])
    n=len(P); D=np.zeros((n,21))
    for k in range(4): np.add.at(D,(np.arange(n),J[:,k].astype(int)),W[:,k])
    D/=D.sum(1,keepdims=True)
    sx=np.abs(P[:,0]); a=ss((sx-0.30)/0.20)*ss((P[:,1]-1.02)/0.12)
    legs=[ix[b+s] for b in('thigh_','shin_','foot_') for s in 'LR']
    O=D.copy(); O[a>0][:,legs]=0
    m=a>0; O[np.ix_(m,legs)]=0; O[m]/=O[m].sum(1,keepdims=True)
    N=np.zeros_like(D); side=np.where(P[:,0]>=0,'L','R')
    for s in 'LR':
        q=side==s; t=sx[q]
        sh=1-ss((t-0.25)/0.20); el=ss((t-0.55)/0.15); wr=ss((t-0.92)/0.13)
        N[q,ix['shoulder_'+s]]=sh
        N[q,ix['upperArm_'+s]]=(1-sh)*(1-el)
        N[q,ix['foreArm_'+s]]=(1-sh)*el*(1-wr)
        N[q,ix['hand_'+s]]=(1-sh)*el*wr
    F=(1-a)[:,None]*O+a[:,None]*N
    top=np.argsort(-F,1)[:,:4]; tw=np.take_along_axis(F,top,1); tw/=tw.sum(1,keepdims=True)
    g.write(p['JOINTS_0'],top); g.write(p['WEIGHTS_0'],tw); g.save(dst)
    # report hand region
    h=sx>1.2; r=F[h].mean(0); print(dst, {names[i]:round(r[i],2) for i in np.argsort(-r)[:4]})
import os; os.makedirs('/workspace/hero-motion/beth-reweight',exist_ok=True)
run('/workspace/hero-motion/godot-fixed/stonetroll_lod1.glb','/workspace/hero-motion/beth-reweight/stonetroll_lod1.glb')
run('/workspace/godot-art/characters/stonetroll.glb','/workspace/hero-motion/beth-reweight/stonetroll.glb')
run('/workspace/godot-art/characters/stonetroll_lod2.glb','/workspace/hero-motion/beth-reweight/stonetroll_lod2.glb')
