"""Check byte integrity, protected refs and secret patterns; never print secret values."""
import gzip
import hashlib
import json
import re
import subprocess
from pathlib import Path
repo=Path('D:/STGPlanner/catkin_ws/src/STGPlanner');out=Path('D:/STGPlanner/codex/outputs')
git=['git','-c','safe.directory='+str(repo),'-c','core.longpaths=true','-C',str(repo)]
manifest=json.loads((repo/'evidence/scene4-progress-fix/evidence_manifest.json').read_text(encoding='utf-8'))
bad=[]
for name,expected in manifest['files'].items():
    if hashlib.sha256((repo/name).read_bytes()).hexdigest()!=expected:bad.append(name)
assert not bad,bad
raw_changes=[name for name in subprocess.check_output(git+['diff','HEAD','--diff-filter=MDRT','--name-only','--','evidence/scene4-progress-fix']).decode().splitlines() if name!='evidence/scene4-progress-fix/progress_trials.json']
assert not raw_changes,raw_changes
assert not subprocess.check_output(git+['diff','HEAD','--name-only','--','evidence/scene4-baselines']).strip()
expected_refs={'main':'dfc712982891f29c266083d7efad72ad48e730a2','repro-baseline-2026-10-26^{}':'dfc712982891f29c266083d7efad72ad48e730a2','benchmark/scene4-baselines':'9dec3c45184259a0d68e3dfe066040966d807aed','scene4-baselines-2026-10-27^{}':'9dec3c45184259a0d68e3dfe066040966d807aed'}
for name,expected in expected_refs.items():assert subprocess.check_output(git+['rev-parse',name],text=True).strip()==expected
patterns={'github_token':rb'gh[pousr]_[A-Za-z0-9_]{36,}','github_pat':rb'github_pat_[A-Za-z0-9_]{50,}',
 'private_key':rb'-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----','aws_access_id':rb'AKIA[0-9A-Z]{16}'}
files=set(manifest['files'])|{'README.md','AGENTS.md','project-context/STATUS.md','project-context/RUNBOOK.md','project-context/SIMULATION_LOCK.json'}
matches=[]
for name in files:
    data=(repo/name).read_bytes()
    if name.endswith('.gz'):
        try:data=gzip.decompress(data)
        except OSError:continue
    if b'\0' in data[:8192]:continue
    for label,pattern in patterns.items():
        if re.search(pattern,data):matches.append({'path':name,'pattern':label})
assert not matches,matches
validation=json.loads((repo/'evidence/scene4-progress-fix/validation.json').read_text())
assert validation['protocol_checks_passed'] and not validation['exploration_goals_passed']
value={'file_count':len(manifest['files']),'all_manifest_hashes_passed':True,'existing_raw_evidence_unchanged':True,
 'original_baseline_unchanged':True,'protected_local_refs_unchanged':True,'credential_pattern_scan_passed':True,
 'fael_success':validation['results']['fael']['after']['finish_reason']=='coverage_threshold',
 'gbp2_unmet_95':validation['results']['gbp2']['after']['finish_reason']=='sim_time_limit'}
(out/'本地备份完整性核验.json').write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(value,indent=2))
