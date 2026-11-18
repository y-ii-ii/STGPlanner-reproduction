import unittest

from team_topology.allocator import Coordinator
from team_topology.graph import GraphStore
from team_topology.traffic import Reservations
from test_offline import graph


class CorridorTests(unittest.TestCase):
    def test_shared_straight_route_moves_both_with_stopping_room(self):
        paths=[[(2.4,0),(5,0)],[(0,0),(4,0)]]
        poses=[(2.4,0,0),(0,0,0)]
        commands=[(1.,0.),(1.,0.)]
        moves,modes,diagnostics=Reservations().select(1.,poses,commands,commands,paths,{},[False]*2)
        self.assertEqual(modes,['PASS','PASS'])
        self.assertEqual(moves,commands)
        self.assertEqual(diagnostics['phase'],'FOLLOW')

    def test_measured_rear_momentum_still_requires_brake(self):
        p=Reservations()
        _,modes,diagnostics=p.select(1.,[(1.3,0,0),(0,0,0)],[(.5,0),(.5,0)],
            [(.5,0),(2.,0)],[[(1.3,0),(3,0)],[(0,0),(3,0)]],{},[False]*2)
        self.assertEqual(modes,['HOLD','HOLD'])
        self.assertEqual(diagnostics['phase'],'BRAKE')

    def test_rotation_and_previous_epoch_hold_are_not_following(self):
        paths=[[(3,0),(5,0)],[(0,0),(5,0)]]
        poses=[(3,0,0),(0,0,0)]
        p=Reservations()
        self.assertEqual(p.select(1.,poses,[(1.,.5),(1.,0)],[(0,0)]*2,paths,{},[False]*2)[1],['HOLD']*2)
        self.assertEqual(p.select(2.,poses,[(1.,0)]*2,[(0,0)]*2,paths,{},[False]*2)[1],['HOLD']*2)


class AllocationContinuityTests(unittest.TestCase):
    def fixture(self):
        a,records,state=graph(1,{'r':[0,0],'e':[1,0],'w':[-2,0]},
            {'e':('r','e',[[0,0],[1,0]]),'w':('r','w',[[0,0],[-1,0],[-2,0]])},
            {'work':['e','w']})
        store=GraphStore()
        store.apply(a.build(records,state))
        return Coordinator(robots=(1,)),store,a,records,state

    def test_cool_nearest_entrance_keeps_another_valid_portal(self):
        c,store,_,_,_=self.fixture()
        initial=c.plan(store,1.)[1]
        self.assertEqual(initial['path'][-1],(1.,0.))
        c.retry_memory.fail(1,initial,1.)
        alternative=c.plan(store,1.1)[1]
        self.assertEqual(alternative['task'],initial['task'])
        self.assertEqual(alternative['path'][-1],(-2.,0.))

    def test_transient_task_loss_keeps_valid_geometry_and_stable_lease(self):
        c,store,a,records,state=self.fixture()
        initial=c.plan(store,1.)[1]
        c.commit_dispatches({1:initial})
        active={1:dict(initial,dispatch_id=5)}
        del records[initial['task']]
        store.apply(a.build(records,state))
        retained=c.plan(store,1.2,10.,active)[1]
        self.assertEqual(retained['task'],initial['task'])
        self.assertEqual(retained['dispatch_id'],5)
        self.assertEqual(c.plan(store,1.3,12.01,active)[1]['mode'],'WAIT')

    def test_unreachable_portal_cannot_be_retained(self):
        c,store,a,records,state=self.fixture()
        initial=c.plan(store,1.)[1]
        del records[initial['task']]
        del records[initial['portal']]
        store.apply(a.build(records,state))
        self.assertEqual(c.plan(store,1.2,10.,{1:initial})[1]['mode'],'WAIT')
