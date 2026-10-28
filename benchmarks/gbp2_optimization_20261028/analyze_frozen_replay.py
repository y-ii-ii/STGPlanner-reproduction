"""Inspect prior read-only native scan queries; never feed public plane data to planner."""
import json
import math
from pathlib import Path
root=Path('D:/STGPlanner')
data=json.loads((root/'codex/outputs/gbp_stagnation_probe_09/result.json').read_text(encoding='utf-8'))
denominator=(360/5)*(30/5)*12
thresholds=[.01,.03,.05,.1]
groups={}
for label in ['projected','flat_sensor']:
    selected=[r for r in data['cases'] if label in r['name']]
    profiles=[]
    for row in selected:
        fraction=row['final_map_unknown_weighted']*.2/denominator
        assert (fraction>=.01)==row['frontier_001']
        profiles.append({'query':row['name'],'native_unknown_ratio':fraction,
                         'unknown_z_bins':row['unknown_z_bins']})
    groups[label]={'queries':len(profiles),'qualified_at_threshold':{str(t):sum(r['native_unknown_ratio']>=t for r in profiles) for t in thresholds},
                   'native_unknown_ratio_range':[min(r['native_unknown_ratio'] for r in profiles),max(r['native_unknown_ratio'] for r in profiles)]}
value={'native_scan_full_fov_denominator':denominator,'native_voxel_size':.2,'groups':groups,
       'scope':'Historical chosen states re-evaluated on final native map, not historical gain reconstruction or proof of reachable alternatives. This only diagnoses the tiny residual gains that can keep a local frontier flag alive.'}
out=root/'codex/outputs/gbp2_optimization_20261028/replay_threshold_sensitivity.json'
out.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(value,ensure_ascii=False,indent=2))
