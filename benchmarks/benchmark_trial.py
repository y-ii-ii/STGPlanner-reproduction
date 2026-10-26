#!/usr/bin/env python3
"""Run real, separately built planners against one fresh Scene4 simulation.

Common observer is upstream STGPlanner known-plane area, not each baseline's
different internal completion estimate. No paths are synthesized for exploration;
TARE's native selected waypoint and GBP2's returned path are adapted to the same
vehicle action used by STGPlanner and FAEL.
"""
import argparse, collections, copy, csv, json, math, os, signal, subprocess, threading, time, traceback
from pathlib import Path
import actionlib, rosgraph, rospy, rosnode, rosparam
from actionlib.action_client import ActionClient, CommState
from std_msgs.msg import Bool, Float32, Float64
from nav_msgs.msg import Odometry, Path as NavPath
from sensor_msgs.msg import PointCloud2
from geometry_msgs.msg import Pose, PointStamped, Twist
from rosgraph_msgs.msg import Log
from control_planner_interface.msg import VehicleExecuteAction, VehicleExecuteGoal, ExplorerPlannerAction, ExplorerPlannerGoal, Path as PlannerPath
from visualization_tools.msg import IterationTime
from planner_msgs.srv import planner_srv, planner_srvRequest

ROOT=Path('/mnt/d/STGPlanner/benchmarks')
class GoalClient:
    """Poll a specific ActionClient handle; terminal means its result arrived.

    SimpleActionClient's shared transition callback can receive a late update
    from a replaced goal. Also, /status can precede /result. Handle-local polling
    keeps the original replacement policy without mislabelling either event.
    """
    def __init__(self,namespace,spec):self.client=ActionClient(namespace,spec);self.handle=None
    def wait_for_server(self,timeout):return self.client.wait_for_server(timeout)
    def send_goal(self,goal):self.handle=self.client.send_goal(goal)
    def get_state(self):
        h=self.handle
        if h is None:return 9
        state=h.get_goal_status()
        if h.get_comm_state()!=CommState.DONE and state in [2,3,4,5,8,9]:return 1
        return state
    def get_result(self):return self.handle.get_result() if self.handle else None
    def cancel_all_goals(self):self.client.cancel_all_goals()
WS={'stgp':'/opt/stgplanner/catkin_ws','fael':'/opt/stgplanner/benchmarks/fael_ws','tare':'/opt/stgplanner/benchmarks/tare_ws','gbp2':'/opt/stgplanner/benchmarks/gbp2_ws'}
parser=argparse.ArgumentParser();parser.add_argument('method',choices=WS);parser.add_argument('--name',required=True);parser.add_argument('--limit',type=float,default=1600);parser.add_argument('--pilot',action='store_true')
a=parser.parse_args();out=ROOT/'results'/a.name;out.mkdir(parents=True,exist_ok=False)
os.environ['ROS_LOG_DIR']=str(out/'ros');Path(os.environ['ROS_LOG_DIR']).mkdir()
children=[];files=[];lock=threading.RLock();finished=threading.Event();active=False
d={'method':a.method,'trial':a.name,'pilot':a.pilot,'sim_time_limit_s':a.limit,'area_threshold_m2':7400.5,'area_denominator_m2':7790,'started_unix':time.time(),'distance_m':0.,'area_m2':0.,'cloud_messages':0,'odom_messages':0,'nonempty_plans':0,'empty_plans':0,'planner_states':{},'motion_states':{},'native_finished':False,'errors':[],'runtime_native_s':[],'request_wall_s':[],'stop_ack':False,'post_stop_distance_m':0.,'max_parked_command':0.}
pose=None;last_odom=None;cloud_wall=0;odom_wall=0;start_wall=None;start_sim=None;end_pose=None;end_wall=None;end_sim=None;last_cmd=0.;native_waypoint=None;waypoint_seq=0
events=(out/'events.jsonl').open('w');metrics=(out/'metrics.jsonl').open('w');trajectory=(out/'trajectory.csv').open('w',newline='');tw=csv.writer(trajectory);tw.writerow(['sim_s','wall_s','x','y','z','distance_m','area_m2'])

