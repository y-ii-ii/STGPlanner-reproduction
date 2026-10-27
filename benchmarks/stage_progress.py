"""Stage this repair independently; never rewrite the original baseline evidence."""
from pathlib import Path
import datetime,gzip,hashlib,json,shutil
task=Path(__file__).resolve().parents[1];out=task/'outputs'
root=Path('D:/STGPlanner/benchmarks');repo=Path('D:/STGPlanner/catkin_ws/src/STGPlanner')
evidence=repo/'evidence/scene4-progress-fix';evidence.mkdir(exist_ok=True)
scripts=['apply_progress_repairs.py','apply_trial_repairs.py','build_progress_repairs.sh','capture_progress_manifest.py','rollback_progress_repairs.py','rollback_trial_repairs.py','Run-ProgressSuite.ps1','ray_cache_regression.py','fael_frontier_regression.cpp','run_fael_frontier_regression.sh','gain_frame_regression.py','gbp_core_regression.py','trial_contract_regression.py','gbp_gain_probe.cpp','run_gbp_gain_probe.sh','prepare_gbp_gain_probe.py','stop_gbp_cache_diagnostic.py','analyze_progress.py','plot_progress.py','make_progress_report.py','progress_trials.json','prepare_ground_map_probe.py','ground_map_probe.cpp','run_ground_map_probe.sh','adaptive_bound_probe.cpp','run_adaptive_bound_probe.sh','offline_rrg_probe.py','run_offline_rrg_probe.sh','validate_frontier_calibration.py','cluster_frontier_regression.py','record_gbp_frontiers.py']
scripts.extend(['run_outcome.py','validate_outcomes_07.py'])
scripts.extend(['path_frontier_repair.py','test_path_frontier_selection.py','cleanup_trial_runtime.py','prepare_formal_09.py','run_formal_trial.py','run_formal_09.sh','prepare_diagnostic_08.py','supervise_diagnostic_08.py','benchmark_diagnostic08.py','run_diagnostic_08.sh','summarize_diagnostic_08.py','audit_live_07.py','refresh_live_07.py','save_poststop_map_07.py'])
scripts.extend(['verify_runtime_freeze_09.py','prepare_passive_attachment_09.py','audit_passive_09_attached.py'])
scripts.extend(['gbp_stagnation_probe_09.cpp','prepare_stagnation_probe_09.py','run_stagnation_probe_09.sh'])
scripts.append('summarize_stagnation_probe_09.py')
scripts.extend(['stage_progress.py','update_progress_docs.py','prepare_backup09.py','private_backup09_api.py'])
scripts.append('verify_archive09.py')
for name in scripts:
    # /benchmarks/** is eol=lf. Hash the exact checkout representation so a
    # new clone verifies on Windows as well as Linux.
    (repo/'benchmarks'/name).write_text((task/'work'/name).read_text(encoding='utf-8'),encoding='utf-8',newline='\n')
shutil.copytree(root/'progress_repairs',repo/'benchmarks/progress_repairs',dirs_exist_ok=True)
shutil.copytree(root/'trial_repairs',repo/'benchmarks/trial_repairs',dirs_exist_ok=True)
shutil.copy2(root/'benchmark_trial.py',repo/'benchmarks/benchmark_trial.py')
shutil.copy2(root/'config/gbp2.yaml',repo/'benchmarks/config/gbp2.yaml')
def gz(source,destination):
    if destination.exists():
        if gzip.decompress(destination.read_bytes())==source.read_bytes():return
        destination=destination.with_name(destination.name[:-3]+'.postrun-complete.gz')
        if destination.exists():
            assert gzip.decompress(destination.read_bytes())==source.read_bytes(),str(destination)
            return
    with source.open('rb') as src,destination.open('wb') as raw,gzip.GzipFile(filename='',fileobj=raw,mode='wb',mtime=0) as dest:shutil.copyfileobj(src,dest)
