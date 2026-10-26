#!/usr/bin/env python3
"""Observe the real exploration lifecycle, including intentional node shutdown."""
import argparse, collections, json, math, subprocess, time, threading
from pathlib import Path
import rospy, rosnode
from sensor_msgs.msg import PointCloud2
from nav_msgs.msg import Odometry, Path as NavPath
from geometry_msgs.msg import Twist
from rosgraph_msgs.msg import Clock, Log
from std_msgs.msg import Bool, Float64
from control_planner_interface.msg import ExplorerPlannerActionResult, VehicleExecuteActionResult
from visualization_tools.msg import ExploredVolumeTravedDistTime
from visualization_msgs.msg import MarkerArray

p=argparse.ArgumentParser()
p.add_argument('--minimum-seconds',type=int,default=1200)
p.add_argument('--maximum-seconds',type=int,default=2400)
p.add_argument('--post-finish-seconds',type=int,default=120)
p.add_argument('--output',required=True)
a=p.parse_args()
out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
for suffix in ('.events.jsonl','.metrics.jsonl'):out.with_suffix(suffix).write_text('')
started=time.monotonic()
event_lock=threading.Lock()
d={'started_unix':time.time(),'pointcloud_messages':0,'odometry_messages':0,'distance_m':0.,'post_finish_distance_m':0.,'path_messages':0,'nonzero_commands':0,'successful_nonempty_plans':0,'planner_states':{},'markers':{},'metrics':[],'events':[],'resources':[],'node_samples':[],'max_active_result_gap':0.,'max_cloud_gap':0.,'max_odom_gap':0.,'max_post_finish_command':0.,'post_finish_max_speed':0.}
finish=None;explorer_finish=None;initial_explore=None;last_position=None;last_cloud=None;last_odom=None;last_result=None;clock_start=None;clock_end=None;clock_at_finish=None
def now():return time.monotonic()-started
def event(kind,**values):
    row={'wall_seconds':now(),'unix_time':time.time(),'kind':kind,**values}
    with event_lock:
        d['events'].append(row)
        with out.with_suffix('.events.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
def cloud(m):
    global last_cloud
    t=now()
    if last_cloud is not None:d['max_cloud_gap']=max(d['max_cloud_gap'],t-last_cloud)
    last_cloud=t;d['pointcloud_messages']+=1
def odom(m):
    global last_position,last_odom
    t=now();pos=(m.pose.pose.position.x,m.pose.pose.position.y)
    if last_odom is not None:d['max_odom_gap']=max(d['max_odom_gap'],t-last_odom)
    if last_position:
        step=math.hypot(pos[0]-last_position[0],pos[1]-last_position[1])
        if step<2:
            d['distance_m']+=step
            if finish is not None and t>finish+10:d['post_finish_distance_m']+=step
    last_position=pos;last_odom=t;d['odometry_messages']+=1
    if finish is not None and t>finish+10:
        speed=math.hypot(m.twist.twist.linear.x,m.twist.twist.linear.y)
        d['post_finish_max_speed']=max(d['post_finish_max_speed'],speed)
def command(m):
    if abs(m.linear.x)+abs(m.angular.z)>.01:d['nonzero_commands']+=1
    if finish is not None and now()>finish+10:d['max_post_finish_command']=max(d['max_post_finish_command'],abs(m.linear.x)+abs(m.angular.z))
def path(m):d['path_messages']+=1
def result(m):
    global last_result
    t=now();key=str(m.status.status)
    d['planner_states'][key]=d['planner_states'].get(key,0)+1
    if last_result is not None and finish is None:d['max_active_result_gap']=max(d['max_active_result_gap'],t-last_result)
    last_result=t
    if m.status.status==3 and any(s.path for s in m.result.paths):d['successful_nonempty_plans']+=1
    elif m.status.status!=3:event('action_result',status=m.status.status,text=m.status.text)
def metric(m):
    row={'wall_seconds':now(),'unix_time':time.time(),'project_elapsed':m.timeConsumed,'metric':m.exploredVolume,'reported_distance':m.travedDist}
    d['metrics'].append(row)
    with out.with_suffix('.metrics.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
def clock(m):
    global clock_start,clock_end
    if clock_start is None:clock_start=m.clock.to_sec()
    clock_end=m.clock.to_sec()
def finishing(m):
    global finish,clock_at_finish
    if m.data and finish is None:
        finish=now();clock_at_finish=clock_end;event('completion_signal')
def explorer_done(m):
    global explorer_finish
    explorer_finish=now();event('explorer_finish',project_unix=m.data)
def inited(m):
    global initial_explore
    initial_explore=now();event('explorer_initialized',project_unix=m.data)
def log(m):
    if m.name in ('/explorer_node','/exploration_data') and (m.level>=Log.WARN or 'EXPLORATION_STOP' in m.msg or 'completion signal' in m.msg or 'exploration process has finished' in m.msg):
        event('ros_log',node=m.name,level=m.level,text=m.msg,sim_time=m.header.stamp.to_sec())
def markers(m,name):
    s=d['markers'].setdefault(name,{'messages':0,'empty_add':0,'delete':0,'nonempty_add':0})
    s['messages']+=1
    for v in m.markers:
        if v.action==v.DELETE:s['delete']+=1
        elif v.action==v.ADD:s['nonempty_add' if v.points else 'empty_add']+=1

def stop_result(m):
    d['stop_action_status']=m.status.status
    event('vehicle_stop_result',status=m.status.status,text=m.status.text)
def stop_signal(m):
    d['stop_signal_latest']=m.data
    if m.data and 'stop_signal_seconds' not in d:
        d['stop_signal_seconds']=now()
        event('follower_stop_signal')

rospy.init_node('stgplanner_long_runtime_test',anonymous=True,disable_signals=True)
subs=[rospy.Subscriber('/jackal/velodyne/velodyne_points',PointCloud2,cloud,queue_size=1),rospy.Subscriber('/base_link/odometry',Odometry,odom,queue_size=100),rospy.Subscriber('/cmd_vel',Twist,command,queue_size=10),rospy.Subscriber('/path',NavPath,path,queue_size=2),rospy.Subscriber('/topo_planner_node/topo_planner/result',ExplorerPlannerActionResult,result,queue_size=50),rospy.Subscriber('/explored_volume_traved_dist_time',ExploredVolumeTravedDistTime,metric,queue_size=100),rospy.Subscriber('/clock',Clock,clock,queue_size=5),rospy.Subscriber('/exploration_data_finish',Bool,finishing,queue_size=10),rospy.Subscriber('/explorer_node/explorer_finish',Float64,explorer_done,queue_size=5),rospy.Subscriber('/explorer_node/explorer_inited',Float64,inited,queue_size=5),rospy.Subscriber('/rosout',Log,log,queue_size=200),rospy.Subscriber('/topo_planner_node/my_topo_markers',MarkerArray,lambda m:markers(m,'topo_map'),queue_size=2),rospy.Subscriber('/topo_planner_node/global_topo_grid',MarkerArray,lambda m:markers(m,'grid_map'),queue_size=2)]
subs.extend([rospy.Subscriber('/path_execution_node/vehicle_stop/result',VehicleExecuteActionResult,stop_result,queue_size=10),rospy.Subscriber('/path_execution_node/stop_move',Bool,stop_signal,queue_size=10)])
last_sample=-30.
while now()<a.maximum_seconds and not rospy.is_shutdown():
    time.sleep(.2)
    t=now()
    if t-last_sample>=30:
        names=rosnode.get_node_names()
        d['node_samples'].append({'wall_seconds':t,'nodes':names,'finished':finish is not None})
        processes=subprocess.check_output(['ps','-eo','pid,comm,rss'],text=True)
        rows=[line.split() for line in processes.splitlines()[1:] if any(k in line for k in ('gzserver','topo_planner','explorer_node'))]
        d['resources'].append({'wall_seconds':t,'processes':rows})
        snapshot={**d,'wall_seconds':t,'finish_seconds':finish,'explorer_finish_seconds':explorer_finish,'finish_reason':rospy.get_param('/exploration_data/finish_reason','not_yet')}
        out.with_suffix('.progress.json').write_text(json.dumps(snapshot,indent=2))
        print(json.dumps({'elapsed':round(t,1),'finish':finish,'plans':d['successful_nonempty_plans'],'metric':d['metrics'][-1] if d['metrics'] else None}),flush=True)
        last_sample=t
    if finish is not None and t>=a.minimum_seconds and t>=finish+a.post_finish_seconds:break

d.update(wall_seconds=now(),finish_seconds=finish,explorer_finish_seconds=explorer_finish,initial_explore_seconds=initial_explore,finish_reason=rospy.get_param('/exploration_data/finish_reason','missing'),map_area=rospy.get_param('/topo_planner_node/map_area',None),clock_start=clock_start,clock_end=clock_end,post_finish_sim_seconds=(clock_end-clock_at_finish if clock_at_finish is not None and clock_end else None),final_nodes=rosnode.get_node_names())
real_timeouts=[e for e in d['events'] if e.get('kind')=='ros_log' and ('timed out after' in e.get('text','') or 'planner timeout' in e.get('text','').lower())]
active_samples=[s for s in d['node_samples'] if not s['finished'] and s['wall_seconds']>30]
d['checks']={'long_observation':d['wall_seconds']>=a.minimum_seconds,'sensor_data':d['pointcloud_messages']>1000 and d['odometry_messages']>1000,'movement':d['distance_m']>500 and d['nonzero_commands']>100,'planning':d['successful_nonempty_plans']>1000,'active_nodes':bool(active_samples) and all('/topo_planner_node' in s['nodes'] and '/explorer_node' in s['nodes'] for s in active_samples),'expected_finish':finish is not None and d['finish_reason']=='coverage_threshold','threshold_met':bool(d['metrics']) and d['map_area'] is not None and d['metrics'][-1]['metric']>=.95*d['map_area'],'prompt_explorer_finish':finish is not None and explorer_finish is not None and 0<=explorer_finish-finish<2.,'no_real_timeout':not real_timeouts,'post_finish_clock_alive':d['post_finish_sim_seconds'] is not None and d['post_finish_sim_seconds']>30,'robot_stopped':d['post_finish_max_speed']<.1,'markers_valid':len(d['markers'])==2 and all(v['messages']>100 and v['empty_add']==0 and v['nonempty_add']>0 for v in d['markers'].values()),'gazebo_alive':'/gazebo' in d['final_nodes']}
d['passed']=all(d['checks'].values())
d['checks']['zero_post_finish_commands']=d['max_post_finish_command']<0.001
d['checks']['post_finish_position_stable']=d['post_finish_distance_m']<0.05
d['checks']['stop_action_succeeded']=d.get('stop_action_status')==3 and d.get('stop_signal_latest') is True
d['passed']=all(d['checks'].values())
out.write_text(json.dumps(d,indent=2))
print(json.dumps({'passed':d['passed'],'checks':d['checks'],'wall_seconds':d['wall_seconds'],'finish_seconds':finish,'explorer_finish_seconds':explorer_finish},indent=2),flush=True)
raise SystemExit(0 if d['passed'] else 1)
