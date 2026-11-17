#!/usr/bin/env bash
# New planner/executor and Python spaces only. All previous native workspaces
# remain immutable; this does not launch ROS, replay a map, or start Gazebo.
set -eo pipefail
base="$(cd "$(dirname "$0")" && pwd)"
if pgrep -x rosmaster >/dev/null || pgrep -x gzserver >/dev/null; then exit 21; fi
source /opt/stgplanner/team_topology_native_task_20261116_ws/devel/setup.bash
native=/opt/stgplanner/team_topology_wall_native_20261117_ws
mkdir -p "$native/src"
cp -a "$base/native_overlay/planner" "$native/src/"
cp -a "$base/native_overlay/path_execution" "$native/src/"
cd "$native"
catkin config --extend /opt/stgplanner/team_topology_native_task_20261116_ws/devel --cmake-args -DCMAKE_BUILD_TYPE=Release -DPYTHON_EXECUTABLE=/usr/bin/python3
catkin build planner path_execution --no-deps -j2 -p1 --no-status
source "$native/devel/setup.bash"
python_ws=/opt/stgplanner/team_topology_wall_20261117_ws
mkdir -p "$python_ws/src"
cp -a "$base/team_topology" "$python_ws/src/"
cd "$python_ws"
catkin config --extend "$native/devel"
catkin build team_topology --no-deps -j2 -p1 --no-status
