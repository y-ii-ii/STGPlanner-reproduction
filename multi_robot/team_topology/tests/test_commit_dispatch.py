import unittest
from team_topology.offline_demo import snapshot
from team_topology.exporter import LocalExporter
from team_topology.graph import GraphStore
from team_topology.allocator import Coordinator
from team_topology.execution import ExecutionSupervisor
from test_dispatch_liveness import ack

class CommitDispatchTests(unittest.TestCase):
 def setup_team(self):
  g=GraphStore()
  for r in (1,2):g.apply(LocalExporter(r,'commit').snapshot(snapshot(r)))
  return g,Coordinator(),ExecutionSupervisor([1,2],'s')

 def test_stop_withheld_intention_does_not_become_ghost_dispatch(self):
  g,c,s=self.setup_team();desired=c.plan(g,1.);actual=s.commands(desired,0.,1.);c.commit_dispatches(actual)
  self.assertTrue(any(p['mode']=='ROUTE' for p in desired.values()));self.assertTrue(all(p['mode']=='STOP' for p in actual.values()))
  self.assertFalse(any(i['state']=='dispatched' for i in c.ledger.items.values()))
  for r in (1,2):self.assertTrue(ack(s,r,.7))
  routes=s.commands(c.plan(g,1.8),.8,1.8);c.commit_dispatches(routes)
  for r,p in routes.items():
   if p['mode']=='ROUTE':self.assertEqual(c.ledger.items[p['task']]['state'],'dispatched')

 def test_failed_start_cooldown_survives_task_id_replacement(self):
  g,c,s=self.setup_team();p=c.plan(g,1.)[1];c.fail_execution(1,p,10.,True)
  # Another source/ID approaching the same unsafe current chassis is also held.
  self.assertTrue(c.retry_memory.blocked(1,[p['path'][0],[p['path'][0][0]+3,p['path'][0][1]]],11.))
  self.assertFalse(c.retry_memory.blocked(2,p['path'],11.))
