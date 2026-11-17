"""This finite trial ledger is separate from all closed historical scopes."""
from pathlib import Path
import json,hashlib,os
ROOT=Path('/mnt/d/STGPlanner')
CODE=Path(__file__).resolve().parents[1]
LIMITS=ROOT/'codex/TOPOLOGY_DISPATCH_LIMITS_20261117.json'
LOCK=ROOT/'codex/SIMULATION_LOCK.json'
UNDERLAY=Path('/opt/stgplanner/team_topology_native_task_20261116_ws')
NATIVE=Path('/opt/stgplanner/team_topology_dispatch_native_20261117_ws')
PLANNER=NATIVE
OVERLAY=Path('/opt/stgplanner/team_topology_dispatch_20261117_ws')
REF=ROOT/'benchmarks/results/dual_validate_scene4_20261102_02_dual'
SCORE_CODE=ROOT/'codex/worktrees/dual-jackal-s1/benchmarks/dual_robot_scene4_validation'
OWNER='01a18661-03d1-7722-b65f-e6257e8ab382'
def dump(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_name(path.name+'.tmp');temp.write_text(json.dumps(value,indent=2,ensure_ascii=False));temp.replace(path)
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def result_path(index):
    assert 1<=index<=4
    return ROOT/'benchmarks/results'/('topology_dispatch_scene4_20261117_%02d_dual'%index)
def runtime():
    names={'rosmaster','roslaunch','roscore','rosout','gzserver','gzclient','topo_planner_no','path_execution_','pathFollower','localPlanner','explorer_node','terrainAnalysis'}
    processes=[]
    for p in Path('/proc').iterdir():
        if not p.name.isdigit():continue
        try:
            if (p/'comm').read_text().strip() in names:processes.append(int(p.name))
        except OSError:pass
    ports={str(n):False for n in (11311,11312,11345)}
    for f in ('tcp','tcp6'):
        for line in Path('/proc/net/'+f).read_text().splitlines()[1:]:
            x=line.split();port=str(int(x[1].split(':')[-1],16))
            if x[3]=='0A' and port in ports:ports[port]=True
    return dict(processes=processes,ports_in_use=ports)
def idle():
    r=runtime();l=json.loads(LOCK.read_text())
    assert not r['processes'] and not any(r['ports_in_use'].values()),r
    assert not l.get('runtime_active') and l['owner_thread']==OWNER,l
