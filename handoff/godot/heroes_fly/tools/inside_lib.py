from mathutils import Vector
DIRS=[Vector((0.31,0.9,0.3)).normalized(),Vector((-0.4,-0.85,0.35)).normalized(),Vector((0.2,-0.3,-0.93)).normalized()]
def is_inside(bvh,p):
    loc,nor,fi,dist=bvh.find_nearest(p)
    if loc is None or dist>0.03 or (p-loc).dot(nor)>-0.002: return False
    odd=0
    for d in DIRS:
        q=p.copy(); h=0
        for _ in range(40):
            l,n,f,dd=bvh.ray_cast(q,d)
            if l is None: break
            h+=1; q=l+d*1e-4
        odd+=h%2
    return odd>=2
def is_bad(bvh,p,margin=0.004):
    loc,nor,fi,dist=bvh.find_nearest(p)
    if loc is not None and dist<margin: return True
    return is_inside(bvh,p)
