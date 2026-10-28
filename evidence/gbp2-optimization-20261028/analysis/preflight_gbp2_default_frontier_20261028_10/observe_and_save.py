"""Passive command/action audit, runtime fingerprints and post-stop native map save."""
import argparse
import hashlib
import json
import math
import threading
import time
from pathlib import Path
import rosgraph
import rospy
import rosparam
from geometry_msgs.msg import Twist
from std_msgs.msg import Bool
from control_planner_interface.msg import VehicleExecuteActionGoal
from voxblox_msgs.srv import FilePath

parser=argparse.ArgumentParser();parser.add_argument('directory',type=Path);args=parser.parse_args();out=args.directory
deadline=time.monotonic()+150
while time.monotonic()<deadline:
    try:
        if rosgraph.is_master_online() and rosgraph.Master('/gbp2_passive').getParam('/use_sim_time') is True:break
    except Exception:pass
    time.sleep(.2)
assert time.monotonic()<deadline,'Sim-time master unavailable'
rospy.init_node('gbp2_passive_audit',anonymous=True,disable_signals=True)
while rospy.get_time()==0 and time.monotonic()<deadline:time.sleep(.05)
handle=(out/'passive_actions.jsonl').open('x');done=threading.Event();io_lock=threading.Lock();last_command=-1.;save_thread=None
def emit(kind,**fields):
    with io_lock:
        handle.write(json.dumps({'kind':kind,'sim':rospy.get_time(),**fields})+'\n');handle.flush()
def command(message):
    global last_command
    now=rospy.get_time()
    if now-last_command>=.1:
        last_command=now;emit('command',linear=message.linear.x,angular=message.angular.z)
def goal(message):
    pts=[p for segment in message.goal.paths for p in segment.path]
    emit('goal',goal_id=message.goal_id.id,points=len(pts),segments=len(message.goal.paths),
         end=[pts[-1].position.x,pts[-1].position.y,pts[-1].position.z] if pts else None)
def save_map():
    record={'after_finish_only':True,'changes_planning_or_motion':False,'request_sim':rospy.get_time()}
    try:
        rospy.wait_for_service('/gbplanner_node/save_map',timeout=3)
        target=out/'poststop_native_map.vxblx';assert not target.exists()
        response=rospy.ServiceProxy('/gbplanner_node/save_map',FilePath)(str(target))
        record.update(response=str(response),exists=target.exists())
        if target.exists():record.update(bytes=target.stat().st_size,sha256=hashlib.sha256(target.read_bytes()).hexdigest())
    except Exception as error:record['error']=str(error)
    (out/'poststop_map_capture.json').write_text(json.dumps(record,indent=2)+'\n')
def finish(message):
    global save_thread
    if message.data and not done.is_set():
        emit('finish_observed');save_thread=threading.Thread(target=save_map);save_thread.start();done.set()
def runtime_fingerprint():
    deadline=time.monotonic()+180
    while not (out/'status.json').exists() and not done.is_set():
        assert time.monotonic()<deadline,'Exploration did not start';time.sleep(.2)
    if done.is_set():return
    rosparam.dump_params(str(out/'live_rosparams.yaml'),'/')
    parameters={name:rospy.get_param(name,None) for name in ['/localPlanner/maxSpeed','/pathFollower/maxSpeed','/localPlanner/autonomySpeed','/pathFollower/autonomySpeed','/use_sim_time']}
    processes=[]
    for proc in Path('/proc').iterdir():
        if proc.name.isdigit():
            try:
                exe=(proc/'exe').resolve(strict=True)
                if exe.name not in ['gbplanner_node','localPlanner','pathFollower','path_execution_node']:continue
                libraries=sorted({line.split()[-1] for line in (proc/'maps').read_text().splitlines() if 'libgbplanner' in line or 'libplanner_common' in line})
                processes.append({'pid':int(proc.name),'exe':str(exe),'sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),
                    'loaded_libraries':[{'path':name,'sha256':hashlib.sha256(Path(name).read_bytes()).hexdigest()} for name in libraries]})
            except OSError:pass
    value={'parameters':parameters,'native_parameters':rospy.get_param('/gbplanner_node'),'processes':processes,'passive_only':True}
    (out/'live_runtime_audit.json').write_text(json.dumps(value,indent=2)+'\n')
    emit('runtime_fingerprint_saved',processes=len(processes))
rospy.Subscriber('/cmd_vel',Twist,command,queue_size=20)
rospy.Subscriber('/path_execution_node/vehicle_execute/goal',VehicleExecuteActionGoal,goal,queue_size=10)
rospy.Subscriber('/benchmark/finish',Bool,finish,queue_size=1)
emit('observer_ready',changes_planner=False)
runtime_thread=threading.Thread(target=runtime_fingerprint,daemon=True);runtime_thread.start()
while not done.is_set() and not rospy.is_shutdown() and not (out/'result.json').exists():time.sleep(.1)
if save_thread is not None:save_thread.join(timeout=12)
emit('observer_ended');handle.close()
