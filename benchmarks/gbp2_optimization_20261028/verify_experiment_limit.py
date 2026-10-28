"""Verify the cap's pure guard logic without starting a simulation or a probe."""
import json
from pathlib import Path
from guard_new_experiment import check_new_experiment
root=Path('/mnt/d/STGPlanner')
limits=json.loads((root/'codex/GBP2_EXPERIMENT_LIMITS.json').read_text())
used=[name for name in limits['counted_trials'] if (root/'benchmarks/results'/name).exists()]
blocked=False
try:check_new_experiment(root)
except AssertionError as error:blocked=True;reason=str(error)
assert blocked and len(used)==limits['max_new_formal_trials']==3
future=['gbp2_frontier015_height_20261028_13','gbp2_frontier015_height_repeat_20261028_14',
        'gbp2_sensor_height_repeat_20261028_13','gbp2_sensor_height_repeat_20261028_14']
assert not any((root/'benchmarks/results'/name).exists() for name in future)
value={'max_new_formal_trials':3,'counted_trials':used,'new_experiment_guard_rejects':True,
       'guard_reason':reason,'cancelled_future_trials_not_started':True,'new_ros_or_gazebo_started_for_this_check':False}
out=root/'codex/outputs/gbp2_optimization_20261028/experiment_limit_validation.json'
out.write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(value,indent=2))
