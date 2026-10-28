"""Validate a completed fresh native-parameter trial without replacing old baselines."""
import argparse
import csv
import hashlib
import json
import math
import re
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('trial')
parser.add_argument('--threshold', type=float, required=True)
parser.add_argument('--robot-height', type=float, default=.456)
args = parser.parse_args()
catalog=json.loads(Path(__file__).with_name('trial_catalog.json').read_text(encoding='utf-8'))
registered=next(row for row in catalog if row['trial']==args.trial)
assert registered['threshold']==args.threshold and registered['height']==args.robot_height
root = Path('D:/STGPlanner')
out = root/'codex/outputs/gbp2_optimization_20261028'
folder = root/'benchmarks/results'/args.trial
def read(name):
    return json.loads((folder/name).read_text(encoding='utf-8'))
def rows(name):
    return [json.loads(line) for line in (folder/name).read_text(encoding='utf-8').splitlines() if line.strip()]
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

result = read('result.json')
metrics = rows('metrics.jsonl')
audit = read('live_runtime_audit.json')
params = audit['native_parameters']
freeze = read('freeze_validation.json')
cleanup = read('runtime_cleanup.json')
capture = read('poststop_map_capture.json')
manifest = read('preflight/manifest.json')
original = json.loads((out/'preflight_audit/audit.json').read_text(encoding='utf-8'))
baseline_config = (out/'preflight_audit/config/gbp2.yaml').read_text(encoding='utf-8')
actual_config = (folder/'preflight/config/gbp2.yaml').read_text(encoding='utf-8')
def normalise(value):
    value=re.sub(r'(?m)^(\s*frontier_percentage_threshold:)\s*[0-9.]+',r'\1 VALUE',value)
    if args.robot_height != .456:
        value=re.sub(r'(?m)^(\s*robot_height:)\s*[0-9.]+',r'\1 VALUE',value)
    return value
actions = rows('passive_actions.jsonl')
commands = [r for r in actions if r['kind'] == 'command']
with (folder/'known_plane_cells.csv').open(encoding='utf-8') as handle:
    cells = list(csv.DictReader(handle))
checks = {
    'protocol_revision_3': result['protocol_revision'] == 3,
    'not_a_pilot': not result['pilot'],
    'no_fatal_error': 'fatal_error' not in result,
    'no_ros_errors': not result['errors'],
    'public_threshold_unchanged': result['area_threshold_m2'] == 7400.5,
    'denominator_unchanged': result['area_denominator_m2'] == 7790,
    'fixed_limit': result['sim_time_limit_s'] == 2400,
    'complete_observation': result['finish_reason'] == 'coverage_threshold' or
        result['finish_reason'] == 'sim_time_limit' and 2400 <= result['sim_time_s'] < 2401,
    'public_success_matches_metric': (result['finish_reason'] == 'coverage_threshold') == (result['area_m2'] > 7400.5),
    'nominal_coverage_ratio': abs(result['coverage_fraction'] - result['area_m2']/7790) < 1e-9,
    'saved_plane_area_matches': abs(len(cells)*.16-result['area_m2']) < .001,
    'native_alive': bool(result['native_health']) and all(r['alive'] for r in result['native_health']),
    'sensor_messages': result['cloud_messages'] > 1000,
    'runtime_cost_recorded': result['runtime_native_s_summary']['count'] > 0,
    'frozen_files_unchanged': freeze['all_frozen_files_unchanged'],
    'source_matches09': all(manifest['hashes'].get(item['path']) == item['sha256'] for item in original['native_files']),
    'only_declared_native_parameters_changed': normalise(actual_config) == normalise(baseline_config),
    'recorded_configuration_matches_prelaunch_copy': actual_config == (out/('preflight_'+args.trial)/'config/gbp2.yaml').read_text(encoding='utf-8'),
    'live_threshold_matches': params['SensorParams']['VLP16']['frontier_percentage_threshold'] == args.threshold,
    'live_sampling_fixed': params['PlanningParams']['num_vertices_max'] == 2000,
    'live_robot_height_matches': params['PlanningParams']['robot_height'] == args.robot_height,
    'native_3d_ray_gain': params['PlanningParams']['use_ray_model_for_volumetric_gain'] and
        params['PlanningParams']['nonuniform_ray_cast'],
    'sensor_range_fixed': params['SensorParams']['VLP16']['max_range'] == 12,
    'same_global_bounds': params['BoundedSpaceParams']['Global']['min_val'] == [-50.,-20.,-2.] and
        params['BoundedSpaceParams']['Global']['max_val'] == [80.,100.,3.],
    'automatic_global_planner': params['PlanningParams']['auto_global_planner_enable'],
    'speed_parameters_fixed': audit['parameters']['/localPlanner/maxSpeed'] == 2 and
        audit['parameters']['/pathFollower/maxSpeed'] == 2,
    'command_sampling_present': len(commands) > 1000,
    'command_limit_fixed': bool(commands) and 0 < max(abs(r['linear']) for r in commands) <= 2+1e-9,
    'native_map_saved': capture.get('exists',False) and (folder/'poststop_native_map.vxblx').is_file(),
    'map_capture_after_finish': capture['after_finish_only'],
    'no_owned_process_left': not cleanup['remaining_owned_pids'],
    'ports_released': all(cleanup['ports_free'].values()),
}
checks['native_map_sha_verified'] = capture.get('sha256') == sha(folder/'poststop_native_map.vxblx')
expected_libs = {r['sha256'] for r in original['native_files'] if r['path'].endswith('.so')}
loaded_libs = {r['sha256'] for proc in audit['processes'] for r in proc['loaded_libraries']}
checks['actual_loaded_native_libraries'] = expected_libs == loaded_libs
reference_runtime=json.loads((root/'benchmarks/results/repair_formal_gbp2_09/live_runtime_audit.json').read_text(encoding='utf-8'))
expected_processes={Path(p['exe']).name:p.get('exe_sha256',p.get('sha256')) for p in reference_runtime['processes']}
actual_processes={Path(p['exe']).name:p['sha256'] for p in audit['processes']}
checks['actual_common_and_gbp_executables_match09']=expected_processes==actual_processes
for key, value in result['validation'].items():
    if key != 'reached_common_threshold':
        checks['runtime.'+key] = bool(value)
