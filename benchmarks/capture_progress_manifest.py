from pathlib import Path
import datetime,hashlib,json
root=Path('/mnt/d/STGPlanner/benchmarks');archive=root/'progress_repairs'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
sources=[]
for before in sorted(archive.glob('*.before')):
    method,relative=before.name[:-7].split('__',1)
    relative=relative.replace('__','/')
    native=Path('/opt/stgplanner/benchmarks')/(method+'_ws/src')/relative
    after=before.with_suffix('.after');after.write_bytes(native.read_bytes())
    sources.append({'method':method,'relative':relative,'original_sha256':sha(before),'repaired_sha256':sha(after),'patch_sha256':sha(before.with_suffix('.patch'))})
binaries={}
for name,p in {
 'fael':Path('/opt/stgplanner/benchmarks/fael_ws/devel/lib/libtopo_planner.so'),
 'gbp2_planner_common':Path('/opt/stgplanner/benchmarks/gbp2_ws/devel/lib/libplanner_common.so'),
 'gbp2':Path('/opt/stgplanner/benchmarks/gbp2_ws/devel/lib/libgbplanner.so'),
}.items():
    if p.exists():binaries[name]={'path':str(p),'sha256':sha(p)}
record={'captured_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'protocol_revision':3,'common_protocol_modified':False,'sources':sources,'binaries':binaries}
(archive/'manifest.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))
