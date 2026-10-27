import hashlib
import json
import subprocess
from pathlib import Path
repo=Path('D:/STGPlanner/catkin_ws/src/STGPlanner')
git=['git','-c','safe.directory='+str(repo),'-c','core.longpaths=true','-C',str(repo)]
manifest=json.loads((repo/'evidence/scene4-progress-fix/evidence_manifest.json').read_text())
index={}
for entry in subprocess.check_output(git+['ls-files','--stage','-z']).split(b'\0'):
    if not entry:continue
    metadata,name=entry.split(b'\t',1)
    mode,sha,stage=metadata.split()
    assert stage==b'0'
    index[name.decode('utf-8')]=sha.decode()
bad=[]
for name in manifest['files']:
    data=(repo/name).read_bytes();sha=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
    if index.get(name)!=sha:bad.append(name)
assert not bad,bad
large=[{'path':name,'bytes':(repo/name).stat().st_size} for name in manifest['files'] if (repo/name).stat().st_size>=100*1024*1024]
assert not large,large
print(json.dumps({'indexed_evidence_files_checked':len(manifest['files']),'index_bytes_match_checkout_and_manifest':True,'no_100MiB_files':True}))
