import bpy,sys
a=sys.argv[sys.argv.index('--')+1:]; out=a[0]; files=a[1:]
ch=open('/workspace/titan2/post/chunks.txt').read().strip().split('\n')
bpy.ops.wm.open_mainfile(filepath=files[0])
for i in range(1,len(ch)):
    names=ch[i].split(',')
    for n in names:
        if n in bpy.data.actions: bpy.data.actions.remove(bpy.data.actions[n])
    with bpy.data.libraries.load(files[i]) as (f,t): t.actions=[x for x in f.actions if x in names]
for x in bpy.data.actions: x.use_fake_user=True
print('ACTS',len(bpy.data.actions))
bpy.ops.wm.save_as_mainfile(filepath=out)
