#!/usr/bin/env bash
# Compile only in an isolated source/build/devel tree. No simulator or map replay.
set -eo pipefail
base="$(cd "$(dirname "$0")" && pwd)"
ws=/opt/stgplanner/team_topology_offline_20261116_ws
source /opt/stgplanner/dual_robot_s1_ws/devel/setup.bash
if pgrep -x rosmaster >/dev/null || pgrep -x gzserver >/dev/null; then
  echo "Refusing offline build while the shared ROS/Gazebo runtime is active" >&2
  exit 1
fi
mkdir -p "$ws/src"
cp -a "$base/native_overlay/planner" "$ws/src/"
cp -a "$base/team_topology" "$ws/src/"
cd "$ws"
catkin config --extend /opt/stgplanner/dual_robot_s1_ws/devel --cmake-args -DCMAKE_BUILD_TYPE=Release -DPYTHON_EXECUTABLE=/usr/bin/python3
catkin build planner team_topology --no-deps -j2 -p1 --no-status
