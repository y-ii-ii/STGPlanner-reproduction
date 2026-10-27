"""Preserve the cache-only attempt and ask its native launch to exit cleanly."""
from pathlib import Path
import datetime,json,os,signal,rospy
from visualization_msgs.msg import MarkerArray
root=Path('/mnt/d/STGPlanner/benchmarks');trial=root/'results/repair_formal_gbp2_01'
rospy.init_node('capture_gbp_projection_diagnostic',anonymous=True)
message=rospy.wait_for_message('/vis/planning_graph',MarkerArray,timeout=25)
points=[{'x':p.x,'y':p.y,'z':p.z} for m in message.markers for p in m.points]
note={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'classification':'intermediate_cache_only_diagnostic','intentional_native_stop':True,'reason':'Coverage plateau returned after ray-cache repair. Native gain uses projected graph height 0.7m instead of physical lidar height 0.456m. Preserve this attempt and recalibrate before a new full run.','graph_point_count':len(points),'graph_z_range':[min(p['z'] for p in points),max(p['z'] for p in points)] if points else None,'sample_graph_points':points[:30]}
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
