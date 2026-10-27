#!/bin/bash
set -eo pipefail
method=$1
source /opt/ros/noetic/setup.bash
base=/mnt/d/STGPlanner/benchmarks
exec > >(tee "$base/logs/progress_build_${method}.log") 2>&1
python3 "$base/apply_progress_repairs.py" "$method"
if [[ "$method" == fael ]]; then
  source /opt/stgplanner/catkin_ws/devel/setup.bash
  cd /opt/stgplanner/benchmarks/fael_ws
  catkin build planner --no-deps -j2 -p1 --no-status --summarize
elif [[ "$method" == gbp2 ]]; then
  cd /opt/stgplanner/benchmarks/gbp2_ws
  catkin build gbplanner -j2 -p1 --no-status --summarize
else
  exit 2
fi
