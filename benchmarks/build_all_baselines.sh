#!/bin/bash
set -eo pipefail
base=/mnt/d/STGPlanner/benchmarks
python3 "$base/prepare_benchmark.py"
bash "$base/build_baseline.sh" tare
bash "$base/build_baseline.sh" fael
bash "$base/build_gbp2.sh"
python3 "$base/instrument_gbp2.py"
python3 "$base/gbp_debug.py"
source /opt/ros/noetic/setup.bash
(cd /opt/stgplanner/benchmarks/gbp2_ws && catkin build gbplanner --no-deps -j2 -p1 --no-status --summarize)
bash "$base/build_coverage.sh"
bash "$base/build_cloud_bridge.sh"
source /opt/stgplanner/catkin_ws/devel/setup.bash
python3 "$base/collect_benchmark_builds.py"
