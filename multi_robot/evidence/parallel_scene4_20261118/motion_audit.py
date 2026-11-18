"""Measure actual odometry and protocol events from completed trial logs."""
from pathlib import Path
from collections import Counter,defaultdict
import json,math

root=Path('D:/STGPlanner');work=root/'codex/work/topology_parallel_20261118'
def read_rows(path):
    with path.open(encoding='utf-8') as source:
        for line in source:
            yield json.loads(line)

report={}
for i in range(1,5):
    name=f'topology_parallel_scene4_20261118_{i:02d}_dual'
    trial=root/'benchmarks/results'/name
    if not (trial/'result.json').exists():continue
    result=json.loads((trial/'result.json').read_text())
    started=next((e['runtime_wall_s'] for e in read_rows(trial/'events.jsonl') if e['kind']=='exploration_start'),None)
    ended=started+result['exploration_wall_s'] if started is not None else None
    reasons=Counter();previous={};observed=defaultdict(float);moving=defaultdict(float)
    zero_motion=Counter();max_twist=defaultdict(float);nonrunning=0
    overlap_seen=overlap_moving=overlap_forward=0.;last_sample=None
    first120_seen=first120_forward=first120_moving=0.
    for row in read_rows(trial/'body_trace.jsonl'):
        now=row['received'];robot=row['robot'];b=row['data']
        if started is None or not started<=now<=ended:continue
        v=abs(b['twist'][0]);max_twist[robot]=max(max_twist[robot],v)
        reasons[b['reason']]+=1
        if last_sample is not None and 0<now-last_sample<=.25 and len(previous)==2:
            # Integrate the last known speeds only where both odometry traces
            # are contemporaneous. Timestamp gaps never count as motion.
            if all(0<=now-stamp<=.25 for stamp,_,_ in previous.values()):
                interval=now-last_sample
                early=max(0.,min(now,started+120.)-last_sample)
                overlap_seen+=interval
                first120_seen+=early
                if all(on for _,on,_ in previous.values()):
                    overlap_moving+=interval
                    first120_moving+=early
                if all(forward for _,_,forward in previous.values()):
                    overlap_forward+=interval
                    first120_forward+=early
        last_sample=now
        if robot in previous:
            last,was_moving,_=previous[robot];dt=now-last
            if 0<dt<=.25:
                observed[robot]+=dt;moving[robot]+=dt*was_moving
        previous[robot]=(now,v>.05,b['twist'][0]>.05)
        if abs(b['output'][0])+abs(b['output'][1])>1e-5:
            if b['phase']!='running':nonrunning+=1
            if abs(b['proposal'][0])+abs(b['proposal'][1])<1e-6:zero_motion[b['reason']]+=1
    stop_reasons={}
    for row in read_rows(trial/'allocation_commands.jsonl'):
        command=row['data']
        if command.get('mode')=='STOP':stop_reasons.setdefault(command.get('stop_id'),command.get('reason'))
    metrics=list(read_rows(trial/'metrics.jsonl'));last=metrics[-1]['coordinator'] if metrics else {}
    stale=[m for m in metrics if m.get('coordinator',{}).get('allocation_diagnostics',{}).get('reason')=='stale_source_state']
    phases=Counter()
    for m in metrics:
        phase=m.get('coordinator',{}).get('execution_phases',{})
        if len(phase)==2:phases[str(sum(p=='running' for p in phase.values()))]+=1
    traffic_modes=defaultdict(Counter)
    for row in read_rows(trial/'traffic.jsonl'):
        if started is None or not started<=row['received']<=ended:continue
        for index,mode in enumerate(row['modes'],1):traffic_modes[f'robot_{index}'][mode]+=1
    contacts=result.get('contacts') or {};distances=result.get('distance_m') or {}
    report[name]=dict(covered_wall_s=dict(observed),moving_wall_s=dict(moving),max_abs_odom_v_m_s=dict(max_twist),
        both_moving_wall_s=overlap_moving,both_observed_wall_s=overlap_seen,
        both_moving_fraction=overlap_moving/overlap_seen if overlap_seen else None,
        both_forward_fraction=overlap_forward/overlap_seen if overlap_seen else None,
        first120_both_forward_fraction=first120_forward/first120_seen if first120_seen>=119. else None,
        first120_both_moving_fraction=first120_moving/first120_seen if first120_seen>=119. else None,
        moving_wall_fraction={r:moving[r]/t for r,t in observed.items() if t},
        per_robot_distance_m=distances,body_trace_reason_count=dict(reasons),
        nonrunning_nonzero_samples=nonrunning,zero_proposal_nonzero_output_by_reason=dict(zero_motion),
        stop_nonce_first_reason=dict(Counter(stop_reasons.values())),
        team_observation_certificates=last.get('team_observation_certificates'),
        command_lease_publisher=last.get('command_lease_publisher'),
        authority_service=last.get('authority_service'),
        stale_source_samples=len(stale),
        coordinator_samples_by_number_running=dict(phases),
        traffic_status_samples_by_mode={r:dict(c) for r,c in traffic_modes.items()},
        contacts=dict(transport_alive=contacts.get('transport_alive'),non_ground=contacts.get('robot_non_ground_pairs')))
(work/'MOTION_AUDIT.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))
