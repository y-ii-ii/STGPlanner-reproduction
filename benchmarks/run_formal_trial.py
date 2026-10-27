"""Run one pre-frozen trial; collect passive evidence and clean owned processes."""
import argparse
import datetime
import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path
from cleanup_trial_runtime import cleanup_owned_runtime

parser=argparse.ArgumentParser(); parser.add_argument('--name',required=True); args=parser.parse_args()
root=Path('/mnt/d/STGPlanner'); bench=root/'benchmarks'; trial=args.name
preflight=root/'codex/outputs'/('preflight_'+trial); out=bench/'results'/trial
lock_path=root/'codex/SIMULATION_LOCK.json'; lock=json.loads(lock_path.read_text())
for obsolete in ('audit_pid','returncode','finish_reason'):
    lock.pop(obsolete,None)
assert lock['trial']==trial and lock['phase']=='preflight_complete'
assert lock['owner_thread']=='01a17c85-9d73-7573-885c-a95dbbc4abbf'
assert not out.exists()
def save_lock(**fields):
    lock.update(fields); lock['updated_at']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat()
    lock_path.write_text(json.dumps(lock,indent=2)+'\n')
with (bench/'logs'/(trial+'.log')).open('x') as log:
    process=subprocess.Popen(['bash',str(bench/'run_benchmark.sh'),'gbp2','--name',trial,'--limit','2400'],stdout=log,stderr=subprocess.STDOUT)
    save_lock(state='running',runtime_active=True,phase='formal_running',supervisor_pid=os.getpid(),benchmark_pid=process.pid,result_path=str(out),
        note='Fresh formal trial running with frozen source/binary/config; one runtime owner, no concurrent native builds.')
    while not out.exists() and process.poll() is None:time.sleep(.1)
    audits=[]
    if out.exists():
        for name in ('native_source_manifest.json','adapter_config_manifest.json','progress_trials.json','benchmark_trial.py'):
            shutil.copy2(preflight/name,out/name)
        shutil.copytree(preflight/'config',out/'config')
        shutil.copy2(preflight/'audit.json',out/'preflight_audit.json')
        shutil.copy2(preflight/'config/gbp2.yaml',out/'native_config.yaml')
        shutil.copy2(preflight/'rrg.cpp.expected09',out/'rrg.cpp.frozen')
        for name in ('audit_live.py','refresh_live.py','save_poststop_map.py'):
            handle=(out/(name+'.log')).open('w')
            command='source /opt/stgplanner/catkin_ws/devel/setup.bash; export PYTHONPATH=/opt/stgplanner/benchmarks/gbp2_ws/devel/lib/python3/dist-packages:$PYTHONPATH; export ROS_MASTER_URI=http://localhost:11311 ROS_HOSTNAME=localhost; exec python3 '+str(preflight/name)
            child=subprocess.Popen(['bash','-c',command],stdout=handle,stderr=subprocess.STDOUT)
            audits.append((child,handle))
        save_lock(audit_pids=[p.pid for p,_ in audits])
    status_path=root/'codex/STATUS.md';status=status_path.read_text()
    status=re.sub(r'## 当前状态：[^\n]+','## 当前状态：GBP2 '+trial+' 正式验证正在运行',status,count=1)
    status_path.write_text(status)
    code=process.wait()
    for child,handle in audits:
        if child.poll() is None:
            try:child.wait(timeout=4)
            except subprocess.TimeoutExpired:
                child.terminate()
                try:child.wait(timeout=3)
                except subprocess.TimeoutExpired:child.kill();child.wait()
        handle.close()
    result=json.loads((out/'result.json').read_text()) if (out/'result.json').exists() else {}
    cleaned=cleanup_owned_runtime(out)
    save_lock(state='idle' if cleaned else 'cleanup_required',runtime_active=not cleaned,phase='formal_finished',returncode=code,
        finish_reason=result.get('finish_reason',result.get('fatal_error','missing_result')),
        note='Trial ended; owned process cleanup and ports checked. See runtime_cleanup.json. Further diagnosis/report remains.')
    status=status_path.read_text()
    status=re.sub(r'## 当前状态：[^\n]+','## 当前状态：GBP2 '+trial+' 已结束，待结果核验',status,count=1)
    status+='\n## '+trial+' 自动结果（待人工核验）\n\n'+json.dumps({k:result.get(k) for k in ('trial','finish_reason','fatal_error','sim_time_s','coverage_fraction','area_m2','distance_m','validation')},ensure_ascii=False,indent=2)+'\n'
    status_path.write_text(status)
    print(json.dumps({'trial':trial,'returncode':code,'ports_cleaned':cleaned,'finish_reason':result.get('finish_reason')}),flush=True)
