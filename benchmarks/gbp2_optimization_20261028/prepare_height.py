"""Conditional native-geometry calibration, without changing native code or ray objective."""
import hashlib
import json
from pathlib import Path
from assert_idle import assert_idle
from guard_new_experiment import check_new_experiment
root=Path('/mnt/d/STGPlanner');out=root/'codex/outputs/gbp2_optimization_20261028'
check_new_experiment(root)
idle=assert_idle(root)
previous=json.loads((out/'gbp2_frontier03_20261028_11_validation.json').read_text())
assert previous['protocol_checks_passed'] and not previous['summary']['public95_reached']
geometry=json.loads((out/'sensor_ground_geometry.json').read_text())
new=round(geometry['nominal_sensor_z_above_wheel_contact_m'],4);assert new==.5192
audit=json.loads((out/'preflight_audit/audit.json').read_text())
for item in audit['native_files']:
    assert hashlib.sha256(Path(item['path']).read_bytes()).hexdigest()==item['sha256']
path=root/'benchmarks/config/gbp2.yaml';before=path.read_text()
assert 'frontier_percentage_threshold: 0.03' in before
assert before.count('robot_height: 0.456')==1
after=before.replace('robot_height: 0.456','robot_height: 0.5192').replace('frontier_percentage_threshold: 0.03','frontier_percentage_threshold: 0.01')
baseline=(out/'preflight_audit/config/gbp2.yaml').read_text()
assert after==baseline.replace('robot_height: 0.456','robot_height: 0.5192')
dest=out/'sensor_height_configuration';dest.mkdir(exist_ok=False)
(dest/'gbp2.yaml.before').write_text(before);(dest/'gbp2.yaml.after').write_text(after)
(dest/'change.json').write_text(json.dumps({'single_change_from_historical09':'PlanningParams/robot_height',
    'before':.456,'after':new,'native_code_unchanged':True,'actual_idle_check':idle,
    'frontier_threshold_restored_to09':.01,'plan':'conditional_followup_plan.v2.json',
    'meaning':'Nominal physical height of the input sensor frame above wheel contact, from captured URDF. This is not a TF shift or a change to common scoring.'},indent=2)+'\n')
path.write_text(after);print('Conditional native robot_height calibration deployed:0.5192m, historical09 frontier0.01')
