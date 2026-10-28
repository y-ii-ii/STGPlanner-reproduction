"""Restore the exact original native TARE files, only with no runtime owner active."""
import hashlib
import json
import shutil
import socket
from pathlib import Path

root = Path('/mnt/d/STGPlanner')
assert not json.loads((root / 'codex/SIMULATION_LOCK.json').read_text())['runtime_active']
for port in (11311, 11345):
    with socket.socket() as connection:
        assert connection.connect_ex(('127.0.0.1', port)) != 0
proposal = root / 'codex/outputs/tare_optimization_20261028/sensor_model_proposal'
manifest = json.loads((proposal / 'APPLIED.json').read_text())
native = Path('/opt/stgplanner/benchmarks/tare_ws/src/tare_planner')
binary = Path('/opt/stgplanner/benchmarks/tare_ws/devel/lib/tare_planner/tare_planner_node')
candidate_backup = proposal / 'tare_planner_node.candidate'
assert not candidate_backup.exists()
shutil.copy2(binary, candidate_backup)
for item in manifest['changes']:
    path = Path(item['native_path'])
    path.resolve().relative_to(native.resolve())
    source = proposal / (path.relative_to(native).as_posix().replace('/', '__') + '.before')
    assert hashlib.sha256(source.read_bytes()).hexdigest() == item['before_sha256']
    # Write exact original bytes but refresh mtime, so Catkin cannot retain
    # candidate objects simply because an archived original had an older mtime.
    path.write_bytes(source.read_bytes())
print('Original native TARE sources restored. Rebuild before next run; retain all candidate results.')
