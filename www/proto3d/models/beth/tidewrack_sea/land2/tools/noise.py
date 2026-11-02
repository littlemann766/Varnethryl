import numpy as np
def _h(ix,iy,iz,seed):
    n=(ix*73856093) ^ (iy*19349663) ^ (iz*83492791) ^ (seed*2654435761)
    n=(n ^ (n>>13))*1274126177; n=n ^ (n>>16)
    return (n & 0xffff).astype(np.float64)/65535.0
def vnoise(p,seed=0):
    p=np.asarray(p,np.float64); i=np.floor(p).astype(np.int64); f=p-i; u=f*f*(3-2*f)
    r=0
    for dx in (0,1):
        for dy in (0,1):
            for dz in (0,1):
                w=(u[:,0] if dx else 1-u[:,0])*(u[:,1] if dy else 1-u[:,1])*(u[:,2] if dz else 1-u[:,2])
                r=r+w*_h(i[:,0]+dx,i[:,1]+dy,i[:,2]+dz,seed)
    return r*2-1
def fbm(p,oct=4,seed=0):
    a=0.5; s=0; p=np.asarray(p,np.float64)
    for o in range(oct): s=s+a*vnoise(p,seed+o); p=p*2.03+17.1; a*=0.5
    return s
def ridged(p,oct=4,seed=0):
    a=0.5; s=0; p=np.asarray(p,np.float64)
    for o in range(oct): s=s+a*(1-np.abs(vnoise(p,seed+o)))**2; p=p*2.07+9.3; a*=0.5
    return s
