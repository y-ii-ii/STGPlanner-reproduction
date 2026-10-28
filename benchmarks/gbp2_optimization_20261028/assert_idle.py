"""Check actual native ROS/Gazebo processes as well as the cooperative lock."""
import json
import socket
from pathlib import Path

RUNTIME_NAMES = {'roscore', 'rosmaster', 'gzserver', 'gzclient', 'gbplanner_node',
                 'localPlanner', 'pathFollower', 'path_execution_node'}

def assert_idle(root, allow_capped=False):
    lock = json.loads((root/'codex/SIMULATION_LOCK.json').read_text())
    assert not lock['runtime_active'], lock
    allowed={'resumed_by_user'}
    if allow_capped:allowed.update({'capped_at_user_limit','optimization_phase_complete'})
    assert lock['gbp2_followup'] in allowed, lock
    processes = []
    for proc in Path('/proc').iterdir():
        if not proc.name.isdigit():
            continue
        try:
            exe = (proc/'exe').resolve(strict=True)
            arguments = (proc/'cmdline').read_bytes().split(b'\0')
            basenames = {Path(a.decode(errors='replace')).name for a in arguments if a}
            if exe.name in RUNTIME_NAMES or basenames & RUNTIME_NAMES:
                processes.append({'pid': int(proc.name), 'exe': str(exe),
                                  'args': [a.decode(errors='replace') for a in arguments if a]})
        except OSError:
            pass
    assert not processes, processes
    ports = {}
    for port in [11311, 11312, 11345]:
        with socket.socket() as client:
            ports[str(port)] = client.connect_ex(('127.0.0.1', port)) != 0
    assert all(ports.values()), ports
    return {'runtime_processes': processes, 'ports_free': ports, 'lock': lock}

if __name__ == '__main__':
    print(json.dumps(assert_idle(Path('/mnt/d/STGPlanner'),allow_capped=True), indent=2))
