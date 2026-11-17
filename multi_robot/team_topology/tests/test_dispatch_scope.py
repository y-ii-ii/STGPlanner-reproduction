import copy
import unittest
from team_topology.execution import ExecutionSupervisor


class DispatchScopeTests(unittest.TestCase):
    def start(self):
        s=ExecutionSupervisor([1],'s')
        wish=dict(robot=1,mode='ROUTE',task='region',version=7,path=[[0,0],[1,0]],
                  scopes=[{'unknown_runs':[[0,8]]}],scope_digest='a'*64,
                  scope_cells=8,task_members=['source/task/1'])
        stop=s.commands({1:wish},0.,0.)[1]
        proof=dict(stop,source='velocity_gate',status='STOPPED',fresh_samples=5,stationary_s=.6,zero_s=.6)
        self.assertTrue(s.feedback(proof,1.))
        return s,wish,s.commands({1:wish},1.,1.)[1]

    def test_same_dispatch_cannot_expand_completion_target(self):
        s,wish,initial=self.start();changed=copy.deepcopy(wish)
        changed.update(scopes=[{'unknown_runs':[[0,52]]}],scope_digest='b'*64,scope_cells=52,
                       task_members=['source/task/1','other/alias'],path=[[.5,0],[1,0]])
        route=s.commands({1:changed},1.1,1.1)[1]
        self.assertEqual(route['dispatch_id'],initial['dispatch_id'])
        for k in ('scopes','scope_digest','scope_cells','task_members'):self.assertEqual(route[k],initial[k])
        self.assertEqual(route['path'],changed['path'])  # Fresh approach geometry remains updateable.
        self.assertEqual(changed['scope_cells'],52)    # Do not mutate allocation input.

    def test_new_scope_requires_new_generation_and_stop(self):
        s,wish,initial=self.start();changed=dict(wish,version=8,scope_digest='b'*64,scope_cells=52)
        stop=s.commands({1:changed},1.1,1.1)[1];self.assertEqual(stop['mode'],'STOP')
        proof=dict(stop,source='velocity_gate',status='STOPPED',fresh_samples=5,stationary_s=.6,zero_s=.6)
        self.assertTrue(s.feedback(proof,2.))
        route=s.commands({1:changed},2.,2.)[1]
        self.assertNotEqual(route['dispatch_id'],initial['dispatch_id']);self.assertEqual(route['scope_cells'],52)

    def test_returned_scope_does_not_mutate_supervisor_snapshot(self):
        s,wish,route=self.start();route['scopes'][0]['unknown_runs'][0][1]=100
        self.assertEqual(s.commands({1:wish},1.1,1.1)[1]['scopes'][0]['unknown_runs'][0][1],8)


if __name__=='__main__':unittest.main()
