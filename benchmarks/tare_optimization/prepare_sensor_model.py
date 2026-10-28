"""Propose/apply only TARE's physical VLP16 vertical model alignment, when idle."""
import argparse
import difflib
import hashlib
import json
import socket
import shutil
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--apply', action='store_true')
args = parser.parse_args()
root = Path('/mnt/d/STGPlanner')
native = Path('/opt/stgplanner/benchmarks/tare_ws/src/tare_planner')
out = root / 'codex/outputs/tare_optimization_20261028/sensor_model_proposal'
out.mkdir(parents=True, exist_ok=True)
changes = {
    'include/lidar_model/lidar_model.h': [
        ('static const int kVerticalFOV = 24;', 'static const int kVerticalFOV = 30;'),
        ('static const int kVerticalVoxelSize = kVerticalFOV / kVerticalResolution;',
         '// Include both physical VLP16 endpoints (-15 and +15 degrees).\n  static const int kVerticalVoxelSize = kVerticalFOV / kVerticalResolution + 1;')],
    'src/viewpoint_manager/viewpoint_manager.cpp': [
        ('kVerticalFOVRatio = tan(M_PI / 15);', 'kVerticalFOVRatio = tan(M_PI / 12);  // VLP16 physical half-FOV: 15 degrees'),
        ('kInFovXYDistThreshold = 3 * (kCoveragePointCloudResolution / 2) / tan(M_PI / 15);',
         'kInFovXYDistThreshold = 3 * (kCoveragePointCloudResolution / 2) / kVerticalFOVRatio;')]
}
records = []
pending = []
for name, substitutions in changes.items():
    path = native / name
    before = path.read_text()
    after = before
    for old, new in substitutions:
        assert after.count(old) == 1, (name, old)
        after = after.replace(old, new)
    key = name.replace('/', '__')
    for suffix, content in [('before', before), ('after', after),
                            ('patch', ''.join(difflib.unified_diff(before.splitlines(True), after.splitlines(True), fromfile=name, tofile=name)))]:
        target = out / (key + '.' + suffix)
        if target.exists():
            assert target.read_text() == content
        else:
            with target.open('x') as handle:
                handle.write(content)
    records.append({'native_path': str(path), 'before_sha256': hashlib.sha256(before.encode()).hexdigest(),
                    'after_sha256': hashlib.sha256(after.encode()).hexdigest()})
    pending.append((path, after))
if args.apply:
    lock = json.loads((root / 'codex/SIMULATION_LOCK.json').read_text())
    assert not lock['runtime_active'], 'Never modify compiled sources during a trial'
    for port in (11311, 11345):
        with socket.socket() as connection:
            assert connection.connect_ex(('127.0.0.1', port)) != 0
    for proc in Path('/proc').iterdir():
        if proc.name.isdigit():
            try:
                assert str((proc / 'exe').resolve()).split('/')[-1] != 'tare_planner_node', 'TARE process still active'
            except OSError:
                pass
    binary = Path('/opt/stgplanner/benchmarks/tare_ws/devel/lib/tare_planner/tare_planner_node')
    backup = out / 'tare_planner_node.before'
    assert not backup.exists()
    shutil.copy2(binary, backup)
    for path, after in pending:
        path.write_text(after)
    applied = out / 'APPLIED.json'
    with applied.open('x') as handle:
        handle.write(json.dumps({'changes': records, 'only_tare_sensor_model_changed': True}, indent=2) + '\n')
else:
    manifest = out / 'proposal_manifest.json'
    if not manifest.exists():
        with manifest.open('x') as handle:
            handle.write(json.dumps({'changes': records, 'native_sources_modified': False}, indent=2) + '\n')
print(json.dumps({'applied': args.apply, 'files': records}, indent=2))
