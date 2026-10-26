#!/usr/bin/env python3
"""Repair the real sources of RobotModel and MarkerArray diagnostics."""
from pathlib import Path
root=Path('/mnt/d/STGPlanner/catkin_ws/src/STGPlanner')
backup=Path('/mnt/d/STGPlanner/logs/rviz_repair/source_before')

def repair(relative,old,new):
    path=root/relative
    text=path.read_text()
    if new in text:return
    if text.count(old)!=1:raise RuntimeError('Unexpected upstream source: '+relative)
    saved=backup/relative
    saved.parent.mkdir(parents=True,exist_ok=True)
    if not saved.exists():saved.write_bytes(path.read_bytes())
    path.write_text(text.replace(old,new,1))

cpp='stgp_planner/planner/src/perception/global_topo_manager.cpp'
repair(cpp,
       '  return graph_markers;\n}\n\nvoid GlobalTopoManager::pubTopoMarkers() const {',
       '  // Empty categories must clear an old marker instead of sending an invalid empty ADD.\n'
       '  for (auto &marker : graph_markers.markers) {\n'
       '    if (marker.points.empty()) marker.action = visualization_msgs::Marker::DELETE;\n'
       '  }\n'
       '  return graph_markers;\n}\n\nvoid GlobalTopoManager::pubTopoMarkers() const {')
repair('stgp_planner/planner/src/perception/grid_map_2d.cpp',
       '        return grid_map_markers;\n',
       '        // DELETE also removes stale geometry when a grid category becomes empty.\n'
       '        for (auto &marker : grid_map_markers.markers) {\n'
       '            if (marker.points.empty()) marker.action = visualization_msgs::Marker::DELETE;\n'
       '        }\n'
       '        return grid_map_markers;\n')

xacro='3rdparty/jackal/jackal_description/urdf/VLP_16.urdf.xacro'
repair(xacro,
       '<joint name="${namespace}/odometry_sensor${odometry_sensor_suffix}_joint" type="revolute">',
       '<joint name="${namespace}/odometry_sensor${odometry_sensor_suffix}_joint" type="fixed">')
repair(xacro,
       '      <limit upper="0" lower="0" effort="0" velocity="0" />\n    </joint>\n    <gazebo>\n      <plugin filename="librotors_gazebo_odometry_no_tf_plugin.so"',
       '    </joint>\n'
       '    <!-- Keep the virtual sensor link for Gazebo odometry while publishing its fixed TF. -->\n'
       '    <gazebo reference="${namespace}/odometry_sensor${odometry_sensor_suffix}_joint">\n'
       '      <preserveFixedJoint>true</preserveFixedJoint>\n'
       '    </gazebo>\n'
       '    <gazebo>\n      <plugin filename="librotors_gazebo_odometry_no_tf_plugin.so"')
print('RViz source repairs applied: fixed virtual sensor TF; empty markers use DELETE.')
