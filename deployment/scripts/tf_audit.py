#!/usr/bin/env python3
import json,time,xml.etree.ElementTree as ET
from pathlib import Path
import rospy,tf2_ros
rospy.init_node('stgplanner_tf_audit',anonymous=True)
buffer=tf2_ros.Buffer()
listener=tf2_ros.TransformListener(buffer)
time.sleep(5)
robot=ET.fromstring(rospy.get_param('/robot_description'))
links=[link.get('name') for link in robot.findall('link')]
missing=[link for link in links if not buffer.can_transform('world',link,rospy.Time(0),rospy.Duration(.1))]
mount='jackal/velodyne/gazebo_gt/odometry_sensor_joint'
sensor='jackal/velodyne/gazebo_gt/odometry_sensor_link'
result={'robot_links':links,'missing_world_transforms':missing,
        'virtual_joint_type':robot.find("joint[@name='%s']"%mount).get('type')}
if not missing:
    transform=buffer.lookup_transform('jackal/velodyne/VLP_16',sensor,rospy.Time(0))
    t=transform.transform.translation;q=transform.transform.rotation
    result['sensor_mount_translation']=[t.x,t.y,t.z]
    result['sensor_mount_rotation']=[q.x,q.y,q.z,q.w]
result['passed']=not missing and result['virtual_joint_type']=='fixed'
Path('/mnt/d/STGPlanner/logs/rviz_repair/tf_after.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
raise SystemExit(0 if result['passed'] else 1)