def event(kind,**kw):
    with lock:
        row={'unix':time.time(),'sim':rospy.get_time() if rospy.core.is_initialized() else None,'kind':kind,**kw};events.write(json.dumps(row)+'\n');events.flush()
    print(json.dumps(row),flush=True)

def launch(label,command,workspace='/opt/stgplanner/catkin_ws'):
    f=(out/(label+'.log')).open('w');files.append(f)
    p=subprocess.Popen(['bash','-c','source '+workspace+'/devel/setup.bash; exec '+command],stdout=f,stderr=subprocess.STDOUT,start_new_session=True,env=os.environ.copy());children.append((label,p));return p

def wait_wall(predicate,timeout):
    until=time.monotonic()+timeout
    while time.monotonic()<until:
        if predicate():return True
        time.sleep(.05)
    return False

def odom(m):
    global pose,last_odom,odom_wall
    t=time.monotonic();p=m.pose.pose.position
    with lock:
        if active and last_odom is not None:
            step=math.hypot(p.x-last_odom[0],p.y-last_odom[1])
            if step<2:
                if not finished.is_set():d['distance_m']+=step
                elif end_wall is not None and t>end_wall+5:d['post_stop_distance_m']+=step
        last_odom=(p.x,p.y);pose=copy.deepcopy(m.pose.pose);odom_wall=t;d['odom_messages']+=1

def cloud(m):
    global cloud_wall
    cloud_wall=time.monotonic();d['cloud_messages']+=1

def area(m):
    d['area_m2']=float(m.data)
    if active and not finished.is_set() and m.data>7400.5:finish('coverage_threshold')

def runtime(m):
    if active and not finished.is_set():d['runtime_native_s'].append(float(m.iterationTime if hasattr(m,'iterationTime') else m.data))

def waypoint(m):
    global native_waypoint,waypoint_seq
    with lock:native_waypoint=copy.deepcopy(m.point);waypoint_seq+=1

def native_finish(m):
    if m.data and not d['native_finished']:d['native_finished']=True;event('native_finish',area=d['area_m2'])

def cmd(m):
    global last_cmd
    last_cmd=max(abs(m.linear.x),abs(m.angular.z))
    if end_wall is not None and time.monotonic()>end_wall+5:d['max_parked_command']=max(d['max_parked_command'],last_cmd)

def roslog(m):
    if active and m.level>=Log.ERROR:
        with lock:
            if len(d['errors'])<150:d['errors'].append({'node':m.name,'message':m.msg[:1000],'sim':rospy.get_time()})

def finish(reason):
    global end_wall,end_sim,end_pose
    with lock:
        if finished.is_set():return
        end_wall=time.monotonic();end_sim=rospy.get_time();end_pose=copy.deepcopy(pose);d['finish_reason']=reason;finished.set()
    event('finish',reason=reason,area=d['area_m2'],distance=d['distance_m'])
    finish_pub.publish(Bool(True))
    threading.Thread(target=stop_vehicle,daemon=True).start()

def stop_vehicle():
    try:
        motion.cancel_all_goals();stop.send_goal(VehicleExecuteGoal());ok=wait_wall(lambda:stop.get_state() not in [0,1,6,7],12)
        d['stop_ack']=ok and stop.get_state()==3;d['stop_state']=stop.get_state();event('stop_result',ack=d['stop_ack'],state=stop.get_state())
    except Exception as e:event('stop_error',error=str(e))

def send_paths(paths):
    if finished.is_set():return
    valid=[x for x in paths if x.path]
    if not valid:return
    goal=VehicleExecuteGoal();goal.header.stamp=rospy.Time.now();goal.header.frame_id='world';goal.paths=valid
    motion.send_goal(goal);d['nonempty_plans']+=1

