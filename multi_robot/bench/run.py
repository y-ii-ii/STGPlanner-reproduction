#!/usr/bin/env python3
"""Bounded Scene4 team trial. Reserve quota before launching; never reuse history."""
import argparse,copy,csv,fcntl,json,math,os,signal,subprocess,threading,time,traceback,shutil
from common import *
from initialization_traffic import TrafficController
from team_topology.traffic_geometry import rectangle,clearance

def main(index):
    idle();out=result_path(index);manifest=json.loads((out/'manifest.json').read_text())
    assert json.loads((out/'offline_preflight.json').read_text())['all_passed']
    for rel,h in manifest['frozen_sha256'].items():assert sha(out/'frozen'/rel)==h,rel
    for p,h in manifest['executables'].items():assert sha(p)==h,p
    for rel,h in manifest['implementation_sha256'].items():assert sha(CODE/rel)==h,rel
    with (ROOT/'codex/TOPOLOGY_TRAFFIC_ATTEMPT_MUTEX').open('w') as f:
        fcntl.flock(f,fcntl.LOCK_EX);limits=json.loads(LIMITS.read_text())
        assert limits['offline_preflight_passed'] and not limits['new_attempts_blocked']
        assert len(limits['attempts'])+1==index and index<=4
        limits['attempts'].append(dict(index=index,trial=out.name,state='reserved',unix=time.time()));dump(LIMITS,limits)
    t0=time.monotonic();token=out.name;os.environ['STGPLANNER_TOPOLOGY_TRIAL_TOKEN']=token;os.environ['ROS_LOG_DIR']=str(out/'ros')
    shutil.copytree(CODE,out/'implementation',ignore=shutil.ignore_patterns('__pycache__','.git','evidence'))
    events=(out/'events.jsonl').open('w');metrics=(out/'metrics.jsonl').open('w');plans=(out/'plans.jsonl').open('w')
    robots=['robot_1','robot_2'];children=[];handles=[];subs=[];syncs=[];errors=[];done=threading.Event();stopping=threading.Event()
    state={r:dict(pose=None,physical=None,odom_at=0.,raw=(0.,0.),raw_at=0.,current=(0.,0.),cmd=(0.,0.),last=None) for r in robots}
    sources={r:set() for r in robots};distance={r:0. for r in robots};frames={r:0 for r in robots};result=dict(trial=out.name,index=index,T95_wall_s=None,T95_sim_s=None,finish_reason=None,checks={},errors=errors)
    active=False;start_sim=None;start_wall=None;rospy=None;contact=None;init_pubs={};init_permissions={r:False for r in robots};gate_thread=None;init_done=threading.Event();plan_count={r:0 for r in robots};feedback_count={};traffic_modes={};coordinator_status={};gate_proofs={};pubs={};stops={};motions={};finish={};inits={};mission=None;mutex=threading.RLock()
    def event(kind,**kw):
        row=dict(kind=kind,runtime_wall_s=time.monotonic()-t0,**kw);events.write(json.dumps(row)+'\n');events.flush();print(json.dumps(row),flush=True)
    def owned():
        ids=[]
        for p in Path('/proc').iterdir():
            if not p.name.isdigit() or int(p.name)==os.getpid():continue
            try:
                if ('STGPLANNER_TOPOLOGY_TRIAL_TOKEN='+token).encode()+b'\0' in (p/'environ').read_bytes():ids.append(int(p.name))
            except OSError:pass
        return ids
    def kill(sig):
        for pid in owned():
            try:os.kill(pid,sig)
            except ProcessLookupError:pass
    def hard_limit():
        if not done.wait(2370):
            errors.append('hard_wall_watchdog');stopping.set();kill(signal.SIGTERM)
            if not done.wait(5):kill(signal.SIGKILL)
    threading.Thread(target=hard_limit,daemon=True).start()
    signal.signal(signal.SIGINT,lambda *_:errors.append('user_interrupt'))
    signal.signal(signal.SIGUSR1,lambda *_:errors.append('diagnostic_abort'))
    def lock_state(value):
        l=json.loads(LOCK.read_text());assert l['owner_thread']==OWNER
        l.update(state=value,runtime_active=value!='idle',phase='topology_traffic_20261116',trial=out.name,result_path=str(out),supervisor_pid=os.getpid())
        l['limits_by_scope']['topology_traffic_20261116'].update(used=index,blocked=index>=4);dump(LOCK,l)
    def launch(name):
        h=(out/(name+'.log')).open('w');handles.append(h)
        p=subprocess.Popen(['roslaunch',str(out/'frozen'/(name+'.launch'))],stdout=h,stderr=subprocess.STDOUT,start_new_session=True);children.append((name,p));event('launch',name=name,pid=p.pid)
    def guard():
        if errors:raise RuntimeError(errors[0])
        if contact and contact.non_ground:raise RuntimeError('non_ground_contact')
        if time.monotonic()-t0>2300:raise TimeoutError('wall_limit_including_startup')
        if rospy and rospy.core.is_initialized() and rospy.get_time()>0 and rospy.get_time()-manifest['world_clock_origin_s']>2320:raise TimeoutError('sim_limit_including_startup')
        dead=[(n,p.poll()) for n,p in children if p.poll() is not None]
        if dead:raise RuntimeError('launch_exit:'+str(dead))
        if all(state[r]['physical'] is not None for r in robots):
            gap=clearance(*(rectangle(state[r]['physical']) for r in robots))
            result['min_footprint_clearance_m']=min(result.get('min_footprint_clearance_m',1e9),gap)
            if gap<.18:raise RuntimeError('independent_footprint_safety_stop')
    def wait(pred,seconds,label):
        until=time.monotonic()+seconds
        while time.monotonic()<until:
            guard()
            if pred():return
            time.sleep(.04)
        raise TimeoutError(label)
    def score():
        union=set().union(*sources.values());area=len(union)*.16
        return dict(area_m2=area,coverage_fraction=area/7790.,individual_m2={r:len(v)*.16 for r,v in sources.items()},overlap_m2=(sum(map(len,sources.values()))-len(union))*.16)
    try:
        import rospy,rosgraph,rosnode,message_filters,numpy as np
        from actionlib import SimpleActionClient
        from std_msgs.msg import Bool,Float64,String,Int32MultiArray
        from nav_msgs.msg import Odometry
        from geometry_msgs.msg import Twist
        from sensor_msgs.msg import PointCloud2
        from gazebo_msgs.msg import ModelStates
        from control_planner_interface.msg import VehicleExecuteAction,VehicleExecuteGoal,Path as PlannerPath
        from observation import transform,peer_keep
        from contacts import ContactMonitor
        lock_state('running');launch('simulation');wait(rosgraph.is_master_online,55,'master unavailable')
        rospy.init_node('topology_trial_supervisor',anonymous=True,disable_signals=True)
        def physical(m):
            for r in robots:
                if r in m.name:
                    p=m.pose[m.name.index(r)];q=p.orientation
                    state[r]['physical']=(p.position.x,p.position.y,math.atan2(2*(q.w*q.z+q.x*q.y),1-2*(q.y*q.y+q.z*q.z)))
        subs.append(rospy.Subscriber('/gazebo/model_states',ModelStates,physical,queue_size=1))
        wait(lambda:all(state[r]['physical'] for r in robots),60,'models unavailable');contact=ContactMonitor(out)
        def odom(m,r):
            nonlocal active
            p=m.pose.pose;q=p.orientation;xy=(p.position.x,p.position.y)
            if active and state[r]['last'] is not None:distance[r]+=math.dist(xy,state[r]['last'])
            state[r].update(last=xy,pose=copy.deepcopy(p),odom_at=time.monotonic(),current=(m.twist.twist.linear.x,m.twist.twist.angular.z),yaw=math.atan2(2*(q.w*q.z+q.x*q.y),1-2*(q.y*q.y+q.z*q.z)))
        def raw(m,r):state[r].update(raw=(m.linear.x,m.angular.z),raw_at=time.monotonic())
        def command(m,r):state[r]['cmd']=(m.linear.x,m.angular.z)
        def cell(m,r):
            with mutex:sources[r]=set(zip(m.data[::2],m.data[1::2]))
        def feedback(m,r):
            v=json.loads(m.data);key=r+'/'+v.get('status','?');feedback_count[key]=feedback_count.get(key,0)+1
            if v.get('source')=='planner':plan_count[r]+=1
            if v.get('status')=='STOPPED':gate_proofs[r]=dict(v,received=time.monotonic())
            if v.get('status')!='TRAFFIC_CAPABILITY':plans.write(json.dumps(dict(v,robot_source=r,received=time.monotonic()-t0))+'\n');plans.flush()
        def traffic(m):
            v=json.loads(m.data);mode=v.get('phase','?');traffic_modes[mode]=traffic_modes.get(mode,0)+1
        def coord(m):coordinator_status.update(json.loads(m.data))
        def cloud(c,o,r):
            offsets={f.name:f.offset for f in c.fields};endian='>' if c.is_bigendian else '<'
            dtype=np.dtype(dict(names=['x','y','z'],formats=[endian+'f4']*3,offsets=[offsets[k] for k in ('x','y','z')],itemsize=c.point_step))
            points=np.ndarray((c.height,c.width),dtype=dtype,buffer=c.data,strides=(c.row_step,c.point_step));xyz=np.column_stack([points[k].ravel() for k in ('x','y','z')]);p=o.pose.pose.position;q=o.pose.pose.orientation
            world=transform(xyz,[p.x,p.y,p.z],[q.x,q.y,q.z,q.w]);keep=np.ones(len(xyz),dtype=bool)
            for peer in robots:
                po=state[peer]['pose']
                if peer!=r and po is not None:
                    k,_=peer_keep(world,dict(stamp=rospy.get_time(),position=[po.position.x,po.position.y,po.position.z],yaw=state[peer]['yaw']),c.header.stamp.to_sec(),max_age=.75);keep &= k
            records=np.ndarray((c.height,c.width),dtype=np.dtype('V'+str(c.point_step)),buffer=c.data,strides=(c.row_step,c.point_step)).ravel()
            msg=copy.copy(c);msg.height=1;msg.width=int(keep.sum());msg.row_step=msg.width*c.point_step;msg.data=records[keep].tobytes();matched=copy.deepcopy(o);matched.header.stamp=c.header.stamp
            pubs[r][0].publish(msg);pubs[r][1].publish(matched);frames[r]+=1
        for r in robots:
            pubs[r]=(rospy.Publisher('/'+r+'/team/cloud',PointCloud2,queue_size=4),rospy.Publisher('/'+r+'/team/odom',Odometry,queue_size=4))
            init_pubs[r]=rospy.Publisher('/'+r+'/cmd_vel',Twist,queue_size=1)
            finish[r]=rospy.Publisher('/'+r+'/team_score/finish',Bool,queue_size=1,latch=True)
            inits[r]=rospy.Publisher('/'+r+'/explorer_node/explorer_inited',Float64,queue_size=1,latch=True)
            motions[r]=SimpleActionClient('/'+r+'/path_execution_node/vehicle_execute',VehicleExecuteAction);stops[r]=SimpleActionClient('/'+r+'/path_execution_node/vehicle_stop',VehicleExecuteAction)
            for topic,typ,fn in [('base_link/odometry',Odometry,odom),('topology/raw_cmd_vel',Twist,raw),('cmd_vel',Twist,command),('team_score/plane_cells',Int32MultiArray,cell),('topology/execution_feedback',String,feedback),('topo_planner_node/topology_feedback',String,feedback)]:
                subs.append(rospy.Subscriber('/'+r+'/'+topic,typ,lambda m,r=r,fn=fn:fn(m,r),queue_size=10,buff_size=8*1024*1024))
            c=message_filters.Subscriber('/'+r+'/velodyne/velodyne_points',PointCloud2,queue_size=3,buff_size=4*1024*1024);o=message_filters.Subscriber('/'+r+'/sensor_to_world/odometry',Odometry,queue_size=30)
            s=message_filters.ApproximateTimeSynchronizer([c,o],30,.03);s.registerCallback(lambda c,o,r=r:cloud(c,o,r));syncs.append(s);subs.extend((c,o))
        mission=rospy.Publisher('/team/mission_start',Bool,queue_size=1,latch=True);mission.publish(Bool(False))
        subs.append(rospy.Subscriber('/topology_traffic/status',String,traffic,queue_size=1));subs.append(rospy.Subscriber('/topology_coordinator/status',String,coord,queue_size=1))
        init_traffic=TrafficController()
        def initialization_gate():
            while not init_done.wait(.04):
                now=time.monotonic();poses=[];commands=[]
                for r in robots:
                    p=state[r]['pose'];poses.append((p.position.x,p.position.y,state[r]['yaw']) if p else (0.,0.,0.))
                    ok=init_permissions[r] and now-state[r]['odom_at']<.65 and now-state[r]['raw_at']<.65 and not stopping.is_set() and not errors
                    v,w=state[r]['raw'] if ok else (0.,0.)
                    if p:
                        target=manifest['initialization_targets'][r];d=math.hypot(p.position.x-target[0],p.position.y-target[1]);cap=min(.6,max(.025,.5*(d-.30)));v=max(-cap,min(cap,v))
                    commands.append((v,w))
                if all(state[r]['pose'] for r in robots):commands,_=init_traffic.select(rospy.get_time(),poses,commands,goals=[manifest['initialization_targets'][r] for r in robots],current=[state[r]['current'] for r in robots])
                for r,(v,w) in zip(robots,commands):
                    msg=Twist();msg.linear.x,msg.angular.z=(0.,0.) if stopping.is_set() or errors else (v,w);init_pubs[r].publish(msg)
        gate_thread=threading.Thread(target=initialization_gate,daemon=True);gate_thread.start()
        launch('stack');launch('mapping')
        wait(lambda:all(state[r]['pose'] and frames[r]>0 and sources[r] for r in robots),100,'mapping unavailable')
        for r in robots:
            assert motions[r].wait_for_server(rospy.Duration(15.)) and stops[r].wait_for_server(rospy.Duration(15.))
        origin=rospy.get_time();wait(lambda:rospy.get_time()-origin>=5.,35,'initial mapping settle')
        for r in robots:
            p=state[r]['pose'];target=manifest['initialization_targets'][r];points=[]
            for j in range(16):
                q=copy.deepcopy(p);q.position.x=p.position.x+(target[0]-p.position.x)*j/15.;q.position.y=p.position.y+(target[1]-p.position.y)*j/15.;q.orientation.x=q.orientation.y=q.orientation.z=0.;q.orientation.w=1.;points.append(q)
            g=VehicleExecuteGoal();g.header.frame_id='world';g.header.stamp=rospy.Time.now();g.paths=[PlannerPath(path=points)];motions[r].send_goal(g);init_permissions[r]=True
        pending=set(robots);began=time.monotonic()
        while pending:
            guard()
            for r in list(pending):
                if motions[r].get_state() not in (0,1,6,7):
                    init_permissions[r]=False;assert motions[r].get_state()==3,('initialization execution',r,motions[r].get_state());stops[r].send_goal(VehicleExecuteGoal());pending.remove(r)
            if time.monotonic()-began>65:raise TimeoutError('initialization motion')
            time.sleep(.04)
        wait(lambda:all(stops[r].get_state()==3 for r in robots),12,'initialization stop')
        origin=rospy.get_time();wait(lambda:rospy.get_time()-origin>=3.,25,'initialization parking settle')
        init_done.set();gate_thread.join(1.)
        for r in robots:init_pubs[r].publish(Twist());init_pubs[r].unregister();inits[r].publish(Float64(time.time()))
        rosnode.kill_nodes(['/'+r+'/path_execution_node' for r in robots]);time.sleep(.5)
        launch('execution');launch('exploration')
        wait(lambda:all(r in gate_proofs and time.monotonic()-gate_proofs[r]['received']<3 for r in robots) and bool(coordinator_status),50,'new stop barriers unavailable')
        # Verify real binaries, final publisher ownership, source isolation and
        # original scorer ABI before defining the exploration time origin.
        runtime_info=[]
        for pid in owned():
            try:
                p=Path('/proc')/str(pid);exe=(p/'exe').resolve();libs=sorted(set(x.split()[-1] for x in (p/'maps').read_text().splitlines() if 'libtopo_planner.so' in x or 'libpath_execution.so' in x));runtime_info.append(dict(pid=pid,exe=str(exe),libraries=libs))
            except OSError:pass
        dump(out/'runtime_fingerprints.json',runtime_info)
        assert sum(Path(x['exe']).name=='topo_planner_node' for x in runtime_info)==2
        assert all(any('/catkin_ws/' in p for p in x['libraries']) for x in runtime_info if Path(x['exe']).name=='team_score')
        graph=rosgraph.Master(rospy.get_name()).getSystemState();publishers=dict(graph[0]);subscribers=dict(graph[1])
        for r in robots:
            assert len(publishers.get('/'+r+'/cmd_vel',[]))==1,(r,publishers.get('/'+r+'/cmd_vel'))
            node='/'+r+'/topo_planner_node';assert node in subscribers.get('/'+r+'/team/cloud',[])
            peer=robots[1-robots.index(r)];assert node not in subscribers.get('/'+peer+'/team/cloud',[])
        result['checks']['startup_binary_graph_source_assertions']=True
        result['initial_poses']={r:[state[r]['pose'].position.x,state[r]['pose'].position.y] for r in robots}
        start_sim=rospy.get_time();start_wall=time.monotonic();active=True;mission.publish(Bool(True));event('exploration_start',clock=start_sim,poses=result['initial_poses'])
        last=0.;gain_area=score()['area_m2'];gain_at=time.monotonic()
        while True:
            guard();now=time.monotonic();sim=rospy.get_time();sc=score()
            if now-last>1.:
                last=now;row=dict(runtime_wall_s=now-t0,wall_s=now-start_wall,sim_s=sim-start_sim,**sc,distance_m=dict(distance),traffic_modes=dict(traffic_modes),coordinator=coordinator_status,robots={r:dict(x=state[r]['pose'].position.x,y=state[r]['pose'].position.y,plans=plan_count[r],cmd=state[r]['cmd']) for r in robots})
                metrics.write(json.dumps(row)+'\n');metrics.flush();dump(out/'status.json',row)
            if sc['area_m2']>=7400.5:
                result.update(T95_wall_s=now-start_wall,T95_sim_s=sim-start_sim,threshold_crossing_score=sc,distance_at_T95_m=dict(distance),finish_reason='coverage_threshold');break
            if sc['area_m2']>gain_area+.32:gain_area=sc['area_m2'];gain_at=now
            if now-gain_at>240:raise RuntimeError('coverage_stagnation_240wall')
            time.sleep(.04)
    except Exception as e:
        result['finish_reason']=str(e);errors.append(traceback.format_exc());event('exception',error=str(e))
    finally:
        active=False;stopping.set();init_done.set()
        result['exploration_wall_s']=time.monotonic()-start_wall if start_wall else None
        result['exploration_sim_s']=rospy.get_time()-start_sim if rospy and start_sim is not None else None
        try:
            if mission:mission.publish(Bool(False))
            for r in robots:
                init_permissions[r]=False
                if r in motions:motions[r].cancel_all_goals()
                if r in stops:
                    from control_planner_interface.msg import VehicleExecuteGoal
                    g=VehicleExecuteGoal();g.execution_lease=json.dumps(dict(request_id=token+'/final/'+r));stops[r].send_goal(g)
                if r in finish:finish[r].publish(Bool(True))
            until=min(t0+2345,time.monotonic()+12.)
            while time.monotonic()<until and any(c.get_state() in (0,1,6,7) for c in stops.values()):time.sleep(.05)
            result['stop_ack']={r:c.get_state()==3 for r,c in stops.items()}
            park={r:state[r]['physical'] for r in robots if state[r]['physical']};time.sleep(2.)
            result['parking_drift_m']={r:math.dist(p[:2],state[r]['physical'][:2]) for r,p in park.items()}
        except Exception as e:errors.append('cleanup_stop:'+str(e))
        result.update(score());result.update(distance_m=distance,total_distance_m=sum(distance.values()),plan_counts=plan_count,feedback_counts=feedback_count,traffic_modes=traffic_modes,source_frames=frames,contacts=contact.result() if contact else None)
        with (out/'union_plane_cells.csv').open('w') as f:
            f.write('ix,iy\n');f.writelines('%d,%d\n'%k for k in sorted(set().union(*sources.values())))
        result['checks']['source_csv_match']={r:(out/r/'score/known_plane_cells.csv').exists() and {(int(x['ix']),int(x['iy'])) for x in csv.DictReader((out/r/'score/known_plane_cells.csv').open())}==sources[r] for r in robots}
        dump(out/'result.json',result)
        for _,p in reversed(children):
            if p.poll() is None:
                try:os.killpg(p.pid,signal.SIGINT)
                except ProcessLookupError:pass
        until=min(t0+2380,time.monotonic()+7.)
        while owned() and time.monotonic()<until:time.sleep(.1)
        if owned():kill(signal.SIGTERM);time.sleep(.5)
        if owned():kill(signal.SIGKILL);time.sleep(.3)
        result['runtime_wall_s']=time.monotonic()-t0;result['post_cleanup_runtime']=runtime();result['remaining_owned_pids']=owned()
        result['checks']['within2400wall']=result['runtime_wall_s']<=2400
        result['checks']['runtime_idle']=not result['post_cleanup_runtime']['processes'] and not any(result['post_cleanup_runtime']['ports_in_use'].values())
        dump(out/'result.json',result);l=json.loads(LIMITS.read_text());l['attempts'][-1].update(state='complete',finish_reason=result['finish_reason'],runtime_wall_s=result['runtime_wall_s'],T95_wall_s=result['T95_wall_s'],area_m2=result['area_m2']);l['new_attempts_blocked']=len(l['attempts'])>=4;dump(LIMITS,l);lock_state('idle');done.set()
        event('complete',reason=result['finish_reason'],wall_s=result['runtime_wall_s'],area_m2=result['area_m2']);events.close();metrics.close();plans.close()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--index',type=int,required=True);main(p.parse_args().index)
