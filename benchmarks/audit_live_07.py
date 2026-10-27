"""Passive recording only; no control publications or planner service calls."""
import hashlib
import json
import math
import os
import subprocess
import threading
import time
from pathlib import Path
import rospy
import rosparam
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from control_planner_interface.msg import VehicleExecuteActionGoal

out = Path('/mnt/d/STGPlanner/benchmarks/results/repair_formal_gbp2_07')
rospy.init_node('passive_runtime_audit_07', anonymous=True, disable_signals=True)
deadline = time.monotonic() + 180
while not rospy.has_param('/pathFollower/maxSpeed'):
    assert time.monotonic() < deadline, 'Controller parameters did not appear'
    time.sleep(.5)
rosparam.dump_params(str(out / 'live_rosparams.yaml'), '/')
params = {name: rospy.get_param(name, None) for name in (
    '/localPlanner/maxSpeed', '/localPlanner/autonomySpeed', '/pathFollower/maxSpeed',
    '/pathFollower/autonomySpeed', '/pathFollower/twoWayDrive', '/use_sim_time',
    '/gbplanner_node/PlanningParams/v_max', '/gbplanner_node/PlanningParams/v_homing_max')}
processes = []
for directory in Path('/proc').iterdir():
    if not directory.name.isdigit(): continue
    try:
        exe = directory.joinpath('exe').resolve(strict=True)
        if exe.name not in ('localPlanner', 'pathFollower', 'path_execution_node', 'gbplanner_node'): continue
        processes.append({'pid': int(directory.name), 'exe': str(exe),
            'exe_sha256': hashlib.sha256(exe.read_bytes()).hexdigest(),
            'cmdline': directory.joinpath('cmdline').read_bytes().replace(b'\0', b' ').decode(),
            'loaded_native_libraries': sorted(set(line.split()[-1] for line in directory.joinpath('maps').read_text().splitlines()
                if 'libgbplanner' in line or 'libplanner_common' in line))})
    except (OSError, ProcessLookupError): pass
(out / 'live_runtime_audit.json').write_text(json.dumps({'parameters': params, 'processes': processes,
    'passive_only': True, 'source': 'running processes /proc/exe and ROS parameter server'}, indent=2) + '\n')
stats = {'cmd_samples': 0, 'max_abs_command_linear_x': 0., 'odom_samples': 0,
    'max_odom_xy_speed': 0., 'vehicle_action_requests': 0}
mutex = threading.Lock()
events = (out / 'passive_global_action_audit.jsonl').open('w')
def cmd(message):
    with mutex:
        stats['cmd_samples'] += 1
        stats['max_abs_command_linear_x'] = max(stats['max_abs_command_linear_x'], abs(message.linear.x))
def odom(message):
    with mutex:
        stats['odom_samples'] += 1
        velocity = message.twist.twist.linear
        stats['max_odom_xy_speed'] = max(stats['max_odom_xy_speed'], math.hypot(velocity.x, velocity.y))
def goal(message):
    with mutex:
        stats['vehicle_action_requests'] += 1
        paths = [{'points': len(p.path), 'start_xy': [p.path[0].position.x,p.path[0].position.y],
            'end_xy': [p.path[-1].position.x,p.path[-1].position.y]} for p in message.goal.paths if p.path]
        events.write(json.dumps({'sim': rospy.get_time(), 'kind': 'actual_global_vehicle_action_goal',
            'goal_id': message.goal_id.id, 'paths': paths}) + '\n')
        events.flush()
rospy.Subscriber('/cmd_vel', Twist, cmd, queue_size=100)
rospy.Subscriber('/base_link/odometry', Odometry, odom, queue_size=100)
rospy.Subscriber('/path_execution_node/vehicle_execute/goal', VehicleExecuteActionGoal, goal, queue_size=30)
while not rospy.is_shutdown():
    with mutex:
        (out / 'passive_speed_audit.json').write_text(json.dumps({'sim': rospy.get_time(), **stats}, indent=2) + '\n')
    time.sleep(2)