def ground_path(poses):
    # Flat Scene4: convert LiDAR-centre native outputs to the common base pose.
    if not poses:return []
    pts=[]
    for p in poses:
        if not math.isfinite(p.position.x+p.position.y):return []
        if not pts or math.hypot(p.position.x-pts[-1].position.x,p.position.y-pts[-1].position.y)>.01:pts.append(copy.deepcopy(p))
    dense=[]
    for i,p in enumerate(pts):
        q=pts[min(i+1,len(pts)-1)];yaw=math.atan2(q.position.y-p.position.y,q.position.x-p.position.x) if i<len(pts)-1 else (math.atan2(p.position.y-pts[i-1].position.y,p.position.x-pts[i-1].position.x) if i else 0.)
        steps=max(1,int(math.ceil(math.hypot(q.position.x-p.position.x,q.position.y-p.position.y)/.2))) if i<len(pts)-1 else 1
        for j in range(steps):
            r=Pose();f=j/steps;r.position.x=p.position.x+f*(q.position.x-p.position.x);r.position.y=p.position.y+f*(q.position.y-p.position.y);r.position.z=pose.position.z if pose else 0.;r.orientation.z=math.sin(yaw/2);r.orientation.w=math.cos(yaw/2);dense.append(r)
    return [PlannerPath(path=dense)] if dense else []

def driver():
    try:
        if a.method in ['stgp','fael']:
            planner=GoalClient('/topo_planner_node/topo_planner',ExplorerPlannerAction)
            if not planner.wait_for_server(rospy.Duration(60)):finish('planner_unavailable');return
            i=0
            while not finished.is_set():
                i+=1;t=time.monotonic();planner.send_goal(ExplorerPlannerGoal(iteration_id=i))
                while not finished.is_set() and planner.get_state() in [0,1,6,7] and time.monotonic()-t<60:time.sleep(.01)
                if finished.is_set():planner.cancel_all_goals();return
                state=planner.get_state();d['planner_states'][str(state)]=d['planner_states'].get(str(state),0)+1;d['request_wall_s'].append(time.monotonic()-t)
                if state in [0,1,6,7]:planner.cancel_all_goals();finish('planner_timeout_60_wall_s');return
                result=planner.get_result()
                if state==3 and result and any(x.path for x in result.paths):send_paths(result.paths)
                else:d['empty_plans']+=1
                # Same replan policy as the supplied exploration manager.
                until=rospy.get_time()+.1
                while not finished.is_set() and rospy.get_time()<until:time.sleep(.01)
        elif a.method=='tare':
            seen=0
            while not finished.is_set():
                with lock:seq=waypoint_seq;point=copy.deepcopy(native_waypoint);current=copy.deepcopy(pose)
                if seq!=seen and point is not None and current:
                    seen=seq;target=Pose();target.position=point
                    send_paths(ground_path([current,target]))
                time.sleep(.02)
        else:
            rospy.wait_for_service('/gbplanner',timeout=60);planner=rospy.ServiceProxy('/gbplanner',planner_srv)
            while not finished.is_set():
                request=planner_srvRequest();request.header.stamp=rospy.Time.now();request.header.frame_id='world';request.bound_mode=0;request.root_pose.orientation.w=1.
                t=time.monotonic()
                try:response=planner(request)
                except rospy.ServiceException as e:
                    event('planner_service_retry',error=str(e));d['empty_plans']+=1;time.sleep(.5);continue
                d['request_wall_s'].append(time.monotonic()-t)
                if finished.is_set():return
                d['planner_states'][str(response.status)]=d['planner_states'].get(str(response.status),0)+1
                if response.path:
                    send_paths(ground_path(response.path));mstart=time.monotonic()
                    # GBP2 normally replans after executing the current segment.
                    while not finished.is_set() and motion.get_state() in [0,1,6,7] and time.monotonic()-mstart<90:time.sleep(.02)
                    state=motion.get_state();d['motion_states'][str(state)]=d['motion_states'].get(str(state),0)+1
                    if not finished.is_set() and state in [0,1,6,7]:motion.cancel_all_goals();event('segment_watchdog_90_wall_s')
                else:d['empty_plans']+=1;time.sleep(.2)
    except Exception as e:
        event('driver_exception',error=str(e),trace=traceback.format_exc());finish('driver_exception')

