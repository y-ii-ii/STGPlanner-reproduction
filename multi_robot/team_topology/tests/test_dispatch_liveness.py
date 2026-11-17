"""Scheduling liveness AND old-owner safety under adversarial stop ordering."""
import unittest
from team_topology.execution import ExecutionSupervisor


def wish(r,task):return dict(robot=r,mode='ROUTE',task=task,version=1,path=[])
def ack(s,r,t):
 st=s.states[r]
 return s.feedback(dict(robot=r,allocation_session=s.session,source='velocity_gate',status='STOPPED',stop_id=st['stop_id'],request_ids=list(st['requests']),fresh_samples=3,stationary_s=.6,zero_s=.6),t)


class DispatchLivenessTests(unittest.TestCase):
 def ready(self):
  s=ExecutionSupervisor((1,2),'s');w={1:wish(1,'A'),2:wish(2,'B')};s.commands(w,0,0)
  self.assertTrue(ack(s,1,.7));self.assertTrue(ack(s,2,.7));s.commands(w,.8,.8);return s,w

 def test_unrelated_repeated_stop_cannot_starve_ready_robot(self):
  s,w=self.ready();s.request_stop(1,'finish-A',1.);s.request_stop(2,'empty-B',1.);w[1]=wish(1,'A2');s.commands(w,1,1)
  self.assertTrue(ack(s,1,1.7));p=s.commands(w,1.7,1.7)
  self.assertEqual(p[1]['mode'],'ROUTE');first=p[1]['dispatch_id']
  for k in range(6):
   t=2.+k;s.request_stop(2,'retry-%d'%k,t);p=s.commands(w,t,t)
   self.assertEqual(p[1]['mode'],'ROUTE');self.assertEqual(p[1]['dispatch_id'],first)

 def test_task_alias_still_waits_for_old_owner_stop(self):
  s,w=self.ready();w[1]=dict(w[1],mode='WAIT');w[2]=dict(wish(2,'alias-A'),task_members=['A']);s.commands(w,1,1)
  self.assertTrue(ack(s,2,1.7));p=s.commands(w,1.7,1.7)
  self.assertEqual(p[2]['mode'],'STOP');self.assertEqual(s.states[2]['blocked_by'],[1])
  self.assertTrue(ack(s,1,1.8));self.assertEqual(s.commands(w,1.8,1.8)[2]['mode'],'ROUTE')

 def test_different_ids_same_unknown_support_cannot_double_dispatch(self):
  s=ExecutionSupervisor((1,2),'s');scope=dict(origin=[0,0],resolution=.4,unknown_runs=[[0,0,2]],portal_runs=[])
  w={1:dict(wish(1,'A'),scopes=[scope]),2:dict(wish(2,'B'),scopes=[scope])}
  s.commands(w,0,0);ack(s,1,.7);ack(s,2,.7);p=s.commands(w,.8,.8)
  self.assertEqual([p[r]['mode'] for r in (1,2)],['ROUTE','STOP'])

 def test_duplicate_idle_request_keeps_nonce_but_new_request_needs_proof(self):
  s,w=self.ready();s.request_stop(1,'fresh',1.);p=s.commands(w,1,1);identifier=p[1]['stop_id'];self.assertTrue(ack(s,1,1.7))
  s.request_stop(1,'fresh',1.8);self.assertEqual(s.states[1]['phase'],'stopped')
  s.request_stop(1,'new',1.9);q=s.commands(w,1.9,1.9)[1]
  self.assertNotEqual(q['stop_id'],identifier);self.assertEqual(s.states[1]['phase'],'stopping')

 def test_pending_duplicate_does_not_renew_timeout(self):
  s,w=self.ready();s.request_stop(1,'same',1.);p=s.commands(w,1,1)[1]
  for t in (2.,3.,4.,5.,6.):s.request_stop(1,'same',t);self.assertEqual(s.commands(w,t,t)[1]['stop_id'],p['stop_id'])
  self.assertEqual(s.commands(w,7.1,7.1)[1]['mode'],'STOP');self.assertEqual(s.states[1]['phase'],'fault')

 def test_unrelated_ready_work_can_start_while_peer_stop_fault_remains(self):
  s,w=self.ready();s.request_stop(1,'no-ack',1.);s.request_stop(2,'finish',1.);w[2]=wish(2,'B2');s.commands(w,1,1);ack(s,2,1.7)
  p=s.commands(w,7.1,7.1);self.assertEqual(s.states[1]['phase'],'fault');self.assertEqual(p[2]['mode'],'ROUTE')


if __name__=='__main__':unittest.main()
