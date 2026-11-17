"""Synthetic offline checks only: never starts ROS, Gazebo or a native map replay."""
import copy
import json
import math
import unittest

from team_topology.graph import DeltaBuilder, GraphStore, Navigation, wire
from team_topology.grid import Grid
from team_topology.tasks import TaskTracker
from team_topology.exporter import LocalExporter
from team_topology.allocator import Coordinator, TaskLedger


def graph(robot, points, edges, tasks=None):
    builder = DeltaBuilder(robot, "test")
    records = {}
    for name, p in points.items():
        records[builder.key("node", name)] = {"kind": "node", "p": p, "role": "stg"}
    for name, (a, b, path) in edges.items():
        records[builder.key("edge", name)] = {"kind": "edge", "a": builder.key("node", a),
            "b": builder.key("node", b), "path": path, "resolution": 1.,
            "evidence": "known_free"}
    for name, portals in (tasks or {}).items():
        records[builder.key("task", name)] = {"kind": "task", "tile": [0, 0],
            "signature": name, "state": "pending", "map_rev": 1,
            "portals": [builder.key("node", p) for p in portals]}
    state = {"root": builder.key("node", "r"), "pose": points["r"], "stamp": 1.0}
    return builder, records, state


class OfflineTests(unittest.TestCase):
    def test_tombstone_replay_gap_and_full_repair(self):
        b, records, state = graph(1, {"r": [0,0], "a": [1,0]},
            {"ra": ("r", "a", [[0,0],[1,0]])})
        store = GraphStore()
        first = b.build(records, state)
        self.assertTrue(store.apply(first))
        self.assertFalse(store.apply(first))
        without = {k: v for k, v in records.items() if "/edge/" not in k}
        second = b.build(without, state)
        third = b.build(without, state)
        with self.assertRaisesRegex(ValueError, "sequence gap"):
            store.apply(third)
        self.assertTrue(store.apply(second))
        self.assertFalse(store.apply(first))
        self.assertFalse(store.live("edge"))
        self.assertTrue(store.apply(b.build(without, state, full=True)))

    def test_foreign_id_rejected_atomically(self):
        b, records, state = graph(1, {"r": [0,0]}, {})
        store = GraphStore()
        d = b.build(records, state)
        d["records"]["2/other/node/x"] = next(iter(d["records"].values()))
        with self.assertRaises(ValueError):store.apply(d)
        self.assertEqual(store.records, {})

    def test_invalid_geometry_and_frame(self):
        b, records, state = graph(1, {"r": [0,0], "a": [2,0]},
            {"ra": ("r", "a", [[0,0],[2,0]])})
        d = b.build(records, state)
        with self.assertRaisesRegex(ValueError, "unsampled"):
            GraphStore().apply(d)
        d["frame"] = "map"
        with self.assertRaisesRegex(ValueError, "frame"):
            GraphStore().apply(d)

    def test_peer_route_and_no_parallel_wall_merge(self):
        a, ar, ast = graph(1, {"r":[0,0], "j":[1,0]},
            {"a":("r","j",[[0,0],[1,0]])})
        b, br, bst = graph(2, {"r":[1,0], "t":[3,0], "parallel":[1,.1]},
            {"b":("r","t",[[1,0],[2,0],[3,0]])})
        store = GraphStore();store.apply(a.build(ar,ast));store.apply(b.build(br,bst))
        nav = Navigation(store)
        route = nav.route(a.key("node","r"),b.key("node","t"))
        self.assertEqual(route["cost"],3)
        self.assertTrue(any(e.startswith("2/") for e in route["edges"]))
        self.assertIsNone(nav.route(a.key("node","r"),b.key("node","parallel")))

    def test_same_tile_split_and_missing_is_not_completed(self):
        # Same 4m tile: two free/unknown corridors separated by a known wall.
        grid = Grid(4,3,1,(0,0),[0,-1,-1,100, 100,100,100,100, 0,-1,-1,100])
        tracker=TaskTracker()
        tasks=tracker.update(grid)
        pending=[t for t in tasks.values() if t["state"]=="pending"]
        self.assertEqual(len(pending),2)
        self.assertEqual(pending[0]["tile"],pending[1]["tile"])
        blocked=Grid(4,3,1,(0,0),[-1]*12)
        self.assertTrue(all(t["state"]=="deferred" for t in tracker.update(blocked).values()))
        observed=Grid(4,3,1,(0,0),[0]*12)
        self.assertTrue(all(t["state"]=="completed" for t in tracker.update(observed).values()))

    def test_no_corner_cut(self):
        g=Grid(2,2,1,(0,0),[0,100,100,0])
        self.assertIsNone(g.path((0,0),(1,1)))

    def test_own_export_does_not_transmit_occupancy(self):
        snapshot={"frame":"world","pose":[.5,.5],"stamp":1.0,
            "grid":{"width":4,"height":2,"resolution":1,"origin":[0,0],
                    "data":[0,0,-1,-1,0,0,-1,-1]},
            "nodes":[{"id":1,"p":[1.5,.5]}],"edges":[]}
        exp=LocalExporter(1,"s");d=exp.snapshot(snapshot)
        data=wire(d)
        self.assertNotIn('"grid"',data)
        self.assertNotIn('"cells"',data)
        store=GraphStore();store.apply(json.loads(data))
        self.assertTrue(store.live("task"))
        self.assertTrue(store.live("edge"))

    def test_graph_distance_beats_euclidean_across_wall(self):
        # r1 is 1m from t by Euclidean distance but its validated path is 7m.
        a,ar,ast=graph(1,{"r":[0,0],"t":[1,0]},
            {"a":("r","t",[[0,0],[0,1],[0,2],[1,2],[2,2],[2,1],[2,0],[1,0]])})
        b,br,bst=graph(2,{"r":[1,-2],"t":[1,0]},
            {"b":("r","t",[[1,-2],[1,-1],[1,0]])},{"work":["t"]})
        store=GraphStore();store.apply(a.build(ar,ast));store.apply(b.build(br,bst))
        c=Coordinator();plans=c.plan(store,1.0)
        self.assertEqual(c.partition(store)[(1.,0.)],2)
        self.assertEqual(plans[2]["mode"],"ROUTE")
        self.assertEqual(plans[2]["cost_m"],2.)
        self.assertEqual(plans[1]["mode"],"WAIT")

    def test_unreachable_not_awarded_and_stale_state_stops(self):
        a,ar,ast=graph(1,{"r":[0,0],"t":[9,9]}, {},{"a":["t"]})
        b,br,bst=graph(2,{"r":[2,0]}, {})
        store=GraphStore();store.apply(a.build(ar,ast));store.apply(b.build(br,bst))
        c=Coordinator()
        self.assertTrue(all(x["mode"]=="WAIT" for x in c.plan(store,1.).values()))
        self.assertTrue(all(x["mode"]=="WAIT" for x in c.plan(store,10.).values()))

    def test_handover_and_stale_ack(self):
        ledger=TaskLedger();item=ledger.assign("task",1);old=item["version"]
        offer=ledger.offer("task",2)
        self.assertFalse(ledger.acknowledge("task",1,old))
        self.assertFalse(ledger.acknowledge("task",1,offer["version"]))
        self.assertTrue(ledger.acknowledge("task",2,offer["version"]))
        self.assertEqual(ledger.items["task"]["owner"],2)
        with self.assertRaises(ValueError):ledger.offer("task",1)
        self.assertFalse(ledger.release("task",1,offer["version"]))
        self.assertTrue(ledger.release("task",2,offer["version"]))
        retry=ledger.offer('task',1)
        self.assertTrue(ledger.release('task',1,retry['version']))
        self.assertNotIn('receiver',ledger.items['task'])
        self.assertEqual(ledger.items['task']['owner'],2)

    def test_equal_distance_deterministic_and_multiportal_unique(self):
        a,ar,ast=graph(1,{"r":[0,0],"t":[1,0]},
            {"a":("r","t",[[0,0],[1,0]])},{"same":["t","r"]})
        b,br,bst=graph(2,{"r":[0,0],"t":[1,0]},
            {"b":("r","t",[[0,0],[1,0]])},{"same":["t","r"]})
        s1,s2=GraphStore(),GraphStore()
        da,db=a.build(ar,ast),b.build(br,bst)
        for d in (da,db):s1.apply(d)
        for d in (db,da):s2.apply(d)
        c1,c2=Coordinator(),Coordinator()
        self.assertEqual(c1.plan(s1,1.),c2.plan(s2,1.))
        self.assertEqual(len(c1.ledger.items),1)

    def test_empty_candidates_not_mission_complete(self):
        tracker=TaskTracker()
        task=tracker.update(Grid(3,1,1,(0,0),[0,-1,-1]))
        self.assertEqual(len(task),1)
        after=tracker.update(Grid(1,1,1,(0,0),[0]))
        self.assertEqual(next(iter(after.values()))["state"],"deferred")

    def test_task_identity_survives_portal_representative_change(self):
        tracker=TaskTracker()
        before=tracker.update(Grid(3,2,1,(0,0),[0,-1,-1,0,-1,-1]))
        original=next(iter(before))
        after=tracker.update(Grid(3,2,1,(0,0),[100,100,100,0,-1,-1]))
        self.assertEqual([k for k,v in after.items() if v['state']=='pending'],[original])
        with self.assertRaisesRegex(ValueError,'fixed world'):
            tracker.update(Grid(3,2,1,(10,0),[0]*6))

    def test_same_sequence_conflict_and_session_restart(self):
        b,records,state=graph(1,{'r':[0,0]}, {})
        store=GraphStore();d=b.build(records,state);store.apply(d)
        changed=copy.deepcopy(d);changed['state']['pose']=[.1,0]
        with self.assertRaisesRegex(ValueError,'same-sequence'):store.apply(changed)
        other=DeltaBuilder(1,'restarted')
        key=other.key('node','r')
        new=other.build({key:{'kind':'node','p':[0,0]}},{'pose':[0,0],'root':key,'stamp':1.})
        with self.assertRaisesRegex(ValueError,'session replacement'):store.apply(new)

    def test_unchanged_map_sends_only_state_heartbeat(self):
        snapshot={'frame':'world','pose':[.5,.5],'stamp':1.,
            'grid':{'width':4,'height':2,'resolution':1,'origin':[0,0],
                    'data':[0,0,-1,-1,0,0,-1,-1]},'nodes':[],'edges':[]}
        exporter=LocalExporter(1,'heartbeat')
        first=exporter.snapshot(snapshot)
        snapshot['stamp']=2.
        second=exporter.snapshot(snapshot)
        self.assertEqual(second['records'],{})
        self.assertLess(len(wire(second)),len(wire(first)))
        store=GraphStore()
        store.apply(json.loads(wire(first)));store.apply(json.loads(wire(second)))

    def test_split_merge_and_reopen_lineage(self):
        tracker=TaskTracker(min_unknown=1)
        original=tracker.update(Grid(4,2,1,(0,0),[0,0,0,0,-1,-1,-1,-1]))
        parent=next(iter(original))
        split=tracker.update(Grid(4,2,1,(0,0),[0,0,0,0,-1,100,100,-1]))
        pending=[(k,v) for k,v in split.items() if v['state']=='pending']
        self.assertEqual(len(pending),2)
        child=next(v for k,v in pending if k!=parent)
        self.assertIn(parent,child['parents'])
        merged=tracker.update(Grid(4,2,1,(0,0),[0,0,0,0,-1,-1,-1,-1]))
        live=[v for v in merged.values() if v['state']=='pending']
        self.assertEqual(len(live),1)
        self.assertTrue(live[0]['parents'])
        tracker.update(Grid(4,2,1,(0,0),[0]*8))
        reopened=tracker.update(Grid(4,2,1,(0,0),[0,0,0,0,-1,100,100,-1]))
        new=[v for v in reopened.values() if v['state']=='pending']
        self.assertEqual(len(new),2)
        self.assertTrue(all(v['parents'] for v in new))

    def test_dispatched_task_cannot_be_stolen_before_ack(self):
        a,ar,ast=graph(1,{'r':[0,0],'t':[1,0]},
            {'a':('r','t',[[0,0],[1,0]])},{'one':['t']})
        b,br,bst=graph(2,{'r':[2,0],'t':[1,0]},
            {'b':('r','t',[[2,0],[1,0]])})
        store=GraphStore();store.apply(a.build(ar,ast));store.apply(b.build(br,bst))
        c=Coordinator();plans=c.plan(store,1.)
        owner=next(r for r,p in plans.items() if p['mode']=='ROUTE')
        command=plans[owner]
        c.commit_dispatches(plans) # Model actual publication, not just bidding.
        self.assertEqual(c.ledger.items[command['task']]['state'],'dispatched')
        with self.assertRaises(ValueError):c.ledger.offer(command['task'],3-owner)
        self.assertFalse(c.feedback(dict(command,status='ACCEPTED',command_seq=0)))
        self.assertFalse(c.feedback(dict(command,status='ACCEPTED',source='planner')))
        self.assertTrue(c.feedback(dict(command,status='EXECUTOR_ACCEPTED',source='executor')))
        native_feedback={k:str(v) for k,v in dict(command,status='EXECUTOR_ACCEPTED',source='executor').items()}
        self.assertTrue(c.feedback(native_feedback))

    def test_single_cell_frontier_is_not_filtered_out(self):
        tracker=TaskTracker()
        result=tracker.update(Grid(2,1,1,(0,0),[0,-1]))
        self.assertEqual(len(result),1)

    def test_unknown_tile_uses_neighbor_tile_portal(self):
        tracker=TaskTracker()
        tasks=tracker.update(Grid(6,1,1,(0,0),[100,100,100,0,-1,-1]))
        pending=[v for v in tasks.values() if v['state']=='pending']
        self.assertEqual(len(pending),1)
        self.assertEqual(pending[0]['tile'],(1,0))
        self.assertEqual(pending[0]['portal_cells'],[(3,0)])

    def test_two_branch_export_exchange_allocate_feedback(self):
        from team_topology.offline_demo import run
        result=run()
        self.assertTrue(result['interrobot_route_contains_peer_edge'])
        self.assertLess(result['unchanged_heartbeat_bytes_two_publications'],
                        result['initial_serialized_bytes_two_publications'])


if __name__=="__main__":
    unittest.main(verbosity=2)
