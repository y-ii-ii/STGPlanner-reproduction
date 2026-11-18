from pathlib import Path
import sys,json,importlib.util
sys.path.insert(0,'/mnt/d/STGPlanner/codex/worktrees/multi-robot-topology/multi_robot/team_topology/src')
from team_topology.graph import GraphStore
old=Path('/mnt/d/STGPlanner/codex/work/topology_dispatch_20261117/trial04_source/team_topology/src/team_topology/graph.py')
spec=importlib.util.spec_from_file_location('historical_graph',old);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
p=Path('/mnt/d/STGPlanner/benchmarks/results/topology_dispatch_scene4_20261117_04_dual/topology_deltas.jsonl')
with p.open('rb') as f:
 f.seek(max(0,p.stat().st_size-8*1024*1024));f.readline();data=[json.loads(l) for l in f]
first={}
for i,d in enumerate(data):
 if d.get('full'):first.setdefault(d['author'],i)
assert len(first)==2
stores=[module.GraphStore(),GraphStore()];counts={'accepted':0,'rejected':0};checked=0
for d in data[min(first.values()):]:
 outcomes=[]
 for store in stores:
  try:outcomes.append(('ok',store.apply(d)))
  except (ValueError,KeyError,TypeError) as e:outcomes.append((type(e).__name__,str(e)))
 assert outcomes[0]==outcomes[1],outcomes
 assert stores[0].digest()==stores[1].digest()
 assert stores[0].states==stores[1].states
 counts['accepted' if outcomes[0][0]=='ok' else 'rejected']+=1;checked+=1
v=dict(no_ros_or_physics=True,packets_checked=checked,**counts,records=len(stores[0].records),digest=stores[0].digest(),all_outcomes_states_and_record_digests_equal=True)
Path('/mnt/d/STGPlanner/codex/work/topology_liveness_20261117/STREAM_DIFFERENTIAL.json').write_text(json.dumps(v,indent=2));print(json.dumps(v))
