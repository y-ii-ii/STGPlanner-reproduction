"""Audit reported completed-task support against the authority completion mask.

Reads recorded JSON and frozen pure graph code only. No map/ROS replay and no
counterfactual mask is applied to any run. This diagnoses unused summaries;
it does not prove an improved allocation result.
"""
from pathlib import Path
import json,sys
sys.dont_write_bytecode=True
R=Path('D:/STGPlanner');W=R/'codex/work/topology_liveness_20261117';sys.path.insert(0,str(W/'trial04_source/team_topology/src'))
from team_topology.graph import GraphStore
from team_topology.scope import unknown_support
answer={}
for i in range(1,5):
 p=R/('benchmarks/results/topology_liveness_scene4_20261117_%02d_dual'%i);file=p/'topology_deltas.jsonl'
 if not file.exists():continue
 full={}
 for line in file.open():
  if '"full": true' not in line and '"full":true' not in line:continue
  try:v=json.loads(line)
  except ValueError:continue
  if v.get('full'):full[v['author']]=v
 store=GraphStore()
 for v in sorted(full.values(),key=lambda v:v['state']['stamp']):assert store.apply(v)
 tasks=[v for v in store.live('task').values() if v['state']=='completed' and v.get('observation')=='all_previous_unknown_observed']
 cells=set().union(*(unknown_support([v['scope']]) for v in tasks)) if tasks else set()
 last=json.loads((p/'status.json').read_text())['coordinator'];mask=last.get('observed_completion_cells',0)
 answer[p.name]=dict(completed=(p/'result.json').exists(),last_full_seq_by_author={k:v['seq'] for k,v in full.items()},reported_observation_completed_tasks=len(tasks),reported_completed_support_union_cells=len(cells),authority_assignee_completion_mask_cells=mask,unused_reported_support_lower_bound_cells=max(0,len(cells)-mask),note='Cardinality lower bound only; last-full snapshots may precede final status. Does not mark unknown free or change ownership/STOP.')
(W/'AUTHOR_OBSERVATION_AUDIT.json').write_text(json.dumps(answer,indent=2),encoding='utf-8');print(json.dumps(answer,indent=1))
