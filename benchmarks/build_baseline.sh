#!/bin/bash
set -eo pipefail
method=$1
source /opt/ros/noetic/setup.bash
root=/opt/stgplanner/benchmarks
sources=/mnt/d/STGPlanner/benchmarks/sources
logs=/mnt/d/STGPlanner/benchmarks/logs
mkdir -p "$root/${method}_ws/src" "$logs"
exec > >(tee "$logs/build_${method}.log") 2>&1
if [[ "$method" == tare ]]; then
  if [[ ! -d "$root/tare_ws/src/tare_planner" ]]; then cp -a "$sources/tare_planner/src/tare_planner" "$root/tare_ws/src/"; fi
  python3 - "$root/tare_ws/src/tare_planner/src/sensor_coverage_planner/sensor_coverage_planner_ground.cpp" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]);s=p.read_text()
s=s.replace('// exploration_path_publisher_.publish(full_path);','exploration_path_publisher_.publish(full_path);')
p.write_text(s)
PY
  cd "$root/tare_ws"
  catkin init
  catkin config --extend /opt/ros/noetic --cmake-args -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_STANDARD=17
  catkin build -j2 -p1 --no-status --summarize
elif [[ "$method" == fael ]]; then
  source /opt/stgplanner/catkin_ws/devel/setup.bash
  if [[ ! -d "$root/fael_ws/src/planner" ]]; then cp -a "$sources/FAEL/fael_planner/planner" "$root/fael_ws/src/"; fi
  python3 - "$root/fael_ws/src/planner/CMakeLists.txt" <<'PY'
from pathlib import Path
import re,sys
p=Path(sys.argv[1]);s=p.read_text()
s=re.sub(r'^#\s*visualization_tools.*$', '        visualization_tools',s,flags=re.M)
p.write_text(s)
PY
  mkdir -p "$root/fael_ws/files/exploration_data"
  cd "$root/fael_ws"
  catkin init
  catkin config --extend /opt/stgplanner/catkin_ws/devel --cmake-args -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_STANDARD=17
  catkin build planner --no-deps -j2 -p1 --no-status --summarize
else
  echo 'Unknown baseline' >&2; exit 2
fi
