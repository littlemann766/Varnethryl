# decimate a card2 GLB (flat tri soup, shared atlas) to a target tri count, keeping wedge UVs; rewrite with writer.write_glb
import sys,json,struct,numpy as np,pymeshlab
sys.path.insert(0,'/workspace/beth-world/audit/cardstyle/tools/v2'); from writer import write_glb
def read(p):
    b=open(p,'rb').read(); n=struct.unpack('<I',b[12:16])[0]; j=json.loads(b[20:20+n]); bin_=b[20+n+8:]
    pr=j['meshes'][0]['primitives'][0]
    def acc(i,dt,nc):
        a=j['accessors'][i]; v=j['bufferViews'][a['bufferView']]; return np.frombuffer(bin_,dt,a['count']*nc,v.get('byteOffset',0)+a.get('byteOffset',0)).reshape(a['count'],nc)
    P=acc(pr['attributes']['POSITION'],np.float32,3); UV=acc(pr['attributes']['TEXCOORD_0'],np.float32,2).copy(); I=acc(pr['indices'],np.uint32,1).ravel()
    UV[:,1]=1-UV[:,1]; return P,UV,I.reshape(-1,3),j['nodes'][0]['name']
def decim(src,dst,target):
    P,UV,F,name=read(src)
    q=np.round(P/1e-3).astype(np.int64); _,inv,=np.unique(q,axis=0,return_inverse=True)[0:2] if False else (None,None)
    u,idx,inv=np.unique(q,axis=0,return_index=True,return_inverse=True); inv=inv.ravel()
    V=P[idx].astype(np.float64); FF=inv[F]
    ok=(FF[:,0]!=FF[:,1])&(FF[:,1]!=FF[:,2])&(FF[:,0]!=FF[:,2]); F=F[ok]; FF=FF[ok]
    # drop exact duplicate faces
    _,ui=np.unique(np.sort(FF,1),axis=0,return_index=True); ui=np.sort(ui); F=F[ui]; FF=FF[ui]
    wuv=np.stack([UV[F[:,k]] for k in range(3)],1).reshape(-1,2).astype(np.float64)
    import tempfile,os
    td=tempfile.mkdtemp(); from PIL import Image; Image.new('RGB',(4,4)).save(td+'/t.png')
    open(td+'/m.mtl','w').write('newmtl a\nmap_Kd t.png\n')
    with open(td+'/m.obj','w') as o:
        o.write('mtllib m.mtl\nusemtl a\n'); o.write(''.join(f'v {x:.5f} {y:.5f} {z:.5f}\n' for x,y,z in V)); o.write(''.join(f'vt {u:.6f} {v:.6f}\n' for u,v in wuv))
        o.write(''.join(f'f {FF[i,0]+1}/{3*i+1} {FF[i,1]+1}/{3*i+2} {FF[i,2]+1}/{3*i+3}\n' for i in range(len(FF))))
    ms=pymeshlab.MeshSet(); ms.load_new_mesh(td+'/m.obj')
    ms.meshing_decimation_quadric_edge_collapse_with_texture(targetfacenum=int(target),qualitythr=0.3,preserveboundary=True,boundaryweight=2.0,optimalplacement=False,preservenormal=True,planarquadric=True)
    m=ms.current_mesh(); V2=m.vertex_matrix(); F2=m.face_matrix(); W=m.wedge_tex_coord_matrix().reshape(-1,3,2)
    Pn=V2[F2].reshape(-1,3); UVn=W.reshape(-1,2)
    n=np.cross(Pn[1::3]-Pn[0::3],Pn[2::3]-Pn[0::3]); n/=np.linalg.norm(n,axis=1,keepdims=True)+1e-12
    write_glb(dst,Pn,np.arange(len(Pn)).reshape(-1,3),UVn,np.repeat(n,3,0),name,'atlas'); return len(F),len(F2)
if __name__=='__main__': print(decim(sys.argv[1],sys.argv[2],float(sys.argv[3])))
