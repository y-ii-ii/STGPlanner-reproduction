#!/bin/bash
set -eo pipefail
source /opt/ros/noetic/setup.bash
export DEBIAN_FRONTEND=noninteractive
unset http_proxy https_proxy all_proxy HTTP_PROXY HTTPS_PROXY ALL_PROXY
base=/mnt/d/STGPlanner/benchmarks
exec > >(tee "$base/logs/build_gbp2.log") 2>&1
apt-get install -y --no-upgrade --no-install-recommends libgoogle-glog-dev libgflags-dev libyaml-cpp-dev protobuf-compiler libprotobuf-dev autoconf automake libtool
ws=/opt/stgplanner/benchmarks/gbp2_ws
mkdir -p "$ws/src"
for pkg in kdtree planner_msgs planner_semantic_msgs planner_common gbplanner; do
  if [[ ! -d "$ws/src/$pkg" ]]; then cp -a "$base/sources/gbplanner_ros/$pkg" "$ws/src/$pkg"; fi
done
for dep in catkin_simple eigen_catkin eigen_checks gflags_catkin glog_catkin minkindr minkindr_ros mav_comm yaml_cpp_catkin protobuf_catkin voxblox adaptive_obb_ros; do
  if [[ ! -d "$ws/src/$dep" ]]; then cp -a "$base/sources/gbp_dependencies/$dep" "$ws/src/$dep"; fi
done
# Use Ubuntu's ABI-matched libraries instead of downloading obsolete wrappers.
python3 - "$ws" <<'PY'
from pathlib import Path
import sys
root=Path(sys.argv[1])/'src'
for pkg,library in [('gflags_catkin','gflags'),('glog_catkin','glog'),('yaml_cpp_catkin','yaml-cpp')]:
    path=root/pkg/'CMakeLists.txt'
    backup=path.with_suffix('.upstream.txt')
    if not backup.exists():backup.write_bytes(path.read_bytes())
    path.write_text('cmake_minimum_required(VERSION 3.0.2)\nproject('+pkg+')\nfind_package(catkin_simple REQUIRED)\ncatkin_simple()\ncs_export(INCLUDE_DIRS /usr/include LIBRARIES '+library+')\n')
PY
cd "$ws"
catkin init
catkin config --extend /opt/ros/noetic --cmake-args -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_STANDARD=17 -DUSE_SYSTEM_EIGEN=ON -DUSE_SYSTEM_PROTOBUF=ON
PYTHONUNBUFFERED=1 catkin build gbplanner -j2 -p1 --no-status --summarize
