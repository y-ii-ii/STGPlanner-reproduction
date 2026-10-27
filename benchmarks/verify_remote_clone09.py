"""Restore the private branch into a fresh checkout and verify recorded evidence."""
import argparse
import datetime
import gzip
import hashlib
import json
import os
import subprocess
from pathlib import Path
parser=argparse.ArgumentParser();parser.add_argument('--refresh',type=Path);args=parser.parse_args()
root=Path('D:/STGPlanner');repo=root/'catkin_ws/src/STGPlanner';out=root/'codex/outputs'
env=os.environ.copy();env.update(GIT_TERMINAL_PROMPT='0',GCM_INTERACTIVE='never')
stamp=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime('%Y%m%d-%H%M%S')
destination=args.refresh or root/'codex/work'/('private-backup-restore-'+stamp)
git=['git','-c','core.longpaths=true','-c','http.proxy=','-c','https.proxy=']
with (root/'codex/work'/('backup-clone-'+stamp+'.log')).open('w',encoding='utf-8') as log:
    if args.refresh:
        assert not subprocess.check_output(git+['-C',str(destination),'status','--porcelain'],env=env).strip()
        subprocess.run(git+['-C',str(destination),'pull','--ff-only'],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    else:
        assert not destination.exists()
        subprocess.run(git+['clone','--branch','fix/fael-gbp2-progress','--single-branch','https://github.com/y-ii-ii/STGPlanner-reproduction.git',str(destination)],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
head=subprocess.check_output(['git','-c','safe.directory='+str(repo),'-C',str(repo),'rev-parse','HEAD'],text=True).strip()
assert subprocess.check_output(git+['-C',str(destination),'rev-parse','HEAD'],text=True).strip()==head
assert not subprocess.check_output(git+['-C',str(destination),'status','--porcelain']).strip()
manifest=json.loads((destination/'evidence/scene4-progress-fix/evidence_manifest.json').read_text())
bad=[name for name,sha in manifest['files'].items() if hashlib.sha256((destination/name).read_bytes()).hexdigest()!=sha]
assert not bad,bad
snapshot=destination/'evidence/scene4-progress-fix/repair_formal_gbp2_09'
capture=json.loads((snapshot/'poststop_map_capture.json').read_text())
assert hashlib.sha256(gzip.decompress((snapshot/'poststop_native_map.vxblx.gz').read_bytes())).hexdigest()==capture['sha256']
for name,sha in {'repro-baseline-2026-10-26^{}':'dfc712982891f29c266083d7efad72ad48e730a2','scene4-baselines-2026-10-27^{}':'9dec3c45184259a0d68e3dfe066040966d807aed'}.items():
    assert subprocess.check_output(git+['-C',str(destination),'rev-parse',name],text=True).strip()==sha
validation=json.loads((destination/'evidence/scene4-progress-fix/validation.json').read_text())
assert validation['protocol_checks_passed'] and not validation['exploration_goals_passed']
value={'verified_at':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),'commit':head,
    'fresh_remote_checkout':str(destination),'all_recorded_hashes_passed':True,'file_count':len(manifest['files']),
    'native_map_decompression_hash_passed':True,'historical_tags_preserved':True,'clean_checkout':True,
    'fael_success_and_gbp2_unmet95_preserved':True}
(out/'私有仓库克隆恢复核验.json').write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(value,ensure_ascii=False,indent=2))
