"""Own-map body tracking and a final braking shield, independent of ROS.

STG still selects the assigned exploration branch. This adapter executes its
locally certified SE(2) prefix without FALCO's one-metre corner cut. No peer map,
Gazebo geometry or pose-based free-space clearing is used. Occupied and unknown
cells both block motion. Traffic admission is followed by a second shield check.
"""
import math
import numpy as np

# Match the successful Scene4 follower's 2m/s and 60deg/s normal limits.
# Recovery remains a separately bounded low-speed motion certificate.
NORMAL_YAW_RATE=math.radians(60.)
ANGULAR_BRAKE=math.radians(60.)


def wrap(a):
    return math.atan2(math.sin(a), math.cos(a))


def shield_output(grid, fresh, pose, current, approved,margin=.15):
    """Last operation after peer admission; can only retain or stop a command."""
    if tuple(approved)==(0.,0.):return (0.,0.),False
    if margin<.15 and (abs(approved[0])>.2 or abs(approved[1])>.3):return (0.,0.),True
    if not fresh or not grid.braking_safe(pose,current,approved,margin):return (0.,0.),True
    return tuple(approved),False


class BodyGrid:
    def __init__(self, width, height, resolution, origin, data):
        if width<=0 or height<=0 or not math.isfinite(resolution) or resolution<=0:
            raise ValueError('invalid grid')
        self.width,self.height,self.res,self.x0,self.y0=width,height,resolution,*origin
        self.bad=np.asarray(data,dtype=np.int16).reshape(height,width)!=0
        self.integral=np.pad(self.bad.astype(np.int32),((1,0),(1,0))).cumsum(0).cumsum(1)

    def free(self, x,y,yaw,margin=.15):
        if not all(math.isfinite(v) for v in (x,y,yaw)):return False
        c,s=math.cos(yaw),math.sin(yaw);ac,ass=abs(c),abs(s)
        hx,hy=.35+margin,.30+margin;r=self.res/2
        ex,ey=hx*ac+hy*ass,hx*ass+hy*ac
        ax,bx=math.floor((x-ex-self.x0)/self.res),math.floor((x+ex-self.x0)/self.res)
        ay,by=math.floor((y-ey-self.y0)/self.res),math.floor((y+ey-self.y0)/self.res)
        if ax<0 or ay<0 or bx>=self.width or by>=self.height:return False
        a=self.integral
        if a[by+1,bx+1]-a[ay,bx+1]-a[by+1,ax]+a[ay,ax]==0:return True
        yy,xx=np.nonzero(self.bad[ay:by+1,ax:bx+1])
        dx=self.x0+(xx+ax+.5)*self.res-x;dy=self.y0+(yy+ay+.5)*self.res-y
        overlap=(abs(dx)<=ex+r)&(abs(dy)<=ey+r)&(abs(dx*c+dy*s)<=hx+r*(ac+ass))&(abs(-dx*s+dy*c)<=hy+r*(ac+ass))
        return not bool(overlap.any())

    def braking_safe(self, pose, current, command,margin=.15):
        """Latency + requested hold + full braking, with measured signed twist.

        2m/s² braking matches the existing traffic policy; .15s latency and .25s
        hold reserve communication/controller lag. Check intermediate rectangles,
        including rotation, rather than just the endpoint or a circular robot.
        """
        if not all(math.isfinite(v) for v in (*pose,*current,*command)):return False
        if abs(command[0])>2. or abs(command[1])>NORMAL_YAW_RATE+1e-9:return False
        x,y,yaw=pose;v,w=current;dt=.04;t=0.
        horizon=.40+max(max(abs(v),abs(command[0]))/2.,max(abs(w),abs(command[1]))/ANGULAR_BRAKE)+.08
        def approach(a,b,amount):
            # Acceleration can be faster than the braking assumption. Treat
            # increasing same-direction speed as instantaneous, never assume a
            # sluggish motor to certify a fast command near an obstacle.
            if a*b>=0 and abs(b)>abs(a):return b
            return a+max(-amount,min(amount,b-a))
        if not self.free(x,y,yaw,margin):return False
        while t<horizon:
            # Keep measured inertia during the latency interval, then approach
            # the actual approved command, then brake both axes to zero.
            target=current if t<.15 else command if t<.40 else (0.,0.)
            v=approach(v,target[0],2.*dt);w=approach(w,target[1],ANGULAR_BRAKE*dt)
            x+=v*math.cos(yaw+w*dt/2)*dt;y+=v*math.sin(yaw+w*dt/2)*dt;yaw+=w*dt
            if not self.free(x,y,yaw,margin):return False
            t+=dt
        return True


