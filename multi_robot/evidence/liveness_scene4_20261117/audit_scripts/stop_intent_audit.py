"""Read-only acceptance: stale PASS can revive a current zero proposal.

Imports frozen trial04 pure Python, never a ROS node/map replay; does not repair
the algorithm after the final attempt was reserved. Observed traffic status is
an audit association, not the exact per-gate permit delivery timestamp.
"""
from pathlib import Path
from types import SimpleNamespace
import sys,json,collections,bisect
sys.dont_write_bytecode=True
R=Path('D:/STGPlanner');W=R/'codex/work/topology_liveness_20261117'
sys.path.insert(0,str(W/'trial04_source/team_topology/src'))
from team_topology.traffic import TrafficGuard
guard=TrafficGuard(1);guard.received=1.;guard.permit=dict(token='same_dispatch',mode='PASS',velocity=[1.,0.])
out,_=guard.filter(SimpleNamespace(phase='running',active_token='same_dispatch',armed_at=0.),(0.,0.),1.1,100.)
assert out==(1.,0.)
evidence=dict(no_ros_or_physics=True,algorithm_changed=False,pure_counterexample=dict(current_proposal=[0.,0.],fresh_same_token_PASS=[1.,0.],filter_output=list(out)),trials={})
def rows(p):
 if not p.exists():return
 for line in p.open(encoding='utf-8'):
  try:yield json.loads(line)
  except ValueError:pass
for i in range(1,5):
 p=R/('benchmarks/results/topology_liveness_scene4_20261117_%02d_dual'%i)
 if not (p/'body_trace.jsonl').exists():continue
 traffic=list(rows(p/'traffic.jsonl'));traffic.sort(key=lambda v:v['received']);times=[v['received'] for v in traffic];counts=collections.Counter();examples=[]
 for v in rows(p/'body_trace.jsonl'):
  d=v['data']
  if d.get('phase')!='running' or sum(map(abs,d.get('proposal',[0,0])))>1e-10 or sum(map(abs,d.get('output',[0,0])))<=1e-5:continue
  k=bisect.bisect_right(times,v['received'])-1;r=int(v['robot'].split('_')[-1])-1
  t=traffic[k] if k>=0 else {};mode=t.get('modes',['unknown','unknown'])[r];age=v['received']-t.get('received',-1e9)
  observed=mode if age<=.15 else 'unassociated';counts[(v['robot'],d['reason'],observed)]+=1
  if observed=='PASS' and d['reason'] in ('BRAKE_BEFORE_TURN','SETTLE_BEFORE_TRANSLATION') and len(examples)<4:examples.append(dict(body=v,last_observed_traffic=t,status_age_s=age))
 evidence['trials'][p.name]=dict(completed=(p/'result.json').exists(),zero_proposal_nonzero_output_samples=[dict(robot=k[0],reason=k[1],last_observed_traffic_mode=k[2],samples=n) for k,n in sorted(counts.items())],guard_PASS_examples=examples)
(W/'STOP_INTENT_AUDIT.json').write_text(json.dumps(evidence,indent=2),encoding='utf-8')
print(json.dumps(dict(counterexample=evidence['pure_counterexample'],trials={k:sum(x['samples'] for x in v['zero_proposal_nonzero_output_samples'] if x['last_observed_traffic_mode']=='PASS') for k,v in evidence['trials'].items()})))
