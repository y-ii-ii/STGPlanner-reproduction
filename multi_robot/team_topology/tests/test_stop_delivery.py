"""Lost ACK delivery is recoverable; old proofs and dead gates never unlock."""
import unittest
from team_topology.execution import ExecutionSupervisor,VelocityFence,no_dispatch_progress
from test_execution import wish

def proof(c):return dict(c,source='velocity_gate',status='STOPPED',fresh_samples=4,stationary_s=.6,zero_s=.6)

class StopDeliveryTests(unittest.TestCase):
 def test_late_stationarity_starts_only_one_fresh_stop_round(self):
  s=ExecutionSupervisor([1],"s",late_stop_recheck=True)
  desired={1:wish()}
  old=s.commands(desired,0.,0.)[1]
  self.assertEqual(s.commands(desired,7.,7.)[1]['mode'],'STOP')
  self.assertEqual(s.states[1]['phase'],'fault')
  proof=dict(old,source='velocity_gate',status='STOPPED',fresh_samples=5,stationary_s=.6,zero_s=.7,stamp=6.)
  self.assertFalse(s.feedback(proof,8.,8.))
  self.assertEqual(s.states[1]['phase'],'fault')
  self.assertFalse(s.feedback(dict(proof,stamp=8.),8.,8.))
  fresh=s.commands(desired,8.,8.)[1]
  self.assertNotEqual(old['stop_id'],fresh['stop_id'])
  self.assertFalse(s.feedback(dict(proof,stamp=8.),8.1,8.1))
  self.assertEqual(s.commands(desired,8.1,8.1)[1]['mode'],'STOP')
  good=dict(proof,stop_id=fresh['stop_id'],stamp=9.)
  self.assertTrue(s.feedback(good,9.,9.))
  self.assertEqual(s.commands(desired,9.,9.)[1]['mode'],'ROUTE')

 def test_late_round_is_bounded_if_fresh_stop_never_arrives(self):
  s=ExecutionSupervisor([1],"s",late_stop_recheck=True)
  desired={1:wish()}
  first=s.commands(desired,0.,0.)[1];s.commands(desired,7.,7.)
  proof=dict(first,source='velocity_gate',status='STOPPED',fresh_samples=5,stationary_s=.6,zero_s=.7,stamp=8.)
  s.feedback(proof,8.,8.)
  retry=s.commands(desired,8.,8.)[1]
  fault=s.commands(desired,15.,15.)[1]
  self.assertTrue(fault['fault'])
  self.assertFalse(s.feedback(dict(proof,stop_id=retry['stop_id'],stamp=16.),16.,16.))
  self.assertEqual(s.commands(desired,16.,16.)[1]['stop_id'],retry['stop_id'])
 def test_dropped_first_ack_is_retransmitted_with_fresh_evidence(self):
  s=ExecutionSupervisor([1],'s');f=VelocityFence(1);acks=[]
  for i in range(61):
   t=i*.05;c=s.commands({1:wish()},t,t)[1];f.receive_command(c,t,t)
   f.receive_odom(t,(0,0,0),(0,0),t,t);v,e=f.tick(t);f.output_published(v,t);acks+=e
  self.assertGreaterEqual(len(acks),3)
  self.assertTrue(all(x['stop_id']==acks[0]['stop_id'] for x in acks))
  self.assertTrue(s.feedback(acks[-1],3.))

 def test_repeated_proof_needs_current_odometry_and_stop_command(self):
  s=ExecutionSupervisor([1],'s');f=VelocityFence(1)
  for i in range(21):
   t=i*.05;f.receive_command(s.commands({1:wish()},t,t)[1],t,t)
   f.receive_odom(t,(0,0,0),(0,0),t,t);v,e=f.tick(t);f.output_published(v,t)
  self.assertEqual(f.phase,'stopped')
  self.assertFalse(f.tick(2.)[1]) # Stale odometry.
  f.receive_odom(3.,(0,0,0),(0,0),3.,3.)
  self.assertFalse(f.tick(3.)[1]) # Also stale STOP lease.

 def test_motion_after_proof_cannot_reuse_stationary_interval(self):
  s=ExecutionSupervisor([1],'s');f=VelocityFence(1)
  for i in range(21):
   t=i*.05;f.receive_command(s.commands({1:wish()},t,t)[1],t,t)
   f.receive_odom(t,(0,0,0),(0,0),t,t);v,e=f.tick(t);f.output_published(v,t)
  for i in range(21,41):
   t=i*.05;f.receive_command(s.commands({1:wish()},t,t)[1],t,t)
   f.receive_odom(t,(t-1.,0,0),(1.,0),t,t);v,e=f.tick(t);f.output_published(v,t)
   self.assertFalse(e)

 def test_timeout_retry_gets_new_nonce_and_has_finite_budget(self):
  s=ExecutionSupervisor([1],'s',stop_retries=1);w={1:wish()};old=s.commands(w,0.,0.)[1]
  new=s.commands(w,6.1,6.1)[1]
  self.assertNotEqual(old['stop_id'],new['stop_id'])
  self.assertFalse(s.feedback(proof(old),6.2))
  for t in (7.,8.,9.,10.,11.):self.assertEqual(s.commands(w,t,t)[1]['stop_id'],new['stop_id'])
  self.assertEqual(s.commands(w,12.2,12.2)[1]['mode'],'STOP');self.assertEqual(s.states[1]['phase'],'fault')
  self.assertFalse(s.feedback(proof(new),12.3))

 def test_only_new_round_proof_can_recover_before_its_deadline(self):
  s=ExecutionSupervisor([1],'s',stop_retries=1);w={1:wish()};old=s.commands(w,0.,0.)[1];new=s.commands(w,6.1,6.1)[1]
  self.assertFalse(s.feedback(proof(old),6.2));self.assertTrue(s.feedback(proof(new),6.8))
  self.assertEqual(s.commands(w,6.9,6.9)[1]['mode'],'ROUTE')

 def test_rolling_updates_do_not_move_dispatch_origin(self):
  s=ExecutionSupervisor([1],'s');w={1:dict(wish(),path=[[0.,0.],[3.,0.]])};c=s.commands(w,0.,0.)[1];s.feedback(proof(c),.7);s.commands(w,.8,.8)
  w[1]['path']=[[.5,0.],[3.,0.]];s.commands(w,1.,1.)
  self.assertTrue(no_dispatch_progress(s.states[1],[.05,0.]))
  self.assertFalse(no_dispatch_progress(s.states[1],[.5,0.]))

if __name__=='__main__':unittest.main()
