#!/usr/bin/env bash
# A new bundle is mandatory: action metadata ABI must not mix with old binaries.
set -eo pipefail
base="$(cd "$(dirname "$0")" && pwd)"
ws=/opt/stgplanner/team_topology_native_task_20261116_ws
source /opt/stgplanner/dual_robot_s1_ws/devel/setup.bash
if pgrep -x rosmaster >/dev/null || pgrep -x gzserver >/dev/null; then
  echo "Shared ROS/Gazebo runtime is active; refusing offline build" >&2
  exit 1
fi
mkdir -p "$ws/src"
for pkg in planner control_planner_interface path_execution explorer; do
  cp -a "$base/native_overlay/$pkg" "$ws/src/"
done
cp -a "$base/team_topology" "$ws/src/"
cd "$ws"
catkin config --extend /opt/stgplanner/dual_robot_s1_ws/devel --cmake-args -DCMAKE_BUILD_TYPE=Release -DPYTHON_EXECUTABLE=/usr/bin/python3
catkin build control_planner_interface path_execution planner exploration_manager team_topology --no-deps -j2 -p1 --no-status
