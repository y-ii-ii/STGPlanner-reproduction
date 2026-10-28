"""Verify new GBP2 archives and immutable previous raw evidence after staging/restoring."""
import argparse
import gzip
import hashlib
import json
import re
import subprocess
from pathlib import Path
parser=argparse.ArgumentParser()
parser.add_argument('--repo',type=Path,default=Path('D:/STGPlanner/catkin_ws/src/STGPlanner'))
parser.add_argument('--output',type=Path,default=Path('D:/STGPlanner/codex/outputs/gbp2_optimization_20261028/delivery_validation.json'))
parser.add_argument('--staged',action='store_true')
args=parser.parse_args();repo=args.repo
def sha(raw):return hashlib.sha256(raw).hexdigest()
new=json.loads((repo/'evidence/gbp2-optimization-20261028/manifest.json').read_text(encoding='utf-8'))
for row in new['files']:
    raw=(repo/row['archive']).read_bytes()
    assert sha(raw)==row['archive_sha256'],row['archive']
    assert sha(gzip.decompress(raw) if row['gzip'] else raw)==row['source_sha256'],row['archive']
previous=json.loads((repo/'evidence/scene4-progress-fix/evidence_manifest.json').read_text(encoding='utf-8'))
for name,expected in previous['files'].items():assert sha((repo/name).read_bytes())==expected,name
tare=json.loads((repo/'evidence/tare-optimization-20261028/manifest.json').read_text(encoding='utf-8'))
for row in tare['files']:
    raw=(repo/row['archive']).read_bytes()
    assert sha(raw)==row['archive_sha256'],row['archive']
    assert sha(gzip.decompress(raw) if row['gzip'] else raw)==row['source_sha256'],row['archive']
git=['git','-c','core.quotepath=false','-C',str(repo)]
if args.staged:
    entries=subprocess.check_output(git+['ls-files','--stage','-z','--','evidence/gbp2-optimization-20261028'])
    index={}
    for entry in entries.split(b'\0'):
        if not entry:continue
        header,path=entry.split(b'\t',1);mode,blob,stage=header.split()
        assert stage==b'0'
        index[path.decode('utf-8')]=blob.decode('ascii')
    for row in new['files']:
        raw=(repo/row['archive']).read_bytes()
        expected=hashlib.sha1(b'blob '+str(len(raw)).encode('ascii')+b'\0'+raw).hexdigest()
        assert index.get(row['archive'])==expected,row['archive']
changed=subprocess.check_output(git+['diff','8c55a9aee073a292df78aeb2d8f82d8aa4e13593','--name-only','--',
    'evidence/scene4-baselines','evidence/scene4-final','evidence/scene4-progress-fix','evidence/tare-optimization-20261028'],text=True).splitlines()
assert changed==['evidence/scene4-progress-fix/evidence_manifest.json'],changed
summary=json.loads((repo/'project-context/GBP2_OPTIMIZATION_SUMMARY.json').read_text(encoding='utf-8'))
assert summary['decision']['phase_complete'] and not summary['paper_statistical_replication_claimed']
assert set(r['trial'] for r in summary['records'])==set(summary['decision']['completed_trials'])
experiment_checks=0
for row in summary['records']:
    assert row['validation']['protocol_checks_passed']
    assert row['validation']['summary']['public95_reached']==(row['result']['area_m2']>7400.5)
    experiment_checks+=row['validation']['check_count']
lock=json.loads((repo/'project-context/SIMULATION_LOCK.json').read_text(encoding='utf-8'))
assert not lock['runtime_active']
assert lock['gbp2_followup']=='optimization_phase_complete'
limits=json.loads((repo/'project-context/GBP2_EXPERIMENT_LIMITS.json').read_text(encoding='utf-8'))
assert limits['new_experiments_blocked'] and limits['max_new_formal_trials']==3
assert len(summary['records'])==3 and set(limits['counted_trials'])==set(summary['decision']['completed_trials'])
assert lock['new_experiments_blocked'] and lock['used_new_formal_trials']==3
deployment=json.loads((repo/'project-context/GBP2_DEPLOYMENT_STATE.json').read_text(encoding='utf-8'))
assert deployment['native_matches09'] and deployment['runtime_idle_verified']
patterns=[rb'gh[pousr]_[A-Za-z0-9_]{36,}',rb'github_pat_[A-Za-z0-9_]{50,}',rb'-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----']
for folder in [repo/'benchmarks/gbp2_optimization_20261028',repo/'evidence/gbp2-optimization-20261028']:
    for path in folder.rglob('*'):
        if not path.is_file():continue
        raw=path.read_bytes()
        if path.suffix=='.gz':raw=gzip.decompress(raw)
        if b'\0' not in raw[:8192]:assert not any(re.search(pattern,raw) for pattern in patterns),path
report=(repo/'docs/GBP2优化测试报告.html').read_text(encoding='utf-8')
assert not re.search(r'<img\b[^>]*src="(?!data:)',report)
value={'all_checks_passed':True,'new_archive_files':len(new['files']),
       'previous_manifest_files':len(previous['files']),'prior_tare_archive_files':len(tare['files']),
       'all_archive_and_decompressed_sha_passed':True,'previous_raw_evidence_unchanged':True,
       'experiment_checks':experiment_checks,'completed_trials':summary['decision']['completed_trials'],
       'public95_trials':[r['trial'] for r in summary['records'] if r['result']['area_m2']>7400.5],
       'decision':summary['decision']['conclusion'],'native_deployment':deployment['description']}
value['user_three_trial_limit_enforced']=True
if args.staged:value['staged_archive_blobs_byte_exact']=True
args.output.parent.mkdir(parents=True,exist_ok=True)
args.output.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(value,ensure_ascii=False,indent=2))
