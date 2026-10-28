#!/bin/bash
set -eo pipefail
root=/mnt/d/STGPlanner
out="$root/codex/outputs/tare_optimization_20261028"
test -e "$out/sensor_model_proposal/APPLIED.json"
test ! -e "$out/build_sensor_model.log"
python3 - <<'PY'
import json,socket
from pathlib import Path
assert not json.loads(Path('/mnt/d/STGPlanner/codex/SIMULATION_LOCK.json').read_text())['runtime_active']
for port in (11311,11345):
    with socket.socket() as s:assert s.connect_ex(('127.0.0.1',port)) != 0
PY
source /opt/ros/noetic/setup.bash
cd /opt/stgplanner/benchmarks/tare_ws
catkin build tare_planner --no-deps -j2 -p1 --no-status --summarize > "$out/build_sensor_model.log" 2>&1
tail -n 14 "$out/build_sensor_model.log"
