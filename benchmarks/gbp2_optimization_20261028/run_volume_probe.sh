#!/bin/bash
set -eo pipefail
root=/mnt/d/STGPlanner
work="$root/codex/work/gbp2_optimization_20261028"
python3 "$work/guard_new_experiment.py"
python3 "$work/assert_idle.py" > /dev/null
trial="$1"
case "$trial" in
  repair_formal_gbp2_09|gbp2_default_frontier_20261028_10|gbp2_frontier03_20261028_11) ;;
  *) echo 'Trial not preregistered for frozen-map diagnostic'; exit 2 ;;
esac
out="$root/codex/outputs/gbp2_optimization_20261028/volume_probe_$trial"
test ! -e "$out"
mkdir "$out"
map="$root/benchmarks/results/$trial/poststop_native_map.vxblx"
test -s "$map"
source /opt/stgplanner/benchmarks/gbp2_ws/devel/setup.bash
export ROS_MASTER_URI=http://localhost:11312 ROS_HOSTNAME=localhost
roscore -p 11312 > "$out/roscore.log" 2>&1 &
master_pid=$!
trap 'kill "$master_pid" 2>/dev/null || true; wait "$master_pid" 2>/dev/null || true' EXIT
for attempt in $(seq 1 30); do rosparam list >/dev/null 2>&1 && break; sleep .2; done
rosparam set /use_sim_time false
config="$root/benchmarks/results/$trial/config"
if [ ! -d "$config" ]; then config="$root/benchmarks/results/$trial/preflight/config"; fi
rosparam load "$config/gbp2.yaml" /gbp2_volume_probe
rosparam load "$config/voxblox.yaml" /gbp2_volume_probe
sha256sum "$map" > "$out/native_map.before.sha256"
# Compile a separate diagnostic executable. No native library/source changes.
g++ -O1 -DNDEBUG -std=c++17 "$work/native_volume_probe.cpp" -o "$out/probe" $(pkg-config --cflags --libs planner_common)
"$out/probe" "$map" "$out/result.json" > "$out/probe.log" 2>&1
sha256sum -c "$out/native_map.before.sha256" > "$out/native_map_verified.txt"
python3 - "$out/result.json" <<'PY'
import json,sys
from pathlib import Path
p=Path(sys.argv[1]);d=json.loads(p.read_text());groups={}
for nonuniform in [True,False]:
    selected=[r for r in d['cases'] if r['nonuniform']==nonuniform]
    groups[str(nonuniform)]={'native_free_origins':len(selected),'box_free_origins':sum(r['box_free'] for r in selected),
      'frontier_counts':{str(t):sum(r['native_ratio']>=t for r in selected) for t in [.01,.03,.1]},
      'box_free_frontier_counts':{str(t):sum(r['box_free'] and r['native_ratio']>=t for r in selected) for t in [.01,.03,.1]},
      'unknown_samples_over_native_known_columns_fraction':sum(r['unknown_over_native_known_column'] for r in selected)/max(1,sum(r['unknown_weighted'] for r in selected))}
v={'map_unchanged':True,'native_only':True,'groups':groups,'scope':'Frozen-map grid queries on native-known free origins. No common coverage input and no reachability proof. Uniform ray casting changes count normalization; it is a diagnostic, not an adopted parameter.'}
(p.parent/'summary.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v,indent=2))
PY
