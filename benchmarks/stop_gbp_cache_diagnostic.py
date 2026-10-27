"""Preserve the cache-only attempt and ask its native launch to exit cleanly."""
from pathlib import Path
import argparse,datetime,json,os,signal,rospy
from visualization_msgs.msg import MarkerArray
p=argparse.ArgumentParser();p.add_argument('--trial',default='repair_formal_gbp2_01');p.add_argument('--reason',default='Cache-only repair still plateaued; sensor height requires calibration.');a=p.parse_args()
root=Path('/mnt/d/STGPlanner/benchmarks');trial=root/'results'/a.trial
if trial.parent.resolve()!=(root/'results').resolve():raise RuntimeError('Invalid trial path')
rospy.init_node('capture_gbp_projection_diagnostic',anonymous=True)
events=[json.loads(l) for l in (trial/'events.jsonl').read_text().splitlines() if l.strip()]
native_end=next((x for x in events if x['kind']=='native_homing_ended'),None)
try:
    message=rospy.wait_for_message('/vis/planning_graph',MarkerArray,timeout=2 if native_end else 25)
    points=[{'x':p.x,'y':p.y,'z':p.z} for m in message.markers for p in m.points]
except rospy.ROSException:
    points=[]
note={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'classification':'intermediate_repair_diagnostic','intentional_native_stop':True,'reason':a.reason,'graph_point_count':len(points),'graph_z_range':[min(p['z'] for p in points),max(p['z'] for p in points)] if points else None,'sample_graph_points':points[:30]}
note['native_homing_end_observed_before_manual_stop']=native_end
(trial/'interruption.json').write_text(json.dumps(note,indent=2))
(trial/'native_source_manifest.json').write_bytes((root/'progress_repairs/manifest.json').read_bytes())
target='/mnt/d/STGPlanner/benchmarks/config/gbp2.launch';pids=[]
for p in Path('/proc').iterdir():
    if not p.name.isdigit():continue
    try:args=(p/'cmdline').read_bytes().split(b'\0')
    except OSError:continue
    if any(x.decode(errors='replace')==target for x in args) and any(b'roslaunch' in x for x in args):pids.append(int(p.name))
if len(pids)!=1:raise RuntimeError('Expected one native roslaunch, found '+str(pids))
os.kill(pids[0],signal.SIGINT)
print(json.dumps({'stopped_native_launch':pids[0],'graph_z_range':note['graph_z_range'],'classification':note['classification']}))
