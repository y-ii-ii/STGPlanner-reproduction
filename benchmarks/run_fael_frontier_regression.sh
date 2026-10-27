#!/bin/bash
set -eo pipefail
source /opt/stgplanner/benchmarks/fael_ws/devel/setup.bash
# The upstream constructor truncates auxiliary text logs. Run this test only
# after a FAEL simulation has stopped, even though it uses a separate master.
python3 - <<'PY'
from pathlib import Path
library=str(Path('/opt/stgplanner/benchmarks/fael_ws/devel/lib/libtopo_planner.so').resolve())
for process in Path('/proc').iterdir():
    if not process.name.isdigit():continue
    try:active=library in (process/'maps').read_text()
    except (OSError,UnicodeError):continue
    if active:raise SystemExit('Stop the active FAEL process before running its constructor regression.')
PY
export ROS_MASTER_URI=http://localhost:11312 ROS_HOSTNAME=localhost
roscore -p 11312 >/tmp/fael-regression-roscore.log 2>&1 &
regression_master=$!
trap 'kill "$regression_master" 2>/dev/null || true' EXIT
for attempt in $(seq 1 30); do rosparam list >/dev/null 2>&1 && break; sleep .2; done
rosparam set /use_sim_time false
if [[ ! -x /opt/stgplanner/benchmarks/bin/fael_frontier_regression || /mnt/d/STGPlanner/benchmarks/fael_frontier_regression.cpp -nt /opt/stgplanner/benchmarks/bin/fael_frontier_regression ]]; then
  g++ -O1 -DNDEBUG -std=c++17 /mnt/d/STGPlanner/benchmarks/fael_frontier_regression.cpp -o /opt/stgplanner/benchmarks/bin/fael_frontier_regression $(pkg-config --cflags --libs planner)
fi
timeout 20 /opt/stgplanner/benchmarks/bin/fael_frontier_regression
