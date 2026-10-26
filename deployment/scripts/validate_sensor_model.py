#!/usr/bin/env python3
import json,subprocess,xml.etree.ElementTree as ET
from pathlib import Path
base=Path('/mnt/d/STGPlanner/logs/rviz_repair')
source='/mnt/d/STGPlanner/catkin_ws/src/STGPlanner/3rdparty/jackal/jackal_description/urdf/jackal.urdf.xacro'
urdf=subprocess.check_output(['rosrun','xacro','xacro',source],text=True)
(base/'robot_fixed.urdf').write_text(urdf)
sdf=subprocess.check_output(['gz','sdf','-p',str(base/'robot_fixed.urdf')],text=True)
(base/'robot_fixed.sdf').write_text(sdf)
link='jackal/velodyne/gazebo_gt/odometry_sensor_link'
joint='jackal/velodyne/gazebo_gt/odometry_sensor_joint'
u=ET.fromstring(urdf);s=ET.fromstring(sdf)
checks={'urdf_fixed_joint':u.find("joint[@name='%s']"%joint).get('type')=='fixed',
        'gazebo_sensor_link_preserved':s.find(".//link[@name='%s']"%link) is not None,
        'gazebo_fixed_joint_preserved':s.find(".//joint[@name='%s']"%joint) is not None,
        'odometry_plugin_link_exists':s.find('.//plugin[@name="odometry_sensor"]/linkName').text==link}
(base/'model_validation.json').write_text(json.dumps(checks,indent=2))
print(json.dumps(checks,indent=2))
assert all(checks.values())
