#!/usr/bin/env python3
"""Traffic authority: observed odometry, executor paths and bounded permits."""
import json,math,threading,time
from team_topology.graph import wire
from team_topology.execution import token
from team_topology.traffic import Reservations

def main():
    import rospy
    from std_msgs.msg import String
    from geometry_msgs.msg import Twist
    from nav_msgs.msg import Odometry,Path
    rospy.init_node('topology_traffic');lock=threading.Lock();policy=Reservations()
    states=[dict(pose=None,stamp=None,odom_at=-1e9,raw=(0.,0.),raw_at=-1e9,token=None,path=[],path_at=-1e9,reverse=False,cap_at=-1e9,current=(0.,0.)) for _ in range(2)]
    acks={};seq=0;sent=0
    pubs=[rospy.Publisher('/robot_%d/topology/traffic_permit'%(i+1),String,queue_size=1) for i in range(2)]
    status=rospy.Publisher('~status',String,queue_size=1)
    def command(m,i):
        try:
            v=json.loads(m.data);new=token(v) if v.get('mode')=='ROUTE' else None
            with lock:
                if states[i]['token']!=new:acks.pop(i,None)
                states[i]['token']=new
        except (ValueError,KeyError,TypeError):pass
    def odom(m,i):
        if m.header.frame_id!='world':return
        stamp=m.header.stamp.to_sec()
        if not 0<=rospy.Time.now().to_sec()-stamp<=.3:return
        p,q=m.pose.pose.position,m.pose.pose.orientation
        yaw=math.atan2(2*(q.w*q.z+q.x*q.y),1-2*(q.y*q.y+q.z*q.z))
        with lock:
            s=states[i];v,w=m.twist.twist.linear.x,m.twist.twist.angular.z
            if s['stamp'] is not None:
                dt=stamp-s['stamp']
                if dt<=0:return
                if dt<.5:
                    # Body-frame speed inferred from pose prevents a missing/
                    # zero twist field from erasing the braking reserve.
                    dv=((p.x-s['pose'][0])*math.cos(yaw)+(p.y-s['pose'][1])*math.sin(yaw))/dt
                    dw=math.atan2(math.sin(yaw-s['pose'][2]),math.cos(yaw-s['pose'][2]))/dt
                    if abs(dv)>abs(v):v=dv
                    if abs(dw)>abs(w):w=dw
            s.update(pose=(p.x,p.y,yaw),stamp=stamp,odom_at=time.monotonic(),current=(v,w))
    def raw(m,i):
        v,w=m.linear.x,m.angular.z
        if not math.isfinite(v) or not math.isfinite(w):return
        with lock:states[i].update(raw=(max(-2.,min(2.,v)),max(-1.5,min(1.5,w))),raw_at=time.monotonic())
    def path(m,i):
        if m.header.frame_id!='world':return
        with lock:states[i].update(path=[(p.pose.position.x,p.pose.position.y) for p in m.poses],path_at=time.monotonic())
    def feedback(m,i):
        try:
            v=json.loads(m.data)
            with lock:
                if v.get('token')!=states[i]['token']:return
                if v.get('status')=='TRAFFIC_STOPPED' and v.get('source')=='velocity_gate' and v.get('epoch')==policy.epoch and int(v.get('fresh_samples',0))>=3 and float(v.get('stationary_s',0))>=.5 and float(v.get('zero_s',0))>=.5:acks[i]=v['epoch']
                if v.get('status')=='TRAFFIC_CAPABILITY':states[i].update(reverse=v.get('reverse_ok') is True,cap_at=time.monotonic())
        except (ValueError,KeyError,TypeError):pass
    for i in range(2):
        for topic,typ,fn in [('topo_planner_node/topology_command',String,command),('base_link/odometry',Odometry,odom),('topology/request_cmd_vel',Twist,raw),('path_execution_node/local_path',Path,path),('topology/execution_feedback',String,feedback)]:
            rospy.Subscriber('/robot_%d/'%(i+1)+topic,typ,lambda m,i=i,fn=fn:fn(m,i),queue_size=5)
    wait=threading.Event()
    while not rospy.is_shutdown():
        with lock:
            now=time.monotonic();seq+=1;paths=[];poses=[s['pose'] for s in states]
            if all(p is not None for p in poses) and all(now-s['odom_at']<=.3 for s in states):
                for s in states:
                    p=s['path'] if now-s['path_at']<2. else []
                    if p:
                        j=min(range(len(p)),key=lambda j:math.dist(p[j],s['pose'][:2]));p=p[j:];sampled=[]
                        for q in p:
                            if not sampled or math.dist(q,sampled[-1])>=.4:sampled.append(q)
                        if p and (not sampled or sampled[-1]!=p[-1]):sampled.append(p[-1])
                        p=sampled
                    paths.append(p)
                commands=[s['raw'] if s['token'] and now-s['raw_at']<=.3 else (0.,0.) for s in states]
                moves,modes,info=policy.select(now,poses,commands,[s['current'] for s in states],paths,acks,[s['reverse'] and now-s['cap_at']<=.3 for s in states])
            else:
                if policy.phase!='BRAKE':policy.brake(now)
                moves=[(0.,0.)]*2;modes=['HOLD']*2;info={'epoch':policy.epoch,'phase':'STALE_ODOMETRY'}
            for i,pub in enumerate(pubs):
                msg=wire(dict(robot=i+1,seq=seq,token=states[i]['token'],stamp=rospy.Time.now().to_sec(),epoch=policy.epoch,mode=modes[i],velocity=moves[i]))
                pub.publish(String(data=msg));sent+=len(msg.encode())+4
            status.publish(String(data=wire(dict(info,paths=paths,modes=modes,velocity=moves,application_published_bytes=sent))))
        wait.wait(.05)

if __name__=='__main__':main()
