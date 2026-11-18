from pathlib import Path
import json,collections
R=Path('D:/STGPlanner/benchmarks/results');W=Path('D:/STGPlanner/codex/work/topology_liveness_20261117');answer={}
for i in range(1,5):
 p=R/('topology_liveness_scene4_20261117_%02d_dual'%i)
 if not (p/'result.json').exists():continue
 rows=[json.loads(l) for l in (p/'metrics.jsonl').open()];modes=collections.Counter();fault=collections.Counter();stale=0;max_pending=0;max_depth=0;max_age={};retry={};services={};stopcounts={}
 for v in rows:
  c=v.get('coordinator',{});d=c.get('allocation_diagnostics',{});modes[d.get('reason','?')]+=1
  if d.get('reason')=='stale_source_state':
   stale+=1
   for k,a in d.get('state_age_s',{}).items():
    if a is not None:max_age[k]=max(max_age.get(k,0),a)
  for k,phase in c.get('execution_phases',{}).items():
   if phase=='fault':fault[k]+=1
  q=c.get('authority_inbox',{});max_pending=max(max_pending,q.get('topology_pending',0));max_depth=max(max_depth,q.get('max_depth',0))
  for k,a in c.get('stop_retry_counts',{}).items():retry[k]=max(retry.get(k,0),a)
  for k,a in c.get('authority_service',{}).items():services[k]=max(services.get(k,0),a)
  stopcounts=c.get('feedback_ack_audit',stopcounts)
 answer[p.name]=dict(metrics_samples=len(rows),allocation_reason_sample_counts=dict(modes),fault_phase_sample_counts=dict(fault),stale_source_state_samples=stale,max_stale_source_age_s=max_age,max_topology_pending_packets=max_pending,max_total_inbox_depth=max_depth,max_stop_retry_counts=retry,service_maxima=services,last_ack_audit=stopcounts)
(W/'AUTHORITY_AUDIT.json').write_text(json.dumps(answer,indent=2),encoding='utf-8');print(json.dumps(answer,indent=1))
