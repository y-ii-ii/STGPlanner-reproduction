"""Short-route reservations plus post-brake evidence, using observed state only.

Geometry and conservative 2 m/s² braking reserve follow Old dual02. The explicit
yield epoch and local retreat certificate are new; they do not complete tasks.
"""
import math
from .traffic_geometry import swept_clearance, braking_uncertainty, segment_distance, free_reverse, RADIUS

def restrict_pass(current,approved):
    """Only scale DOWN the admitted curve; never revive a newer brake/turn.

    A PASS is an upper permission bound, not an old velocity command. A changed
    sign/zero component waits for a compatible fresh permit. RETREAT remains a
    separate, explicitly certified operation and is not routed through this.
    """
    if not all(math.isfinite(v) for v in (*current,*approved)):return (0.,0.)
    if sum(map(abs,current))<1e-6:return (0.,0.)
    scale=1.
    for request,limit in zip(current,approved):
        if abs(limit)<1e-6:continue
        if abs(request)<1e-6 or request*limit<0:return (0.,0.)
        scale=min(scale,abs(request/limit))
    return tuple(v*scale for v in approved)


def route_conflict(paths):
    if not all(paths):
        return False
    # Sampled actual executor paths, not allocator straight lines. The 0.5 m
    # sampling reserve prevents crossings between samples being overlooked.
    def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    for a,b in zip(paths[0],paths[0][1:]):
        for c,d in zip(paths[1],paths[1][1:]):
            if cross(a,b,c)*cross(a,b,d)<=0 and cross(c,d,a)*cross(c,d,b)<=0:
                if max(min(a[0],b[0]),min(c[0],d[0]))<=min(max(a[0],b[0]),max(c[0],d[0])) and max(min(a[1],b[1]),min(c[1],d[1]))<=min(max(a[1],b[1]),max(c[1],d[1])):return True
            if min(segment_distance(a,c,d),segment_distance(b,c,d),segment_distance(c,a,b),segment_distance(d,a,b))<1.2:return True
    return False


