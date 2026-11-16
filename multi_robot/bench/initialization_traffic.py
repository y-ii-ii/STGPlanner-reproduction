"""Unchanged Old dual02 initialization admission policy; no exploration allocation."""
from team_topology.traffic_geometry import *
class TrafficController:
 def __init__(self):self.winner=0;self.conflict_start=None;self.retreat=None;self.retreat_used=0.;self.lease_until=0.;self.last_mode=None
 def select(self,now,poses,commands,grids=None,goals=None,current=None):
  def predicted(proposal,limits=None):return swept_clearance(poses,proposal,goals=limits)-braking_uncertainty(current,proposal)
  margin=.24;info={};both=predicted(commands,goals);info['both_clearance_lower_m']=both
  alone=[]
  for i in range(2):
   one=[(0.,0.),(0.,0.)];one[i]=commands[i];alone.append(predicted(one,goals))
  if both>=margin and min(alone)>=margin:
   if math.dist(poses[0][:2],poses[1][:2])>3.:self.conflict_start=None;self.retreat=None;self.retreat_used=0.;self.lease_until=0.
   return list(commands),dict(info,mode='BOTH',winner=self.winner,predicted_clearance_lower_m=both)
  if self.conflict_start is None:self.conflict_start=now;self.lease_until=now+5.
  if now>=self.lease_until:self.winner=1-self.winner;self.lease_until=now+5.
  # Test the actual complete command set, including the parked peer.
  order=[self.winner,1-self.winner]
  if sum(abs(x) for x in commands[order[0]])<1e-4:order.reverse()
  for winner in order:
   for scale in [1.,.5,.25,.1]:
    proposed=[(0.,0.),(0.,0.)];proposed[winner]=tuple(x*scale for x in commands[winner]);gap=alone[winner] if scale==1 else predicted(proposed,goals)
    if gap>=margin and sum(abs(x) for x in commands[winner])>1e-4:
     self.winner=winner;self.retreat=None
     return proposed,dict(info,mode='YIELD',winner=winner,speed_scale=scale,predicted_clearance_lower_m=gap,wait_sim_s=now-self.conflict_start)
  if self.retreat is not None:
   loser,origin,started=self.retreat;distance=math.dist(poses[loser][:2],origin[:2])
   if distance>=.75 or now-started>4.5:self.retreat_used+=distance;self.retreat=None
  if self.retreat is None and now-self.conflict_start>.6 and self.retreat_used<1.6 and grids:
   for loser in [1-self.winner,self.winner]:
    g=grids[loser]
    if g and g.get('fresh',False) and free_reverse(g,poses[loser]):self.retreat=(loser,poses[loser],now);break
  if self.retreat is not None:
   loser,origin,started=self.retreat;proposed=[(0.,0.),(0.,0.)];proposed[loser]=(-.2,0.)
   gap=predicted(proposed)
   if gap>=margin and grids and grids[loser] and grids[loser].get('fresh',False) and free_reverse(grids[loser],poses[loser],distance=.25):
    return proposed,dict(info,mode='RETREAT',winner=1-loser,retreat_robot=loser,predicted_clearance_lower_m=gap,wait_sim_s=now-self.conflict_start)
   self.retreat=None
  rotations=[(0.,w) for v,w in commands];gap=predicted(rotations)
  if gap<margin:rotations=[(0.,0.),(0.,0.)]
  return rotations,dict(info,mode='HOLD_REPLAN',winner=self.winner,predicted_clearance_lower_m=max(0.,gap),wait_sim_s=now-self.conflict_start,request_replan=now-self.conflict_start>6.)
