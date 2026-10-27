# Native repair checkpoint

This branch preserves the original main and Scene4 baseline tags. Full reports
and final acceptance are pending the new GBP2 long run; this is a source backup.

- FAEL: frontier lifecycle, neighbour updates, consistent viewpoint filtering,
  current roadmap and disconnected tour rejection. Real Scene4 run reached
  95.3366% at 1017.008 simulated seconds, 1351.931m. Stop checks passed.
- GBP2: ray-cache dimensions and last-column bounds; physical sensing frame;
  raised lateral ground-ray distance compensation; spherical LiDAR ray lengths;
  parentheses in the outbound + optional-home time budget expression.
- Actual native ray layout is 73 by 6 (438 endpoints). Cache regression
  reproduces 335 aliased values before the repair and zero afterwards.
- The real extracted ground projection regression reproduces z=0.20m before
  and z=0.70m after on a horizontal plane with central unknown / lateral hit.
- Cache-only and height-only attempts remained near 41% and were deliberately
  stopped for diagnosis. They are not final successful repetitions.

`manifest.json` identifies original/repaired source and compiled libraries.
The originals already include the previous baseline's build compatibility and
diagnostic changes. Rebuild locked baselines before applying these repairs.
Editing the source clones on D: does not change the /opt compiled copies.

Use build_progress_repairs.sh fael / gbp2. For rollback, stop all planners,
inspect rollback_progress_repairs.py (dry run default), then --apply and rebuild.
Switching a Git tag alone does not revert /opt native sources or binaries.
No new completion threshold, gain weights, common controller or common metric
was used to manufacture progress. Final claims must follow the full real run.
