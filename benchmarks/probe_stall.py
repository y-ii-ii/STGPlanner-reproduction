import rospy,json,time
from nav_msgs.msg import Odometry,Path
from geometry_msgs.msg import PointStamped,Twist
from control_planner_interface.msg import ExplorerPlannerActionResult
rospy.init_node('probe_scene4_stall',anonymous=True)
out={}
for name,typ in [('/base_link/odometry',Odometry),('/path_execution_node/look_ahead_goal',PointStamped),('/cmd_vel',Twist),('/path_execution_node/executed_path',Path),('/path',Path),('/topo_planner_node/topo_planner/result',ExplorerPlannerActionResult)]:
    try:
        m=rospy.wait_for_message(name,typ,timeout=3)
        if isinstance(m,Odometry):out[name]={'pose':str(m.pose.pose),'twist':str(m.twist.twist)}
        elif isinstance(m,PointStamped):out[name]=str(m)
        elif isinstance(m,Twist):out[name]=str(m)
        elif isinstance(m,Path):out[name]={'frame':m.header.frame_id,'size':len(m.poses),'points':[[p.pose.position.x,p.pose.position.y,p.pose.position.z] for p in m.poses[:15]],'last':str(m.poses[-1].pose) if m.poses else None}
        else:out[name]={'status':m.status.status,'segments':[[[p.position.x,p.position.y,p.position.z] for p in segment.path[:20]] for segment in m.result.paths[:5]]}
    except Exception as e:out[name]={'error':str(e)}
print(json.dumps(out,indent=2),flush=True)
open('/mnt/d/STGPlanner/benchmarks/logs/fael_stall_probe.json','w').write(json.dumps(out,indent=2))
