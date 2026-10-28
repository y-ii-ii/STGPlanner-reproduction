"""Verify Git-staged/restored TARE evidence and protected historical artifacts."""
import argparse
import gzip
import hashlib
import json
import re
import subprocess
from pathlib import Path

parser=argparse.ArgumentParser()
parser.add_argument('--repo',type=Path,default=Path('D:/STGPlanner/catkin_ws/src/STGPlanner'))
parser.add_argument('--output',type=Path,default=Path('D:/STGPlanner/codex/outputs/tare_optimization_20261028/delivery_validation.json'))
args=parser.parse_args();repo=args.repo
new=json.loads((repo/'evidence/tare-optimization-20261028/manifest.json').read_text(encoding='utf-8'))
for row in new['files']:
    raw=(repo/row['archive']).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==row['archive_sha256'],row['archive']
    assert hashlib.sha256(gzip.decompress(raw) if row['gzip'] else raw).hexdigest()==row['source_sha256'],row['archive']
old=json.loads((repo/'evidence/scene4-progress-fix/evidence_manifest.json').read_text(encoding='utf-8'))
for name,sha in old['files'].items():assert hashlib.sha256((repo/name).read_bytes()).hexdigest()==sha,name
git=['git','-c','core.quotepath=false','-C',str(repo)]
changed=subprocess.check_output(git+['diff','7a1b99e5042906097b7e60beaa98e2db6390e6f7','--name-only','--','evidence/scene4-baselines','evidence/scene4-final','evidence/scene4-progress-fix'],text=True).splitlines()
assert changed==['evidence/scene4-progress-fix/evidence_manifest.json'],changed
assert 'GBP2' in (repo/'project-context/STATUS.md').read_text(encoding='utf-8')
summary=json.loads((repo/'project-context/TARE_OPTIMIZATION_SUMMARY.json').read_text(encoding='utf-8'))
validation=json.loads((repo/'project-context/TARE_OPTIMIZATION_VERIFIED.json').read_text(encoding='utf-8'))
assert validation['all_checks_passed']
assert len(summary['records'])==4
lock=json.loads((repo/'project-context/SIMULATION_LOCK.json').read_text(encoding='utf-8'))
assert not lock['runtime_active'] and lock['gbp2_followup']=='paused_by_user' and lock['tare_followup']=='complete'
assert summary['paper_statistical_replication_claimed'] is False
assert hashlib.sha256((repo/'evidence/scene4-baselines/formal_tare_01/result.json').read_bytes()).hexdigest()==new['old_baseline_result_sha256']
patterns=[rb'gh[pousr]_[A-Za-z0-9_]{36,}',rb'github_pat_[A-Za-z0-9_]{50,}',rb'-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----']
for folder in [repo/'benchmarks/tare_optimization',repo/'project-context',repo/'evidence/tare-optimization-20261028']:
    for path in folder.rglob('*'):
        if path.is_file():
            raw=path.read_bytes()
            if path.suffix=='.gz':raw=gzip.decompress(raw)
            if b'\0' not in raw[:8192]:assert not any(re.search(pattern,raw) for pattern in patterns),path
report=(repo/'docs/TARE优化测试报告.html').read_text(encoding='utf-8')
assert not re.search(r'<img\b[^>]*src="(?!data:)',report)
value={'all_checks_passed':True,'new_archive_files':len(new['files']),'previous_manifest_files':len(old['files']),
       'all_new_archive_and_decompressed_sha_passed':True,'historical_raw_evidence_unchanged':True,
       'native_experiment_checks':validation['check_count'],'TARE_followup_complete':True,'GBP2_followup':'paused_by_user',
       'decision':summary['decision'],'deployment':summary['deployment']}
args.output.parent.mkdir(parents=True,exist_ok=True)
args.output.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(value,ensure_ascii=False,indent=2))
