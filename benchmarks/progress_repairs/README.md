# Native progress repairs

FAEL reached95.3366% at1017.008simulated seconds. GBP2 attempts03 and05
completed2400s but remained41.7582% and41.4049%; they did not complete exploration.
Attempt04 corrected native HOMING semantics but also ended below95%.

Native repairs: ray-cache bounds, physical sensing frame, lateral ground-ray
distance, spherical LiDAR geometry, time-expression precedence, native HOMING
status, and clustered-gain vertex type propagation. All source before/after and
patches are archived. Original files include preceding compatibility repairs.

Declared parameter calibration: sampling limits4x, time model2/1m/s, native
sensor-frontier fraction0.05->0.01. Common observer/controller/95% stop unchanged.
See trial_repairs/manifest.json. Offline probes and unit tests are not full runs.

Latest run06 was selected before its outcome and is undergoing real2400s
verification. Final claims must follow its recorded result. Prior failures remain.
Use build_progress_repairs.sh to rebuild native copies under/opt. Restoring a Git
tag alone does not revert those sources/binaries. Both rollback scripts default
to checks; --apply restores archived originals and then requires rebuilding.
