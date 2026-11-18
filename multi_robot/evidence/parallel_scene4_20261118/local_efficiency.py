"""Measure execution interruption and candidate conflicts from saved trial logs."""
from bisect import bisect_right
from collections import Counter
import json
from pathlib import Path
import sys

root = Path('D:/STGPlanner')
work = root / 'codex/work/topology_parallel_20261118'


def rows(path, name):
    with (path / f'{name}.jsonl').open(encoding='utf-8') as stream:
        for line in stream:
            if line.endswith('\n'):
                yield json.loads(line)


def analyze(path):
    start = next(row['runtime_wall_s'] for row in rows(path,'events')
                 if row['kind']=='exploration_start')
    traffic = list(rows(path,'traffic'))
    stamps = [row['received'] for row in traffic]
    windows = {'overall': Counter(), 'first120': Counter(), 'from260': Counter()}
    continuation=Counter()
    waiting={}
    for row in rows(path,'body_trace'):
        wall = row['received'] - start
        if wall < 0:
            continue
        body = row['data']
        i = int(row['robot'][-1])-1
        keys = [body['reason']]
        if body['reason']=='PREFIX_CONTINUATION_WAIT':
            if i not in waiting:
                waiting[i]=body['token'],row['received']
                continuation['wait_episodes']+=1
            if any(abs(v)>1e-6 for v in body['output']):
                continuation['nonzero_during_wait']+=1
        elif i in waiting:
            token,when=waiting[i]
            if body['token']!=token or body['phase']!='running':
                continuation['released_without_same_dispatch_motion']+=1
                del waiting[i]
            elif any(abs(v)>1e-6 for v in body['output']):
                continuation['same_dispatch_resumes']+=1
                continuation['max_wall_s_until_same_dispatch_motion']=max(
                    continuation['max_wall_s_until_same_dispatch_motion'],row['received']-when)
                del waiting[i]
        if body['phase']=='running':
            keys.append('running_samples')
            v, w = body['proposal']
            j = bisect_right(stamps,row['received'])-1
            if j>=0 and row['received']-stamps[j]<=.15:
                record=traffic[j]
                if record['phase']=='FREE' and record['modes'][i]=='PASS' and abs(v)>.05:
                    keys.append('free_translation_requested')
                    if abs(body['output'][0])<=.05:
                        keys.append('free_translation_below_gate')
                        _, angular_approval=record['velocity'][i]
                        if 1e-6<abs(angular_approval)<=.03 and (abs(w)<1e-6 or angular_approval*w<0):
                            keys.append('free_translation_denied_with_small_angular_mismatch')
        windows['overall'].update(keys)
        if wall<=120.:windows['first120'].update(keys)
        if wall>=260.:windows['from260'].update(keys)
    epochs = {record['epoch'] for record in traffic
              if record['received']>=start and record['phase']=='BRAKE'}
    early = [row for row in traffic if start<=row['received']<=start+120.]
    modes = Counter(row['phase'] for row in early)
    held, excluded = Counter(), Counter()
    prestart_retries={}
    for row in rows(path,'metrics'):
        coordinator=row['coordinator']
        held.update(r for r,peers in coordinator.get('execution_blocked_by',{}).items() if peers)
        excluded.update({r:int(n>0) for r,n in coordinator.get('allocation_diagnostics',{})
                         .get('excluded_peer_contract_candidates',{}).items()})
        for robot,failures in coordinator.get('execution_retry_memory',{}).items():
            for entry in failures:
                if entry.get('before_execution'):
                    prestart_retries[robot,entry['last']]=round(entry['until']-entry['last'],3)
    retreats, after_motion, previous = 0, 0, None
    for row in traffic:
        if row['received']>=start and previous and row['phase']=='RETREAT' and previous['phase']!='RETREAT':
            retreats+=1
            if (row['epoch']==previous['epoch'] and 0<=row['received']-previous['received']<=.2
                    and any(abs(v)>.05 for v in previous['velocity'][row['winner']])):
                after_motion+=1
        previous=row
    rejected=Counter(row.get('mode','unknown') for row in rows(path,'plans')
                     if row.get('status')=='EXECUTOR_REJECTED')
    return dict(staged_brake_epochs=len(epochs), first120_traffic_modes=dict(modes),
                first120_brake_epochs=len({row['epoch'] for row in early if row['phase']=='BRAKE'}),
                held_by_other_work_samples=dict(held), conflicting_bid_exclusion_samples=dict(excluded),
                retreat_episodes=retreats, retreat_episodes_after_previous_motion=after_motion,
                executor_rejections_by_mode=dict(rejected),segment_continuation=dict(continuation),
                pre_certificate_retry_delay_samples=dict(Counter(prestart_retries.values())),
                by_window={name:dict(counts) for name,counts in windows.items()})


data={}
for i in range(1,5):
    trial=root/'benchmarks/results'/f'topology_parallel_scene4_20261118_{i:02d}_dual'
    if (trial/'result.json').exists() and any(row['kind']=='exploration_start' for row in rows(trial,'events')):
        data[trial.name]=analyze(trial)
if len(sys.argv)>1:
    trial=root/'benchmarks/results'/f'topology_parallel_scene4_20261118_{int(sys.argv[1]):02d}_dual'
    data[trial.name]=analyze(trial)
else:
    (work/'LOCAL_EFFICIENCY.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
print(json.dumps(data,indent=2))
