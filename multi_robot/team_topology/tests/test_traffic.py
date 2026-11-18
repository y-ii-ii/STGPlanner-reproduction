import unittest
from team_topology.traffic import Reservations,TrafficGuard,route_conflict
from team_topology.execution import VelocityFence

class TrafficTests(unittest.TestCase):
    def test_crossing_and_parallel_reservations(self):
        self.assertTrue(route_conflict([[(-2,0),(2,0)],[(0,-2),(0,2)]]))
        self.assertFalse(route_conflict([[(-2,0),(2,0)],[(-2,3),(2,3)]]))
    def test_reservation_requires_both_current_stop_proofs(self):
        t=Reservations();poses=[(-2,0,0),(0,-2,1.57)]
        args=(poses,[(1.,0.),(1.,0.)],[(0.,0.)]*2,[[(-2,0),(2,0)],[(0,-2),(0,2)]])
        v,m,info=t.select(0.,*args,{},[False]*2)
        self.assertEqual(m,['HOLD']*2);epoch=t.epoch
        self.assertEqual(t.select(.6,*args,{0:epoch,1:epoch-1},[False]*2)[1],['HOLD']*2)
        v,m,_=t.select(.7,*args,{0:epoch,1:epoch},[False]*2)
        self.assertLessEqual(sum(sum(abs(x) for x in q)>0 for q in v),1)
    def test_guard_rejects_old_generation_and_unchecked_reverse(self):
        g=TrafficGuard(1);f=VelocityFence(1);f.phase='running';f.active_token='new';f.armed_at=0.
        self.assertFalse(g.receive(dict(robot=1,seq=1,token='old',epoch=1,stamp=0.,mode='PASS',velocity=[1.,0.]),'new',0.))
        self.assertTrue(g.receive(dict(robot=1,seq=2,token='new',epoch=1,stamp=0.,mode='RETREAT',velocity=[-.2,0.]),'new',0.))
        self.assertEqual(g.filter(f,(1.,0.),.1,.1)[0],(0.,0.))
        self.assertEqual(g.filter(f,(1.,0.),2.,2.)[0],(0.,0.));self.assertEqual(f.phase,'tripped')
    def test_yield_ack_needs_post_nonce_odometry_and_zero_publication(self):
        g=TrafficGuard(1);f=VelocityFence(1);f.active_token='t';f.phase='running'
        g.receive(dict(robot=1,seq=1,token='t',epoch=4,stamp=1.,mode='HOLD',velocity=[0.,0.]),'t',0.)
        for i in range(1,20):
            w=i*.05
            g.receive(dict(robot=1,seq=i+1,token='t',epoch=4,stamp=1+w,mode='HOLD',velocity=[0.,0.]),'t',w)
            g.odom(1+w,(0.,0.,0.),(0.,0.),w,1+w)
            self.assertFalse(g.filter(f,(1.,0.),w,1+w)[1])
        proof=[]
        for i in range(20,36):
            w=i*.05;g.receive(dict(robot=1,seq=i+1,token='t',epoch=4,stamp=1+w,mode='HOLD',velocity=[0.,0.]),'t',w)
            g.odom(1+w,(0.,0.,0.),(0.,0.),w,1+w);v,ev=g.filter(f,(1.,0.),w,1+w);g.published(v,w);proof+=ev
        self.assertEqual(len(proof),1);self.assertEqual(proof[0]['epoch'],4)
    def test_same_token_new_epoch_cannot_renew_wait_forever(self):
        g=TrafficGuard(1);f=VelocityFence(1);f.phase='running';f.active_token='t'
        for i in range(22):
            g.receive(dict(robot=1,seq=i+1,token='t',epoch=i,stamp=float(i),mode='HOLD',velocity=[0.,0.]),'t',float(i))
            g.before_tick(f,float(i))
        self.assertEqual(f.phase,'tripped');self.assertEqual(f.events[-1]['reason'],'TRAFFIC_WAIT_REPLAN')
    def test_held_peer_cannot_be_driven_through(self):
        t=Reservations();t.phase='PASS';t.epoch=1
        v,_,_=t.select(.1,[(0,0,0),(1.,0,3.14)],[(2.,0.),(0.,0.)],[(2.,0.),(0.,0.)],[[],[]],{0:1,1:1},[False]*2)
        self.assertEqual(v,[(0.,0.),(0.,0.)])

    def test_transient_priority_pause_does_not_request_reverse(self):
        t=Reservations();t.phase='PASS';t.epoch=1
        poses=[(0,0,0),(4,0,3.14)]
        paths=[[(0,0),(4,0)],[(4,0),(1,0)]]
        current=[(0.,0.)]*2
        def tick(now,motion):
            return t.select(now,poses,motion,current,paths,{0:1,1:1},[True]*2)
        self.assertEqual(tick(10.,[(.5,0),(.5,0)])[1],['PASS','HOLD'])
        self.assertEqual(tick(10.05,[(0,0),(.5,0)])[1],['HOLD','HOLD'])
        self.assertEqual(tick(10.70,[(0,0),(.5,0)])[1],['HOLD','HOLD'])
        self.assertEqual(tick(10.75,[(.5,0),(.5,0)])[1],['PASS','HOLD'])
        self.assertEqual(t.epoch,1)

    def test_persistent_geometric_blockage_still_allows_certified_retreat(self):
        t=Reservations();t.phase='PASS';t.epoch=1
        poses=[(0,0,0),(1.2,0,3.14)]
        paths=[[(0,0),(2,0)],[(1.2,0),(0,0)]]
        def tick(now):
            return t.select(now,poses,[(2,0),(0,0)],[(0,0)]*2,paths,{0:1,1:1},[True]*2)
        self.assertEqual(tick(10.)[1],['HOLD','HOLD'])
        self.assertEqual(tick(10.9)[1],['HOLD','HOLD'])
        self.assertEqual(tick(11.1)[1],['HOLD','RETREAT'])

    def test_idle_priority_goes_through_fresh_bilateral_ack(self):
        t=Reservations();t.phase='PASS';t.epoch=1
        poses=[(0,0,0),(4,0,3.14)]
        paths=[[(0,0),(4,0)],[(4,0),(1,0)]]
        def tick(now,commands,acks):
            return t.select(now,poses,commands,[(0,0)]*2,paths,acks,[True]*2)
        self.assertEqual(tick(20.,[(0,0)]*2,{0:1,1:1})[1],['HOLD','HOLD'])
        self.assertEqual(tick(22.,[(0,0),(.5,0)],{0:1,1:1})[1],['HOLD','HOLD'])
        self.assertEqual(tick(24.1,[(0,0),(.5,0)],{0:1,1:1})[2]['phase'],'BRAKE')
        self.assertEqual(t.epoch,2)
        self.assertEqual(tick(24.9,[(0,0),(.5,0)],{0:2,1:1})[1],['HOLD','HOLD'])
        self.assertEqual(tick(25.,[(0,0),(.5,0)],{0:2,1:2})[1],['HOLD','PASS'])
