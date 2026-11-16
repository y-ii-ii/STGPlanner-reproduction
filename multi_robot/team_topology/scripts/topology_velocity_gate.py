#!/usr/bin/env python3
"""Sole final cmd_vel publisher. The follower MUST publish to raw_cmd_vel."""
import json
import math
import threading
import time

from team_topology.execution import VelocityFence
from team_topology.graph import wire
from team_topology.traffic import TrafficGuard


def main():
    import rospy
    from std_msgs.msg import String
    from nav_msgs.msg import Odometry
    from geometry_msgs.msg import Twist
    rospy.init_node("topology_velocity_gate")
    robot=int(rospy.get_param("~robot_id"))
    fence,lock=VelocityFence(robot),threading.Lock()
    traffic=TrafficGuard(robot)
    traffic_required=rospy.get_param('~traffic_required',True)
    namespace="/robot_%d" % robot
    output=rospy.Publisher(namespace+"/cmd_vel",Twist,queue_size=1)
    feedback=rospy.Publisher(namespace+"/topology/execution_feedback",String,queue_size=20)

    def command(msg):
        with lock:
            try:fence.receive_command(json.loads(msg.data),time.monotonic(),rospy.Time.now().to_sec())
            except (ValueError,KeyError,TypeError):pass

    def permit(msg):
        with lock:
            try:fence.receive_permit(json.loads(msg.data),time.monotonic())
            except (ValueError,KeyError,TypeError):pass

    def raw(msg):
        with lock:fence.receive_raw(msg.linear.x,msg.angular.z,time.monotonic())

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
            fence.receive_odom(msg.header.stamp.to_sec(),(p.x,p.y,yaw),(speed,angular),
                               time.monotonic(),rospy.Time.now().to_sec())
            traffic.odom(msg.header.stamp.to_sec(),(p.x,p.y,yaw),(speed,angular),time.monotonic(),rospy.Time.now().to_sec())

    rospy.Subscriber(namespace+"/topo_planner_node/topology_command",String,command,queue_size=10)
    rospy.Subscriber(namespace+"/topology/execution_permit",String,permit,queue_size=10)
    rospy.Subscriber(namespace+"/topology/raw_cmd_vel",Twist,raw,queue_size=1)
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
                if traffic_required:traffic.before_tick(fence,now)
                velocity,events=fence.tick(now)
                if traffic_required:
                    velocity,extra=traffic.filter(fence,velocity,now,rospy.Time.now().to_sec());events+=extra
                msg=Twist();msg.linear.x,msg.angular.z=velocity
                output.publish(msg)
                fence.output_published(velocity,now)
                traffic.published(velocity,now)
                if traffic_required and now-last_capability>.1:
                    last_capability=now
                    events.append(dict(source='velocity_gate',status='TRAFFIC_CAPABILITY',robot=robot,token=fence.active_token,reverse_ok=traffic.reverse_ok(now,rospy.Time.now().to_sec())))
                for event in events:
                    event["stamp"]=rospy.Time.now().to_sec()
                    feedback.publish(String(data=wire(event)))
            wait.wait(.02)
    finally:
        output.publish(Twist())


if __name__=="__main__":main()
