"""Read-only preflight: actual process/port state and TARE source/build locations."""
import hashlib
import json
import subprocess
import socket
from pathlib import Path

processes = []
needles = ['rosmaster', 'roslaunch', 'gzserver', 'gzclient', 'benchmark_trial.py',
           'sensor_coverage_planner', 'tare_planner_node', 'run_formal_trial.py', 'gbplanner_node', 'topo_planner']
for entry in Path('/proc').iterdir():
    if entry.name.isdigit():
        try:
            command = (entry / 'cmdline').read_bytes().replace(b'\0', b' ').decode(errors='replace')
            if any(word in command for word in needles):
                processes.append({'pid': int(entry.name), 'command': command})
        except (OSError, PermissionError):
            pass
ports = []
for port in (11311, 11345):
    with socket.socket() as connection:
        connection.settimeout(1)
        if connection.connect_ex(('127.0.0.1', port)) == 0:
            ports.append(port)
workspace = Path('/opt/stgplanner/benchmarks/tare_ws')
sources = list((workspace / 'src').rglob('sensor_coverage_planner_ground.cpp'))
binaries = list((workspace / 'devel/lib/tare_planner').glob('*'))
value = {'processes': processes, 'occupied_simulation_ports': ports,
         'native_sources': [str(p) for p in sources],
         'binaries': [{'path': str(p), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in binaries if p.is_file()],
         'agents_files': [str(p) for p in (workspace / 'src').rglob('AGENTS.md')]}
out = Path('/mnt/d/STGPlanner/codex/outputs/tare_optimization_20261028')
out.mkdir(exist_ok=True)
(out / 'runtime_before.json').write_text(json.dumps(value, indent=2) + '\n')
print(json.dumps(value, indent=2))
