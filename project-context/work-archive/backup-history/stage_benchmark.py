from pathlib import Path
import hashlib,json,shutil,datetime,subprocess
root=Path('D:/STGPlanner/benchmarks');repo=Path('D:/STGPlanner/catkin_ws/src/STGPlanner');dest=repo/'benchmarks';dest.mkdir(exist_ok=True)
files=['build_baseline.sh','build_gbp2.sh','build_all_baselines.sh','build_coverage.sh','build_cloud_bridge.sh','benchmark_coverage.cpp','benchmark_cloud_bridge.cpp','benchmark_trial.py','run_benchmark.sh','prepare_benchmark.py','instrument_gbp2.py','gbp_debug.py','collect_benchmark_builds.py','clone_locked_sources.py','benchmark_protocol.md','sources.lock.json','environment.json','Run-Scene4Suite.ps1','path_contract_regression.py','probe_stall.py','probe_obstacles.py']
for name in files:shutil.copy2(root/name,dest/name)
for name in ['config','patches']:shutil.copytree(root/name,dest/name,dirs_exist_ok=True)
manifest={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'upstream_reproduction_baseline':'dfc712982891f29c266083d7efad72ad48e730a2','protocol_revision':3,'files':{}}
for path in sorted(dest.rglob('*')):
    if path.is_file() and path.name!='protocol_manifest.json':manifest['files'][path.relative_to(repo).as_posix()]=hashlib.sha256(path.read_bytes()).hexdigest()
cpp=repo/'stgp_planner/robot_move/path_execution/src/path_execution.cpp';manifest['files'][cpp.relative_to(repo).as_posix()]=hashlib.sha256(cpp.read_bytes()).hexdigest()
(dest/'protocol_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8',newline='\n')
(root/'protocol_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8',newline='\n')
print('Staged',len(manifest['files']),'protocol files')
