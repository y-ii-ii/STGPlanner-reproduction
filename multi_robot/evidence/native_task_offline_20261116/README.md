# Native task / stop ACK offline evidence — 2026-11-16

Code snapshot: 66b9b0f3ba79f78d14c48f30703554db581026ec. Report: ../../docs/NATIVE_TASK_EXECUTION_20261116.md.

- validation.json: source and binary fingerprints, preservation counters, package/test totals.
- python_tests.log: 46 synthetic Python tests (WSL); Windows passed the same suite.
- native_gate.log / native_task_scope.log / execution_lease.log / action_abi.log: 51 ASan+UBSan C++ assertions, including generated ROS-action serialization without ros::init/master.
- build_summary.log: final isolated five-package build, no warnings or failures.
- ENVIRONMENT_VERIFICATION.json: offline node/package lookup, action fields and library resolution; no node started.
- canvas_cpu.json / task_equivalence.json: one synthetic CPU illustration and task/wire equivalence, not physics experiments, native map replay, bandwidth measurements or T95.

Protected successful binaries, historical result inventory and the first-stage candidate were checked unchanged. No raw historical experiment data is uploaded here. Each evidence file records the limits of the associated check; online five-state visits, physical stopping, dual-robot avoidance and 95% coverage remain unvalidated.
