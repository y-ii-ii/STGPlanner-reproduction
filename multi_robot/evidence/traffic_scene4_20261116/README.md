# Scene4 topology/traffic validation — 2026-11-16

Code snapshot: b505e98. Scope closed 4/4, no fifth attempt. The candidate failed to reach 95%; final wheel-wall contact aborted trial04. No new T95 or superiority claim. Do not replace single04 or Old dual02.

TRIAL_SUMMARY.json records all counted outcomes, including the startup failure and unsuccessful stop ACKs in trials02/03. MECHANISM_AUDIT.json records final stop nonces, yield proofs, status counters and the repeated wall-contact pair. FINAL_PRESERVATION.json records original-file and new-archive checks. FINAL04_NATIVE_VERIFICATION.json pins 84 new package sources/configs and the two new planner binaries alongside old hash checks.

54 Python tests and 22 C++ assertions passed offline; these do not certify online safety. coverage_wall.png / coverage_wall.csv are aggregate coverage curves from frozen historical/new metrics, not raw ROS records. Native compile succeeded with pre-existing upstream UFOMap ambiguity/C-flag warnings; original source was not changed. Full logs, frozen scripts and 28 archived executables remain local in codex/work/topology_traffic_20261116.
