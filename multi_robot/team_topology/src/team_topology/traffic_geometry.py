# Adapted from the preserved Old dual02 traffic geometry; no source file is modified.
"""Peer admission/yield state machine. Uses odometry and observed local grids only."""
import math
LENGTH=.7;WIDTH=.6;RADIUS=math.hypot(LENGTH,WIDTH)/2
def rectangle(p,length=LENGTH,width=WIDTH):
 c=math.cos(p[2]);s=math.sin(p[2]);return [(p[0]+c*x-s*y,p[1]+s*x+c*y) for x,y in [(-length/2,-width/2),(length/2,-width/2),(length/2,width/2),(-length/2,width/2)]]
def segment_distance(p,a,b):
 x=b[0]-a[0];y=b[1]-a[1];t=max(0.,min(1.,((p[0]-a[0])*x+(p[1]-a[1])*y)/(x*x+y*y))) if x*x+y*y>1e-15 else 0.
 return math.hypot(p[0]-a[0]-t*x,p[1]-a[1]-t*y)
def clearance(a,b):
 separated=False
 for polygon in (a,b):
  for i,p in enumerate(polygon):
   q=polygon[(i+1)%4];ax=-(q[1]-p[1]);ay=q[0]-p[0];u=[ax*x+ay*y for x,y in a];v=[ax*x+ay*y for x,y in b]
   if max(u)<min(v)-1e-10 or max(v)<min(u)-1e-10:separated=True
 if not separated:return 0.
 return min(segment_distance(p,poly[i],poly[(i+1)%4]) for points,poly in [(a,b),(b,a)] for p in points for i in range(4))
def advance(p,v,w,dt):
 x,y,yaw=p
 if abs(w)<1e-8:return (x+v*math.cos(yaw)*dt,y+v*math.sin(yaw)*dt,yaw)
 return (x+v/w*(math.sin(yaw+w*dt)-math.sin(yaw)),y-v/w*(math.cos(yaw+w*dt)-math.cos(yaw)),yaw+w*dt)
def swept_clearance(poses,commands,horizon=2.5,dt=.1,goals=None):
 # Continuous-motion lower bound: subtract a Lipschitz bound between samples.
 speed=sum(abs(v)+RADIUS*abs(w) for v,w in commands);bound=speed*dt/2
 positions=list(poses);remaining=[math.hypot(goals[i][0]-p[0],goals[i][1]-p[1]) if goals and goals[i] else float('inf') for i,p in enumerate(poses)]
 minimum=1e9
 for _ in range(int(round(horizon/dt))+1):
  if math.dist(positions[0][:2],positions[1][:2])>2*RADIUS+2.:
   gap=math.dist(positions[0][:2],positions[1][:2])-2*RADIUS
  else:gap=clearance(rectangle(positions[0]),rectangle(positions[1]))
  minimum=min(minimum,gap)
  for i,(v,w) in enumerate(commands):
   step_v=math.copysign(min(abs(v),remaining[i]/dt),v);positions[i]=advance(positions[i],step_v,w,dt);remaining[i]=max(0.,remaining[i]-abs(step_v)*dt)
 return minimum-bound
def braking_uncertainty(current,commands,horizon=2.5):
 if current is None:return 0.
 extra=0.
 for (actual_v,actual_w),(v,w) in zip(current,commands):
  # Team-only admission reserve: 2m/s2 and2rad/s2; the prior8/10 assumptions were optimistic against recorded stopping.
  if actual_v*v<0 or abs(actual_v)>abs(v):extra+=(actual_v-v)**2/4.
  extra+=(RADIUS+abs(v)*horizon)*(actual_w-w)**2/4.
 return extra
def free_footprint(grid,pose,margin=.15):
 if not grid or grid.get('frame')!='world':return False
 res=grid['resolution'];ox,oy=grid['origin'];width,height=grid['width'],grid['height'];poly=rectangle(pose,LENGTH+2*margin,WIDTH+2*margin)
 lo_x=math.floor((min(p[0] for p in poly)-ox)/res);hi_x=math.floor((max(p[0] for p in poly)-ox)/res);lo_y=math.floor((min(p[1] for p in poly)-oy)/res);hi_y=math.floor((max(p[1] for p in poly)-oy)/res)
 if lo_x<0 or lo_y<0 or hi_x>=width or hi_y>=height:return False
 for y in range(lo_y,hi_y+1):
  for x in range(lo_x,hi_x+1):
   if grid['data'][y*width+x]==0:continue
   cell=rectangle((ox+(x+.5)*res,oy+(y+.5)*res,0),res,res)
   if clearance(poly,cell)<1e-8:return False
 return True
def free_reverse(grid,pose,distance=.8):return all(free_footprint(grid,advance(pose,-distance,0,i/16.)) for i in range(17))
