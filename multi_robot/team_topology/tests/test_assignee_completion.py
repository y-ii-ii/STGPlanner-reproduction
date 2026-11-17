"""Task-author/assignee separation: observations plus stop proof, never map fusion."""
import copy
import unittest
from test_offline import graph
from team_topology.graph import GraphStore
from team_topology.allocator import Coordinator
from team_topology.scope import completion_signature


class AssigneeCompletionTests(unittest.TestCase):
    def fixture(self):
        a, records, state = graph(1, {"r":[0,0], "t":[2,0]},
            {"a":("r","t",[[0,0],[1,0],[2,0]])}, {"work":["t"]})
        key=a.key("task","work")
        records[key]["scope"]={"resolution":1., "origin":[0,0],
            "unknown_runs":[[1,2,3]], "portal_runs":[[0,2,2]], "map_rev":1}
        b, br, bst=graph(2,{"r":[2,0]}, {})
        store=GraphStore();store.apply(a.build(records,state));store.apply(b.build(br,bst))
        c=Coordinator();route=dict(c.plan(store,1.)[2],dispatch_id=7,allocation_session="s")
        proof={k:route[k] for k in ("robot","task","version","dispatch_id","allocation_session","scope_digest")}
        proof.update(source="planner",status="OBSERVATION_COMPLETED",required_cells=2,observed_cells=2,map_stamp=1.)
        return c,store,a,records,state,key,route,proof

    def test_foreign_task_completes_without_rewriting_author_record(self):
        c,store,a,records,state,key,route,proof=self.fixture()
        self.assertTrue(key.startswith("1/"));self.assertEqual(route["robot"],2)
        self.assertTrue(c.observe_completed(proof,route,1.1))
        self.assertEqual(store.live("task")[key]["state"],"pending")
        self.assertNotEqual(c.ledger.items[key]["state"],"completed")
        self.assertTrue(all(v["mode"]=="WAIT" for v in c.plan(store,1.2).values()))
        # In production only a nonce-verified supervisor release calls this.
        self.assertTrue(c.ledger.release(key,2,route["version"]))
        self.assertEqual(c.ledger.items[key]["state"],"completed")

    def test_old_or_partial_or_stale_observation_cannot_finish(self):
        c,store,a,records,state,key,route,proof=self.fixture()
        for change in ({"dispatch_id":6},{"version":99},{"robot":1},{"scope_digest":"x"},
                       {"observed_cells":1},{"required_cells":1},{"map_stamp":-1.},{"map_stamp":float("nan")}):
            self.assertFalse(c.observe_completed(dict(proof,**change),route,1.1))
        self.assertFalse(c.completed_support)

    def test_grown_support_reopens_only_after_stop_with_new_version(self):
        c,store,a,records,state,key,route,proof=self.fixture()
        self.assertTrue(c.observe_completed(proof,route,1.1))
        records[key]["scope"]["unknown_runs"]=[[1,2,4]]
        state["stamp"]=1.2;store.apply(a.build(records,state))
        self.assertEqual(c.plan(store,1.2)[2]["mode"],"WAIT")
        c.ledger.release(key,2,route["version"])
        new=c.plan(store,1.3)[2]
        self.assertEqual(new["mode"],"ROUTE");self.assertGreater(new["version"],route["version"])
        self.assertNotEqual(new["scope_digest"],route["scope_digest"])
        self.assertFalse(c.observe_completed(proof,dict(new,dispatch_id=8,allocation_session="s"),1.3))

    def test_signature_ignores_alias_heartbeat_but_not_unknown_geometry(self):
        _,_,_,_,_,_,route,_=self.fixture()
        scope=route["scopes"][0];alias=copy.deepcopy(scope);alias["map_rev"]=99
        alias["portal_runs"]=[[0,1,2]]
        self.assertEqual(completion_signature([scope]),completion_signature([scope,alias]))
        alias["unknown_runs"]=[[1,2,4]]
        self.assertNotEqual(completion_signature([scope]),completion_signature([alias]))

    def test_renamed_task_cannot_reassign_already_observed_world_support(self):
        c,store,a,records,state,key,route,proof=self.fixture()
        self.assertTrue(c.observe_completed(proof,route,1.1))
        alias=a.key('task','renamed');records[alias]=records.pop(key);state['stamp']=1.2
        store.apply(a.build(records,state))
        self.assertTrue(all(v['mode']=='WAIT' for v in c.plan(store,1.2).values()))
        self.assertEqual(store.live('task')[alias]['state'],'pending')
        self.assertNotEqual(c.ledger.items[key]['state'],'completed') # Still needs physical STOP.

    def test_renamed_task_with_novel_cells_is_not_falsely_completed(self):
        c,store,a,records,state,key,route,proof=self.fixture()
        c.observe_completed(proof,route,1.1);c.ledger.release(key,2,route['version'])
        alias=a.key('task','renamed');records[alias]=records.pop(key);records[alias]['scope']['unknown_runs']=[[1,2,4]];state['stamp']=1.2
        store.apply(a.build(records,state));self.assertTrue(any(v['mode']=='ROUTE' for v in c.plan(store,1.2).values()))
