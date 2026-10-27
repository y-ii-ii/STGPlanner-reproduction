"""Read-only archive/report checks for the completed Scene4 stage; no ROS calls."""
import argparse
import datetime
import gzip
import hashlib
import json
import re
import subprocess
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--repo', type=Path, default=Path('D:/STGPlanner/catkin_ws/src/STGPlanner'))
parser.add_argument('--output', type=Path, default=Path('D:/STGPlanner/codex/outputs/Scene4阶段完成核验.json'))
args = parser.parse_args()
repo = args.repo
checks = {}

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def check(name, value):
    checks[name] = bool(value)
    assert value, name

manifest = json.loads((repo / 'evidence/scene4-progress-fix/evidence_manifest.json').read_text(encoding='utf-8'))
for name, expected in manifest['files'].items():
    check('manifest:' + name, digest(repo / name) == expected)
old = json.loads((repo / manifest['previous_manifest']).read_text(encoding='utf-8'))
raw_names = [name for name in old['files'] if name.startswith('evidence/')]
for name in raw_names:
    check('preserved_raw:' + name, digest(repo / name) == old['files'][name])
git = ['git', '-c', 'core.quotepath=false', '-C', str(repo)]
changes = subprocess.check_output(git + ['diff', manifest['previous_snapshot_commit'], '--name-only', '--',
                                           'evidence/scene4-baselines', 'evidence/scene4-final', 'evidence/scene4-progress-fix'], text=True).splitlines()
check('only_evidence_manifest_metadata_changed', changes == ['evidence/scene4-progress-fix/evidence_manifest.json'])
for ref, expected in {'main': 'dfc712982891f29c266083d7efad72ad48e730a2',
                     'repro-baseline-2026-10-26^{}': 'dfc712982891f29c266083d7efad72ad48e730a2',
                     'scene4-baselines-2026-10-27^{}': '9dec3c45184259a0d68e3dfe066040966d807aed'}.items():
    resolved = subprocess.run(git + ['rev-parse', '--verify', ref], capture_output=True, text=True)
    if resolved.returncode and ref == 'main':
        resolved = subprocess.run(git + ['rev-parse', '--verify', 'refs/remotes/origin/main'], capture_output=True, text=True)
    check('protected_ref:' + ref, resolved.returncode == 0 and resolved.stdout.strip() == expected)

stage = json.loads((repo / 'project-context/SCENE4_STAGE_COMPLETION.json').read_text(encoding='utf-8'))
check('stage_complete', stage['status'] == 'stage_complete')
check('GBP2_followup_paused', stage['gbp2_followup'] == 'paused_by_user')
check('no_new_simulation', stage['new_simulation_started'] is False)
lock = json.loads((repo / 'project-context/SIMULATION_LOCK.json').read_text(encoding='utf-8'))
check('paused_lock', lock['state'] == 'paused_by_user' and not lock['runtime_active'] and lock['stage_status'] == 'stage_complete')
summary = json.loads((repo / 'docs/Scene4四算法与论文对比汇总.json').read_text(encoding='utf-8'))
check('four_algorithms', [r['algorithm'] for r in summary['records']] == ['STGPlanner', 'TARE', 'FAEL', 'GBP2'])
success = []
for record in summary['records']:
    trial = record['trial']
    folder = 'scene4-progress-fix' if trial.startswith('repair_') else 'scene4-baselines'
    raw = repo / 'evidence' / folder / trial / 'result.json'
    check('summary_source_sha:' + trial, digest(raw) == record['source_sha256'])
    result = json.loads(raw.read_text(encoding='utf-8'))
    for key, value in record['local'].items():
        check('summary_value:' + trial + ':' + key, result[key] == value)
    reached = result['validation']['reached_common_threshold']
    success.append(reached)
    check('protocol3:' + trial, result['protocol_revision'] == 3 and result['area_threshold_m2'] == 7400.5)
    for key in ('stop_ack', 'parked_command_zero', 'parking_drift_under_0_1m', 'sensor_stream_live'):
        check('health:' + trial + ':' + key, result['validation'][key])
check('three_success_GBP2_unmet', success == [True, True, True, False])
gbp = summary['records'][-1]
check('GBP2_censored_paper_value', gbp['paper']['censored_lower_bounds'] and gbp['descriptive_difference_from_paper_mean'] is None)

move_manifest = json.loads((repo / 'project-context/work-archive/move_manifest.json').read_text(encoding='utf-8'))
for item in move_manifest['moves']:
    saved = (repo / 'benchmarks/reporting' / Path(item['new_path']).name if item['category'] == 'reporting'
             else repo / 'project-context/work-archive' / item['category'] / Path(item['new_path']).name)
    check('moved_bytes:' + Path(item['old_path']).name, digest(saved) == item.get('current_sha256', item['sha256']))

md = (repo / 'docs/Scene4四算法与论文对比汇总.md').read_text(encoding='utf-8')
table = md[md.index('| 算法（本地版本）'):md.index('\n## 口径与结论')].strip()
for name in ['Scene4基线算法对比报告', 'Scene4探索停滞修复报告', 'FAEL成功与GBP2未完成阶段总结', 'STGPlanner部署报告']:
    text = (repo / 'docs' / (name + '.md')).read_text(encoding='utf-8')
    check('identical_latest_table:' + name, table in text and '阶段性完成' in text)
    html = (repo / 'docs' / (name + '.html')).read_text(encoding='utf-8')
    check('html_latest_table:' + name, '56.3389%' in html and '1017.008' in html)
    check('html_images_embedded:' + name, not re.search(r'<img\b[^>]*src="(?!data:)', html))
for name in ['STATUS.md', 'RUNBOOK.md']:
    text = (repo / 'project-context' / name).read_text(encoding='utf-8')
    check('handoff_complete_paused:' + name, '阶段性完成' in text and 'GBP2' in text and '暂停' in text)
check('README_latest_table', table in (repo / 'README.md').read_text(encoding='utf-8'))

patterns = [rb'gh[pousr]_[A-Za-z0-9_]{36,}', rb'github_pat_[A-Za-z0-9_]{50,}',
            rb'-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----', rb'AKIA[0-9A-Z]{16}']
for name in manifest['files']:
    data = (repo / name).read_bytes()
    if name.endswith('.gz'):
        data = gzip.decompress(data)
    if b'\0' not in data[:8192]:
        check('credential_pattern_scan:' + name, not any(re.search(pattern, data) for pattern in patterns))

capture = repo / 'evidence/scene4-progress-fix/repair_formal_gbp2_09'
expected = json.loads((capture / 'poststop_map_capture.json').read_text(encoding='utf-8'))['sha256']
check('native_map_decompressed_sha', hashlib.sha256(gzip.decompress((capture / 'poststop_native_map.vxblx.gz').read_bytes())).hexdigest() == expected)
value = {'verified_at': datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),
         'repository_path': str(repo), 'stage_status': 'stage_complete', 'GBP2_followup': 'paused_by_user',
         'new_simulation_started': False, 'manifest_file_count': len(manifest['files']),
         'preserved_raw_evidence_file_count': len(raw_names), 'moved_file_count': len(move_manifest['moves']),
         'all_checks_passed': True, 'check_count': len(checks),
         'verification_scope': '只读报告、数据、归档字节和交接核验；不作为新算法测试/新进程核验', 'checks': checks}
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps({k: v for k, v in value.items() if k != 'checks'}, ensure_ascii=False, indent=2))
