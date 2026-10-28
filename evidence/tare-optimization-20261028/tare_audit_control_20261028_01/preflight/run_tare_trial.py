"""Freeze and supervise a fresh TARE run; preserve all prior data and common code."""
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

sys.path.insert(0, '/mnt/d/STGPlanner/codex/work')
from cleanup_trial_runtime import cleanup_owned_runtime

parser = argparse.ArgumentParser()
parser.add_argument('--name', required=True)
parser.add_argument('--variant', required=True)
parser.add_argument('--limit', type=float, default=1600)
parser.add_argument('--pilot', action='store_true')
args = parser.parse_args()
root = Path('/mnt/d/STGPlanner')
bench = root / 'benchmarks'
out = bench / 'results' / args.name
preflight = root / 'codex/outputs/tare_optimization_20261028' / ('preflight_' + args.name)
assert not out.exists() and not preflight.exists(), 'Never overwrite prior run'
for port in (11311, 11345):
    with socket.socket() as connection:
        assert connection.connect_ex(('127.0.0.1', port)) != 0, 'Runtime port busy'
preflight.mkdir(parents=True)
shutil.copytree(bench / 'config', preflight / 'config')
native = Path('/opt/stgplanner/benchmarks/tare_ws')
manifest = {}
for path in (native / 'src/tare_planner').rglob('*'):
    if path.is_file() and path.suffix in ('.cpp', '.h', '.yaml', '.txt'):
        manifest[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
binary = native / 'devel/lib/tare_planner/tare_planner_node'
manifest[str(binary)] = hashlib.sha256(binary.read_bytes()).hexdigest()
for path in [bench / 'benchmark_trial.py', bench / 'config/movement.launch', bench / 'config/terrain_static.launch']:
    manifest[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
record = {'trial': args.name, 'variant': args.variant, 'pilot': args.pilot, 'limit_s': args.limit,
          'public_threshold_m2': 7400.5, 'common_max_speed_m_s': 2.0, 'hashes': manifest,
          'preflight_unix': time.time(), 'observation_only': True, 'protocol_revision': 3}
(preflight / 'manifest.json').write_text(json.dumps(record, indent=2) + '\n')
shutil.copy2(bench / 'benchmark_trial.py', preflight / 'benchmark_trial.py')
shutil.copy2(Path(__file__), preflight / 'run_tare_trial.py')
shutil.copy2(Path(__file__).with_name('observe_tare.py'), preflight / 'observe_tare.py')
lock_path = root / 'codex/SIMULATION_LOCK.json'
previous = json.loads(lock_path.read_text())
assert previous.get('runtime_active') is False
(preflight / 'previous_simulation_lock.json').write_text(json.dumps(previous, indent=2) + '\n')
lock = {'owner_thread': '01a17c85-9d73-7573-885c-a95dbbc4abbf', 'trial': args.name,
        'method': 'tare', 'state': 'running', 'phase': 'tare_optimization_running', 'runtime_active': True,
        'gbp2_followup': 'paused_by_user', 'stage_status': 'Scene4_prior_baseline_complete_TARE_followup_authorized',
        'result_path': str(out), 'supervisor_pid': os.getpid()}

def save_lock(**fields):
    lock.update(fields)
    lock['updated_at'] = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat()
    lock_path.write_text(json.dumps(lock, indent=2) + '\n')

save_lock()
observer = None
with (bench / 'logs' / (args.name + '.log')).open('x') as log:
    command = ['bash', str(bench / 'run_benchmark.sh'), 'tare', '--name', args.name, '--limit', str(args.limit)]
    if args.pilot:
        command.append('--pilot')
    process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
    save_lock(benchmark_pid=process.pid)
    while not out.exists() and process.poll() is None:
        time.sleep(.1)
    if out.exists():
        shutil.copytree(preflight, out / 'preflight')
        observer_log = (out / 'observer.log').open('x')
        observer_command = 'source /opt/stgplanner/catkin_ws/devel/setup.bash; export ROS_MASTER_URI=http://localhost:11311 ROS_HOSTNAME=localhost; exec python3 ' + str(preflight / 'observe_tare.py') + ' ' + str(out)
        observer = subprocess.Popen(['bash', '-c', observer_command], stdout=observer_log, stderr=subprocess.STDOUT)
        save_lock(observer_pid=observer.pid)
    code = process.wait()
    if observer is not None:
        try:
            observer.wait(timeout=4)
        except subprocess.TimeoutExpired:
            observer.terminate()
            observer.wait(timeout=4)
        observer_log.close()
    result = json.loads((out / 'result.json').read_text()) if (out / 'result.json').exists() else {}
    clean = cleanup_owned_runtime(out)
    changed = [name for name, expected in manifest.items()
               if hashlib.sha256(Path(name).read_bytes()).hexdigest() != expected]
    (out / 'freeze_validation.json').write_text(json.dumps({'all_frozen_files_unchanged': not changed, 'changed_files': changed}, indent=2) + '\n')
    save_lock(state='idle' if clean else 'cleanup_required', runtime_active=not clean, phase='tare_optimization_trial_ended',
              returncode=code, finish_reason=result.get('finish_reason', result.get('fatal_error', 'missing_result')))
    print(json.dumps({'trial': args.name, 'returncode': code, 'ports_cleaned': clean, 'changed_frozen_files': changed,
                      'result': {key: result.get(key) for key in ['finish_reason', 'sim_time_s', 'coverage_fraction', 'distance_m', 'validation']}}), flush=True)
