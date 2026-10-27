"""Real native planner service on a frozen real map; no robot or Gazebo motion."""
from pathlib import Path
import datetime,json,os,signal,subprocess,threading,time
import rospy,rosparam
from nav_msgs.msg import Odometry
from planner_msgs.srv import planner_srv,planner_srvRequest
from voxblox_msgs.srv import FilePath
root=Path('/mnt/d/STGPlanner/benchmarks');rospy.init_node('offline_rrg_probe',anonymous=True)
publisher=rospy.Publisher('/probe/odometry',Odometry,queue_size=5,latch=True)
halt=threading.Event()
def publish():
    while not halt.is_set():
        msg=Odometry();msg.header.stamp=rospy.Time.now();msg.header.frame_id='world';msg.child_frame_id='probe_sensor'
        msg.pose.pose.position.x=18.4979;msg.pose.pose.position.y=55.4525;msg.pose.pose.position.z=.456
        msg.pose.pose.orientation.z=.7071067811865475;msg.pose.pose.orientation.w=.7071067811865476
        publisher.publish(msg);time.sleep(.05)
threading.Thread(target=publish,daemon=True).start()
results=[]
for vertices in [500,2000]:
  for repeat in range(1,4):
    name='gbp_probe_'+str(vertices)+'_'+str(repeat);ns='/'+name
    for filename in ['gbp2.yaml','voxblox.yaml']:
      path=root/'config'/filename
      if filename=='gbp2.yaml' and (root/'trial_repairs/config__gbp2.yaml.before').exists():path=root/'trial_repairs/config__gbp2.yaml.before'
      for params,namespace in rosparam.load_file(str(path),default_namespace=ns):rosparam.upload_params(namespace,params)
    scale=vertices//500
    for key,val in [('num_vertices_max',vertices),('num_edges_max',5000*scale),('num_loops_cutoff',2000*scale),('num_loops_max',20000*scale)]:rospy.set_param(ns+'/PlanningParams/'+key,val)
    # Explicit request root avoids a fresh node planning from an uninitialised
    # odometry state before the ROS publisher/subscriber handshake completes.
    rospy.set_param(ns+'/PlanningParams/use_current_state',False)
    log=(root/'logs'/('offline_rrg_'+str(vertices)+'_'+str(repeat)+'.log')).open('w')
    node=subprocess.Popen(['/opt/stgplanner/benchmarks/gbp2_ws/devel/lib/gbplanner/gbplanner_node','__name:='+name,'odometry:=/probe/odometry'],stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    item={'vertices':vertices,'repeat':repeat,'node':ns}
    try:
      rospy.wait_for_service(ns+'/load_map',timeout=30)
      deadline=time.monotonic()+10
      while publisher.get_num_connections()<1 and time.monotonic()<deadline:time.sleep(.1)
      # Upstream explicitly clears its map on the first odometry callback.
      # Wait for that reset BEFORE loading the frozen map, or it gets erased.
      logpath=root/'logs'/('offline_rrg_'+str(vertices)+'_'+str(repeat)+'.log')
      deadline=time.monotonic()+15
      while 'Received the first odometry, reset the map' not in logpath.read_text(errors='replace'):
        if time.monotonic()>deadline:raise RuntimeError('first odometry reset not observed')
        time.sleep(.1)
      time.sleep(.3)
      rospy.ServiceProxy(ns+'/load_map',FilePath)(str(root/'gbp_ground_snapshot.vxblx'))
      rospy.wait_for_service('/gbplanner',timeout=20);time.sleep(.3)
      request=planner_srvRequest();request.header.stamp=rospy.Time.now();request.header.frame_id='world';request.bound_mode=0;request.root_pose.orientation.w=1.
      request.root_pose.position.x=18.4979;request.root_pose.position.y=55.4525;request.root_pose.position.z=.456
      request.root_pose.orientation.z=.7071067811865475;request.root_pose.orientation.w=.7071067811865476
      box={};done=threading.Event();start=time.monotonic()
      def call():
        try:box['response']=rospy.ServiceProxy('/gbplanner',planner_srv)(request)
        except Exception as error:box['error']=str(error)
        done.set()
      threading.Thread(target=call,daemon=True).start()
      if not done.wait(60):raise RuntimeError('controlled service timeout')
      if 'error' in box:raise RuntimeError(box['error'])
      response=box['response'];path=[{'x':p.position.x,'y':p.position.y,'z':p.position.z} for p in response.path]
      item.update(service_wall_s=time.monotonic()-start,status=response.status,path=path,corridor_advance=any(17<=p['x']<=19.3 and p['y']>=58 for p in path))
    except Exception as error:item['error']=str(error)
    finally:
      if node.poll() is None:os.killpg(node.pid,signal.SIGINT)
      try:node.wait(timeout=10)
      except subprocess.TimeoutExpired:os.killpg(node.pid,signal.SIGKILL);node.wait()
      log.close()
    results.append(item);print(json.dumps({k:v for k,v in item.items() if k!='path'}),flush=True)
halt.set()
value={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'controlled_native_service':True,'robot_motion':False,'explicit_request_root':True,'map_loaded_after_first_odometry_reset':True,'frozen_map':'gbp_ground_snapshot.vxblx','pose':[18.4979,55.4525,.456],'repeats_per_setting':3,'cases':results,'note':'Independent fresh native process per query with explicit root pose and correct map loading order. This diagnoses sampling at a corridor; it is not a full exploration trial.'}
(root/'offline_rrg_probe.json').write_text(json.dumps(value,indent=2))