class Reservations:
    def __init__(self):
        self.epoch=0;self.phase='FREE';self.winner=0;self.began=0.;self.clear_since=None
        self.retreat_origin=None;self.retreat_used=0.

    def brake(self,now):
        self.epoch+=1;self.phase='BRAKE';self.began=now;self.clear_since=None

    @staticmethod
    def following(poses, commands, measured, gap, margin):
        # Overlapping future polylines can describe two cars following the same
        # corridor. Permit that only with a straight, aligned current request
        # and room for the rear car to stop behind a suddenly stationary leader.
        if measured is None or any(v<=.05 or abs(w)>.025 for v,w in commands):
            return None
        if any(v<-.05 or abs(w)>.12 for v,w in measured):
            return None
        yaw=poses[0][2]
        diff=poses[1][2]-yaw
        if abs(math.atan2(math.sin(diff),math.cos(diff)))>.16:
            return None
        dx=poses[1][0]-poses[0][0];dy=poses[1][1]-poses[0][1]
        longitudinal=dx*math.cos(yaw)+dy*math.sin(yaw)
        lateral=-dx*math.sin(yaw)+dy*math.cos(yaw)
        if abs(lateral)>.40:return None
        front=1 if longitudinal>0 else 0
        rear=1-front
        for scale in (1.,.75,.5,.25):
            move=list(commands)
            rv,rw=commands[rear]
            move[rear]=(rv*scale,rw*scale)
            rear_speed=max(abs(measured[rear][0]),rv*scale)
            # Circumscribed rectangles, 0.4 s combined approval/sensing
            # delay, 2 m/s² braking, and the existing inter-car margin.
            if abs(longitudinal)<2*RADIUS+margin+.4*rear_speed+rear_speed**2/4:
                continue
            if gap(move)>=margin:return move
        return None

    def select(self,now,poses,commands,current,paths,acks,reverse_ok):
        zero=[(0.,0.),(0.,0.)];margin=.24
        def gap(v):return swept_clearance(poses,v)-braking_uncertainty(current,v)
        both=gap(commands);shared_path=route_conflict(paths);conflict=shared_path or both<margin
        if shared_path and self.phase in ('FREE','PASS'):
            following=self.following(poses,commands,current,gap,margin)
            if following is not None:
                # Measure new proposals every tick. Existing epoch brake/retreat
                # barriers still run before this can be used again.
                self.clear_since=None
                return following,['PASS']*2,dict(epoch=self.epoch,phase='FOLLOW',winner=self.winner)
        info={'epoch':self.epoch,'phase':self.phase,'winner':self.winner}
        if self.phase=='FREE' and not conflict:return list(commands),['PASS']*2,info
        if self.phase=='FREE':
            if sum(map(abs,commands[self.winner]))<1e-4:self.winner=1-self.winner
            self.brake(now)
        if self.phase=='BRAKE':
            # Ownership of an intersecting route never changes on elapsed time
            # alone. Both velocity gates must prove fresh post-epoch stops.
            if all(acks.get(i)==self.epoch for i in (0,1)):
                self.phase='PASS';self.began=now
            else:return zero,['HOLD']*2,dict(info,epoch=self.epoch,phase='BRAKE')
        if self.phase=='RETREAT':
            loser=1-self.winner
            if (math.dist(poses[loser][:2],self.retreat_origin)>=.75
                    or now-self.began>4.5 or not reverse_ok[loser]):
                self.brake(now)
                return zero,['HOLD']*2,dict(info,epoch=self.epoch,phase='BRAKE')
            move=list(zero);move[loser]=(-.2,0.)
            if gap(move)>=margin:return move,['HOLD' if i!=loser else 'RETREAT' for i in (0,1)],dict(info,epoch=self.epoch,phase='RETREAT')
            self.brake(now)
            return zero,['HOLD']*2,dict(info,epoch=self.epoch,phase='BRAKE')
        if not conflict:
            if self.clear_since is None:self.clear_since=now
            if now-self.clear_since>=.6:
                self.phase='FREE';self.retreat_used=0.
                return list(commands),['PASS']*2,dict(info,epoch=self.epoch,phase='FREE')
        else:self.clear_since=None
        winner=self.winner
        for scale in (1.,.5,.25,.1):
            move=list(zero);move[winner]=tuple(v*scale for v in commands[winner])
            if sum(abs(v) for v in move[winner])>1e-4 and gap(move)>=margin:
                return move,['PASS' if i==winner else 'HOLD' for i in (0,1)],dict(info,epoch=self.epoch,phase='PASS',scale=scale)
        if now-self.began>1. and self.retreat_used<1.6:
            loser=1-winner;move=list(zero);move[loser]=(-.2,0.)
            if reverse_ok[loser] and gap(move)>=margin:
                self.phase='RETREAT';self.retreat_origin=poses[loser][:2];self.began=now;self.retreat_used+=.8
                return move,['RETREAT' if i==loser else 'HOLD' for i in (0,1)],dict(info,epoch=self.epoch,phase='RETREAT')
        if now-self.began>6.:
            self.winner=1-winner;self.brake(now)
        return zero,['HOLD']*2,dict(info,epoch=self.epoch,phase=self.phase)


