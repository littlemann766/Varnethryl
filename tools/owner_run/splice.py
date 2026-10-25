import json,struct,re,sys
src,dst=sys.argv[1],sys.argv[2]
jobs=[('newrun.json','Running'),('newwalk.json','Walking')]
b=open(src,'rb').read()
jl=struct.unpack('<I',b[12:16])[0];j=json.loads(b[20:20+jl]);o=20+jl
bl=struct.unpack('<I',b[o:o+4])[0];bin_=bytearray(b[o+8:o+8+bl])
san=lambda s:re.sub(r'[\[\]\.:/\s]','',s)
idx={san(n.get('name','')):i for i,n in enumerate(j['nodes'])}
for JS,NAME in jobs:
  raw=json.load(open(JS))
  san=lambda s:re.sub(r'[\[\]\.:/\s]','',s)
  idx={san(n.get('name','')):i for i,n in enumerate(j['nodes'])}
  def add(arr,typ,comp=None):
    global bin_
    while len(bin_)%4: bin_.append(0)
    off=len(bin_);bin_+=struct.pack('<%df'%len(arr),*arr)
    j['bufferViews'].append({'buffer':0,'byteOffset':off,'byteLength':len(arr)*4})
    n={'SCALAR':1,'VEC3':3,'VEC4':4}[typ];acc={'bufferView':len(j['bufferViews'])-1,'componentType':5126,'count':len(arr)//n,'type':typ}
    if typ=='SCALAR':acc['min']=[min(arr)];acc['max']=[max(arr)]
    j['accessors'].append(acc);return len(j['accessors'])-1
  ti=add(raw['times'],'SCALAR')
  samplers=[];channels=[]
  def ch(node,path,acc):
    samplers.append({'input':ti,'output':acc,'interpolation':'LINEAR'});channels.append({'sampler':len(samplers)-1,'target':{'node':node,'path':path}})
  ch(idx['mixamorigHips'],'translation',add(raw['hipsPos'],'VEC3'))
  for n,v in raw['tracks'].items(): ch(idx[n],'rotation',add(v,'VEC4'))
  an=[a for a in j['animations'] if a['name']==NAME][0]
  an['samplers']=samplers;an['channels']=channels
  an.setdefault('extras',{})['varnethryl']='owner-run-rework 2026-10-25: procedural '+NAME+', native ground speed %.2f m/s, cycle %.2f s'%(raw['P']['v'],raw['P']['T'])
while len(bin_)%4: bin_.append(0)
j['buffers'][0]['byteLength']=len(bin_)
js=json.dumps(j,separators=(',',':')).encode()
while len(js)%4: js+=b' '
out=struct.pack('<III',0x46546C67,2,12+8+len(js)+8+len(bin_))+struct.pack('<II',len(js),0x4E4F534A)+js+struct.pack('<II',len(bin_),0x004E4942)+bytes(bin_)
open(dst,'wb').write(out);print('ok',len(out),len(channels))
