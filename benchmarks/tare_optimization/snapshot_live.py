"""Read actual ROS parameters and process binaries during an owned TARE trial."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import rospy
from std_msgs.msg import Int32

parser = argparse.ArgumentParser()
parser.add_argument('trial')
args = parser.parse_args()
rospy.init_node('tare_runtime_fingerprint', anonymous=True, disable_signals=True)
params = rospy.get_param('/sensor_coverage_planner/tare_planner_node')
speed_params = {key: rospy.get_param(key) for key in rospy.get_param_names()
                if any(token in key for token in ('maxSpeed', 'autonomySpeed', 'maxAccel', 'sensorRange'))}
processes = []
for entry in Path('/proc').iterdir():
    if entry.name.isdigit():
        try:
            exe = str((entry / 'exe').resolve())
            if Path(exe).name in ['tare_planner_node', 'localPlanner', 'pathFollower', 'path_execution_node']:
                processes.append({'pid': int(entry.name), 'executable': exe,
                                  'sha256': hashlib.sha256(Path(exe).read_bytes()).hexdigest()})
        except (OSError, PermissionError):
            pass
try:
    momentum_count = rospy.wait_for_message('/sensor_coverage_planner/momentum_activation_count', Int32, timeout=4).data
except rospy.ROSException:
    momentum_count = None
value = {'sim_absolute': rospy.get_time(), 'tare_parameters': params, 'control_speed_parameters': speed_params, 'processes': processes,
         'native_momentum_activation_count': momentum_count}
out = Path('/mnt/d/STGPlanner/benchmarks/results') / args.trial
target = out / 'runtime_fingerprint.json'
index = 2
while target.exists():
    target = out / ('runtime_fingerprint_' + str(index) + '.json')
    index += 1
with target.open('x') as handle:
    handle.write(json.dumps(value, indent=2) + '\n')
print(json.dumps({'kUseMomentum': params.get('kUseMomentum'), 'kSensorRange': params.get('kSensorRange'),
                  'speed_parameters': speed_params, 'process_count': len(processes), 'momentum_activation_count': momentum_count}, indent=2))
