from pathlib import Path
import json,collections,sys
W=Path('D:/STGPlanner/codex/work/topology_liveness_20261117');p=Path('D:/STGPlanner/benchmarks/results/topology_liveness_scene4_20261117_%02d_dual'%int(sys.argv[1]));groups={}
for line in (p/'allocation_commands.jsonl').open():
 v=json.loads(line);d=v['data']
 if d.get('mode')!='ROUTE':continue
 key=(v['robot'],d['task'],d['version'],d['dispatch_id']);g=groups.setdefault(key,dict(digests=set(),counts=set(),begin=v['received'],end=v['received']))
 g['digests'].add(d.get('scope_digest'));g['counts'].add(d.get('scope_cells'));g['end']=v['received']
out=[dict(robot=k[0],task=k[1],version=k[2],dispatch_id=k[3],distinct_scope_digests=len(v['digests']),scope_cell_counts=sorted(v['counts']),duration_wall_s=v['end']-v['begin']) for k,v in groups.items() if len(v['digests'])>1]
result=dict(trial=p.name,route_dispatches=len(groups),mutating_scope_dispatches=len(out),examples=sorted(out,key=lambda d:d['distinct_scope_digests'],reverse=True)[:15])
(W/('SCOPE_MUTATION_%02d.json'%int(sys.argv[1]))).write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
