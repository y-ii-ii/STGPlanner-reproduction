#!/bin/bash
set -eo pipefail
root=/mnt/d/STGPlanner
python3 "$root/codex/work/prepare_stagnation_probe_09.py"
source /opt/stgplanner/benchmarks/gbp2_ws/devel/setup.bash
export ROS_MASTER_URI=http://localhost:11312 ROS_HOSTNAME=localhost
python3 -c 'import socket; s=socket.socket(); assert s.connect_ex(("127.0.0.1",11312)) != 0, "Port occupied"'
out="$root/codex/outputs/gbp_stagnation_probe_09"
roscore -p 11312 >"$out/roscore.log" 2>&1 &
master_pid=$!
trap 'kill "$master_pid" 2>/dev/null || true' EXIT
for attempt in $(seq 1 30); do rosparam list >/dev/null 2>&1 && break; sleep .2; done
rosparam set /use_sim_time false
rosparam load "$root/benchmarks/results/repair_formal_gbp2_09/config/gbp2.yaml" /gbp_stagnation_probe_09
rosparam load "$root/benchmarks/results/repair_formal_gbp2_09/config/voxblox.yaml" /gbp_stagnation_probe_09
g++ -O1 -DNDEBUG -std=c++17 "$root/codex/work/gbp_stagnation_probe_09.cpp" -o "$out/probe" $(pkg-config --cflags --libs planner_common)
"$out/probe" "$root/benchmarks/results/repair_formal_gbp2_09/poststop_native_map.vxblx" "$out/positions.txt" "$root/benchmarks/results/repair_formal_gbp2_09/known_plane_cells.csv" "$out/result.json" >"$out/probe.log" 2>&1
python3 -c 'import json;from pathlib import Path;p=Path("/mnt/d/STGPlanner/codex/outputs/gbp_stagnation_probe_09/result.json");d=json.loads(p.read_text());print(json.dumps({"cases":len(d["cases"]),"output":str(p)}))'
