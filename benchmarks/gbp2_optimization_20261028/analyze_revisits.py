"""Post-hoc pose revisits and subsequent area growth; never used by planning."""
import bisect
import json
import math
import re
from pathlib import Path
root=Path('D:/STGPlanner');out=root/'codex/outputs/gbp2_optimization_20261028'
catalog=json.loads(Path(__file__).with_name('trial_catalog.json').read_text(encoding='utf-8'))
names=['repair_formal_gbp2_09']+[r['trial'] for r in catalog]
radius=1.;history_lag=60.;future_horizon=100.
records={}
def segment_distance(x,y,a,b):
    dx=b['x']-a['x'];dy=b['y']-a['y'];length2=dx*dx+dy*dy
    ratio=max(0.,min(1.,((x-a['x'])*dx+(y-a['y'])*dy)/length2)) if length2 else 0.
    return math.hypot(x-a['x']-ratio*dx,y-a['y']-ratio*dy)
for name in names:
    folder=root/'benchmarks/results'/name
    if not (folder/'result.json').exists():continue
    result=json.loads((folder/'result.json').read_text(encoding='utf-8'))
    rows=[json.loads(line) for line in (folder/'metrics.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
    events=[json.loads(line) for line in (folder/'events.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
    start=next(r['sim'] for r in events if r['kind']=='exploration_start')
    times=[r['sim_s'] for r in rows]
    log=(folder/'native_planner.log').read_text(encoding='utf-8',errors='replace')
    cut=result['sim_time_s'];selected=[]
    for line in log.splitlines():
        if 'Calling HOMING instead' in line:
            stamps=re.findall(r'\[[\d.]+,\s*([\d.]+)\]:',line)
            if stamps and float(stamps[-1])-start>=0:cut=min(cut,float(stamps[-1])-start)
        hit=re.search(r'\[INFO\]\s*\[[\d.]+,\s*([\d.]+)\]:\s*GBP_DIAGNOSTIC_SELECTED',line)
        if hit:
            entry={k:float(v) for k,v in re.findall(r'(\w+)=(-?\d+(?:\.\d+)?)',line)}
            if all(k in entry for k in ['root_x','root_y','leaf_x','leaf_y','path_frontiers','gain']):
                entry['t']=float(hit[1])-start;selected.append(entry)
    def enrich(t,x,y):
        if t<history_lag or t>=cut:return None
        stop=bisect.bisect_right(times,t-history_lag)
        if stop<2:return None
        distance=min(segment_distance(x,y,a,b) for a,b in zip(rows[:stop-1],rows[1:stop]))
        at=max(0,bisect.bisect_right(times,t)-1)
        future=bisect.bisect_left(times,t+future_horizon)
        delta=rows[future]['area_m2']-rows[at]['area_m2'] if future<len(rows) and t+future_horizon<=cut else None
        return {'t':t,'distance_to_old_trajectory_m':distance,'revisit':distance<=radius,
                'following100s_area_gain_m2':delta,'stagnant100s':delta<1 if delta is not None else None}
    cases=[];root_fit=[]
    for entry in selected:
        if not 0<=entry['t']<cut:continue
        index=min(range(max(0,bisect.bisect_left(times,entry['t'])-1),min(len(rows),bisect.bisect_left(times,entry['t'])+2)),
                  key=lambda i:abs(times[i]-entry['t']))
        root_fit.append(math.hypot(entry['root_x']-rows[index]['x'],entry['root_y']-rows[index]['y']))
        enriched=enrich(entry['t'],entry['leaf_x'],entry['leaf_y'])
        if enriched:cases.append(enriched)
    def summarize(items):
        complete=[r for r in items if r['stagnant100s'] is not None]
        return {'queries':len(items),'near_old_trajectory':sum(r['revisit'] for r in items),
                'near_old_fraction':sum(r['revisit'] for r in items)/len(items) if items else None,
                'complete100s_windows':len(complete),'stagnant100s_windows':sum(r['stagnant100s'] for r in complete),
                'revisit_and_stagnant100s':sum(r['revisit'] and r['stagnant100s'] for r in complete)}
    value={'before_homing_command_s':cut,'native_selected_leaf':summarize(cases),
           'native_selected_leaf_after1000s':summarize([r for r in cases if r['t']>=1000]),
           'root_pose_time_alignment_median_m':sorted(root_fit)[len(root_fit)//2] if root_fit else None}
    if (folder/'passive_actions.jsonl').exists():
        goals=[json.loads(line) for line in (folder/'passive_actions.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
        actual=[]
        for item in goals:
            if item['kind']=='goal' and item['end'] is not None:
                enriched=enrich(item['sim']-start,*item['end'][:2])
                if enriched:actual.append(enriched)
        value['recorded_action_endpoints']=summarize(actual)
    records[name]=value
value={'revisit_radius_m':radius,'history_lag_s':history_lag,'area_horizon_s':future_horizon,'records':records,
       'scope':'Offline association only. Chosen native leaf is not necessarily the truncated executed action endpoint. Legitimate global backtracking can revisit old poses. A near-old pose does not prove previously complete sensor visibility. Homing return and post-native-end hold excluded; area growth never fed back into the planner. No historical native map/gain reconstruction.'}
(out/'revisit_diagnostics.json').write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(value,indent=2))
