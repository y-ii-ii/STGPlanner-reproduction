#!/bin/bash
set -eo pipefail
source /opt/stgplanner/benchmarks/gbp2_ws/devel/setup.bash
root=/mnt/d/STGPlanner
export ROS_MASTER_URI=http://localhost:11312 ROS_HOSTNAME=localhost
python3 -c 'import socket; s=socket.socket(); assert s.connect_ex(("127.0.0.1",11312)) != 0, "Port occupied"'
roscore -p 11312 >"$root/codex/outputs/gbp_sampling_probe_07/roscore.log" 2>&1 &
master_pid=$!
trap 'kill "$master_pid" 2>/dev/null || true' EXIT
for attempt in $(seq 1 30); do rosparam list >/dev/null 2>&1 && break; sleep .2; done
rosparam set /use_sim_time false
rosparam load "$root/benchmarks/config/gbp2.yaml" /gbp_sampling_probe_07
rosparam load "$root/benchmarks/config/voxblox.yaml" /gbp_sampling_probe_07
g++ -O1 -DNDEBUG -std=c++17 "$root/codex/work/gbp_sampling_probe_07.cpp" -o "$root/codex/outputs/gbp_sampling_probe_07/probe" $(pkg-config --cflags --libs planner_common)
"$root/codex/outputs/gbp_sampling_probe_07/probe" "$root/benchmarks/gbp_ground_snapshot.vxblx" "$root/codex/outputs/gbp_sampling_probe_07/positions.txt" "$root/codex/outputs/gbp_sampling_probe_07/result.json" >"$root/codex/outputs/gbp_sampling_probe_07/probe.log" 2>&1
python3 -c 'import json; from pathlib import Path; p=Path("/mnt/d/STGPlanner/codex/outputs/gbp_sampling_probe_07/result.json"); d=json.loads(p.read_text()); print(json.dumps({"cases":len(d["cases"]), "output":str(p)}))'
