#!/usr/bin/env bash
set -eo pipefail
base="$(cd "$(dirname "$0")" && pwd)"
out="$1"
test -n "$out"
mkdir -p "$out"
PYTHONPATH="$base/team_topology/src" python3 -m unittest discover -s "$base/team_topology/tests" -v 2>&1 | tee "$out/python_tests.log"
# Non-PIE avoids the ASan/PIE address-layout failure seen in this WSL runtime.
# A bounded process and disabled SEGV interception prevent recursive signal logs.
g++ -std=c++17 -O1 -g -no-pie -fsanitize=address,undefined -fno-omit-frame-pointer \
  -I"$base/native_overlay/planner/include" "$base/tests/test_topology_gate.cpp" -o "$out/test_topology_gate"
ASAN_OPTIONS=handle_segv=0:detect_leaks=1 timeout -k 1 15 "$out/test_topology_gate" 2>&1 | tee "$out/native_gate.log"
