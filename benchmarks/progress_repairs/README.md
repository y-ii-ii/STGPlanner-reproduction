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

## Continuation checkpoint: sampling and native-end contract

The complete geometry-repaired _03 run still stopped at its2400s limit with
41.7582% and2840.573m. Correct native service diagnostics on the same frozen
map/doorway pose found0/3corridor advances with500vertices and3/3with2000.
New trial_repairs explicitly archives sampling/time configuration and adapter
changes. Native gain weights, sensing params, bounds and95% metric are unchanged.
Native HOMING now reportsIDLstatus2 (ordinary repositioning remains3). The
adapter executes the return once, then observes parked until the same common
coverage/time limit; incomplete native termination is never counted as95%.
All10actual-function/contract/scope regressions passed. Final selection_04
is running; reports and full release verification remain pending.
