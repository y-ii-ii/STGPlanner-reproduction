import unittest
from team_topology.execution import ExecutionSupervisor, VelocityFence, token
from team_topology.scope import contains, task_scope
from team_topology.grid import Grid
from team_topology.tasks import TaskTracker
from team_topology.traffic import TrafficGuard


def wish(robot=1, task="work", version=1):
    return {"robot":robot,"mode":"ROUTE","task":task,"version":version,"path":[[0,0],[1,0]]}


def prove(fence, start=0., count=20):
    events=[]
    for i in range(1,count+1):
        now=start+i*.05
        fence.receive_odom(now,(0.,0.,0.),(0.,0.),now,now)
        output, new=fence.tick(now)
        fence.output_published(output,now)
        events.extend(new)
    return events


class ExecutionTests(unittest.TestCase):
    def test_initial_stop_requires_new_stationary_odometry_and_zero_output(self):
        s=ExecutionSupervisor([1],"session");f=VelocityFence(1)
        cmd=s.commands({1:wish()},0.,0.)[1]
        self.assertEqual(cmd["mode"],"STOP")
        f.receive_command(cmd,0.,0.)
        self.assertFalse(f.tick(0.)[1])
        events=prove(f)
        ack=next(x for x in events if x['status']=='STOPPED')
        self.assertTrue(s.feedback(ack,1.))
        route=s.commands({1:wish()},1.,1.)[1]
        self.assertEqual(route['mode'],'ROUTE')
        self.assertTrue(f.receive_command(route,1.,1.))

    def test_repeated_or_missing_odometry_never_acks(self):
        s=ExecutionSupervisor([1],"s");f=VelocityFence(1)
        f.receive_command(s.commands({1:wish()},0.,0.)[1],0.,0.)
        f.receive_odom(.01,(0.,0.,0.),(0.,0.),.01,.01)
        for i in range(1,30):
            now=i*.05;f.receive_odom(.01,(0.,0.,0.),(0.,0.),now,now)
            v,e=f.tick(now);f.output_published(v,now)
            self.assertFalse(e)

    def test_zero_not_published_is_not_stop_ack(self):
        s=ExecutionSupervisor([1],"s");f=VelocityFence(1)
        f.receive_command(s.commands({1:wish()},0.,0.)[1],0.,0.)
        for i in range(1,30):
            now=i*.05;f.receive_odom(now,(0.,0.,0.),(0.,0.),now,now)
            self.assertFalse(f.tick(now)[1])

    def test_wrong_old_and_late_acks_cannot_unlock(self):
        s=ExecutionSupervisor([1],"s")
        c=s.commands({1:wish()},0.,0.)[1]
        good=dict(c,source='velocity_gate',status='STOPPED',fresh_samples=10,stationary_s=.7,zero_s=.8)
        self.assertFalse(s.feedback(dict(good,source='planner'),1.))
        self.assertFalse(s.feedback(dict(good,stop_id='old'),1.))
        self.assertFalse(s.feedback(good,7.))
        self.assertEqual(s.commands({1:wish()},7.,7.)[1]['mode'],'STOP')
        self.assertEqual(s.states[1]['phase'],'fault')
        self.assertFalse(s.feedback(good,7.1))

    def running(self,cost_m=None):
        s=ExecutionSupervisor([1],"s");f=VelocityFence(1)
        f.receive_command(s.commands({1:wish()},0.,0.)[1],0.,0.)
        s.feedback(next(x for x in prove(f) if x['status']=='STOPPED'),1.)
        task=wish()
        if cost_m is not None:task['cost_m']=cost_m
        route=s.commands({1:task},1.,1.)[1]
        f.receive_command(route,1.,1.)
        permit={'token':token(route),'issuer':'executor','permit_seq':1,'allow':True}
        f.receive_permit(permit,1.)
        f.receive_odom(1.01,(0.,0.,0.),(0.,0.),1.01,1.01)
        f.receive_raw(1.,.1,1.01)
        return s,f,route,permit

    def test_long_approach_can_continue_only_with_bounded_measured_progress(self):
        s,f,_,permit=self.running(33.)
        def tick(now,cost,x,seq):
            wish_now=dict(wish(),cost_m=cost)
            f.receive_command(s.commands({1:wish_now},now,now)[1],now,now)
            f.receive_odom(now,(x,0.,0.),(0.,0.),now,now)
            f.receive_permit(dict(permit,permit_seq=seq),now)
            f.receive_raw(.6,0.,now)
            return f.tick(now)
        self.assertEqual(tick(61.1,20.,9.,2),((.6,0.),[]))
        command,events=tick(114.,10.,12.,3)
        self.assertEqual(command,(0.,0.))
        self.assertEqual(events[0]['reason'],'EXECUTION_DEADLINE')

    def test_graph_cost_jump_alone_does_not_extend_execution(self):
        s,f,_,permit=self.running(33.)
        now=61.1
        f.receive_command(s.commands({1:dict(wish(),cost_m=5.)},now,now)[1],now,now)
        f.receive_odom(now,(.4,0.,0.),(0.,0.),now,now)
        f.receive_permit(dict(permit,permit_seq=2),now)
        self.assertEqual(f.tick(now)[1][0]['reason'],'EXECUTION_DEADLINE')

    def test_executor_exit_and_coordinator_exit_force_zero(self):
        s,f,c,p=self.running()
        self.assertEqual(f.tick(1.02)[0],(1.,.1))
        v,e=f.tick(1.5)
        self.assertEqual(v,(0.,0.))
        self.assertEqual(e[0]['reason'],'EXECUTOR_TIMEOUT')
        self.assertFalse(f.receive_permit(dict(p,permit_seq=2),1.51))
        s,f,c,p=self.running()
        f.receive_permit(dict(p,permit_seq=2),2.6)
        v,e=f.tick(2.6)
        self.assertEqual(v,(0.,0.))
        self.assertEqual(e[0]['reason'],'COORDINATOR_TIMEOUT')

    def test_task_change_waits_for_stop_and_old_goal_cannot_resume(self):
        s,f,c,p=self.running()
        stop=s.commands({1:wish(task='other',version=2)},1.1,1.1)[1]
        self.assertEqual(stop['mode'],'STOP')
        self.assertTrue(f.receive_command(stop,1.1,1.1))
        self.assertFalse(f.receive_permit(dict(p,permit_seq=99),1.2))
        self.assertFalse(f.receive_command(dict(c,command_seq=99,stamp=1.2),1.2,1.2))
        self.assertEqual(f.phase,'stopping')
        ack=next(x for x in prove(f,1.1) if x['status']=='STOPPED')
        self.assertTrue(s.feedback(ack,2.1))
        new=s.commands({1:wish(task='other',version=2)},2.1,2.1)[1]
        self.assertNotEqual(token(new),token(c))

    def test_halted_ros_clock_cannot_make_stop_ack(self):
        s=ExecutionSupervisor([1],"s");f=VelocityFence(1)
        f.receive_command(s.commands({1:wish()},0.,0.)[1],0.,0.)
        for i in range(1,30):
            wall=i*.05;f.receive_odom(0.,(0.,0.,0.),(0.,0.),wall,0.)
            v,e=f.tick(wall);f.output_published(v,wall)
            self.assertFalse(e)

    def test_scope_distinguishes_same_tile_wall_and_neighbor_tile(self):
        g=Grid(4,3,1,(0,0),[0,-1,-1,100,100,100,100,100,0,-1,-1,100])
        tasks=[v for v in TaskTracker().update(g).values() if v['state']=='pending']
        a,b=[task_scope(g,t) for t in tasks]
        self.assertTrue(contains(a,1.5,.5))
        self.assertFalse(contains(a,1.5,2.5))
        self.assertTrue(contains(b,1.5,2.5))

    def test_stationary_twist_does_not_hide_moving_pose(self):
        s=ExecutionSupervisor([1],"s");f=VelocityFence(1)
        f.receive_command(s.commands({1:wish()},0.,0.)[1],0.,0.)
        for i in range(1,30):
            t=i*.05;f.receive_odom(t,(t,0.,0.),(0.,0.),t,t)
            v,e=f.tick(t);f.output_published(v,t);self.assertFalse(e)

    def test_goal_replacements_do_not_reset_stall_budget(self):
        s,f,c,p=self.running()
        found=[]
        for i in range(1,100):
            t=1.+i*.1
            c=s.commands({1:wish()},t,t)[1]
            f.receive_command(c,t,t)
            f.receive_permit(dict(p,permit_seq=i+1),t)
            f.receive_odom(t,(0.,0.,0.),(0.,0.),t,t)
            f.receive_raw(1.,0.,t)
            v,e=f.tick(t);f.output_published(v,t);found.extend(e)
        self.assertTrue(any(e.get('reason')=='EXECUTION_STALL' for e in found))

    def test_prefix_rollover_is_zero_and_waits_for_new_local_proposal(self):
        _,f,_,p=self.running()
        self.assertTrue(f.receive_permit(dict(p,permit_seq=2,paused='true',goal_seq='5'),1.03))
        self.assertEqual(f.tick(1.04),((0.,0.),[]))
        self.assertTrue(f.receive_permit(dict(p,permit_seq=3,paused='false',goal_seq='6'),1.05))
        self.assertEqual(f.tick(1.055),((0.,0.),[]))
        f.receive_odom(1.06,(0.,0.,0.),(0.,0.),1.06,1.06)
        f.receive_raw(.5,0.,1.06)
        self.assertEqual(f.tick(1.07),((.5,0.),[]))
        self.assertFalse(f.receive_permit(dict(p,permit_seq=4,goal_seq='5'),1.08))
        self.assertEqual(f.armed_at,1.)

    def test_rollover_does_not_override_stop_or_peer_gate(self):
        s,f,_,p=self.running()
        f.receive_permit(dict(p,permit_seq=2,paused=True),1.03)
        traffic=TrafficGuard(1)
        traffic.receive(dict(robot=1,seq=1,token=f.active_token,epoch=1,stamp=1.03,
                             mode='RETREAT',velocity=[-.2,0.]),f.active_token,1.03)
        traffic.reverse_ok=lambda *_:True
        self.assertEqual(traffic.filter(f,(1.,0.),1.04,1.04)[0],(0.,0.))
        stop=s.commands({1:wish(task='other',version=2)},1.1,1.1)[1]
        f.receive_command(stop,1.1,1.1)
        self.assertFalse(f.receive_permit(dict(p,permit_seq=3,paused=False),1.11))
        self.assertEqual(f.tick(1.12),((0.,0.),[]))

    def test_lost_rollover_renewal_still_times_out(self):
        _,f,_,p=self.running()
        f.receive_permit(dict(p,permit_seq=2,paused=True),1.03)
        velocity,events=f.tick(1.34)
        self.assertEqual(velocity,(0.,0.))
        self.assertEqual(events[0]['reason'],'EXECUTOR_TIMEOUT')

    def test_external_stop_nonce_is_bound_to_request_id(self):
        s,f,c,p=self.running()
        s.request_stop(1,'request-A',1.1)
        cmd=s.commands({1:wish()},1.1,1.1)[1]
        f.receive_command(cmd,1.1,1.1)
        ack=next(x for x in prove(f,1.1) if x['status']=='STOPPED')
        self.assertFalse(s.feedback(dict(ack,request_ids=['request-B']),2.1))
        self.assertTrue(s.feedback(ack,2.1))

    def test_property_tree_false_is_not_motion_permission(self):
        s,f,c,p=self.running()
        self.assertTrue(f.receive_permit(dict(p,permit_seq=2,allow='false'),1.02))
        self.assertEqual(f.tick(1.02)[0],(0.,0.))
        self.assertEqual(f.phase,'tripped')

    def test_cached_follower_velocity_is_not_reused_on_new_dispatch(self):
        s=ExecutionSupervisor([1],'s');f=VelocityFence(1)
        f.receive_command(s.commands({1:wish()},0.,0.)[1],0.,0.)
        s.feedback(next(x for x in prove(f) if x['status']=='STOPPED'),1.)
        route=s.commands({1:wish()},1.,1.)[1];f.receive_command(route,1.,1.)
        f.receive_raw(2.,0.,1.01)
        f.receive_permit({'token':token(route),'issuer':'executor','permit_seq':1,'allow':True},1.02)
        self.assertEqual(f.tick(1.03)[0],(0.,0.))
        f.receive_raw(.3,0.,1.04)
        self.assertEqual(f.tick(1.04)[0],(.3,0.))

    def test_delayed_stop_is_safe_but_delayed_motion_is_rejected(self):
        s,f,c,p=self.running()
        stop=s.commands({1:dict(wish(),mode='WAIT')},1.1,1.1)[1]
        self.assertTrue(f.receive_command(stop,5.,5.))
        self.assertEqual(f.tick(5.)[0],(0.,0.))
        self.assertFalse(f.receive_command(dict(c,command_seq=99),5.,5.))

    def test_team_handover_waits_for_both_old_executors(self):
        s=ExecutionSupervisor([1,2],'s')
        desired={1:wish(),2:wish(robot=2,task='second',version=2)}
        stops=s.commands(desired,0.,0.)
        def ack(c):return dict(c,source='velocity_gate',status='STOPPED',fresh_samples=5,stationary_s=.7,zero_s=.8)
        for r in (1,2):self.assertTrue(s.feedback(ack(stops[r]),.8))
        routes=s.commands(desired,1.,1.)
        new={1:dict(wish(),mode='WAIT'),2:wish(robot=2,version=3)}
        stops=s.commands(new,1.1,1.1)
        self.assertEqual([stops[r]['mode'] for r in (1,2)],['STOP','STOP'])
        self.assertTrue(s.feedback(ack(stops[2]),2.))
        self.assertEqual(s.commands(new,2.,2.)[2]['mode'],'STOP')
        self.assertTrue(s.feedback(ack(stops[1]),2.1))
        self.assertEqual(s.commands(new,2.1,2.1)[2]['mode'],'ROUTE')

    def test_delayed_pre_request_odom_does_not_count(self):
        s=ExecutionSupervisor([1],'s');f=VelocityFence(1)
        c=s.commands({1:wish()},1.,1.)[1];f.receive_command(c,1.,1.)
        for i in range(1,20):
            now=1.+i*.05
            f.receive_odom(.99,(0.,0.,0.),(0.,0.),now,now)
            v,e=f.tick(now);f.output_published(v,now)
            self.assertFalse(e)


if __name__=='__main__':unittest.main()
