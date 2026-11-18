from pathlib import Path
import json,collections
R=Path('D:/STGPlanner');W=R/'codex/work/topology_liveness_20261117';audit={}
def rows(p):
 if not p.exists():return
 for line in p.open(encoding='utf-8'):
  try:yield json.loads(line)
  except ValueError:pass
for i in range(1,5):
 p=R/('benchmarks/results/topology_liveness_scene4_20261117_%02d_dual'%i)
 if not (p/'result.json').exists():continue
 selection=collections.Counter();methods=collections.Counter();reject=collections.Counter();examples={};native_states=collections.Counter()
 for v in rows(p/'plans.jsonl'):
  if v.get('source')=='planner':
   selection[(v.get('selection'),v.get('status'))]+=1
   if v.get('body_route_method'):methods[(v.get('body_route_method'),v.get('status'))]+=1
  for state in v.get('native_states',[]):native_states[str(state)]+=1
  if v.get('status')!='EXECUTOR_REJECTED':continue
  same=v.get('goal_token')==v.get('current_token');pending=v.get('stop_pending') in ('true',True)
  ahead=int(v.get('goal_command_seq',0))>int(v.get('current_command_seq',0))
  label='same_token_goal_ahead_without_stop' if same and ahead and not pending else 'stop_pending' if pending else 'other'
  reject[label]+=1;examples[label]=v
 dispatches={r:set() for r in ('robot_1','robot_2')};tasks={r:set() for r in dispatches};nonces={r:set() for r in dispatches}
 for v in rows(p/'allocation_commands.jsonl'):
  r=v['robot'];d=v['data']
  if d.get('mode')=='ROUTE':dispatches[r].add((d.get('version'),d.get('dispatch_id')));tasks[r].add(d.get('task'))
  if d.get('stop_id'):nonces[r].add(d['stop_id'])
 metrics=list(rows(p/'metrics.jsonl'));last=metrics[-1].get('coordinator',{}) if metrics else {}
 crashes=[]
 for name in ('stack.log','execution.log','exploration.log'):
  file=p/name
  if file.exists():
   for line in file.read_text(errors='replace').splitlines():
    if ('exit code -11' in line or 'SIGSEGV' in line or 'Fatal native' in line):crashes.append(dict(file=name,line=line))
 audit[p.name]=dict(selection_feedback=[dict(selection=k[0],status=k[1],messages=v) for k,v in sorted(selection.items(),key=lambda x:str(x[0]))],body_route_methods=[dict(method=k[0],status=k[1],messages=v) for k,v in sorted(methods.items())],native_state_visits=dict(native_states),execution_rejection_categories=dict(reject),last_execution_rejection_examples=examples,distinct_route_dispatches={k:len(v) for k,v in dispatches.items()},distinct_route_tasks={k:len(v) for k,v in tasks.items()},distinct_stop_nonces={k:len(v) for k,v in nonces.items()},last_retry_memory=last.get('execution_retry_memory'),last_completion_cells=last.get('observed_completion_cells'),last_ledger_state_counts=last.get('ledger_state_counts'),native_crash_lines=crashes)
(W/'LIVENESS_AUDIT.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:{x:y for x,y in v.items() if x not in ('last_execution_rejection_examples','last_retry_memory')} for k,v in audit.items()},ensure_ascii=False,indent=2))
