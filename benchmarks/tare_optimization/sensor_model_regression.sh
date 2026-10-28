#!/bin/bash
set -eo pipefail
source /opt/stgplanner/benchmarks/tare_ws/devel/setup.bash
root=/mnt/d/STGPlanner
dest="$root/codex/outputs/tare_optimization_20261028/sensor_model_regression"
mkdir -p "$dest"
label="${1:?baseline or candidate required}"
test ! -e "$dest/$label.log"
native=/opt/stgplanner/benchmarks/tare_ws/src/tare_planner
python3 - "$label" <<'PY'
import json,shlex,subprocess,sys
from pathlib import Path
root=Path('/mnt/d/STGPlanner');native=Path('/opt/stgplanner/benchmarks/tare_ws/src/tare_planner')
build=Path('/opt/stgplanner/benchmarks/tare_ws/build/tare_planner')
out=root/'codex/outputs/tare_optimization_20261028/sensor_model_regression';label=sys.argv[1]
flags=(build/'CMakeFiles/lidar_model.dir/flags.make').read_text()
includes=next(line.split('=',1)[1] for line in flags.splitlines() if line.startswith('CXX_INCLUDES ='))
link=shlex.split((build/'CMakeFiles/tare_planner_node.dir/link.txt').read_text())
libraries=[arg for arg in link if arg.startswith(('-L','-l','-Wl,')) or (arg.startswith('/') and '.so' in arg)]
utility=Path('/opt/stgplanner/benchmarks/tare_ws/devel/lib/libmisc_utils.a')
assert utility.exists()
command=['/usr/bin/c++','-O1','-std=c++17','-ffunction-sections','-fdata-sections','-Wl,--gc-sections']+shlex.split(includes)+[str(root/'codex/work/tare_optimization/sensor_model_regression.cpp'),str(native/'src/lidar_model/lidar_model.cpp'),str(utility)]+libraries+['-o',str(out/label)]
with (out/(label+'.compile.json')).open('x') as handle:handle.write(json.dumps(command,indent=2)+'\n')
with (out/(label+'.compile.log')).open('x') as handle:subprocess.run(command,stdout=handle,stderr=subprocess.STDOUT,check=True)
PY
set +e
"$dest/$label" > "$dest/$label.log"
code=$?
set -e
printf '%s\n' "$code" > "$dest/$label.exitcode"
cat "$dest/$label.log"
exit 0
