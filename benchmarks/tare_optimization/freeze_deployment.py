"""Read and record the final idle native TARE deployment, without changing it."""
import hashlib
import json
import socket
import time
from pathlib import Path
root = Path('/mnt/d/STGPlanner')
assert not json.loads((root / 'codex/SIMULATION_LOCK.json').read_text())['runtime_active']
for port in (11311, 11345):
    with socket.socket() as connection:
        assert connection.connect_ex(('127.0.0.1', port)) != 0
native = Path('/opt/stgplanner/benchmarks/tare_ws')
binary = native / 'devel/lib/tare_planner/tare_planner_node'
hashes = {str(binary): hashlib.sha256(binary.read_bytes()).hexdigest()}
for path in [native/'src/tare_planner/include/lidar_model/lidar_model.h', native/'src/tare_planner/src/viewpoint_manager/viewpoint_manager.cpp']:
    hashes[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
trial_root = root / 'benchmarks/results'
versions = {}
for trial in ['tare_audit_control_20261028_01', 'tare_sensor_model_20261028_01']:
    frozen = json.loads((trial_root / trial / 'preflight/manifest.json').read_text())['hashes']
    versions[trial] = all(frozen[path] == sha for path, sha in hashes.items())
assert sum(versions.values()) == 1
mode = 'aligned_sensor_model' if versions['tare_sensor_model_20261028_01'] else 'original_stock'
value = {'verified_unix': time.time(), 'deployment': mode, 'native_hashes': hashes,
         'matches_frozen_version': versions, 'simulation_ports_free': True, 'GBP2_followup': 'paused_by_user'}
out = root / 'codex/outputs/tare_optimization_20261028/deployment_state.json'
assert not out.exists()
with out.open('x') as handle:
    handle.write(json.dumps(value, indent=2) + '\n')
print(json.dumps(value, indent=2))
