from pathlib import Path
import hashlib,json,shutil
task=Path(__file__).resolve().parents[1];root=Path('D:/STGPlanner/benchmarks');repo=Path('D:/STGPlanner/catkin_ws/src/STGPlanner')
scripts=['apply_progress_repairs.py','apply_trial_repairs.py','build_progress_repairs.sh','capture_progress_manifest.py','rollback_progress_repairs.py','rollback_trial_repairs.py','Run-ProgressSuite.ps1','ray_cache_regression.py','fael_frontier_regression.cpp','run_fael_frontier_regression.sh','gain_frame_regression.py','gbp_core_regression.py','trial_contract_regression.py','gbp_gain_probe.cpp','run_gbp_gain_probe.sh','prepare_gbp_gain_probe.py','stop_gbp_cache_diagnostic.py','analyze_progress.py','plot_progress.py','make_progress_report.py','progress_trials.json','prepare_ground_map_probe.py','run_ground_map_probe.sh','adaptive_bound_probe.cpp','run_adaptive_bound_probe.sh','offline_rrg_probe.py','run_offline_rrg_probe.sh']
for name in scripts:shutil.copy2(task/'work'/name,repo/'benchmarks'/name)
shutil.copytree(root/'progress_repairs',repo/'benchmarks/progress_repairs',dirs_exist_ok=True)
shutil.copytree(root/'trial_repairs',repo/'benchmarks/trial_repairs',dirs_exist_ok=True)
shutil.copy2(root/'benchmark_trial.py',repo/'benchmarks/benchmark_trial.py')
shutil.copy2(root/'config/gbp2.yaml',repo/'benchmarks/config/gbp2.yaml')
shutil.copy2(root/'sources/gbplanner_ros/LICENSE',repo/'benchmarks/progress_repairs/GBP2_LICENSE')
evidence=repo/'evidence/scene4-progress-fix';evidence.mkdir(exist_ok=True)
for name in ['ray_cache_regression.json','fael_frontier_regression.json','gain_frame_regression.json','gbp_core_regression.json','trial_contract_regression.json','gbp_gain_probe.json','offline_rrg_probe.json','gbp_ground_probe.json','gbp_adaptive_bound_before.json']:
    shutil.copy2(root/name,evidence/name)
for trial in ['repair_formal_fael_01','repair_formal_gbp2_01','repair_formal_gbp2_02','repair_formal_gbp2_03']:
    dest=evidence/trial;dest.mkdir(exist_ok=True)
    for name in ['result.json','interruption.json','native_source_manifest.json']:
        if (root/'results'/trial/name).exists():shutil.copy2(root/'results'/trial/name,dest/name)
status='''# Native repair checkpoint

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
'''
status+='''
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
'''
(repo/'benchmarks/progress_repairs/README.md').write_text(status,encoding='utf-8',newline='\n')
attributes=repo/'.gitattributes';text=attributes.read_text(encoding='utf-8')
for line in ['/evidence/scene4-progress-fix/** -text','/evidence/scene4-progress-fix/** whitespace=-blank-at-eol,-blank-at-eof','/benchmarks/progress_repairs/** -text','/benchmarks/progress_repairs/** whitespace=-blank-at-eol,-blank-at-eof','/benchmarks/trial_repairs/** -text','/benchmarks/trial_repairs/** whitespace=-blank-at-eol,-blank-at-eof']:
    if line not in text:text+='\n'+line
attributes.write_text(text.rstrip()+'\n',encoding='utf-8',newline='\n')
print('Prepared native-source checkpoint with regressions and completed/interrupted results.')
