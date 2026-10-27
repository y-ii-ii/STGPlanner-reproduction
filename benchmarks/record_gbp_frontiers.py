"""Passive native visualization/path observer. Never issues planning or motion calls."""
from pathlib import Path
import json,threading,time
import rospy
from nav_msgs.msg import Path as NavPath,Odometry
from visualization_msgs.msg import MarkerArray
root=Path('/mnt/d/STGPlanner/benchmarks/results/repair_formal_gbp2_06')
rospy.init_node('gbp_passive_frontier_audit',anonymous=True)
out=(root/'passive_frontier_audit.jsonl').open('a');lock=threading.Lock();pose=None;last_path_wall=0
def write(value):
    value.update(sim=rospy.get_time(),robot=pose)
    with lock:out.write(json.dumps(value)+'\n');out.flush()
def odom(m):
    global pose
    p=m.pose.pose.position;pose=[p.x,p.y,p.z]
def graph(m,topic):
    markers=[]
    for v in m.markers:
        pts=v.points
        region=[[p.x,p.y,p.z] for p in pts if 17<=p.x<=20 and 53<=p.y<=69]
        markers.append({'ns':v.ns,'id':v.id,'type':v.type,'count':len(pts),'connector_points':region[:100],'connector_count':len(region)})
    write({'kind':'native_markers','topic':topic,'markers':markers})
def path(m):
    global last_path_wall
    if time.monotonic()-last_path_wall<1:return
    last_path_wall=time.monotonic()
    stride=max(1,len(m.poses)//100)
    write({'kind':'local_controller_candidate_path','frame':m.header.frame_id,'original_count':len(m.poses),'stride':stride,'points':[[p.pose.position.x,p.pose.position.y,p.pose.position.z] for p in m.poses[::stride]]})
rospy.Subscriber('/base_link/odometry',Odometry,odom,queue_size=1)
rospy.Subscriber('/path',NavPath,path,queue_size=3)
for topic in ['/vis/planning_graph','/vis/planning_global_graph']:
    rospy.Subscriber(topic,MarkerArray,graph,callback_args=topic,queue_size=1)
write({'kind':'observer_start','note':'Read-only visualization/path subscriber attached after run start; connector box used only for diagnostics. The /path topic is a localPlanner candidate in its header frame, not the native global path; early records labelled submitted_controller_path also refer to this local candidate. Subsequent local path records are throttled to1Hz and spatially sampled.'})
while not rospy.is_shutdown() and not (root/'result.json').exists():time.sleep(1)
out.close()
