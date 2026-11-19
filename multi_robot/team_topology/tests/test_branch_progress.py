import unittest

from team_topology.allocator import Coordinator
from team_topology.branch_progress import BranchProgress
from team_topology.graph import GraphStore
from team_topology.scope import unknown_support
from test_offline import graph


def scope(row, first=0, last=0):
    return dict(origin=[0,0],resolution=.4,unknown_runs=[[row,first,last]],
                portal_runs=[[0,1,1]],map_rev=1)


class BranchProgressTests(unittest.TestCase):
    def test_loop_is_not_progress_and_observation_resets_it(self):
        history=BranchProgress()
        lease=dict(dispatch_id=2,portal='near',path=[(0,0),(1,0)])
        for i in range(12):
            self.assertFalse(history.update(1,lease,(0,.5*(i%2)),float(i)))
        self.assertTrue(history.update(1,lease,(0,0),12.))
        self.assertFalse(history.update(1,lease,(0,0),12.3,observation_count=1))

    def test_defer_follows_overlapping_alias_and_expires(self):
        history=BranchProgress()
        history.defer_viewpoint(1,dict(path=[(0,0),(1,0)],scopes=[scope(2,0,2)]),1.)
        aliased=unknown_support([scope(2,1,3)])
        self.assertTrue(history.blocked(1,(1.2,0),aliased,5.))
        self.assertFalse(history.blocked(1,(1.2,0),unknown_support([scope(3)]),5.))
        self.assertFalse(history.blocked(1,(2.8,0),aliased,5.))
        self.assertFalse(history.blocked(1,(1.2,0),aliased,91.))

    def test_residual_gain_beats_small_nearby_patch(self):
        builder,records,state=graph(1,{'r':[0,0],'a':[1,0],'b':[3,0]},
            {'a':('r','a',[[0,0],[1,0]]),'b':('a','b',[[1,0],[2,0],[3,0]])},
            {'small':['a'],'branch':['b']})
        small=builder.key('task','small');branch=builder.key('task','branch')
        records[small]['scope']=scope(1)
        records[branch]['scope']=scope(2,0,24)
        store=GraphStore();store.apply(builder.build(records,state))
        c=Coordinator(robots=(1,))
        self.assertEqual(c.plan(store,1.)[1]['task'],branch)
        c.observed_support.update(unknown_support([records[branch]['scope']]))
        self.assertEqual(c.plan(store,1.1)[1]['task'],small)

    def test_nearby_alias_keeps_frozen_dispatch_after_transient_timer(self):
        builder,records,state=graph(1,{'r':[0,0],'a':[1,0],'b':[2,0]},
            {'a':('r','a',[[0,0],[1,0]]),'b':('a','b',[[1,0],[2,0]])}, {'initial':['a']})
        initial=builder.key('task','initial')
        records[initial]['scope']=scope(2,0,4)
        store=GraphStore();store.apply(builder.build(records,state))
        c=Coordinator(robots=(1,))
        active=dict(c.plan(store,1.)[1],dispatch_id=3)
        c.commit_dispatches({1:active})
        alias=builder.key('task','alias')
        records[alias]=dict(records.pop(initial),signature='alias',portals=[builder.key('node','b')])
        store.apply(builder.build(records,state))
        c.plan(store,1.1,10.,{1:active})
        held=c.plan(store,1.2,13.,{1:active})[1]
        self.assertEqual(held['task'],initial)
        self.assertEqual(held['dispatch_id'],3)
        self.assertEqual(held['scope_digest'],active['scope_digest'])

    def test_running_branch_keeps_a_feasible_portal_on_small_cost_difference(self):
        builder,records,state=graph(1,{'r':[0,0],'a':[1,0],'b':[1.6,0]},
            {'a':('r','a',[[0,0],[1,0]]),'b':('a','b',[[1,0],[1.6,0]])}, {'work':['a','b']})
        store=GraphStore();store.apply(builder.build(records,state))
        c=Coordinator(robots=(1,))
        first=c.plan(store,1.)[1]
        self.assertEqual(first['path'][-1],(1.,0.))
        active=dict(first,portal=builder.key('node','b'),path=[(0,0),(1.6,0)],dispatch_id=1)
        self.assertEqual(c.plan(store,1.1,committed={1:active})[1]['path'][-1],(1.6,0.))

    def test_graph_advance_allows_a_winding_route_far_from_goal(self):
        history=BranchProgress()
        lease=dict(dispatch_id=1,portal='far',path=[(0,0),(9,0)],cost_m=18.)
        for i in range(24):
            # The chassis alternates nearby positions, while the active path
            # becomes shorter as it follows the known detour.
            self.assertFalse(history.update(1,dict(lease,cost_m=18.-.15*i),(0,.5*(i%2)),float(i)))
        replay=BranchProgress()
        for i in range(18):
            self.assertFalse(replay.update(1,lease,(0,.5*(i%2)),float(i)))
        self.assertTrue(replay.update(1,lease,(0,0),18.))
