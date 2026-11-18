import unittest

from team_topology.allocator import Coordinator
from team_topology.body_tracking import BodyTracker
from team_topology.execution import ExecutionSupervisor
from team_topology.graph import GraphStore
from team_topology.traffic import Reservations
from test_offline import graph
import test_body_tracking


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

    def test_rear_can_follow_turning_leader_with_stopping_room(self):
        paths=[[(3,0),(5,0)],[(0,0),(5,0)]]
        poses=[(3,0,.15),(0,0,0)]
        p=Reservations()
        p.winner=1
        moves,modes,info=p.select(1.,poses,[(0,.2),(1.,0)],[(0,.2),(.5,0)],paths,{},[False]*2)
        self.assertEqual(modes,['PASS']*2)
        self.assertGreater(moves[1][0],0)
        self.assertEqual(info['winner'],0)

    def test_following_never_shortcuts_a_reversing_leader(self):
        paths=[[(2.4,0),(0,0)],[(0,0),(4,0)]]
        _,modes,_=Reservations().select(1.,[(2.4,0,0),(0,0,0)],
            [(-.35,0),(1.,0)],[(-.1,0),(0,0)],paths,{},[False]*2)
        self.assertEqual(modes,['HOLD']*2)

    def test_reservation_prefix_preserves_unconsumed_corner(self):
        tracker=BodyTracker()
        tracker.receive([(0,0,0),(1,0,0),(2,0,0),(2,0,1.57),(2,5,1.57)],'east')
        tracker.cursor=2
        self.assertEqual(tracker.reservation_prefix((1.5,0,0),2.),
                         [(1.5,0),(2,0),(2,1.5)])

    def test_small_straight_angular_jitter_never_changes_turn_sign(self):
        tracker=BodyTracker()
        tracker.receive([(0,0,0),(2,0,0)],'east')
        grid=test_body_tracking.BodyTrackingTests().grid()
        positive,_=tracker.propose((0,0,.01),(0,0),grid)
        negative,_=tracker.propose((0,0,-.01),(0,0),grid)
        correction,_=tracker.propose((0,0,-.04),(0,0),grid)
        self.assertGreater(positive[0],.05)
        self.assertEqual(positive,negative)
        self.assertEqual(positive[1],0)
        self.assertGreater(correction[1],0)


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

    def test_rebid_available_task_while_peer_retains_overlapping_work(self):
        store=GraphStore()
        a,ar,ast=graph(1,{'r':[0,0]}, {})
        b,br,bst=graph(2,{'r':[0,0],'near':[1,0],'far':[0,2]}, {
            'n':('r','near',[[0,0],[1,0]]),'f':('r','far',[[0,0],[0,1],[0,2]])},
            {'alias':['near'],'independent':['far']})
        near=b.key('task','alias')
        far=b.key('task','independent')
        scope=dict(resolution=1.,origin=[0,0],unknown_runs=[[0,1,1]],portal_runs=[[0,0,0]],map_rev=1)
        br[near]['scope']=scope
        br[far]['scope']=dict(scope,unknown_runs=[[2,0,0]])
        store.apply(a.build(ar,ast))
        store.apply(b.build(br,bst))
        allocated=Coordinator().plan(store,1.)
        self.assertEqual(allocated[2]['task'],near)
        # A different ID can still be physically reserved by an old owner
        # that has entered STOP and has yet to send the nonce-bound ACK.
        old=dict(task=a.key('task','old'),scopes=[scope])
        changed=Coordinator().plan(store,1.,reserved={1:old})
        self.assertEqual(changed[2]['task'],far)
        self.assertFalse(ExecutionSupervisor.work_conflict(changed[2],old))
