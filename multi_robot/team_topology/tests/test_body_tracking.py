import math
import unittest
from team_topology.body_tracking import BodyGrid,BodyTracker,shield_output


class BodyTrackingTests(unittest.TestCase):
    def grid(self,wall=None):
        data=[0]*16000
        if wall is not None:
            for y in range(100):
                for x in range(160):
                    if -8+(x+.5)*.1>=wall:data[y*160+x]=100
        return BodyGrid(160,100,.1,(-8,-5),data)

    def test_free_body_and_map_border(self):
        g=self.grid();self.assertTrue(g.free(0,0,.7));self.assertFalse(g.free(7.9,0,0))

    def test_unknown_does_not_become_free(self):
        self.assertFalse(BodyGrid(20,20,.1,(-1,-1),[-1]*400).free(0,0,0))

    def test_braking_distance_exceeds_point_check(self):
        g=self.grid(1.5);self.assertTrue(g.free(0,0,0))
        self.assertFalse(g.braking_safe((0,0,0),(2.,0.),(2.,0.)))
        self.assertTrue(g.braking_safe((0,0,0),(0.,0.),(.2,0.)))

    def test_rotating_body_hits_wall(self):
        g=self.grid(.6);self.assertTrue(g.free(0,0,0))
        self.assertFalse(g.braking_safe((0,0,0),(0.,1.5),(0.,1.5)))

    def test_reverse_checked_too(self):
        g=self.grid();g.bad[:,:74]=True
        g.integral=__import__('numpy').pad(g.bad.astype('int32'),((1,0),(1,0))).cumsum(0).cumsum(1)
        self.assertFalse(g.braking_safe((0,0,0),(-1.,0.),(-1.,0.)))

    def test_tracker_preserves_turn_before_translation(self):
        t=BodyTracker();t.receive([(0,0,0),(0,0,math.pi/2),(0,1,math.pi/2)],'a')
        v,status=t.propose((0,0,0),(0,0),self.grid());self.assertEqual(v[0],0);self.assertGreater(v[1],0)
        self.assertEqual(t.cursor,1)

    def test_same_path_does_not_reset_cursor(self):
        t=BodyTracker();p=[(0,0,0),(1,0,0)];t.receive(p,'a');t.propose((0,0,0),(0,0),self.grid())
        t.receive(p,'a');self.assertEqual(t.cursor,1)
        t.receive(p,'b');self.assertEqual(t.cursor,0)

    def test_reverse_not_pi_rotation(self):
        t=BodyTracker();t.receive([(0,0,0),(-1,0,0)],'a')
        v,_=t.propose((0,0,0),(0,0),self.grid());self.assertLess(v[0],0);self.assertAlmostEqual(v[1],0)

    def test_no_path_and_invalid_values(self):
        t=BodyTracker();self.assertEqual(t.propose((0,0,0),(0,0),self.grid())[0],(0.,0.))
        self.assertFalse(t.receive([(float('nan'),0,0)],'a'))
        self.assertFalse(self.grid().braking_safe((0,0,0),(0,0),(3.,0)))

    def test_traffic_old_approved_command_checked_again(self):
        g=self.grid(1.)
        self.assertTrue(g.braking_safe((0,0,0),(0,0),(.2,0)))
        self.assertEqual(shield_output(g,True,(0,0,0),(0,0),(2.,0.)),((0.,0.),True))

    def test_stale_geometry_and_stop_cannot_grant_motion(self):
        self.assertEqual(shield_output(None,False,None,(0,0),(.2,0)),((0.,0.),True))
        self.assertEqual(shield_output(None,False,None,(0,0),(0.,0.)),((0.,0.),False))

    def test_straight_primitives_can_use_original_speed_cap(self):
        t=BodyTracker();t.receive([(0,0,0),(.45,0,0),(.9,0,0),(2.7,0,0)],'a')
        v,_=t.propose((0,0,0),(0,0),self.grid());self.assertEqual(v[0],2.)

    def test_rolling_path_anchor_does_not_request_spurious_reverse(self):
        t=BodyTracker();t.receive([(0,0,0),(0,0,0),(.45,0,0),(.9,0,0),(2.7,0,0)],'next')
        v,_=t.propose((.65,0,0),(1.5,0),self.grid());self.assertGreater(v[0],0);self.assertGreaterEqual(t.cursor,3)

    def test_moving_anchor_cannot_skip_unexecuted_turn(self):
        t=BodyTracker();t.receive([(0,0,0),(0,0,math.pi/2),(0,.45,math.pi/2)],'next')
        v,_=t.propose((0,.05,0),(0,0),self.grid());self.assertEqual(v[0],0);self.assertEqual(t.cursor,1)

    def test_recenter_certificate_caps_speed_and_margin(self):
        t=BodyTracker();self.assertTrue(t.receive([(0,0,0),(-.45,0,0)],'recover',.05))
        v,status=t.propose((0,0,0),(0,0),self.grid());self.assertEqual(status,'RECENTER_TRACK')
        self.assertLessEqual(abs(v[0]),.2);self.assertLessEqual(abs(v[1]),.3)
        self.assertEqual(shield_output(self.grid(),True,(0,0,0),(0,0),(.3,0),.05),((0.,0.),True))
        self.assertFalse(t.receive([(0,0,0),(-.45,0,0)],'bad',.01))

    def test_measurement_anchor_cannot_turn_back_to_old_yaw(self):
        t=BodyTracker();t.receive([(0,0,0),(0,0,0),(.45*math.cos(.32),.45*math.sin(.32),.32)],'a')
        v,_=t.propose((0,0,.20),(0,.2),self.grid());self.assertGreater(v[1],0)

    def test_diverged_old_anchor_waits_for_replan(self):
        t=BodyTracker();t.receive([(0,0,0),(1,0,0)],'a')
        v,status=t.propose((.5,.3,.3),(1,0),self.grid());self.assertEqual(v,(0.,0.));self.assertEqual(status,'PATH_START_DIVERGED')

    def test_inertial_tracking_through_l_corner_keeps_body_free(self):
        data=[]
        for y in range(60):
            for x in range(60):
                wx,wy=-1.5+(x+.5)*.1,-1.5+(y+.5)*.1
                free=(-.8<=wx<=2.8 and -.8<=wy<=.8) or (1.2<=wx<=2.8 and -.8<=wy<=2.8)
                data.append(0 if free else 100)
        g=BodyGrid(60,60,.1,(-1.5,-1.5),data);t=BodyTracker()
        t.receive([(0,0,0),(2,0,0),(2,0,math.pi/2),(2,2,math.pi/2)],'corner')
        pose=(0.,0.,0.);current=(0.,0.);finished=False
        for _ in range(700):
            command,status=t.propose(pose,current,g)
            current=tuple(a+max(-.10,min(.10,b-a)) for a,b in zip(current,command))
            x,y,yaw=pose;v,w=current;pose=(x+v*math.cos(yaw+w*.025)*.05,y+v*math.sin(yaw+w*.025)*.05,yaw+w*.05)
            self.assertTrue(g.free(*pose),pose)
            if status=='PATH_END':finished=True;break
        self.assertTrue(finished);self.assertLess(math.dist(pose[:2],(2,2)),.2)


if __name__=='__main__':unittest.main()