class BodyTracker:
    def __init__(self):
        self.path=[];self.cursor=0;self.key=None;self.margin=.15

    def receive(self, path, key,margin=.15):
        if not path or any(not all(math.isfinite(v) for v in p) for p in path):return False
        if margin not in (.05,.15):return False
        # Repeated publication of the same full path must not reset progress.
        digest=(key,margin,tuple(tuple(p) for p in path));self.margin=margin
        if digest!=self.key:self.path=[tuple(p) for p in path];self.cursor=0;self.key=digest
        return True

    def clear(self):
        self.path=[];self.cursor=0;self.key=None;self.margin=.15

    def propose(self, pose, current, grid):
        if not self.path:return (0.,0.),'NO_PATH'
        tolerance=.035 if self.margin<.15 else .14
        yaw_tolerance=.04 if self.margin<.15 else .12
        anchor_tolerance=.05 if self.margin<.15 else tolerance
        if self.cursor==0 and len(self.path)>1:
            # Rolling replacements are generated while the chassis is moving.
            # Skip an old anchor only if pose and yaw are already on the first
            # directed primitive; do not drive back to a stale planning start.
            a=self.path[0]
            if math.dist(a[:2],pose[:2])<anchor_tolerance:
                # Pose zero is a measured planning anchor, not a requested turn
                # back to its already stale heading. True following in-place
                # turn waypoints remain checked by the ordinary sequence.
                self.cursor=1
                while self.cursor<len(self.path) and math.dist(a[:2],self.path[self.cursor][:2])<1e-7 and abs(wrap(a[2]-self.path[self.cursor][2]))<1e-7:self.cursor+=1
            for k,b in enumerate(self.path[1:],1):
                ex,ey=b[0]-a[0],b[1]-a[1];length=math.hypot(ex,ey)
                if length<.01:continue
                along=((pose[0]-a[0])*ex+(pose[1]-a[1])*ey)/length
                cross=abs((pose[0]-a[0])*ey-(pose[1]-a[1])*ex)/length
                if along>=0 and cross<anchor_tolerance and abs(wrap(b[2]-pose[2]))<.12:self.cursor=k
                break
            if self.cursor==0 and math.dist(a[:2],pose[:2])>=anchor_tolerance:
                # Replan from a fresh pose rather than inventing a reverse
                # connector to an old root across an unexecuted corner.
                return (0.,0.),'PATH_START_DIVERGED'
        # Consume in order, including zero-length turn waypoints. Never select a
        # spatially nearest later segment across a corner/crossing.
        while self.cursor<len(self.path):
            p=self.path[self.cursor];d=math.dist(p[:2],pose[:2]);a=wrap(p[2]-pose[2])
            position_tolerance=.006 if self.margin<.15 and self.cursor==len(self.path)-1 else tolerance
            angle_tolerance=.012 if self.margin<.15 and self.cursor==len(self.path)-1 else yaw_tolerance
            passed=False
            if self.cursor and abs(a)<.12:
                prev=self.path[self.cursor-1];ex,ey=p[0]-prev[0],p[1]-prev[1];length=math.hypot(ex,ey)
                if length>.05:
                    along=((pose[0]-p[0])*ex+(pose[1]-p[1])*ey)/length
                    cross=abs((pose[0]-p[0])*ey-(pose[1]-p[1])*ex)/length
                    passed=along>=0 and cross<tolerance
            if self.margin<.15 and self.cursor==len(self.path)-1:passed=False
            if (d<position_tolerance or passed) and abs(a)<angle_tolerance:self.cursor+=1
            else:break
        if self.cursor==len(self.path):return (0.,0.),'PATH_END'
        p=self.path[self.cursor];dx,dy=p[0]-pose[0],p[1]-pose[1];d=math.hypot(dx,dy)
        target_tolerance=.006 if self.margin<.15 and self.cursor==len(self.path)-1 else tolerance
        if d>=target_tolerance:
            # Join only collinear primitives with the SAME direction and yaw.
            # This allows the common 2m/s cap on long straights while never
            # looking through a certified turn or forward/reverse transition.
            base=p
            for q in self.path[self.cursor+1:]:
                ex,ey=q[0]-p[0],q[1]-p[1]
                if math.hypot(ex,ey)<.01:break
                if abs(wrap(q[2]-base[2]))>.03 or ex*dx+ey*dy<=0:break
                if abs(ex*dy-ey*dx)>max(.01,.03*math.hypot(ex,ey)*d):break
                p=q
            dx,dy=p[0]-pose[0],p[1]-pose[1];d=math.hypot(dx,dy)
        if d<target_tolerance:
            desired=(0.,max(-NORMAL_YAW_RATE,min(NORMAL_YAW_RATE,2.*wrap(p[2]-pose[2]))))
        else:
            # A certified reverse edge retains the chassis yaw, opposite its
            # displacement. Tracking is slow in reverse, not a surprise pi turn.
            bearing=math.atan2(dy,dx);reverse=abs(wrap(bearing-p[2]))>math.pi/2
            error=wrap(bearing+(math.pi if reverse else 0.)-pose[2])
            w=max(-NORMAL_YAW_RATE,min(NORMAL_YAW_RATE,2.2*error));v=min(2.,max(.10,1.2*d))
            if abs(error)>.24:v=0.
            if self.margin<.15:v=min(v,max(.025,1.2*d))
            if reverse:v=-min(.35,v)
            # Stop at each short primitive instead of overshooting into the
            # next turn. The shield independently checks the resulting motion.
            v=math.copysign(min(abs(v),math.sqrt(max(0.,2.*max(0.,d-(.002 if self.margin<.15 else .10))))),v)
            desired=(v,w)
        if self.margin<.15:desired=(max(-.2,min(.2,desired[0])),max(-.3,min(.3,desired[1])))
        # Differential-drive inertia is measured, not inferred from the last
        # zero command. Do not combine a new in-place turn with residual forward
        # motion, or accelerate a straight edge while the previous turn persists.
        # Occupancy/clearance and normal speed caps stay unchanged.
        if abs(desired[0])<1e-9 and abs(desired[1])>.08 and abs(current[0])>.08:
            return (0.,0.),'BRAKE_BEFORE_TURN'
        if abs(desired[0])>.10 and abs(desired[1])<.15 and abs(current[1])>.35:
            return (0.,0.),'SETTLE_BEFORE_TRANSLATION'
        for scale in (1.,.65,.35,.15):
            cmd=tuple(scale*v for v in desired)
            if grid.braking_safe(pose,current,cmd,self.margin):return cmd,'RECENTER_TRACK' if self.margin<.15 else 'TRACK'
        return (0.,0.),'BODY_BRAKE'
