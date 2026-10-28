"""Check all four TARE observations and the independent native-model experiment."""
import hashlib
import json
from pathlib import Path
root = Path('D:/STGPlanner')
out = root / 'codex/outputs/tare_optimization_20261028'
trials = ['formal_tare_01', 'tare_audit_control_20261028_01', 'tare_sensor_model_20261028_01', 'tare_sensor_model_20261028_02']
checks = {}

def check(name, value):
    checks[name] = bool(value)
    assert value, name

original_table = json.loads((root / 'codex/outputs/Scene4四算法与论文对比汇总.json').read_text(encoding='utf-8'))
original_record = next(r for r in original_table['records'] if r['algorithm'] == 'TARE')
check('old_TARE_result_exactly_preserved', hashlib.sha256((root / 'benchmarks/results/formal_tare_01/result.json').read_bytes()).hexdigest() == original_record['source_sha256'])
results = {}
for name in trials:
    folder = root / 'benchmarks/results' / name
    result = json.loads((folder / 'result.json').read_text(encoding='utf-8'))
    results[name] = result
    check(name + ':protocol3', result['protocol_revision'] == 3)
    check(name + ':common_area', result['area_threshold_m2'] == 7400.5 and result['area_denominator_m2'] == 7790)
    check(name + ':no_fatal', not result.get('fatal_error'))
    for key, value in result['validation'].items():
        check(name + ':validation:' + key, value == (result['finish_reason']=='coverage_threshold') if key=='reached_common_threshold' else value)
    if name != 'formal_tare_01':
        freeze = json.loads((folder / 'freeze_validation.json').read_text(encoding='utf-8'))
        check(name + ':frozen_sources_unchanged', freeze['all_frozen_files_unchanged'])
        cleanup = json.loads((folder / 'runtime_cleanup.json').read_text(encoding='utf-8'))
        check(name + ':ports_free', all(cleanup['ports_free'].values()))
        check(name + ':no_owned_processes_left', not cleanup['remaining_owned_pids'])
        fp = json.loads((folder / 'runtime_fingerprint.json').read_text(encoding='utf-8'))
        check(name + ':momentum_off', fp['tare_parameters']['kUseMomentum'] is False)
        check(name + ':sensor_range_12', fp['tare_parameters']['kSensorRange'] == 12.)
        check(name + ':max_speed_2', fp['control_speed_parameters']['/localPlanner/maxSpeed'] == 2. and fp['control_speed_parameters']['/pathFollower/maxSpeed'] == 2.)
        events = [json.loads(line) for line in (folder / 'events.jsonl').read_text(encoding='utf-8').splitlines()]
        check(name + ':unique_start_finish', sum(r['kind']=='exploration_start' for r in events)==1 and sum(r['kind']=='finish' for r in events)==1)

folder = root / 'benchmarks/results'
control = json.loads((folder / trials[1] / 'preflight/manifest.json').read_text(encoding='utf-8'))['hashes']
candidate = json.loads((folder / trials[2] / 'preflight/manifest.json').read_text(encoding='utf-8'))['hashes']
confirmation = json.loads((folder / trials[3] / 'preflight/manifest.json').read_text(encoding='utf-8'))['hashes']
changed = [name for name in control if control[name] != candidate[name]]
check('only_two_native_files_and_native_binary_changed', len(changed)==3 and all(name.endswith(('lidar_model.h','viewpoint_manager.cpp','tare_planner_node')) for name in changed))
check('candidate_repeat_exact_same_frozen_sources_and_binary', candidate == confirmation)
control_fp = json.loads((folder / trials[1] / 'runtime_fingerprint.json').read_text(encoding='utf-8'))
for name in trials[2:]:
    fp = json.loads((folder / name / 'runtime_fingerprint.json').read_text(encoding='utf-8'))
    old_controls = {p['executable']:p['sha256'] for p in control_fp['processes'] if not p['executable'].endswith('tare_planner_node')}
    new_controls = {p['executable']:p['sha256'] for p in fp['processes'] if not p['executable'].endswith('tare_planner_node')}
    check(name + ':same_three_common_control_binaries', len(old_controls)==3 and old_controls==new_controls)
    check(name + ':same_all_ROS_TARE_parameters', fp['tare_parameters']==control_fp['tare_parameters'])
regression = out / 'sensor_model_regression'
check('old_model_14_of_16', 'visible_physical_rays 14' in (regression / 'baseline_v2.log').read_text(encoding='utf-8'))
check('aligned_model_16_of_16', 'visible_physical_rays 16' in (regression / 'candidate.log').read_text(encoding='utf-8'))
check('aligned_fixture_exit0', (regression / 'candidate.exitcode').read_text().strip() == '0')
value = {'all_checks_passed': all(checks.values()), 'check_count': len(checks), 'trials': trials,
         'changed_native_files': changed, 'checks': checks,
         'scope': 'Protocol, original preservation, actual runtime and experiment isolation; not statistical proof of performance gain.'}
(out / 'validation.json').write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')
print(json.dumps({key:value[key] for key in ['all_checks_passed','check_count','trials','changed_native_files']}, indent=2))
