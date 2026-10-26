import rospy,json,math
from sensor_msgs.msg import PointCloud2
from gazebo_msgs.msg import ModelStates
from gazebo_msgs.srv import GetLinkState
import sensor_msgs.point_cloud2 as pc
rospy.init_node('probe_scene4_obstacles',anonymous=True)
out={}
models=rospy.wait_for_message('/gazebo/model_states',ModelStates,timeout=5)
out['near_models']=[{'name':n,'pose':str(p)} for n,p in zip(models.name,models.pose) if n=='jackal' or (abs(p.position.x-45.945)<15 and abs(p.position.y-67.065)<15)]
srv=rospy.ServiceProxy('/gazebo/get_link_state',GetLinkState)
for name in ['30m_0.4_clone_0::Wall_44','30m_0.4_clone_0_clone::Wall_44','jackal::base_link']:
    try:out[name]=str(srv(name,'world'))
    except Exception as e:out[name]=str(e)
for name in ['/registered_point_cloud','/terrain_map']:
    m=rospy.wait_for_message(name,PointCloud2,timeout=5)
    points=[p for p in pc.read_points(m,field_names=('x','y','z','intensity'),skip_nans=True) if abs(p[0]-45.945)<2 and 66.9<p[1]<68.2]
    out[name]={'frame':m.header.frame_id,'points_near_wall':len(points),'xyz_intensity_sample':points[:15]}
print(json.dumps(out,indent=2))
open('/mnt/d/STGPlanner/benchmarks/logs/fael_obstacles_probe.json','w').write(json.dumps(out,indent=2))
