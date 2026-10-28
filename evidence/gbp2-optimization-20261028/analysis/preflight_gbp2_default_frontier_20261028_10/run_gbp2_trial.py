"""One fresh GBP2 trial with fixed public protocol and exact source/config freeze."""
import argparse
import datetime
import hashlib
import json
import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path
sys.path.insert(0,'/mnt/d/STGPlanner/codex/work')
from cleanup_trial_runtime import cleanup_owned_runtime

parser=argparse.ArgumentParser();parser.add_argument('--name',required=True);parser.add_argument('--variant',required=True);parser.add_argument('--limit',type=float,default=2400);args=parser.parse_args()
root=Path('/mnt/d/STGPlanner');bench=root/'benchmarks';out=bench/'results'/args.name
preflight=root/'codex/outputs/gbp2_optimization_20261028'/('preflight_'+args.name)
assert not out.exists() and not preflight.exists()
lock_path=root/'codex/SIMULATION_LOCK.json';previous=json.loads(lock_path.read_text());assert not previous['runtime_active'] and previous['gbp2_followup']=='resumed_by_user'
for port in [11311,11312,11345]:
    with socket.socket() as s:assert s.connect_ex(('127.0.0.1',port))!=0
preflight.mkdir();shutil.copytree(bench/'config',preflight/'config')
hashes={}
native=Path('/opt/stgplanner/benchmarks/gbp2_ws')
for component in ['gbplanner','planner_common']:
    for path in (native/'src'/component).rglob('*'):
        if path.is_file() and path.suffix in ['.cpp','.h','.hpp','.yaml','.txt']:
            hashes[str(path)]=hashlib.sha256(path.read_bytes()).hexdigest()
for path in [native/'devel/lib/libgbplanner.so',native/'devel/lib/libplanner_common.so',bench/'benchmark_trial.py',bench/'config/movement.launch',bench/'config/terrain_static.launch']:
    hashes[str(path)]=hashlib.sha256(path.read_bytes()).hexdigest()
manifest={'trial':args.name,'variant':args.variant,'limit_s':args.limit,'hashes':hashes,'protocol_revision':3,'public_threshold_m2':7400.5,'native_gain_objective':'unchanged 3D ray volume'}
(preflight/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
for source in [bench/'benchmark_trial.py',Path(__file__),Path(__file__).with_name('observe_and_save.py')]:shutil.copy2(source,preflight/source.name)
shutil.copy2(native/'src/gbplanner/src/rrg.cpp',preflight/'rrg.cpp.frozen')
(preflight/'previous_lock.json').write_text(json.dumps(previous,indent=2)+'\n')
lock={'owner_thread':'01a17c85-9d73-7573-885c-a95dbbc4abbf','method':'gbp2','trial':args.name,'state':'running','phase':'gbp2_optimization_running',
      'runtime_active':True,'gbp2_followup':'resumed_by_user','tare_followup':'complete_original_deployment_restored','result_path':str(out),'supervisor_pid':os.getpid()}
def save_lock(**fields):
    lock.update(fields);lock['updated_at']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat();lock_path.write_text(json.dumps(lock,indent=2)+'\n')
save_lock()
with (bench/'logs'/(args.name+'.log')).open('x') as log:
    process=subprocess.Popen(['bash',str(bench/'run_benchmark.sh'),'gbp2','--name',args.name,'--limit',str(args.limit)],stdout=log,stderr=subprocess.STDOUT)
    save_lock(benchmark_pid=process.pid)
    while not out.exists() and process.poll() is None:time.sleep(.1)
    observer=None
    if out.exists():
        shutil.copytree(preflight,out/'preflight')
        observer_log=(out/'passive_observer.log').open('x')
        command='source /opt/stgplanner/catkin_ws/devel/setup.bash; export PYTHONPATH=/opt/stgplanner/catkin_ws/devel/lib/python3/dist-packages:/opt/stgplanner/benchmarks/gbp2_ws/devel/lib/python3/dist-packages:$PYTHONPATH; export ROS_MASTER_URI=http://localhost:11311 ROS_HOSTNAME=localhost; exec python3 '+str(preflight/'observe_and_save.py')+' '+str(out)
        observer=subprocess.Popen(['bash','-c',command],stdout=observer_log,stderr=subprocess.STDOUT);save_lock(observer_pid=observer.pid)
    code=process.wait()
    if observer is not None:
        try:observer.wait(timeout=5)
        except subprocess.TimeoutExpired:observer.terminate();observer.wait(timeout=4)
        observer_log.close()
    result=json.loads((out/'result.json').read_text()) if (out/'result.json').exists() else {}
    clean=cleanup_owned_runtime(out)
    changed=[name for name,sha in hashes.items() if hashlib.sha256(Path(name).read_bytes()).hexdigest()!=sha]
    (out/'freeze_validation.json').write_text(json.dumps({'all_frozen_files_unchanged':not changed,'changed_files':changed},indent=2)+'\n')
    save_lock(state='idle' if clean else 'cleanup_required',runtime_active=not clean,phase='gbp2_optimization_trial_ended',returncode=code,finish_reason=result.get('finish_reason',result.get('fatal_error','missing_result')))
    print(json.dumps({'trial':args.name,'returncode':code,'ports_cleaned':clean,'changed_frozen_files':changed,
        'result':{key:result.get(key) for key in ['finish_reason','sim_time_s','distance_m','coverage_fraction','native_finished','validation','fatal_error']}}),flush=True)
