"""Capture settled runtime after initialization; does not control the trial."""
import datetime
import hashlib
import json
import time
from pathlib import Path
import rospy
import rosparam

out = Path('/mnt/d/STGPlanner/benchmarks/results/repair_formal_gbp2_09')
rospy.init_node('capture_settled_runtime_07', anonymous=True, disable_signals=True)
deadline = time.monotonic() + 100
while not (out / 'status.json').exists():
    assert time.monotonic() < deadline, 'Trial did not start exploration'
    time.sleep(.5)
rosparam.dump_params(str(out / 'live_rosparams.yaml'), '/')
all_params = rospy.get_param('/')
params = {name: rospy.get_param(name, None) for name in (
    '/localPlanner/maxSpeed', '/localPlanner/autonomySpeed', '/pathFollower/maxSpeed',
    '/pathFollower/autonomySpeed', '/pathFollower/twoWayDrive', '/use_sim_time')}
native_params = {key: value for key, value in all_params.items() if key in ('gbplanner_node','PlanningParams','RrgParams')}
processes = []
for directory in Path('/proc').iterdir():
    if not directory.name.isdigit(): continue
    try:
        exe = directory.joinpath('exe').resolve(strict=True)
        if exe.name not in ('localPlanner','pathFollower','path_execution_node','gbplanner_node'): continue
        libraries = sorted(set(line.split()[-1] for line in directory.joinpath('maps').read_text().splitlines()
            if 'libgbplanner' in line or 'libplanner_common' in line))
        processes.append({'pid': int(directory.name), 'exe': str(exe),
            'exe_sha256': hashlib.sha256(exe.read_bytes()).hexdigest(),
            'cmdline': directory.joinpath('cmdline').read_bytes().replace(b'\0',b' ').decode(),
            'loaded_native_libraries': [{'path': p, 'sha256': hashlib.sha256(Path(p).read_bytes()).hexdigest()} for p in libraries]})
    except (OSError, ProcessLookupError): pass
assert len(processes) == 4, processes
record = {'captured_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'parameters': params, 'native_parameters': native_params, 'processes': processes,
    'passive_only': True, 'capture_phase': 'after_exploration_start'}
(out / 'live_runtime_audit.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps({'parameters': params, 'processes': [{k:p[k] for k in ('pid','exe','exe_sha256')} for p in processes]}))
