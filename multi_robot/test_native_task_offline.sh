#!/usr/bin/env bash
set -eo pipefail
base="$(cd "$(dirname "$0")" && pwd)"
out="$1"
test -n "$out"
mkdir -p "$out"
bash "$base/test_offline.sh" "$out"
for kind in native_task_scope execution_lease; do
  g++ -std=c++17 -O1 -g -no-pie -fsanitize=address,undefined -fno-omit-frame-pointer \
    -I"$base/native_overlay/planner/include" -I"$base/native_overlay/control_planner_interface/include" \
    "$base/tests/test_$kind.cpp" -o "$out/test_$kind"
  ASAN_OPTIONS=handle_segv=0:detect_leaks=1 timeout -k 1 15 "$out/test_$kind" | tee "$out/$kind.log"
done
ws=/opt/stgplanner/team_topology_native_task_20261116_ws
g++ -std=c++17 -O1 -g -no-pie -fsanitize=address,undefined -fno-omit-frame-pointer \
  -I"$ws/devel/include" -I/opt/ros/noetic/include -I"$base/native_overlay/control_planner_interface/include" \
  "$base/tests/test_action_abi.cpp" -L/opt/ros/noetic/lib -lroscpp_serialization -lrostime -lcpp_common \
  -o "$out/test_action_abi"
LD_LIBRARY_PATH=/opt/ros/noetic/lib ASAN_OPTIONS=handle_segv=0:detect_leaks=1 timeout -k 1 15 "$out/test_action_abi" | tee "$out/action_abi.log"
