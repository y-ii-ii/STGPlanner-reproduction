"""Check or restore the recorded adapter/config changes; default is dry-run."""
from pathlib import Path
import argparse,hashlib,json
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--apply',action='store_true');a=p.parse_args()
root=Path('/mnt/d/STGPlanner/benchmarks');archive=root/'trial_repairs';manifest=json.loads((archive/'manifest.json').read_text());pending=[]
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
for relative,item in manifest['files'].items():
    path=root/relative[len('benchmarks/'):]
    if not str(path.resolve()).startswith(str(root.resolve())+'/'):raise RuntimeError('Path escaped benchmark directory')
    before=archive/(item['archive_stem']+'.before');actual=sha(path)
    if sha(before)!=item['original_sha256'] or actual not in [item['original_sha256'],item['repaired_sha256']]:raise RuntimeError('Unrecorded edits: '+str(path))
    pending.append((path,before,actual==item['original_sha256']))
if a.apply:
    for process in Path('/proc').iterdir():
        if not process.name.isdigit():continue
        try:args=(process/'cmdline').read_bytes().split(b'\0')
        except OSError:continue
        if any(x.endswith(b'/benchmark_trial.py') for x in args):raise RuntimeError('Stop the active benchmark before restoring its adapter/config')
    for path,before,already in pending:
        if not already:path.write_bytes(before.read_bytes())
for path,_,already in pending:print(('already original: ' if already else 'restored: ' if a.apply else 'would restore: ')+str(path))