def copy_evidence(source,destination):
    if destination.exists() and destination.read_bytes()!=source.read_bytes():
        if source.suffix=='.json':
            try:
                if json.loads(destination.read_text())==json.loads(source.read_text()):return
            except (ValueError,UnicodeError):pass
        destination=destination.with_name(destination.stem+'.postrun-complete'+destination.suffix)
        if destination.exists():
            assert destination.read_bytes()==source.read_bytes(),str(destination)
            return
    shutil.copy2(source,destination)
selection=json.loads((root/'progress_trials.json').read_text())
for trial in selection['pilot_runs']+selection['intermediate_runs']+selection.get('diagnostic_runs',[])+list(selection['final_runs'].values()):
    source=root/'results'/trial;dest=evidence/trial;dest.mkdir(exist_ok=True)
    for name in ['result.json','metrics.jsonl','events.jsonl','trajectory.csv','coverage.ufo','interruption.json','user_pause.json','native_source_manifest.json','native_stop_script.py','adapter_config_manifest.json','native_config.yaml','benchmark_trial.py','live_rosparams.yaml','live_runtime_audit.json','passive_speed_audit.json','preflight_audit.json','progress_trials.json','diagnostic_manifest.json','selection_diagnostic_summary.json','benchmark_diagnostic08.py','runtime_cleanup.json','poststop_map_capture.json','rrg.cpp.frozen']:
        if (source/name).exists():copy_evidence(source/name,dest/name)
    for name in ['known_plane_cells.csv','native_planner.log','movement.log','simulation.log','coverage.log','cloud_bridge.log','fael_traversability.log','passive_frontier_audit.jsonl','passive_global_action_audit.jsonl']:
        if (source/name).exists():gz(source/name,dest/(name+'.gz'))
    if (source/'config').exists():shutil.copytree(source/'config',dest/'config',dirs_exist_ok=True)
    for snapshot in list(source.glob('native_snapshot_*.vxblx'))+list(source.glob('poststop_native_map.vxblx')):
        gz(snapshot,dest/(snapshot.name+'.gz'))
    for name in ['runtime_freeze_validation.json','passive_audit_attachment.json']:
        if (source/name).exists():shutil.copy2(source/name,dest/name)
    for name in ['audit_live.py.log','refresh_live.py.log','save_poststop_map.py.log']:
        if (source/name).exists():gz(source/name,dest/(name+'.gz'))
    if (root/'logs'/(trial+'.log')).exists():gz(root/'logs'/(trial+'.log'),dest/'launcher.log.gz')
    preflight=task/'outputs'/('preflight_'+trial)
    if preflight.exists():shutil.copytree(preflight,evidence/('preflight_'+trial),dirs_exist_ok=True)
for name in ['ray_cache_regression.json','fael_frontier_regression.json','gain_frame_regression.json','gbp_core_regression.json','trial_contract_regression.json','gbp_gain_probe.json','gbp_gain_probe_calibrated.json','gbp_gain_positions.txt','gbp_ground_probe.json','gbp_ground_context.json','gbp_ground_positions.txt','gbp_adaptive_bound_before.json','offline_rrg_probe.json','offline_rrg_probe_initialization.json','offline_rrg_probe_preload_reset.json','protocol_manifest.json','progress_trials.json','gbp_corridor_gain.json','frontier_calibration_validation.json','cluster_frontier_regression.json']:
    if name=='progress_trials.json':shutil.copy2(root/name,evidence/name)
    else:copy_evidence(root/name,evidence/name)
for name in ['outcome_classification_validation.json','path_frontier_selection_regression.json']:
    shutil.copy2(root/name,evidence/name)
diagnostic_setup=task/'outputs/diagnostic_gbp2_gain_08_setup'
if diagnostic_setup.exists():shutil.copytree(diagnostic_setup,evidence/'diagnostic_gbp2_gain_08_setup',dirs_exist_ok=True)
stagnation=task/'outputs/gbp_stagnation_probe_09'
if stagnation.exists():
    stagnation_dest=evidence/'gbp_stagnation_probe_09';stagnation_dest.mkdir(exist_ok=True)
    for name in ['result.json','summary.json','inputs.json','positions.txt','probe.log','roscore.log']:
        if (stagnation/name).exists():shutil.copy2(stagnation/name,stagnation_dest/name)
