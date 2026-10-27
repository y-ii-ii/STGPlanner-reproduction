"""Prepare final-map replay only after formal09 and runtime cleanup finish."""
import hashlib
import json
import re
from pathlib import Path
root=Path('/mnt/d/STGPlanner');folder=root/'benchmarks/results/repair_formal_gbp2_09'
lock=json.loads((root/'codex/SIMULATION_LOCK.json').read_text())
assert lock['state']=='idle' and not lock['runtime_active'], 'Wait for formal trial cleanup'
result=json.loads((folder/'result.json').read_text())
snapshot=folder/'poststop_native_map.vxblx'
assert snapshot.exists(), 'Final native snapshot unavailable; do not fabricate a replay'
out=root/'codex/outputs/gbp_stagnation_probe_09';out.mkdir(exist_ok=False)
rows=[]
for line in (folder/'native_planner.log').read_text(errors='replace').splitlines():
    if 'GBP_DIAGNOSTIC_SELECTED' not in line:continue
    row={key:float(value) for key,value in re.findall(r'(\w+)=(-?\d+(?:\.\d+)?)',line)}
    if 'leaf_yaw' in row:rows.append(row)
chosen=rows[-60::5]
positions=[]
for index,row in enumerate(chosen):
    for kind in ('root','leaf'):
        x,y,z,yaw=[row[kind+'_'+key] for key in ('x','y','z','yaw')]
        positions.append(f'{kind}_projected_{index} {x} {y} {z+.456-.7} {yaw} {row[kind+"_unknown"]}\n')
        positions.append(f'{kind}_flat_sensor_{index} {x} {y} .456 {yaw} {row[kind+"_unknown"]}\n')
(out/'positions.txt').write_text(''.join(positions))
(out/'inputs.json').write_text(json.dumps({'source_trial':result['trial'],'finish_reason':result['finish_reason'],
    'sampled_selected_records':len(chosen),'queries':len(positions),'native_map':str(snapshot),
    'native_map_sha256':hashlib.sha256(snapshot.read_bytes()).hexdigest(),
    'selection_records':chosen,
    'note':'Replay historical root/leaf states on final saved native map, not historical-gain reconstruction. Compare native projected sensing height with measured flat-scene sensor height. Public known-plane map used only for offline diagnosis; never fed to planner.'},indent=2)+'\n')
print(json.dumps({'queries':len(positions),'out':str(out)}))
