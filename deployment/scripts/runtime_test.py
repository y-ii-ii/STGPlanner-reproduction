#!/usr/bin/env python3
"""Collect real ROS traffic; wall-clock bounds still work if /clock stalls."""
import argparse
import json
import math
import time
from pathlib import Path
import rospy
import rosnode
from sensor_msgs.msg import PointCloud2
from nav_msgs.msg import Odometry, Path as NavPath
from geometry_msgs.msg import Twist
from rosgraph_msgs.msg import Clock
from control_planner_interface.msg import ExplorerPlannerActionResult
from visualization_tools.msg import ExploredVolumeTravedDistTime

parser = argparse.ArgumentParser()
parser.add_argument('--seconds', type=int, default=180)
parser.add_argument('--output', default='/mnt/d/STGPlanner/logs/runtime_test.json')
args = parser.parse_args()
start = time.monotonic()
data = dict(pointcloud_messages=0, pointcloud_max_points=0, odometry_messages=0,
            odometry_distance_m=0.0, command_messages=0, nonzero_commands=0,
            path_messages=0, max_path_poses=0, planner_results=0,
            successful_nonempty_plans=0, explored_volume_max=0.0,
            reported_travel_distance_max=0.0, sim_time_start=None,
            sim_time_end=None, initial_position=None, final_position=None)
trajectory = []

def cloud(msg):
    data['pointcloud_messages'] += 1
    data['pointcloud_max_points'] = max(data['pointcloud_max_points'], msg.width * msg.height)

def odom(msg):
    p = msg.pose.pose.position
    position = [p.x, p.y, p.z]
    if data['final_position'] is not None:
        q = data['final_position']
        step = math.hypot(p.x-q[0], p.y-q[1])
        if step < 2.0:
            data['odometry_distance_m'] += step
    else:
        data['initial_position'] = position
    data['final_position'] = position
    data['odometry_messages'] += 1
    if not trajectory or time.monotonic()-trajectory[-1][0] > 0.5:
        trajectory.append([time.monotonic(), msg.header.stamp.to_sec(), *position])

def command(msg):
    data['command_messages'] += 1
    if abs(msg.linear.x) + abs(msg.angular.z) > 0.01:
        data['nonzero_commands'] += 1

def path(msg):
    data['path_messages'] += 1
    data['max_path_poses'] = max(data['max_path_poses'], len(msg.poses))

def result(msg):
    data['planner_results'] += 1
    if msg.status.status == 3 and any(p.path for p in msg.result.paths):
        data['successful_nonempty_plans'] += 1

def metrics(msg):
    data['explored_volume_max'] = max(data['explored_volume_max'], msg.exploredVolume)
    data['reported_travel_distance_max'] = max(data['reported_travel_distance_max'], msg.travedDist)

def clock(msg):
    value = msg.clock.to_sec()
    if data['sim_time_start'] is None:
        data['sim_time_start'] = value
    data['sim_time_end'] = value

rospy.init_node('stgplanner_deployment_test', anonymous=True, disable_signals=True)
subscriptions = [
    rospy.Subscriber('/jackal/velodyne/velodyne_points', PointCloud2, cloud, queue_size=1),
    rospy.Subscriber('/base_link/odometry', Odometry, odom, queue_size=100),
    rospy.Subscriber('/cmd_vel', Twist, command, queue_size=20),
    rospy.Subscriber('/path', NavPath, path, queue_size=5),
    rospy.Subscriber('/topo_planner_node/topo_planner/result', ExplorerPlannerActionResult, result, queue_size=20),
    rospy.Subscriber('/explored_volume_traved_dist_time', ExploredVolumeTravedDistTime, metrics, queue_size=20),
    rospy.Subscriber('/clock', Clock, clock, queue_size=10),
]
last_progress = 0.0
while time.monotonic()-start < args.seconds and not rospy.is_shutdown():
    time.sleep(0.25)
    elapsed = time.monotonic()-start
    if elapsed-last_progress > 15:
        progress = dict(data)
        progress['wall_seconds'] = elapsed
        Path(args.output).with_suffix('.progress.json').write_text(json.dumps(progress, indent=2))
        last_progress = elapsed
data['wall_seconds'] = time.monotonic()-start
data['nodes'] = rosnode.get_node_names()
data['topics'] = rospy.get_published_topics()
required_nodes = ['/gazebo', '/topo_planner_node', '/explorer_node',
                  '/path_execution_node', '/localPlanner', '/pathFollower', '/exploration_data']
data['node_health'] = {name: rosnode.rosnode_ping(name, max_count=1, verbose=False)
                       for name in required_nodes}
data['checks'] = {
    'required_nodes_alive': all(data['node_health'].values()),
    'laser_points': data['pointcloud_messages'] >= 10 and data['pointcloud_max_points'] > 100,
    'odometry': data['odometry_messages'] >= 10,
    'robot_moves': data['odometry_distance_m'] > 1.0,
    'velocity_commands': data['nonzero_commands'] > 10,
    'local_paths': data['max_path_poses'] > 1,
    'exploration_plans': data['successful_nonempty_plans'] > 0,
    'map_exploration_metrics': data['explored_volume_max'] > 1.0,
    'clock_advances': data['sim_time_start'] is not None and data['sim_time_end']-data['sim_time_start'] > 5.0,
}
data['passed'] = all(data['checks'].values())
output = Path(args.output)
output.write_text(json.dumps(data, indent=2, ensure_ascii=False))
output.with_suffix('.trajectory.csv').write_text('wall_seconds,sim_seconds,x,y,z\n' + ''.join(
    ','.join(str(v) for v in [row[0]-start, *row[1:]])+'\n' for row in trajectory))
print(json.dumps(data, indent=2, ensure_ascii=False))
raise SystemExit(0 if data['passed'] else 1)
