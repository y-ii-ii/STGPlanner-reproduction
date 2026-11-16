#!/usr/bin/env bash
# Build only new candidate spaces; the native-task and successful workspaces
# are read-only underlays. Never use the older build script for this stage.
set -eo pipefail
base="$(cd "$(dirname "$0")" && pwd)"
if pgrep -x rosmaster >/dev/null || pgrep -x gzserver >/dev/null; then
  echo "Runtime active: refusing candidate build" >&2; exit 21
fi
source /opt/stgplanner/team_topology_native_task_20261116_ws/devel/setup.bash
planner_ws=/opt/stgplanner/team_topology_traffic_native_20261116_ws
mkdir -p "$planner_ws/src"
cp -a "$base/native_overlay/planner" "$planner_ws/src/"
cd "$planner_ws"
catkin config --extend /opt/stgplanner/team_topology_native_task_20261116_ws/devel --cmake-args -DCMAKE_BUILD_TYPE=Release -DPYTHON_EXECUTABLE=/usr/bin/python3
catkin build planner --no-deps -j2 -p1 --no-status
source "$planner_ws/devel/setup.bash"
python_ws=/opt/stgplanner/team_topology_traffic_final_20261116_ws
mkdir -p "$python_ws/src"
cp -a "$base/team_topology" "$python_ws/src/"
cd "$python_ws"
catkin config --extend "$planner_ws/devel"
catkin build team_topology --no-deps -j2 -p1 --no-status
