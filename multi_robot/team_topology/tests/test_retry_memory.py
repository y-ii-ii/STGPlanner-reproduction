import unittest
from team_topology.retry_memory import RetryMemory

class RetryMemoryTests(unittest.TestCase):
 def test_renamed_tasks_same_ingress_do_not_reset_cooldown(self):
  m=RetryMemory();m.fail(1,dict(task='A',path=[[0,0],[2,0],[9,0]]),0.)
  for i in range(77):self.assertTrue(m.blocked(1,[[.01,0],[2,0],[20+i,0]],1.))

 def test_other_direction_robot_and_new_pose_remain_available(self):
  m=RetryMemory();m.fail(1,dict(path=[[0,0],[2,0]]),0.)
  self.assertFalse(m.blocked(1,[[0,0],[0,2]],1.));self.assertFalse(m.blocked(2,[[0,0],[2,0]],1.));self.assertFalse(m.blocked(1,[[2,0],[4,0]],1.))

 def test_current_unsafe_body_blocks_all_ingresses_until_bounded_retry(self):
  m=RetryMemory();m.fail(1,dict(path=[[0,0],[2,0]]),0.,True)
  self.assertTrue(m.blocked(1,[[0,0],[0,2]],1.));self.assertFalse(m.blocked(1,[[0,0],[0,2]],15.1))

 def test_repeated_failures_backoff_without_permanent_completion(self):
  m=RetryMemory();p=dict(path=[[0,0],[2,0]])
  m.fail(1,p,0.);m.fail(1,p,16.);self.assertTrue(m.blocked(1,p['path'],40.));self.assertFalse(m.blocked(1,p['path'],46.1))

 def test_closed_loop_path_has_no_arbitrary_direction_exemption(self):
  m=RetryMemory();m.fail(1,dict(path=[[0,0],[.01,0]]),0.)
  self.assertTrue(m.blocked(1,[[0,0],[2,0]],1.))

 def test_pre_execution_failure_uses_bounded_alias_shared_backoff(self):
  m=RetryMemory();p=dict(task='first',path=[[0,0],[2,0]])
  other=dict(task='other',path=[[.01,0],[2.1,0]])
  m.fail(1,p,0.,before_execution=True)
  self.assertTrue(m.blocked(1,other['path'],3.9))
  self.assertFalse(m.blocked(1,other['path'],4.1))
  m.fail(1,other,4.1,before_execution=True)
  self.assertTrue(m.blocked(1,p['path'],12.))
  self.assertFalse(m.blocked(1,p['path'],12.2))
  for now in (12.2,28.3,58.4):m.fail(1,p,now,before_execution=True)
  self.assertTrue(m.blocked(1,p['path'],88.3))
  self.assertFalse(m.blocked(1,p['path'],88.5))

 def test_pre_execution_feedback_cannot_shorten_an_unsafe_body_cooldown(self):
  m=RetryMemory();p=dict(path=[[0,0],[2,0]])
  m.fail(1,p,0.,unsafe_start=True)
  m.fail(1,p,1.,before_execution=True)
  self.assertTrue(m.blocked(1,[[0,0],[0,2]],14.9))
  self.assertFalse(m.blocked(1,p['path'],15.1))
