import datetime
import hashlib
import json
import os
import shutil
import subprocess
import time
from pathlib import Path
from cleanup_trial_runtime import cleanup_owned_runtime

root=Path('/mnt/d/STGPlanner'); bench=root/'benchmarks'; trial='diagnostic_gbp2_gain_08'
out=bench/'results'/trial; setup=root/'codex/outputs/diagnostic_gbp2_gain_08_setup'
assert not out.exists()
lock_path=root/'codex/SIMULATION_LOCK.json'; lock=json.loads(lock_path.read_text())
assert lock['trial']==trial and lock['owner_thread']=='01a17c85-9d73-7573-885c-a95dbbc4abbf'
def save_lock(**kwargs):
    lock.update(kwargs); lock['updated_at']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat()
    lock_path.write_text(json.dumps(lock,indent=2)+'\n')
manifest=json.loads((setup/'setup_manifest.json').read_text())
manifest['compiled_libraries']=[{'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in (
    Path('/opt/stgplanner/benchmarks/gbp2_ws/devel/lib/libgbplanner.so'),Path('/opt/stgplanner/benchmarks/gbp2_ws/devel/lib/libplanner_common.so'))]
(setup/'runtime_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
with (bench/'logs'/(trial+'.log')).open('x') as log:
    process=subprocess.Popen(['python3',str(root/'codex/work/benchmark_diagnostic08.py'),'gbp2','--name',trial,'--limit','1400','--pilot'],stdout=log,stderr=subprocess.STDOUT)
    save_lock(runtime_active=True,phase='diagnostic_running',supervisor_pid=os.getpid(),benchmark_pid=process.pid,result_path=str(out),note='Logging-only1400s diagnostic running; algorithm chat exclusively owns runtime. Native snapshots at600/1000/1300s; formal07 preserved.')
    while not out.exists() and process.poll() is None:time.sleep(.1)
    audits=[]
    if out.exists():
        shutil.copy2(setup/'runtime_manifest.json',out/'diagnostic_manifest.json')
        shutil.copytree(bench/'config',out/'config')
        shutil.copy2(root/'codex/work/benchmark_diagnostic08.py',out/'benchmark_diagnostic08.py')
        for name in ('audit_live_08.py','refresh_live_08.py'):
            handle=(out/(name+'.log')).open('w')
            child=subprocess.Popen(['bash','-c','source /opt/stgplanner/catkin_ws/devel/setup.bash; exec python3 '+str(root/'codex/work'/name)],stdout=handle,stderr=subprocess.STDOUT)
            audits.append((child,handle))
    code=process.wait()
    for child,handle in audits:
        if child.poll() is None:
            child.terminate()
            try:child.wait(timeout=5)
            except subprocess.TimeoutExpired:child.kill();child.wait()
        handle.close()
    result=json.loads((out/'result.json').read_text()) if (out/'result.json').exists() else {}
    cleaned=cleanup_owned_runtime(out)
    save_lock(state='idle' if cleaned else 'cleanup_required',runtime_active=not cleaned,phase='diagnostic_finished',returncode=code,result_path=str(out),finish_reason=result.get('finish_reason',result.get('fatal_error','missing_result')))
    status_path=root/'codex/STATUS.md'
    status=status_path.read_text()
    status+='\n## 08诊断自动结果（待人工核验）\n\n'+json.dumps({k:result.get(k) for k in ('trial','finish_reason','fatal_error','sim_time_s','coverage_fraction','area_m2','distance_m','validation')},ensure_ascii=False,indent=2)+'\n'
    status_path.write_text(status)
    print(json.dumps({'trial':trial,'code':code,'finish_reason':result.get('finish_reason')}),flush=True)
