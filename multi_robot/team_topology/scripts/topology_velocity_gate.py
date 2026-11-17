#!/usr/bin/env python3
"""Sole final cmd_vel publisher. The follower MUST publish to raw_cmd_vel."""
import json
import math
import threading
import time

from team_topology.execution import VelocityFence
from team_topology.graph import wire
from team_topology.traffic import TrafficGuard
from team_topology.body_tracking import BodyGrid,BodyTracker,wrap,shield_output


def main():
    import rospy
    from std_msgs.msg import String
    from nav_msgs.msg import Odometry,OccupancyGrid
    from geometry_msgs.msg import Twist
    rospy.init_node("topology_velocity_gate")
    robot=int(rospy.get_param("~robot_id"))
    fence,lock=VelocityFence(robot),threading.Lock()
    traffic=TrafficGuard(robot)
    tracker=BodyTracker()
    own={'grid':None,'grid_at':-1e9,'grid_stamp':-1e9,'path_at':-1e9,'twist':(0.,0.)}
    traffic_required=rospy.get_param('~traffic_required',True)
    namespace="/robot_%d" % robot
    output=rospy.Publisher(namespace+"/cmd_vel",Twist,queue_size=1)
    feedback=rospy.Publisher(namespace+"/topology/execution_feedback",String,queue_size=20)
    request=rospy.Publisher(namespace+"/topology/request_cmd_vel",Twist,queue_size=1)
    trace=rospy.Publisher(namespace+"/topology/body_trace",String,queue_size=1)

    def command(msg):
        with lock:
            try:
                previous=fence.active_token
                fence.receive_command(json.loads(msg.data),time.monotonic(),rospy.Time.now().to_sec())
                if previous!=fence.active_token:tracker.clear();own['path_at']=-1e9
            except (ValueError,KeyError,TypeError):pass

    def permit(msg):
        with lock:
            try:fence.receive_permit(json.loads(msg.data),time.monotonic())
            except (ValueError,KeyError,TypeError):pass

    def certified(msg):
        try:
            v=json.loads(msg.data);stamp=float(v['stamp'])
            with lock:
                if v['token']!=fence.active_token or not 0<=rospy.Time.now().to_sec()-stamp<=.3:return
                if tracker.receive([tuple(map(float,p)) for p in v['path']],(v['token'],int(v['goal_seq'])),float(v.get('body_margin_m',.15))):own['path_at']=time.monotonic()
        except (ValueError,KeyError,TypeError):pass

    def fine_map(msg):
        if msg.header.frame_id!='world':return
        try:
            g=BodyGrid(msg.info.width,msg.info.height,msg.info.resolution,
                       (msg.info.origin.position.x,msg.info.origin.position.y),msg.data)
            with lock:own.update(grid=g,grid_at=time.monotonic(),grid_stamp=msg.header.stamp.to_sec())
        except (ValueError,TypeError):pass

    def traffic_permit(msg):
        try:
            value=json.loads(msg.data)
            if not 0<=rospy.Time.now().to_sec()-value['stamp']<=.3:return
            with lock:traffic.receive(value,fence.active_token,time.monotonic())
        except (ValueError,KeyError,TypeError):pass

    def snapshot(msg):
        try:
            v=json.loads(msg.data);g=v['grid']
            with lock:
                traffic.grid=dict(g,frame=v['frame'],stamp=v['stamp'])
                traffic.grid_received=time.monotonic()
        except (ValueError,KeyError,TypeError):pass

    def odom(msg):
        if msg.header.frame_id!="world":return
        p,q=msg.pose.pose.position,msg.pose.pose.orientation
        yaw=math.atan2(2*(q.w*q.z+q.x*q.y),1-2*(q.y*q.y+q.z*q.z))
        v,w=msg.twist.twist.linear,msg.twist.twist.angular
        speed=math.sqrt(v.x*v.x+v.y*v.y+v.z*v.z)
        angular=math.sqrt(w.x*w.x+w.y*w.y+w.z*w.z)
        with lock:
            signed=(v.x*math.cos(yaw)+v.y*math.sin(yaw),w.z) if msg.child_frame_id=='world' else (v.x,w.z)
            previous=fence.odom
            if previous and msg.header.stamp.to_sec()>previous['stamp']:
                dt=msg.header.stamp.to_sec()-previous['stamp']
                if dt<.5:
                    dv=((p.x-previous['pose'][0])*math.cos(yaw)+(p.y-previous['pose'][1])*math.sin(yaw))/dt
                    dw=wrap(yaw-previous['pose'][2])/dt
                    signed=(dv if abs(dv)>abs(signed[0]) else signed[0],dw if abs(dw)>abs(signed[1]) else signed[1])
            own['twist']=signed
            fence.receive_odom(msg.header.stamp.to_sec(),(p.x,p.y,yaw),(speed,angular),
                               time.monotonic(),rospy.Time.now().to_sec())
            traffic.odom(msg.header.stamp.to_sec(),(p.x,p.y,yaw),(speed,angular),time.monotonic(),rospy.Time.now().to_sec())

    rospy.Subscriber(namespace+"/topo_planner_node/topology_command",String,command,queue_size=10)
    rospy.Subscriber(namespace+"/topology/execution_permit",String,permit,queue_size=10)
    rospy.Subscriber(namespace+"/topology/certified_path",String,certified,queue_size=1)
    rospy.Subscriber(namespace+"/topo_planner_node/native_execution_grid",OccupancyGrid,fine_map,queue_size=1)
    rospy.Subscriber(namespace+"/base_link/odometry",Odometry,odom,queue_size=1)
    rospy.Subscriber(namespace+'/topology/traffic_permit',String,traffic_permit,queue_size=1)
    rospy.Subscriber(namespace+'/topo_planner_node/topology_snapshot',String,snapshot,queue_size=1,buff_size=8*1024*1024)
    wait=threading.Event()
    last_capability=-1e9
    try:
        # Wall-clock loop continues when /clock is paused or the planner exits.
        while not rospy.is_shutdown():
            with lock:
                now=time.monotonic()
                ros_now=rospy.Time.now().to_sec()
                g=own['grid'];fresh=g is not None and now-own['grid_at']<=1.5 and 0<=ros_now-own['grid_stamp']<=1.5 and fence.odom is not None and now-fence.odom['at']<=.3
                proposal,reason=(0.,0.),'NOT_RUNNING'
                if fence.phase=='running' and fresh and now-own['path_at']<=.3:
                    proposal,reason=tracker.propose(fence.odom['pose'],own['twist'],g)
                elif fence.phase=='running':reason='STALE_GEOMETRY_OR_PATH'
                # Peer reservations evaluate this tracker proposal. They must
                # not approve the unrelated FALCO lookahead command.
                req=Twist();req.linear.x,req.angular.z=proposal;request.publish(req)
                fence.receive_raw(*proposal,now)
                if traffic_required:traffic.before_tick(fence,now)
                velocity,events=fence.tick(now)
                if traffic_required:
                    velocity,extra=traffic.filter(fence,velocity,now,ros_now);events+=extra
                # Recheck the ACTUAL traffic-approved output, which can differ
                # from this tick's proposal (including an authorized retreat).
                velocity,rejected=shield_output(g,fresh and now-own['path_at']<=.3,fence.odom['pose'] if fence.odom else None,own['twist'],velocity,tracker.margin)
                if rejected:reason='FINAL_BODY_BRAKE'
                msg=Twist();msg.linear.x,msg.angular.z=velocity
                output.publish(msg)
                fence.output_published(velocity,now)
                traffic.published(velocity,now)
                trace.publish(String(data=wire(dict(stamp=ros_now,token=fence.active_token,phase=fence.phase,
                    pose=fence.odom['pose'] if fence.odom else None,twist=own['twist'],proposal=proposal,output=velocity,
                    reason=reason,cursor=tracker.cursor,path_size=len(tracker.path),body_margin_m=tracker.margin,map_stamp=own['grid_stamp']))))
                if traffic_required and now-last_capability>.1:
                    last_capability=now
                    events.append(dict(source='velocity_gate',status='TRAFFIC_CAPABILITY',robot=robot,token=fence.active_token,reverse_ok=traffic.reverse_ok(now,rospy.Time.now().to_sec())))
                for event in events:
                    event["stamp"]=rospy.Time.now().to_sec()
                    feedback.publish(String(data=wire(event)))
            wait.wait(.04)
    finally:
        output.publish(Twist())


if __name__=="__main__":main()