checks['reported_success_matches_metric'] = result['validation']['reached_common_threshold'] == (result['area_m2'] > 7400.5)
checks['static_terrain_protocol'] = result['controller_static_terrain']
for key in ['sim_s','area_m2','distance_m']:
    checks['monotonic_'+key] = all(b[key] >= a[key] for a,b in zip(metrics,metrics[1:]))

native_end = result.get('native_finish_sim_s')
hold_summary={}
if native_end is not None:
    parked = [r for r in metrics if r['sim_s'] > native_end+2]
    checks['no_planning_restart_after_native_end'] = bool(parked) and all(
        (r['nonempty_plans'],r['empty_plans']) == (parked[0]['nonempty_plans'],parked[0]['empty_plans']) for r in parked)
    if parked:
        first=parked[0];last=metrics[-1]
        start_event=next(r for r in rows('events.jsonl') if r['kind']=='exploration_start')
        held_commands=[r for r in commands if r['sim']>=start_event['sim']+native_end+2]
        hold_summary={'native_end_hold_travel_m':last['distance_m']-first['distance_m'],
          'native_end_hold_displacement_m':math.hypot(last['x']-first['x'],last['y']-first['y']),
          'native_end_hold_area_gain_m2':last['area_m2']-first['area_m2'],
          'native_end_hold_max_abs_command_linear_x':max((abs(r['linear']) for r in held_commands),default=None),
          'native_end_hold_max_abs_command_angular_z':max((abs(r['angular']) for r in held_commands),default=None),
          'distance_at_first_sample_after_native_end_m':first['distance_m'],
          'area_at_first_sample_after_native_end_m2':first['area_m2']}
log = (folder/'native_planner.log').read_text(encoding='utf-8',errors='replace')
selected = []
incomplete = 0
for line in log.splitlines():
    if 'GBP_DIAGNOSTIC_SELECTED' in line:
        item = {k:float(v) for k,v in re.findall(r'(\w+)=(-?\d+(?:\.\d+)?)',line)}
        if all(k in item for k in ['path_frontiers','any_frontier','gain']):
            selected.append(item)
        else:
            incomplete += 1
checks['selected_paths_have_valid_frontier'] = bool(selected) and all(r['path_frontiers'] >= 1 for r in selected)
summary = {k:result.get(k) for k in ['trial','sim_time_s','wall_time_s','distance_m','area_m2','coverage_fraction',
    'finish_reason','native_finished','native_finish_sim_s','runtime_native_s_summary','average_speed_m_s','nonempty_plans','empty_plans']}
summary.update(native_frontier_threshold=args.threshold,native_robot_height=args.robot_height,public95_reached=result['area_m2']>7400.5,
    observed_hold_after_native_end_s=result['sim_time_s']-native_end if native_end is not None else None,
    native_global_transitions=log.count('[GBPLANNER] Very low local gain. Triggering global planner'),
    native_global_targets=log.count('Found the best frontier to go is:'),
    local_selected_paths=len(selected),incomplete_or_interleaved_selection_lines=incomplete,
    coverage_at_1600=next((r['coverage_fraction'] for r in metrics if r['sim_s']>=1600),result['coverage_fraction']),
    final100s_area_gain_m2=result['area_m2']-next(r['area_m2'] for r in metrics if r['sim_s']>=result['sim_time_s']-100),
    coverage_milestones={str(p):next((r['sim_s'] for r in metrics if r['coverage_fraction']>=p/100),None) for p in [40,50,60,75,90,95]},
    command_samples=len(commands),max_abs_command_linear_x=max(abs(r['linear']) for r in commands))
summary.update(hold_summary)
value = {'summary':summary,'checks':checks,'protocol_checks_passed':all(checks.values()),
    'check_count':len(checks),'failed_checks':[name for name,passed in checks.items() if not passed],
    'scope':'A single parameter trial. Protocol and sensor/parking health are distinct from public95 success; a native early end is separately reported.'}
target = out/(args.trial+'_validation.json')
target.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(value,ensure_ascii=False,indent=2))
if not value['protocol_checks_passed']:
    raise SystemExit(1)
