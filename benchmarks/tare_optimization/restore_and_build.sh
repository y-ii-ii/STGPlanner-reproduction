#!/bin/bash
set -eo pipefail
root=/mnt/d/STGPlanner
out="$root/codex/outputs/tare_optimization_20261028"
test ! -e "$out/build_restored_original.log"
python3 "$root/codex/work/tare_optimization/restore_sensor_model.py"
source /opt/ros/noetic/setup.bash
cd /opt/stgplanner/benchmarks/tare_ws
catkin build tare_planner --no-deps -j2 -p1 --no-status --summarize > "$out/build_restored_original.log" 2>&1
tail -n 14 "$out/build_restored_original.log"
python3 - <<'PY'
import hashlib,json,shutil
from pathlib import Path
out=Path('/mnt/d/STGPlanner/codex/outputs/tare_optimization_20261028')
original=out/'sensor_model_proposal/tare_planner_node.before'
target=Path('/opt/stgplanner/benchmarks/tare_ws/devel/lib/tare_planner/tare_planner_node').resolve()
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
frozen=json.loads(Path('/mnt/d/STGPlanner/benchmarks/results/tare_audit_control_20261028_01/preflight/manifest.json').read_text())['hashes']
expected=frozen['/opt/stgplanner/benchmarks/tare_ws/devel/lib/tare_planner/tare_planner_node']
assert digest(original)==expected
rebuilt=digest(target)
if rebuilt != expected:
    shutil.copy2(target,out/'sensor_model_proposal/tare_planner_node.original_rebuilt')
    shutil.copy2(original,target)
assert digest(target)==expected
(out/'restored_binary_verification.json').write_text(json.dumps({'rebuilt_sha256':rebuilt,'deployed_sha256':expected,
    'exact_original_frozen_binary_restored':True,'source_restored_and_rebuilt':True},indent=2)+'\n')
print('Original tested native binary SHA verified: '+expected)
PY
