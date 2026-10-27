"""Check or restore only the recorded native-source changes. Rebuild afterwards."""
from pathlib import Path
import argparse,hashlib,json
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--method',choices=['fael','gbp2','all'],default='all')
p.add_argument('--apply',action='store_true',help='Restore recorded .before files; refuses unknown edits or active native libraries')
a=p.parse_args();base=Path('/opt/stgplanner/benchmarks');archive=Path('/mnt/d/STGPlanner/benchmarks/progress_repairs')
manifest=json.loads((archive/'manifest.json').read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
pending=[]
for item in manifest['sources']:
    if a.method!='all' and item['method']!=a.method:continue
    path=base/(item['method']+'_ws/src')/item['relative']
    if not str(path.resolve()).startswith(str(base.resolve())+'/'):raise RuntimeError('Native source escaped workspace')
    before=archive/(item['method']+'__'+item['relative'].replace('/','__')+'.before')
    if sha(before)!=item['original_sha256']:raise RuntimeError('Original archive changed: '+str(before))
    current=sha(path)
    if current not in [item['original_sha256'],item['repaired_sha256']]:raise RuntimeError('Unrecorded source edits: '+str(path))
    pending.append((path,before,current==item['original_sha256']))
if a.apply:
    libraries=[str(Path(x['path']).resolve()) for x in manifest['binaries'].values()]
    for process in Path('/proc').iterdir():
        if not process.name.isdigit():continue
        try:maps=(process/'maps').read_text()
        except (OSError,UnicodeError):continue
        if any(x in maps for x in libraries):raise RuntimeError('A native planner library is active in PID '+process.name+'; stop the simulation first')
    for path,before,already in pending:
        if not already:path.write_bytes(before.read_bytes())
for path,_,already in pending:print(('already-original ' if already else 'restored ' if a.apply else 'would-restore ')+str(path))
print('Dry run only.' if not a.apply else 'Native sources restored. Rebuild each affected workspace before running.')
