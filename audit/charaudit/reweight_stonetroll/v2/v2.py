from g import *
def ss(x): x=np.clip(x,0,1); return x*x*(3-2*x)
EL,WR=0.72,1.08
def run(base,orig,dst):
    g=G(base); o=G(orig); p=g.j['meshes'][0]['primitives'][0]['attributes']
    sk=g.j['skins'][0]; names=[g.j['nodes'][i]['name'] for i in sk['joints']]; ix={n:i for i,n in enumerate(names)}
    newt={}
    for s,sg in (('L',1),('R',-1)):
        newt['foreArm_'+s]=sg*(EL-0.25); newt['hand_'+s]=sg*(WR-EL)
    shift={}
    for s,sg in (('L',1),('R',-1)):
        fa=g.j['nodes'][sk['joints'][ix['foreArm_'+s]]]; ha=g.j['nodes'][sk['joints'][ix['hand_'+s]]]
        d1=newt['foreArm_'+s]-fa['translation'][0]; d2=d1+newt['hand_'+s]-ha['translation'][0]
        shift['foreArm_'+s]=d1; shift['hand_'+s]=d2
        fa['translation'][0]=newt['foreArm_'+s]; ha['translation'][0]=newt['hand_'+s]
    ib,_=g.view(sk['inverseBindMatrices']); ib=ib.copy()
    for n,d in shift.items():
        M=np.linalg.inv(ib[ix[n]].reshape(4,4).T); M[0,3]+=d; ib[ix[n]]=np.linalg.inv(M).T.reshape(16)
    g.write(sk['inverseBindMatrices'],ib)
    nid={sk['joints'][ix[n]]:n for n in newt}; seen={}
    for a in g.j['animations']:
        for c in a['channels']:
            if c['target']['path']=='translation' and c['target']['node'] in nid:
                acc=a['samplers'][c['sampler']]['output']; n=nid[c['target']['node']]
                assert seen.setdefault(acc,n)==n
                v,_=g.view(acc); v=v.copy(); v[:,0]=newt[n]; g.write(acc,v)
    # weights from original
    po=o.j['meshes'][0]['primitives'][0]['attributes']
    P,_=o.view(po['POSITION']); J,_=o.view(po['JOINTS_0']); W,_=o.view(po['WEIGHTS_0'])
    n=len(P); D=np.zeros((n,21))
    for k in range(4): np.add.at(D,(np.arange(n),J[:,k].astype(int)),W[:,k])
    D/=D.sum(1,keepdims=True)
    sx=np.abs(P[:,0]); a=ss((sx-0.30)/0.20)*ss((P[:,1]-1.02)/0.12)
    legs=[ix[b+s] for b in('thigh_','shin_','foot_') for s in 'LR']
    O=D.copy(); m=a>0; O[np.ix_(m,legs)]=0; O[m]/=O[m].sum(1,keepdims=True)
    N=np.zeros_like(D); side=np.where(P[:,0]>=0,'L','R')
    for s in 'LR':
        q=side==s; t=sx[q]
        sh=1-ss((t-0.25)/0.20); el=ss((t-(EL-0.08))/0.16); wr=ss((t-(WR-0.06))/0.12)
        N[q,ix['shoulder_'+s]]=sh; N[q,ix['upperArm_'+s]]=(1-sh)*(1-el)
        N[q,ix['foreArm_'+s]]=(1-sh)*el*(1-wr); N[q,ix['hand_'+s]]=(1-sh)*el*wr
    F=(1-a)[:,None]*O+a[:,None]*N
    top=np.argsort(-F,1)[:,:4]; tw=np.take_along_axis(F,top,1); tw/=tw.sum(1,keepdims=True)
    g.write(p['JOINTS_0'],top); g.write(p['WEIGHTS_0'],tw); g.save(dst); print(dst,shift)
import os; B='/workspace/hero-motion/beth-reweight/'; os.makedirs(B+'v2',exist_ok=True)
run(B+'stonetroll_lod1.glb','/workspace/hero-motion/godot-fixed/stonetroll_lod1.glb',B+'v2/stonetroll_lod1.glb')
run(B+'stonetroll.glb','/workspace/godot-art/characters/stonetroll.glb',B+'v2/stonetroll.glb')
run(B+'stonetroll_lod2.glb','/workspace/godot-art/characters/stonetroll_lod2.glb',B+'v2/stonetroll_lod2.glb')
