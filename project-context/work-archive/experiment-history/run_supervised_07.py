"""Run the already-authorized trial, preserve frozen evidence, and record exit."""
import datetime
import json
import shutil
import subprocess
import time
from pathlib import Path

root = Path('/mnt/d/STGPlanner')
bench = root / 'benchmarks'
trial = 'repair_formal_gbp2_07'
out = bench / 'results' / trial
preflight = root / 'codex/outputs' / ('preflight_' + trial)
lock_path = root / 'codex/SIMULATION_LOCK.json'
record = json.loads(lock_path.read_text())
assert record['owner_thread'] == '01a17c85-9d73-7573-885c-a95dbbc4abbf'
assert record['trial'] == trial and record['phase'] == 'preflight_complete'
assert not out.exists()
def update(**fields):
    record.update(fields)
    record['updated_at'] = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat()
    lock_path.write_text(json.dumps(record, indent=2) + '\n')
with (bench / 'logs' / (trial + '.log')).open('x') as log:
    process = subprocess.Popen(['bash', str(bench / 'run_benchmark.sh'), 'gbp2', '--name', trial, '--limit', '2400'],
        stdout=log, stderr=subprocess.STDOUT)
    update(runtime_active=True, phase='launching', supervisor_pid=__import__('os').getpid(), benchmark_pid=process.pid)
    for _ in range(600):
        if out.exists() or process.poll() is not None: break
        time.sleep(.1)
    audit = None
    if out.exists():
        for name in ('native_source_manifest.json', 'adapter_config_manifest.json', 'progress_trials.json', 'benchmark_trial.py'):
            shutil.copy2(preflight / name, out / name)
        shutil.copytree(preflight / 'config', out / 'config')
        shutil.copy2(preflight / 'audit.json', out / 'preflight_audit.json')
        audit_log = (out / 'passive_runtime_audit.log').open('w')
        audit = subprocess.Popen(['bash', '-c', 'source /opt/stgplanner/catkin_ws/devel/setup.bash; export ROS_MASTER_URI=http://localhost:11311 ROS_HOSTNAME=localhost; exec python3 /mnt/d/STGPlanner/codex/work/audit_live_07.py'],
            stdout=audit_log, stderr=subprocess.STDOUT)
        update(phase='running', audit_pid=audit.pid, result_path=str(out))
    returncode = process.wait()
    if audit is not None:
        audit.terminate()
        try: audit.wait(timeout=5)
        except subprocess.TimeoutExpired: audit.kill(); audit.wait()
        audit_log.close()
    result = json.loads((out / 'result.json').read_text()) if (out / 'result.json').exists() else {}
    update(state='idle', runtime_active=False, phase='trial_finished', returncode=returncode,
        finish_reason=result.get('finish_reason', result.get('fatal_error', 'missing_result')))
    status_path = root / 'codex/STATUS.md'
    status = status_path.read_text()
    status = status.replace('## 当前状态：用户已恢复，GBP2 07正在运行', '## 当前状态：用户已恢复，GBP2 07已结束，待结果审计')
    marker = '07结果（自动记录，待人工核验）'
    status += '\n## ' + marker + '\n\n' + json.dumps({key: result.get(key) for key in (
        'trial','finish_reason','fatal_error','sim_time_s','coverage_fraction','area_m2','distance_m','validation')}, ensure_ascii=False, indent=2) + '\n'
    status_path.write_text(status)
    print(json.dumps({'returncode': returncode, 'result': str(out / 'result.json'), 'finish_reason': record['finish_reason']}, indent=2), flush=True)