try:
    if rosgraph.is_master_online():raise RuntimeError('A ROS master already exists; use a fresh dedicated distro session.')
    launch('simulation','roslaunch exploration_manager sim_env.launch world:=Scene4 gazebo_gui:=false')
    if not wait_wall(rosgraph.is_master_online,60):raise RuntimeError('master did not start')
    # roslaunch starts its master before uploading parameters. Set this before
    # rospy initialization, otherwise rospy can permanently use wall time.
    rospy.set_param('/use_sim_time',True)
    rospy.init_node('scene4_benchmark',disable_signals=True)
    rospy.Subscriber('/jackal/velodyne/velodyne_points',PointCloud2,cloud,queue_size=1)
    rospy.Subscriber('/rosout_agg',Log,roslog,queue_size=50)
    rospy.wait_for_service('/gazebo/unpause_physics',timeout=180)
    subprocess.run(['rosservice','call','/gazebo/unpause_physics'],stdout=subprocess.DEVNULL,timeout=15,check=True)
    if not wait_wall(lambda:d['cloud_messages']>5,120):raise RuntimeError('no lidar')
    launch('movement','roslaunch exploration_manager robot_move.launch')
    rospy.Subscriber('/base_link/odometry',Odometry,odom,queue_size=100)
    rospy.Subscriber('/cmd_vel',Twist,cmd,queue_size=10)
    if not wait_wall(lambda:pose is not None,90):raise RuntimeError('no base odometry')
    motion=GoalClient('/path_execution_node/vehicle_execute',VehicleExecuteAction);stop=GoalClient('/path_execution_node/vehicle_stop',VehicleExecuteAction)
    if not motion.wait_for_server(rospy.Duration(60)) or not stop.wait_for_server(rospy.Duration(60)):raise RuntimeError('no common controller')
    launch('cloud_bridge','/opt/stgplanner/benchmarks/bin/benchmark_cloud_bridge')
    for params,ns in rosparam.load_file(str(ROOT/'config/coverage.yaml'),default_namespace='/benchmark_coverage'):rosparam.upload_params(ns,params)
    rospy.set_param('/benchmark_coverage/output_directory',str(out))
    rospy.Subscriber('/benchmark/known_area',Float64,area,queue_size=1)
    finish_pub=rospy.Publisher('/benchmark/finish',Bool,queue_size=1,latch=True);finish_pub.publish(Bool(False))
    inited_pub=rospy.Publisher('/explorer_node/explorer_inited',Float64,queue_size=1,latch=True)
    launch('coverage','/opt/stgplanner/benchmarks/bin/benchmark_coverage point_cloud:=/jackal/velodyne/velodyne_points sensor_odometry:=/sensor_to_world/odometry')
    rospy.Subscriber('/topo_planner_node/iteration_time',IterationTime,runtime,queue_size=100)
    rospy.Subscriber('/runtime',Float32,runtime,queue_size=100)
    rospy.Subscriber('/benchmark/native_runtime',Float64,runtime,queue_size=100)
    rospy.Subscriber('/way_point',PointStamped,waypoint,queue_size=1)
    rospy.Subscriber('/sensor_coverage_planner/exploration_finish',Bool,native_finish,queue_size=1)
    if a.method=='fael':
        # The official FAEL robot_move launch includes this terrain classifier.
        # STGPlanner's global UFOMap planner does not require this extra node.
        launch('fael_traversability','roslaunch traversability_analysis traversability_analysis_3d.launch')
    launch('native_planner','roslaunch '+str(ROOT/'config'/(a.method+'.launch')),WS[a.method])
    expected={'stgp':'/topo_planner_node','fael':'/topo_planner_node','tare':'/sensor_coverage_planner/tare_planner_node','gbp2':'/gbplanner_node'}[a.method]
    if not wait_wall(lambda:expected in rosnode.get_node_names(),60):raise RuntimeError('native node did not register')
    # Map the same initialization motion in every planner, as in the upstream
    # launch order. In particular, ground projection needs floor observations
    # beneath the final robot position, which a stationary VLP16 cannot see.
    rospy.sleep(5.)
    event('initialization_mapping_ready')
    target=Pose();target.position.x=3.;target.position.y=.1;target.orientation.w=1
    goal=VehicleExecuteGoal();goal.header.frame_id='world';goal.header.stamp=rospy.Time.now();goal.paths=ground_path([copy.deepcopy(pose),target]);motion.send_goal(goal)
    if not wait_wall(lambda:motion.get_state() not in [0,1,6,7],60) or motion.get_state()!=3:raise RuntimeError('initialization motion failed')
    stop.send_goal(VehicleExecuteGoal());wait_wall(lambda:stop.get_state() not in [0,1,6,7],12)
    d['initial_pose']={'x':pose.position.x,'y':pose.position.y,'z':pose.position.z};event('initialized',pose=d['initial_pose'])
    inited_pub.publish(Float64(time.time()))
    # Clock starts at the first exploration request, after initialization.
    start_sim=rospy.get_time();start_wall=time.monotonic();active=True
    start_pub=rospy.Publisher('/start_exploration',Bool,queue_size=1,latch=True);start_pub.publish(Bool(True))
    event('exploration_start',sim=start_sim)
    threading.Thread(target=driver,daemon=True).start();lastwrite=0
    while not finished.is_set():
        t=time.monotonic();sim=rospy.get_time()
        if sim-start_sim>=a.limit:finish('pilot_time_limit' if a.pilot else 'sim_time_limit');break
        if t-start_wall>a.limit*4+240:finish('wall_watchdog');break
        if t-cloud_wall>30:finish('lidar_stalled');break
        if t-odom_wall>20:finish('odometry_stalled');break
        dead=[label for label,p in children if p.poll() is not None]
        if dead:finish('process_exit:'+','.join(dead));break
        if t-lastwrite>=1:
            lastwrite=t
            with lock:
                row={'sim_s':sim-start_sim,'wall_s':t-start_wall,'area_m2':d['area_m2'],'coverage_fraction':d['area_m2']/7790,'distance_m':d['distance_m'],'x':pose.position.x,'y':pose.position.y,'nonempty_plans':d['nonempty_plans'],'empty_plans':d['empty_plans']}
                metrics.write(json.dumps(row)+'\n');metrics.flush();tw.writerow([row['sim_s'],row['wall_s'],row['x'],row['y'],pose.position.z,d['distance_m'],d['area_m2']]);trajectory.flush()
                (out/'status.json').write_text(json.dumps(row,indent=2))
        time.sleep(.05)
    time.sleep(9)
    d['sim_time_s']=end_sim-start_sim;d['wall_time_s']=end_wall-start_wall;d['average_speed_m_s']=d['distance_m']/d['sim_time_s'] if d['sim_time_s'] else None;d['coverage_fraction']=d['area_m2']/7790
    for key in ['runtime_native_s','request_wall_s']:
        values=d[key];d[key+'_summary']={'count':len(values),'mean':sum(values)/len(values) if values else None,'max':max(values) if values else None}
    d['validation']={'reached_common_threshold':d['finish_reason']=='coverage_threshold','sensor_stream_live':time.monotonic()-cloud_wall<10,'stop_ack':d['stop_ack'],'parked_command_zero':d['max_parked_command']<1e-5,'parking_drift_under_0_1m':d['post_stop_distance_m']<.1,'planner_produced_motion':d['nonempty_plans']>0 and d['distance_m']>1}
except Exception as e:
    d['fatal_error']=str(e);d['traceback']=traceback.format_exc();event('fatal_error',error=str(e))
finally:
    (out/'result.json').write_text(json.dumps(d,indent=2))
    for label,p in reversed(children):
        if p.poll() is None:
            try:os.killpg(p.pid,signal.SIGINT)
            except ProcessLookupError:pass
    deadline=time.monotonic()+8
    while time.monotonic()<deadline and any(p.poll() is None for _,p in children):time.sleep(.2)
    for label,p in reversed(children):
        if p.poll() is None:
            try:os.killpg(p.pid,signal.SIGKILL)
            except ProcessLookupError:pass
    for f in files+[events,metrics,trajectory]:f.close()
    print(json.dumps({k:v for k,v in d.items() if k not in ['runtime_native_s','request_wall_s','errors']},indent=2),flush=True)
    if rospy.core.is_initialized():rospy.signal_shutdown('trial complete')
