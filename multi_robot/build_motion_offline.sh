#!/usr/bin/env bash
# New STOP/dispatch candidate only. Previous native/Python spaces stay read-only.
set -eo pipefail
base="$(cd "$(dirname "$0")" && pwd)"
if pgrep -x rosmaster >/dev/null || pgrep -x gzserver >/dev/null; then exit 21; fi
source /opt/stgplanner/team_topology_native_task_20261116_ws/devel/setup.bash
native=/opt/stgplanner/team_topology_motion_native_20261118_ws
mkdir -p "$native/src"
for package in control_planner_interface planner path_execution explorer; do
  cp -a "$base/native_overlay/$package" "$native/src/"
done
cd "$native"
catkin config --extend /opt/stgplanner/team_topology_native_task_20261116_ws/devel --cmake-args -DCMAKE_BUILD_TYPE=RelWithDebInfo -DPYTHON_EXECUTABLE=/usr/bin/python3
catkin build control_planner_interface planner path_execution exploration_manager --no-deps -j2 -p1 --no-status
source "$native/devel/setup.bash"
python_ws=/opt/stgplanner/team_topology_motion_20261118_ws
mkdir -p "$python_ws/src"
cp -a "$base/team_topology" "$python_ws/src/"
cd "$python_ws"
catkin config --extend "$native/devel"
catkin build team_topology --no-deps -j2 -p1 --no-status
