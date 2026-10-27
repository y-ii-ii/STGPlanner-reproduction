#!/bin/bash
set -eo pipefail
source /opt/stgplanner/benchmarks/gbp2_ws/devel/setup.bash
base=/mnt/d/STGPlanner/benchmarks
export ROS_MASTER_URI=http://localhost:11312 ROS_HOSTNAME=localhost
roscore -p 11312 >/tmp/ground-map-probe-roscore.log 2>&1 &
probe_master=$!
trap 'kill "$probe_master" 2>/dev/null || true' EXIT
for attempt in $(seq 1 30); do rosparam list >/dev/null 2>&1 && break; sleep .2; done
rosparam set /use_sim_time false
rosparam load "$base/config/gbp2.yaml" /gbp_ground_probe
rosparam load "$base/config/voxblox.yaml" /gbp_ground_probe
g++ -O1 -DNDEBUG -std=c++17 "$base/ground_map_probe.cpp" -o /opt/stgplanner/benchmarks/bin/ground_map_probe $(pkg-config --cflags --libs planner_common)
/opt/stgplanner/benchmarks/bin/ground_map_probe "$base/gbp_ground_snapshot.vxblx" "$base/gbp_ground_positions.txt" "$base/gbp_ground_probe.json"
