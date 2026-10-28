"""One passive odometry/frame snapshot; no planner or motion service calls."""
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
import rospy
from nav_msgs.msg import Odometry
from sensor_msgs.msg import PointCloud2

folder=Path(sys.argv[1]);assert folder.is_dir()
target=folder/'sensor_frame_snapshot.json';assert not target.exists()
rospy.init_node('gbp2_sensor_frame_audit',anonymous=True,disable_signals=True)
value={'read_only':True,'odometry':{}}
for topic in ['/sensor_to_world/odometry','/base_link/odometry','/jackal/velodyne/gazebo_gt/odometry']:
    try:
        message=rospy.wait_for_message(topic,Odometry,timeout=8)
        p=message.pose.pose.position;q=message.pose.pose.orientation
        value['odometry'][topic]={'frame':message.header.frame_id,'child':message.child_frame_id,
          'stamp':message.header.stamp.to_sec(),'position':[p.x,p.y,p.z],'orientation':[q.x,q.y,q.z,q.w]}
    except Exception as error:value['odometry'][topic]={'error':str(error)}
cloud=rospy.wait_for_message('/jackal/velodyne/velodyne_points',PointCloud2,timeout=8)
value['cloud_frame']=cloud.header.frame_id
for name in rospy.get_param_names():
    if name.endswith('robot_description'):
        description=rospy.get_param(name)
        tree=ET.fromstring(description)
        joints=[]
        for joint in tree.findall('joint'):
            if any(term in str(ET.tostring(joint)) for term in ['velodyne','lidar','laser']):
                joints.append(ET.tostring(joint,encoding='unicode'))
        value['robot_description_parameter']=name;value['sensor_joints']=joints
target.write_text(json.dumps(value,indent=2)+'\n')
print(json.dumps(value,indent=2))
