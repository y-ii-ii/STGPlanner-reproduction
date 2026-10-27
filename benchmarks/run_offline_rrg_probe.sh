#!/bin/bash
set -eo pipefail
source /opt/stgplanner/benchmarks/gbp2_ws/devel/setup.bash
export ROS_MASTER_URI=http://localhost:11312 ROS_HOSTNAME=localhost
roscore -p 11312 >/tmp/offline-rrg-probe-roscore.log 2>&1 &
probe_master=$!
trap 'kill "$probe_master" 2>/dev/null || true' EXIT
for attempt in $(seq 1 30); do rosparam list >/dev/null 2>&1 && break; sleep .2; done
rosparam set /use_sim_time false
python3 /mnt/d/STGPlanner/benchmarks/offline_rrg_probe.py