prior_review=task/'outputs/trial07_review'
if prior_review.exists():shutil.copytree(prior_review,evidence/'trial07_review',dirs_exist_ok=True)
regression_folder=task/'outputs/path_frontier_selection_regression'
regression_dest=evidence/'path_frontier_selection_regression';regression_dest.mkdir(exist_ok=True)
for name in ['result.json','actual_selection_regression.cpp','selection.original.cpp','selection.repaired.cpp','native_before_selection_repair.cpp']:
    if (regression_folder/name).exists():shutil.copy2(regression_folder/name,regression_dest/name)
gz(root/'gbp_gain_snapshot.vxblx',evidence/'gbp_gain_snapshot.vxblx.gz')
gz(root/'gbp_ground_snapshot.vxblx',evidence/'gbp_ground_snapshot.vxblx.gz')
shutil.copy2(root/'progress_report/progress_validation.json',evidence/'validation.json')
for name in ['progress_build_fael.log','progress_build_gbp2.log','progress_build_gbp2_stdout.log','progress_build_gbp2_frame_stdout.log','progress_build_gbp2_core_stdout.log','progress_build_gbp2_end_stdout.log','progress_suite.log','fael_frontier_regression.log','fael_frontier_regression.err','gbp_gain_probe.log','gbp_gain_probe.err','gbp_gain_range_replay.log','gbp_gain_range_replay.err','repair_formal_fael_01.err','repair_formal_gbp2_01.err','repair_formal_gbp2_02.err','repair_formal_gbp2_03.err','repair_formal_gbp2_04.err','repair_formal_gbp2_05.err','repair_formal_gbp2_06.err','progress_build_gbp2_cluster_stdout.log','progress_build_gbp2_cluster_stderr.log','corridor_gain_probe.log','corridor_gain_probe.err','offline_rrg_probe_ordered.log','ground_map_probe.log','adaptive_bound_probe.log']:
    if (root/'logs'/name).exists():gz(root/'logs'/name,evidence/(name+'.gz'))
for source in (root/'logs').glob('offline_rrg_*.log'):gz(source,evidence/(source.name+'.gz'))
for name in ['FAEL成功与GBP2未完成阶段总结.md','FAEL成功与GBP2未完成阶段总结.html','Scene4探索停滞修复报告.md','Scene4探索停滞修复报告.html','Scene4修复长测结果.json','scene4_progress_curves.png','scene4_progress_maps.png','Scene4基线算法对比报告.md','Scene4基线算法对比报告.html','STGPlanner部署报告.md','STGPlanner部署报告.html']:
    shutil.copy2(out/name,repo/'docs'/name)
files={p.relative_to(repo).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(evidence.rglob('*')) if p.is_file() and p.name!='evidence_manifest.json'}
for folder in ['progress_repairs','trial_repairs']:
    for p in sorted((repo/'benchmarks'/folder).rglob('*')):
        if p.is_file():files[p.relative_to(repo).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
for relative in ['benchmarks/benchmark_trial.py','benchmarks/config/gbp2.yaml']:
    files[relative]=hashlib.sha256((repo/relative).read_bytes()).hexdigest()
for name in scripts:files['benchmarks/'+name]=hashlib.sha256((repo/'benchmarks'/name).read_bytes()).hexdigest()
for name in ['FAEL成功与GBP2未完成阶段总结.md','FAEL成功与GBP2未完成阶段总结.html','Scene4探索停滞修复报告.md','Scene4探索停滞修复报告.html','Scene4修复长测结果.json','scene4_progress_curves.png','scene4_progress_maps.png','Scene4基线算法对比报告.md','Scene4基线算法对比报告.html','STGPlanner部署报告.md','STGPlanner部署报告.html']:
    files['docs/'+name]=hashlib.sha256((repo/'docs'/name).read_bytes()).hexdigest()
manifest={'generated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':files}
(evidence/'evidence_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8',newline='\n')
(out/'Scene4修复证据校验清单.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8',newline='\n')
print('Staged',len(files),'new source / evidence files; original evidence untouched.')
