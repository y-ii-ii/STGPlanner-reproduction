"""Passive TARE diagnostic subscriber; never publishes or changes parameters."""
import argparse
import json
import math
import time
from pathlib import Path
import rospy
import rosgraph
from geometry_msgs.msg import PointStamped, Twist
from nav_msgs.msg import Odometry, Path as NavPath
from std_msgs.msg import Bool

parser = argparse.ArgumentParser()
parser.add_argument('directory', type=Path)
args = parser.parse_args()
directory = args.directory
until = time.monotonic() + 150
while time.monotonic() < until and not rosgraph.is_master_online():
    time.sleep(.2)
assert rosgraph.is_master_online(), 'No master for passive observer'
rospy.init_node('tare_passive_observer', disable_signals=True)
handle = (directory / 'tare_diagnostics.jsonl').open('x')
position = None
yaw = 0.
last_direction = None
last_command_time = -1.
done = False

def emit(kind, **fields):
    handle.write(json.dumps({'kind': kind, 'sim': rospy.get_time(), **fields}) + '\n')
    handle.flush()

def odometry(message):
    global position, yaw
    p = message.pose.pose.position
    q = message.pose.pose.orientation
    position = (p.x, p.y, p.z)
    yaw = math.atan2(2 * (q.w*q.z + q.x*q.y), 1 - 2 * (q.y*q.y + q.z*q.z))

def waypoint(message):
    global last_direction
    if position is None:
        return
    p = message.point
    dx, dy = p.x-position[0], p.y-position[1]
    direction = math.atan2(dy, dx)
    wrap = lambda value: math.atan2(math.sin(value), math.cos(value))
    emit('waypoint', x=p.x, y=p.y, z=p.z, robot_x=position[0], robot_y=position[1], robot_yaw=yaw,
         target_distance_m=math.hypot(dx, dy), yaw_error_rad=wrap(direction-yaw),
         direction_change_rad=wrap(direction-last_direction) if last_direction is not None else None)
    last_direction = direction

def command(message):
    global last_command_time
    now = rospy.get_time()
    if now-last_command_time >= .1:
        last_command_time = now
        emit('command', linear=message.linear.x, angular=message.angular.z)

def path(message, label):
    pts = [[p.pose.position.x, p.pose.position.y, p.pose.position.z] for p in message.poses]
    length = sum(math.hypot(b[0]-a[0], b[1]-a[1]) for a, b in zip(pts, pts[1:]))
    emit(label, nodes=len(pts), length_m=length, points=pts)

def finish(message):
    global done
    if message.data:
        done = True

rospy.Subscriber('/base_link/odometry', Odometry, odometry, queue_size=10)
rospy.Subscriber('/way_point', PointStamped, waypoint, queue_size=10)
rospy.Subscriber('/cmd_vel', Twist, command, queue_size=10)
rospy.Subscriber('/sensor_coverage_planner/local_path', NavPath, lambda m: path(m, 'local_path'), queue_size=1)
rospy.Subscriber('/sensor_coverage_planner/global_path', NavPath, lambda m: path(m, 'global_path'), queue_size=1)
rospy.Subscriber('/sensor_coverage_planner/exploration_path', NavPath, lambda m: path(m, 'exploration_path'), queue_size=1)
rospy.Subscriber('/benchmark/finish', Bool, finish, queue_size=1)
emit('observer_started', topics=rospy.get_published_topics())
deadline = time.monotonic() + 180
while not done and not rospy.is_shutdown():
    if (directory / 'result.json').exists():
        break
    if not (directory / 'status.json').exists() and time.monotonic() > deadline:
        break
    time.sleep(.1)
emit('observer_ended')
handle.close()
