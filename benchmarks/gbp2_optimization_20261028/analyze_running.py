"""Read-only matched-budget summaries and native decision telemetry."""
import argparse
import json
import re
import statistics
from pathlib import Path
parser=argparse.ArgumentParser();parser.add_argument('trial');args=parser.parse_args()
root=Path('D:/STGPlanner');folder=root/'benchmarks/results'/args.trial
def rows(path):
    result=[]
    if not path.exists():return result
    for line in path.read_text(encoding='utf-8',errors='replace').splitlines():
        try:result.append(json.loads(line))
        except json.JSONDecodeError:pass
    return result
metrics=rows(folder/'metrics.jsonl');events=rows(folder/'events.jsonl')
old=rows(root/'benchmarks/results/repair_formal_gbp2_09/metrics.jsonl')
value={'trial':args.trial,'last_metric':metrics[-1] if metrics else None,'native_homing_events':[r for r in events if r['kind']=='native_homing_ended']}
if metrics:
    matched=[r for r in old if r['sim_s']<=metrics[-1]['sim_s']]
    value['reference09_same_budget']=matched[-1] if matched else None
log=(folder/'native_planner.log').read_text(encoding='utf-8',errors='replace') if (folder/'native_planner.log').exists() else ''
selections=[]
incomplete_selections=0
for line in log.splitlines():
    if 'GBP_DIAGNOSTIC_SELECTED' in line:
        entry={k:float(v) for k,v in re.findall(r'(\w+)=(-?\d+(?:\.\d+)?)',line)}
        if all(key in entry for key in ['path_frontiers','any_frontier','gain']):selections.append(entry)
        else:incomplete_selections+=1
value['local_selected_paths']=len(selections)
value['incomplete_or_interleaved_selection_lines']=incomplete_selections
value['selected_without_valid_frontier']=sum(r.get('path_frontiers',0)<1 for r in selections)
value['telemetry_counts']={pattern:log.count(pattern) for pattern in ['No frontier','global planner','Global planner','Homing','fully explored','Global graph:']}
value['native_global_transitions']=log.count('[GBPLANNER] Very low local gain. Triggering global planner')
value['native_global_targets']=log.count('Found the best frontier to go is:')
tail=[r for r in selections[-50:] if all(k in r for k in ['root_unknown','leaf_unknown'])]
if tail:
    value['tail_native_gain_ratios']={'complete_selection_rows':len(tail),
        'scope':'Native logged weighted gain counts at the tail, not measured new area; cluster gain can be copied from a representative.',
        **{label:{'median':statistics.median(r[key]*.2/5184 for r in tail),
                  'range':[min(r[key]*.2/5184 for r in tail),max(r[key]*.2/5184 for r in tail)],
                  'at_or_above0015':sum(r[key]*.2/5184>=.015 for r in tail)}
            for label,key in [('root','root_unknown'),('leaf','leaf_unknown')]}}
fingerprint=folder/'live_runtime_audit.json'
if fingerprint.exists():
    live=json.loads(fingerprint.read_text(encoding='utf-8'))
    value['actual_frontier_threshold']=live['native_parameters']['SensorParams']['VLP16']['frontier_percentage_threshold']
    value['actual_robot_height']=live['native_parameters']['PlanningParams']['robot_height']
    value['actual_speed_parameters']=live['parameters']
    value['runtime_processes']=len(live['processes'])
out=root/'codex/outputs/gbp2_optimization_20261028'
(out/(args.trial+'_progress.json')).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(value,ensure_ascii=False,indent=2))
