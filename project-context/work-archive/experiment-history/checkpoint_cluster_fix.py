from pathlib import Path
import shutil,gzip
task=Path(__file__).resolve().parents[1];root=Path('D:/STGPlanner/benchmarks');repo=Path('D:/STGPlanner/catkin_ws/src/STGPlanner')
source=(task/'work/stage_progress.py').read_text(encoding='utf-8')
exec(source[:source.index('\ndef gz(')],{'__file__':str(task/'work/stage_progress.py')})
evidence=repo/'evidence/scene4-progress-fix'
for name in ['frontier_calibration_validation.json','cluster_frontier_regression.json','gbp_corridor_gain.json','progress_trials.json']:
    shutil.copy2(root/name,evidence/name)
for trial in ['repair_formal_gbp2_04','repair_formal_gbp2_05']:
    dest=evidence/trial;dest.mkdir(exist_ok=True)
    for name in ['result.json','interruption.json','metrics.jsonl','events.jsonl','native_source_manifest.json','adapter_config_manifest.json','native_config.yaml','benchmark_trial.py']:
        if (root/'results'/trial/name).exists():shutil.copy2(root/'results'/trial/name,dest/name)
    src=root/'results'/trial/'native_planner.log'
    with src.open('rb') as a,(dest/'native_planner.log.gz').open('wb') as b,gzip.GzipFile(filename='',fileobj=b,mode='wb',mtime=0) as c:shutil.copyfileobj(a,c)
p=repo/'benchmarks/progress_repairs/README.md'
p.write_text('''# Native progress repairs

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
''',encoding='utf-8',newline='\n')
print('Prepared cluster source checkpoint and complete failed05 evidence.')