class TrafficGuard:
    """Per-robot gate: traffic permission never overrides execution fencing."""
    def __init__(self,robot):
        self.robot=robot;self.permit={};self.received=-math.inf;self.seq=0
        self.epoch=None;self.hold_start=None;self.samples=0;self.stationary=None
        self.zero_since=None;self.zero_last=-math.inf;self.sent=False;self.prev=None
        self.grid=None;self.grid_received=-math.inf;self.pause_at=None
        self.wait_since=None;self.wait_token=None

    def receive(self,p,token,now):
        if (p.get('token')!=token or int(p.get('robot',0))!=self.robot
                or int(p.get('seq',0))<=self.seq or p.get('mode') not in ('PASS','HOLD','RETREAT')
                or not all(math.isfinite(float(v)) for v in p.get('velocity',[]))
                or len(p.get('velocity',[]))!=2 or abs(p['velocity'][0])>2. or abs(p['velocity'][1])>1.5):return False
        if p['mode']=='HOLD' and (p['epoch']!=self.epoch or self.permit.get('mode')!='HOLD' or self.permit.get('token')!=token):
            self.hold_start=now;self.hold_ros=p['stamp'];self.samples=0;self.stationary=None
            self.zero_since=None;self.zero_last=-math.inf;self.sent=False
        self.permit=dict(p);self.received=now;self.seq=p['seq'];self.epoch=p['epoch']
        if self.wait_token!=token:self.wait_token=token;self.wait_since=None
        if p['mode']=='HOLD' and self.wait_since is None:self.wait_since=now
        elif p['mode']!='HOLD' and sum(map(abs,p['velocity']))>1e-4:self.wait_since=None
        return True

    def odom(self,stamp,pose,twist,now,ros_now):
        if not all(math.isfinite(v) for v in [stamp,*pose,*twist]) or not 0<=ros_now-stamp<=.3:return
        old=self.prev
        if old is not None and stamp<=old[0]:return
        self.prev=(stamp,pose,now)
        still=abs(twist[0])<=.05 and abs(twist[1])<=.09
        if old:
            dt=stamp-old[0];dyaw=math.atan2(math.sin(pose[2]-old[1][2]),math.cos(pose[2]-old[1][2]))
            still=still and math.dist(pose[:2],old[1][:2])/dt<=.05 and abs(dyaw)/dt<=.09
        if self.permit.get('mode')=='HOLD' and stamp>self.hold_ros:
            if not old or now-old[2]>.3 or not still:self.stationary=None;self.samples=0
            else:
                if self.stationary is None:self.stationary=now
                self.samples+=1

    def reverse_ok(self,now,ros_now):
        return bool(self.grid and self.prev and now-self.grid_received<=1.5
                    and 0<=ros_now-self.grid['stamp']<=1.5
                    and free_reverse(self.grid,self.prev[1]))

    def before_tick(self,fence,now):
        if (self.permit.get('mode')=='HOLD' and self.permit.get('token')==fence.active_token
                and now-self.received<=.3 and self.hold_start is not None):
            # Authorized traffic waiting does not masquerade as wall stagnation.
            if self.pause_at is not None:fence.armed_at+=max(0.,now-self.pause_at)
            fence.progress_at=now
            if self.wait_since is not None and now-self.wait_since>20.:fence._trip('TRAFFIC_WAIT_REPLAN')
        self.pause_at=now

    def filter(self,fence,velocity,now,ros_now):
        events=[]
        fresh=(now-self.received<=.3 and self.permit.get('token')==fence.active_token)
        if fence.phase=='running':
            if not fresh:
                if now-fence.armed_at>1.:fence._trip('TRAFFIC_TIMEOUT')
                velocity=(0.,0.)
            else:
                mode=self.permit['mode']
                velocity=(restrict_pass(velocity,tuple(self.permit['velocity'])) if mode=='PASS'
                          else tuple(self.permit['velocity']) if mode=='RETREAT' else (0.,0.))
                if mode=='RETREAT' and not self.reverse_ok(now,ros_now):velocity=(0.,0.)
        else:velocity=(0.,0.)
        if (fresh and self.permit.get('mode')=='HOLD' and not self.sent
                and self.prev and now-self.prev[2]<=.3 and self.stationary is not None
                and now-self.stationary>=.5 and self.samples>=3
                and self.zero_since is not None and now-self.zero_since>=.5 and now-self.zero_last<=.1):
            events=[{'source':'velocity_gate','status':'TRAFFIC_STOPPED','robot':self.robot,
                     'epoch':self.epoch,'token':self.permit['token'],'fresh_samples':self.samples,
                     'stationary_s':now-self.stationary,'zero_s':now-self.zero_since}]
            self.sent=True
        return velocity,events

    def published(self,v,now):
        if tuple(v)==(0.,0.):
            if self.zero_since is None or now-self.zero_last>.1:self.zero_since=now
            self.zero_last=now
        else:self.zero_since=None
