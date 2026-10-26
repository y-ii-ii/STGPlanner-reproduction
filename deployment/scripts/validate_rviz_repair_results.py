#!/usr/bin/env python3
import json
from pathlib import Path
base=Path('/mnt/d/STGPlanner/logs/rviz_repair')
history=[json.loads(line) for line in (base/'status_after.history.jsonl').read_text().splitlines() if line.strip()]
recent=history[-10:]
statuses={}
for name in ('RobotModel','topo_map','grid_map'):
    statuses[name]=len(recent)==10 and all(
        snap['displays'].get(name,{}).get('enabled') and
        snap['displays'][name]['status'] and
        all(s['name']=='Status: Ok' for s in snap['displays'][name]['status'])
        for snap in recent)
markers=json.loads((base/'markers_after.json').read_text())
tf=json.loads((base/'tf_after.json').read_text())
runtime=json.loads((base/'runtime_after.json').read_text())
model=json.loads((base/'model_validation.json').read_text())
checks={'enabled_displays_stable_ok':all(statuses.values()),
        'status_stable_seconds':len(recent)==10 and recent[-1]['unix_time']-recent[0]['unix_time']>=15,
        'all_robot_links_have_tf':tf['passed'],
        'sensor_link_retained_in_gazebo':all(model.values()),
        'motion_planning_regression':runtime['passed']}
for name,s in markers['topics'].items():
    checks[name+'_real_messages']=s['messages']>=10 and s['nonempty_add']>0
    checks[name+'_no_invalid_add']=s['empty_add']==0 and s['invalid_floats']==0 and s['odd_line_lists']==0
    checks[name+'_empty_categories_cleared']=s['delete']>0
result={'passed':all(checks.values()),'checks':checks,'rviz_status_ok':statuses,
        'stable_samples':len(recent),'stable_seconds':recent[-1]['unix_time']-recent[0]['unix_time'],
        'last_rviz_status':recent[-1],'markers':markers['topics'],
        'robot_link_count':len(tf['robot_links']),
        'runtime_seconds':runtime['wall_seconds'],'distance_m':runtime['odometry_distance_m'],
        'successful_nonempty_plans':runtime['successful_nonempty_plans']}
(base/'verification_summary.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
raise SystemExit(0 if result['passed'] else 1)
