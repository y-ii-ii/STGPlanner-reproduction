#!/usr/bin/env python3
"""Traffic authority: observed odometry, executor paths and bounded permits."""
import json,math,threading,time
from team_topology.graph import wire
from team_topology.execution import token
from team_topology.traffic import Reservations
from team_topology.body_tracking import NORMAL_YAW_RATE

def main():
    import rospy
    from std_msgs.msg import String
    from nav_msgs.msg import Odometry
    rospy.init_node('topology_traffic');lock=threading.Lock();policy=Reservations()
    states=[dict(pose=None,stamp=None,odom_at=-1e9,request=None,token=None,
                 reverse=False,cap_at=-1e9,current=(0.,0.)) for _ in range(2)]
    acks={};seq=0;sent=0
    pubs=[rospy.Publisher('/robot_%d/topology/traffic_permit'%(i+1),String,queue_size=1) for i in range(2)]
    status=rospy.Publisher('~status',String,queue_size=1)
    def command(m,i):
        try:
            v=json.loads(m.data);new=token(v) if v.get('mode')=='ROUTE' else None
            with lock:
                if states[i]['token']!=new:
                    acks.pop(i,None);states[i]['request']=None
                states[i]['token']=new
        except (ValueError,KeyError,TypeError):pass
    def odom(m,i):
        if m.header.frame_id!='world':return
        stamp=m.header.stamp.to_sec()
        if not 0<=rospy.Time.now().to_sec()-stamp<=.3:return
        p,q=m.pose.pose.position,m.pose.pose.orientation
        yaw=math.atan2(2*(q.w*q.z+q.x*q.y),1-2*(q.y*q.y+q.z*q.z))
        linear=m.twist.twist.linear
        v=linear.x*math.cos(yaw)+linear.y*math.sin(yaw) if m.child_frame_id=='world' else linear.x
        w=m.twist.twist.angular.z
        if not all(math.isfinite(value) for value in (stamp,p.x,p.y,yaw,v,w)):return
        with lock:
            s=states[i]
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
    def preview(m,i):
        try:
            body=json.loads(m.data);stamp=float(body['stamp'])
            vx,wz=map(float,body['proposal'])
            path=[(float(x),float(y)) for x,y in body['reservation_prefix']]
            if (not 0<=rospy.Time.now().to_sec()-stamp<=.3 or abs(vx)>2. or abs(wz)>NORMAL_YAW_RATE
                    or not all(math.isfinite(v) for v in (vx,wz))
                    or not all(math.isfinite(v) for point in path for v in point)):
                return
            if body['phase']!='running':
                vx,wz=0.,0.;path=[]
            with lock:
                state=states[i];last=state['request']
                # Reserve the gate's actual unconsumed certificate, in the
                # same timestamped packet as its matching local velocity.
                if (not state['token'] or body['token']!=state['token']
                        or last is not None and stamp<last['stamp']):
                    return
                state['request']=dict(stamp=stamp,at=time.monotonic(),path=path,raw=(vx,wz))
        except (ValueError,KeyError,TypeError):pass
    def feedback(m,i):
        try:
            v=json.loads(m.data)
            with lock:
                if v.get('token')!=states[i]['token']:return
                if v.get('status')=='TRAFFIC_STOPPED' and v.get('source')=='velocity_gate' and v.get('epoch')==policy.epoch and int(v.get('fresh_samples',0))>=3 and float(v.get('stationary_s',0))>=.5 and float(v.get('zero_s',0))>=.5:acks[i]=v['epoch']
                if v.get('status')=='TRAFFIC_CAPABILITY':states[i].update(reverse=v.get('reverse_ok') is True,cap_at=time.monotonic())
        except (ValueError,KeyError,TypeError):pass
    for i in range(2):
        for topic,typ,fn in [('topo_planner_node/topology_command',String,command),('base_link/odometry',Odometry,odom),
                            ('topology/body_trace',String,preview),('topology/execution_feedback',String,feedback)]:
            rospy.Subscriber('/robot_%d/'%(i+1)+topic,typ,lambda m,i=i,fn=fn:fn(m,i),queue_size=5)
    wait=threading.Event()
    while not rospy.is_shutdown():
        with lock:
            now=time.monotonic();ros_now=rospy.Time.now().to_sec();seq+=1;paths=[];poses=[s['pose'] for s in states]
            if all(p is not None for p in poses) and all(now-s['odom_at']<=.3 for s in states):
                commands=[]
                for s in states:
                    request=s['request']
                    fresh=request is not None and now-request['at']<=.3 and 0<=ros_now-request['stamp']<=.3
                    paths.append(request['path'] if fresh else [])
                    commands.append(request['raw'] if fresh else (0.,0.))
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
