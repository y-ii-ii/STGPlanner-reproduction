import copy,unittest
from team_topology.graph import GraphStore
from test_offline import graph

class IncrementalStoreTests(unittest.TestCase):
 def setup_store(self):
  b,r,s=graph(1,{'r':[0,0],'a':[1,0]},{'edge':('r','a',[[0,0],[1,0]])});g=GraphStore();g.apply(b.build(r,s));return b,r,s,g

 def test_node_change_revalidates_old_incident_edge_atomically(self):
  b,r,s,g=self.setup_store();digest=g.digest();r[b.key('node','a')]['p']=[2,0]
  with self.assertRaisesRegex(ValueError,'endpoint mismatch'):g.apply(b.build(r,s))
  self.assertEqual(g.digest(),digest);self.assertEqual(g.live('node')[b.key('node','a')]['p'],[1,0])

 def test_state_only_heartbeat_preserves_immutable_path_records(self):
  b,r,s,g=self.setup_store();record=g.records[b.key('edge','edge')];digest=g.digest();s['stamp']=2.
  g.apply(b.build(r,s));self.assertIs(record,g.records[b.key('edge','edge')]);self.assertEqual(g.digest(),digest);self.assertEqual(g.states[1]['stamp'],2.)

 def test_input_alias_cannot_corrupt_validated_records(self):
  b,r,s=graph(1,{'r':[0,0]},{});d=b.build(r,s);g=GraphStore();g.apply(d);d['records'][b.key('node','r')]['value']['p'][0]=90
  self.assertEqual(g.live('node')[b.key('node','r')]['p'],[0,0])

 def test_endpoint_reappearance_checks_previously_dangling_edge(self):
  b,r,s,g=self.setup_store();old=copy.deepcopy(r);r.pop(b.key('node','a'));g.apply(b.build(r,s));digest=g.digest();r=old;r[b.key('node','a')]['p']=[3,0]
  with self.assertRaisesRegex(ValueError,'endpoint mismatch'):g.apply(b.build(r,s))
  self.assertEqual(g.digest(),digest)
