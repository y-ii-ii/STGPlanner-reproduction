#!/bin/bash
set -eo pipefail
source /opt/stgplanner/benchmarks/gbp2_ws/devel/setup.bash
base=/mnt/d/STGPlanner/benchmarks
export ROS_MASTER_URI=http://localhost:11312 ROS_HOSTNAME=localhost
roscore -p 11312 >/tmp/gbp-gain-probe-roscore.log 2>&1 &
probe_master=$!
trap 'kill "$probe_master" 2>/dev/null || true' EXIT
for attempt in $(seq 1 30); do rosparam list >/dev/null 2>&1 && break; sleep .2; done
rosparam set /use_sim_time false
rosparam load "$base/config/gbp2.yaml" /gbp_gain_probe
rosparam load "$base/config/voxblox.yaml" /gbp_gain_probe
if [[ ! -x /opt/stgplanner/benchmarks/bin/gbp_gain_probe || "$base/gbp_gain_probe.cpp" -nt /opt/stgplanner/benchmarks/bin/gbp_gain_probe ]]; then
  g++ -O1 -DNDEBUG -std=c++17 "$base/gbp_gain_probe.cpp" -o /opt/stgplanner/benchmarks/bin/gbp_gain_probe $(pkg-config --cflags --libs planner_common)
fi
/opt/stgplanner/benchmarks/bin/gbp_gain_probe "${2:-$base/gbp_gain_snapshot.vxblx}" "${3:-$base/gbp_gain_positions.txt}" "${1:-$base/gbp_gain_probe_calibrated.json}"
