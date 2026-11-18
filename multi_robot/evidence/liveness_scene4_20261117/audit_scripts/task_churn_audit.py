"""Recorded dispatch/STOP diagnostic; overlap alone never proves task identity.

No task is merged/reassigned and no ROS/node is started by this audit.
"""
from pathlib import Path
import json,sys,collections,math
sys.dont_write_bytecode=True
R=Path('D:/STGPlanner');W=R/'codex/work/topology_liveness_20261117';sys.path.insert(0,str(W/'trial04_source/team_topology/src'))
from team_topology.scope import unknown_support
from team_topology.retry_memory import ingress
answer={}
for i in range(1,5):
 p=R/('benchmarks/results/topology_liveness_scene4_20261117_%02d_dual'%i);file=p/'allocation_commands.jsonl'
 if not file.exists():continue
 seen=set();stops={};previous={};counts=collections.Counter();examples=[];cache={}
 for line in file.open():
  try:v=json.loads(line)
  except ValueError:continue
  r=v['robot'];d=v['data']
  if d['mode']=='STOP':stops.setdefault((r,d['stop_id']),d.get('reason'));continue
  key=(r,d['version'],d['dispatch_id'])
  if key in seen:continue
  seen.add(key);old=previous.get(r)
  if old:
   changed=old['task']!=d['task'];counts['task_id_changes']+=int(changed)
   def support(c):
    digest=c['scope_digest']
    if digest not in cache:cache[digest]=unknown_support(c.get('scopes',[]))
    return cache[digest]
   a,b=support(old),support(d);overlap=len(a&b)/max(1,min(len(a),len(b)))
   x,y=ingress(old.get('path',[])),ingress(d.get('path',[]))
   same=bool(x and y and math.dist(x[0],y[0])<.75 and x[1] and y[1] and sum(a*b for a,b in zip(x[1],y[1]))>.7)
   if changed and overlap>=.5:counts['changed_id_support_overlap_ge_half']+=1
   if changed and overlap>=.5 and same:
    counts['changed_id_overlap_ge_half_same_ingress']+=1
    if len(examples)<6:examples.append(dict(robot=r,received=v['received'],previous_task=old['task'],task=d['task'],overlap_coefficient=overlap,previous_origin=x[0],origin=y[0]))
  previous[r]=d
 reasons=collections.Counter(stops.values());answer[p.name]=dict(completed=(p/'result.json').exists(),actual_route_dispatches=len(seen),unique_stop_nonces=len(stops),stop_nonce_first_reason=dict(reasons),consecutive_dispatch_diagnostics=dict(counts),examples=examples,note='Diagnostic only: shared unknown support/entrance is not proof of equal free-space connectivity. Do not merge across a wall without validation.')
(W/'TASK_CHURN_AUDIT.json').write_text(json.dumps(answer,indent=2),encoding='utf-8');print(json.dumps({k:{x:y for x,y in v.items() if x not in ('examples','note')} for k,v in answer.items()},indent=1))
