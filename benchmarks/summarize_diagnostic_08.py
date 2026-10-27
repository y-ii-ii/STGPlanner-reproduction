import json
import re
import math
import argparse
from pathlib import Path
parser=argparse.ArgumentParser();parser.add_argument('--trial',default='diagnostic_gbp2_gain_08');args=parser.parse_args()
folder=Path('D:/STGPlanner/benchmarks/results')/args.trial
text=(folder/'native_planner.log').read_text(errors='replace') if (folder/'native_planner.log').exists() else ''
rows=[]
for line in text.splitlines():
    if 'GBP_DIAGNOSTIC_SELECTED' not in line:continue
    values={key:float(value) for key,value in re.findall(r'(\w+)=(-?\d+(?:\.\d+)?)',line)}
    timestamp=re.search(r'\[\d+\.\d+,\s*(\d+\.\d+)\]',line)
    if timestamp:values['absolute_sim']=float(timestamp.group(1))
    if 'path_frontiers' in values:rows.append(values)
events=[json.loads(line) for line in (folder/'events.jsonl').read_text().splitlines() if line.strip()]
start=next(event['sim'] for event in events if event['kind']=='exploration_start')
metrics=[]
for line in (folder/'metrics.jsonl').read_text().splitlines():
    try:metrics.append(json.loads(line))
    except json.JSONDecodeError:pass
for row in rows:
    before=[r for r in metrics if r['sim_s']<row.get('absolute_sim',start)-start-2]
    row['earlier_trajectory_distance_m']=min((math.hypot(r['x']-row['leaf_x'],r['y']-row['leaf_y']) for r in before),default=None)
status=json.loads((folder/'status.json').read_text()) if (folder/'status.json').exists() else None
value={'status':status,'selection_records':len(rows),'selected_paths_without_frontier':sum(r['path_frontiers']==0 for r in rows),
    'nonfrontier_selected_while_other_frontier_exists':sum(r['path_frontiers']==0 and r['any_frontier']==1 for r in rows),
    'selected_leaf_without_frontier':sum(r['leaf_frontier']==0 for r in rows),
    'selected_frontier_leaf_within_1m_of_earlier_trajectory':sum(r['leaf_frontier']==1 and r['earlier_trajectory_distance_m'] is not None and r['earlier_trajectory_distance_m']<=1 for r in rows),
    'latest_selected_path':rows[-1] if rows else None,
    'snapshots':[{'name':p.name,'bytes':p.stat().st_size} for p in folder.glob('native_snapshot_*.vxblx')]}
(folder/'selection_diagnostic_summary.json').write_text(json.dumps(value,indent=2)+'\n')
print(json.dumps(value,indent=2))
