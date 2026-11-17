#!/usr/bin/env bash
set -eo pipefail
base="$(cd "$(dirname "$0")" && pwd)"
out="$1"
test -n "$out"
mkdir -p "$out"
PYTHONPATH="$base/team_topology/src" python3 -m unittest discover -s "$base/team_topology/tests" -v 2>&1 | tee "$out/python_tests.log"
for name in topology_gate own_observation_union body_route execution_endpoint stop_proof_cache execution_clock fatal_trace command_wait; do
  g++ -std=c++17 -O1 -g -no-pie -fsanitize=address,undefined -fno-omit-frame-pointer \
    -I"$base/native_overlay/planner/include" -I"$base/native_overlay/path_execution/include" \
    "$base/tests/test_$name.cpp" -pthread -o "$out/test_$name"
  ASAN_OPTIONS=handle_segv=0:detect_leaks=1 timeout -k 1 30 "$out/test_$name" 2>&1 | tee "$out/$name.log"
done
g++ -std=c++17 -O1 -g -no-pie -fsanitize=address,undefined -fno-omit-frame-pointer \
  -I"$base/native_overlay/planner/include" $(pkg-config --cflags opencv4) \
  "$base/tests/test_graph_coordinate_lifetime.cpp" $(pkg-config --libs opencv4) -o "$out/test_graph_coordinate_lifetime"
ASAN_OPTIONS=handle_segv=0:detect_leaks=1 timeout -k 1 30 "$out/test_graph_coordinate_lifetime" 2>&1 | tee "$out/graph_coordinate_lifetime.log"
