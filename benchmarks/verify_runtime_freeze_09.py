"""Compare settled runtime evidence with the frozen candidate and prior baseline."""
import hashlib
import json
from pathlib import Path
root=Path('D:/STGPlanner');folder=root/'benchmarks/results/repair_formal_gbp2_09'
frozen=json.loads((folder/'native_source_manifest.json').read_text())
prior=json.loads((root/'benchmarks/results/repair_formal_gbp2_07/native_source_manifest.json').read_text())
live=json.loads((folder/'live_runtime_audit.json').read_text())
preflight=json.loads((folder/'preflight_audit.json').read_text())
adapter=json.loads((folder/'adapter_config_manifest.json').read_text())
old={(row['method'],row['relative']):row['repaired_sha256'] for row in prior['sources']}
changed=[(row['method'],row['relative']) for row in frozen['sources'] if row['repaired_sha256']!=old[(row['method'],row['relative'])]]
loaded={library['sha256'] for process in live['processes'] for library in process['loaded_native_libraries']}
expected={row['sha256'] for name,row in frozen['binaries'].items() if name.startswith('gbp2')}
control_hashes={row['sha256'] for row in preflight['common_controller_files']}
controls=[p for p in live['processes'] if Path(p['exe']).name in ('localPlanner','pathFollower','path_execution_node')]
native=live['native_parameters'].get('gbplanner_node',live['native_parameters'])
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
checks={
 'only_rrg_native_source_changed_since07':changed==[('gbp2','gbplanner/src/rrg.cpp')],
 'loaded_gbp2_libraries_match_frozen09':loaded==expected,
 'three_running_common_controller_binaries_match':len(controls)==3 and all(p['exe_sha256'] in control_hashes for p in controls),
 'both_live_speed_limits_2m_s':all(live['parameters']['/'+node+'/maxSpeed']==2.0 for node in ('localPlanner','pathFollower')),
 'native_time_model_unchanged_2_and_1':native['PlanningParams']['v_max']==2.0 and native['PlanningParams']['v_homing_max']==1.0,
 'native_sampling_unchanged_2000':native['PlanningParams']['num_vertices_max']==2000,
 'native_frontier_threshold_unchanged_001':native['SensorParams']['VLP16']['frontier_percentage_threshold']==.01,
 'benchmark_driver_matches_frozen_adapter':sha(folder/'benchmark_trial.py')==adapter['files']['benchmarks/benchmark_trial.py']['repaired_sha256'],
 'gbp2_config_matches_frozen_adapter':sha(folder/'config/gbp2.yaml')==adapter['files']['benchmarks/config/gbp2.yaml']['repaired_sha256'],
 'selected_trial_frozen_before_outcome':json.loads((folder/'progress_trials.json').read_text())==json.loads((root/'benchmarks/progress_trials.json').read_text()),
 'frozen_rrg_source_matches_native_manifest':sha(folder/'rrg.cpp.frozen')==next(row['repaired_sha256'] for row in frozen['sources'] if row['method']=='gbp2' and row['relative']=='gbplanner/src/rrg.cpp'),
}
value={'checks':checks,'passed':all(checks.values()),'changed_native_sources':changed,
 'note':'Pre-completion runtime consistency audit; exploration/parking success must be verified from final result separately.'}
(folder/'runtime_freeze_validation.json').write_text(json.dumps(value,indent=2)+'\n')
print(json.dumps(value,indent=2))
assert value['passed']
