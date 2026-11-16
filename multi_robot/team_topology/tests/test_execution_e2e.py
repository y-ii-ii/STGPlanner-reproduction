"""Synthetic message/feedback sequence, not a physics simulation or ROS run."""
import json
import unittest
from team_topology.offline_demo import snapshot
from team_topology.exporter import LocalExporter
from team_topology.graph import GraphStore,wire
from team_topology.allocator import Coordinator
from team_topology.execution import ExecutionSupervisor,VelocityFence,token
from team_topology.scope import contains


class EndToEndTests(unittest.TestCase):
    def test_real_export_to_partition_to_fence_then_executor_loss(self):
        store=GraphStore()
        for r in (1,2):
            store.apply(json.loads(wire(LocalExporter(r,'e2e').snapshot(snapshot(r)))))
        c=Coordinator();s=ExecutionSupervisor([1,2],'e2e')
        fences={r:VelocityFence(r) for r in (1,2)}
        stops=s.commands(c.plan(store,1.),0.,1.)
        for r,f in fences.items():self.assertTrue(f.receive_command(stops[r],0.,1.))
        for i in range(1,20):
            wall=i*.05;ros=wall+1.
            for r,f in fences.items():
                p=snapshot(r)['pose']
                f.receive_odom(ros,(p[0],p[1],0.),(0.,0.),wall,ros)
                v,events=f.tick(wall);f.output_published(v,wall)
                for e in events:self.assertTrue(s.feedback(e,wall))
        routes=s.commands(c.plan(store,1.95),.95,1.95)
        self.assertNotEqual(routes[1]['task'],routes[2]['task'])
        for r,f in fences.items():
            route=routes[r];self.assertTrue(f.receive_command(route,.95,1.95))
            self.assertTrue(any(contains(scope,*route['path'][-1]) for scope in route['scopes']))
            # Actual native property_tree representation uses string scalars.
            permit={'token':token(route),'issuer':'executor-%d'%r,'permit_seq':'1','allow':'true'}
            self.assertTrue(f.receive_permit(permit,.95))
            f.receive_raw(.5,0.,.96)
            self.assertEqual(f.tick(.97)[0],(.5,0.))
        # One executor vanishes; no permit renewal and no cached stop ACK.
        v,events=fences[1].tick(1.3)
        self.assertEqual(v,(0.,0.));self.assertEqual(events[0]['reason'],'EXECUTOR_TIMEOUT')
        self.assertTrue(s.feedback(events[0],1.3))
        commands=s.commands(c.plan(store,2.3),1.3,2.3)
        self.assertEqual(commands[1]['mode'],'STOP')
        self.assertEqual(commands[2]['mode'],'ROUTE')
        self.assertEqual(c.ledger.items[routes[1]['task']]['state'],'dispatched')
        fences[1].receive_command(commands[1],1.3,2.3)
        self.assertFalse(fences[1].receive_permit(
            {'token':token(routes[1]),'issuer':'executor-1','permit_seq':99,'allow':True},1.31))
        for i in range(1,20):
            wall=1.3+i*.05;ros=wall+1.
            fences[1].receive_odom(ros,(1.5,4.5,0.),(0.,0.),wall,ros)
            v,events=fences[1].tick(wall);fences[1].output_published(v,wall)
            for e in events:self.assertTrue(s.feedback(e,wall))
        robot,old=s.released.pop(0)
        self.assertTrue(c.ledger.release(old['task'],robot,old['version']))
        self.assertEqual(c.ledger.items[old['task']]['state'],'assigned')
        self.assertTrue(all(t['state']=='pending' for t in store.live('task').values()))

    def test_stall_defers_only_execution_not_observation_completion(self):
        store=GraphStore()
        for r in (1,2):store.apply(LocalExporter(r,'deferral').snapshot(snapshot(r)))
        c=Coordinator();plan=c.plan(store,1.)
        task=plan[1]['task'];c.defer(1,task,10.,8.)
        self.assertEqual(c.plan(store,1.1,wall_now=10.1)[1]['mode'],'WAIT')
        self.assertEqual(store.live('task')[task]['state'],'pending')
        self.assertEqual(c.ledger.items[task]['state'],'dispatched')


if __name__=='__main__':unittest.main()
