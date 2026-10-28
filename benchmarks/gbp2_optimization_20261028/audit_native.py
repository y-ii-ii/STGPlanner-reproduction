"""Read actual runtime and snapshot the active native GBP2 baseline before changes."""
import hashlib
import json
import shutil
import socket
from pathlib import Path
root=Path('/mnt/d/STGPlanner')
out=root/'codex/outputs/gbp2_optimization_20261028/preflight_audit'
out.mkdir(parents=True,exist_ok=False)
processes=[]
for proc in Path('/proc').iterdir():
    if proc.name.isdigit():
        try:
            exe=str((proc/'exe').resolve())
            if Path(exe).name in ['rosmaster','roslaunch','gzserver','gzclient','gbplanner_node','tare_planner_node','topo_planner_node']:
                processes.append({'pid':int(proc.name),'exe':exe})
        except OSError:pass
ports={}
for port in [11311,11312,11345]:
    with socket.socket() as s:ports[str(port)]=s.connect_ex(('127.0.0.1',port))!=0
assert not processes and all(ports.values()),'Runtime already active'
native=Path('/opt/stgplanner/benchmarks/gbp2_ws')
items={
 'rrg.cpp':native/'src/gbplanner/src/rrg.cpp',
 'params.cpp':native/'src/planner_common/src/params.cpp',
 'params.h':native/'src/planner_common/include/planner_common/params.h',
 'voxblox_alt_impl.cpp':native/'src/planner_common/src/voxblox/voxblox_alt_impl.cpp',
 'map_manager_voxblox_impl.h':native/'src/planner_common/include/planner_common/map_manager_voxblox_impl.h',
 'libgbplanner.so':native/'devel/lib/libgbplanner.so',
 'libplanner_common.so':native/'devel/lib/libplanner_common.so'}
files=[]
for name,path in items.items():
    assert path.exists(),path
    shutil.copy2(path,out/name)
    files.append({'path':str(path),'saved':name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
shutil.copytree(root/'benchmarks/config',out/'config')
old=root/'benchmarks/results/repair_formal_gbp2_09/rrg.cpp.frozen'
value={'runtime_processes':processes,'ports_free':ports,'native_files':files,
       'rrg_matches_formal09':hashlib.sha256(old.read_bytes()).hexdigest()==hashlib.sha256(items['rrg.cpp'].read_bytes()).hexdigest(),
       'agents_files':[str(p) for p in (native/'src').rglob('AGENTS.md')]}
(out/'audit.json').write_text(json.dumps(value,indent=2)+'\n')
print(json.dumps(value,indent=2))
