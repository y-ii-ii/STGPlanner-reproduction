import copy,json,unittest
from team_topology.traffic import TrafficGuard,restrict_pass
from team_topology.execution import VelocityFence
from team_topology.observations import TeamObservations
from team_topology.lease_publisher import LeasePublisher
from team_topology.scope import completion_signature
from team_topology.exporter import LocalExporter
from team_topology.graph import GraphStore
import test_assignee_completion as fixtures


class PassBrakeTests(unittest.TestCase):
    def test_recorded_zero_intent_cannot_be_revived(self):
        g=TrafficGuard(1);f=VelocityFence(1);f.phase='running';f.active_token='t';f.armed_at=0.
        g.receive(dict(robot=1,seq=1,token='t',epoch=1,stamp=10.,mode='PASS',velocity=[1.,0.]),'t',0.)
        self.assertEqual(g.filter(f,(0.,0.),.1,10.1)[0],(0.,0.))
    def test_current_linear_brake_bounds_old_curve(self):
        self.assertEqual(restrict_pass((.5,.1),(2.,.2)),(.5,.05))
    def test_current_angular_brake_scales_whole_curve(self):
        v,w=restrict_pass((1.,.2),(1.,.6));self.assertAlmostEqual(w,.2);self.assertAlmostEqual(v,1./3.)
    def test_new_turn_and_reverse_wait_for_compatible_admission(self):
        self.assertEqual(restrict_pass((0.,.3),(1.,0.)),(0.,0.))
        self.assertEqual(restrict_pass((-.2,0.),(1.,0.)),(0.,0.))
        self.assertEqual(restrict_pass((0.,.2),(0.,.3)),(0.,.2))
    def test_nonfinite_and_zero_request_fail_closed(self):
        self.assertEqual(restrict_pass((float('nan'),0.),(1.,0.)),(0.,0.))
        self.assertEqual(restrict_pass((0.,0.),(0.,.3)),(0.,0.))


class AuthorObservationTests(unittest.TestCase):
    def fixture(self):
        c,store,a,records,state,key,route,_=fixtures.AssigneeCompletionTests().fixture()
        digest,count=completion_signature([records[key]['scope']])
        task=copy.deepcopy(records[key]);task.update(state='completed',observation='all_previous_unknown_observed',map_rev=2)
        task['observation_proof']=dict(schema=1,frame='world',author=a.author,evidence='own_observed_support',scope_digest=digest,required_cells=count,observed_cells=count,map_rev=2,stamp=1.2)
        return c,store,a,records,dict(state,stamp=1.2,map_rev=2),key,route,task
    def test_author_summary_retires_other_assignee_but_not_ownership(self):
        c,store,a,records,state,key,route,task=self.fixture();c.commit_dispatches({2:route})
        edges=copy.deepcopy(store.live('edge'));records[key]=task;delta=a.build(records,state);store.apply(delta)
        c.ingest_author_observations(store,delta['records'])
        self.assertEqual(len(c.observed_support),2);self.assertTrue(c.team_completed(route))
        self.assertEqual(c.ledger.items[key]['state'],'dispatched');self.assertEqual(store.live('edge'),edges)
        c.ledger.release(key,2,route['version']);self.assertEqual(c.ledger.items[key]['state'],'completed')
    def test_forged_partial_future_and_mismatched_proofs_cannot_add_cells(self):
        _,_,a,_,state,key,_,task=self.fixture();state['author']=a.author
        for change in ({'author':'2/foreign'},{'observed_cells':1},{'observed_cells':2.5},{'scope_digest':'bad'},{'stamp':9.},{'map_rev':3},{'frame':'map'}):
            bad=copy.deepcopy(task);bad['observation_proof'].update(change);support=set()
            self.assertFalse(TeamObservations(support).accept(key,bad,state));self.assertFalse(support)
    def test_duplicates_and_aliases_do_not_inflate_world_support(self):
        _,_,a,_,state,key,_,task=self.fixture();state['author']=a.author;support=set();o=TeamObservations(support)
        self.assertTrue(o.accept(key,task,state));self.assertFalse(o.accept(key,task,state))
        self.assertTrue(o.accept(key+'alias',task,state));self.assertEqual(len(support),2);self.assertEqual(o.new_cells,2)
    def test_novel_unknown_cells_not_completed_by_old_summary(self):
        c,store,a,records,state,key,route,task=self.fixture();state['author']=a.author
        c.team_observations.accept(key,task,state)
        grown=copy.deepcopy(route);grown['scopes'][0]['unknown_runs']=[[1,2,4]]
        self.assertFalse(c.team_completed(grown))
    def test_exporter_certifies_only_actual_own_observation_and_reuses_proof(self):
        e=LocalExporter(1,'own');data=[0]*24;data[8]=data[9]=-1
        snap=dict(frame='world',pose=[.5,.5],stamp=10.,nodes=[],edges=[],grid=dict(width=6,height=4,resolution=1.,origin=[0,0],data=data))
        first=e.snapshot(snap);self.assertFalse(any('observation_proof' in r.get('value',{}) for r in first['records'].values() if not r['deleted']))
        snap=copy.deepcopy(snap);snap['stamp']=10.5;snap['grid']['data'][8]=0;snap['grid']['data'][9]=100
        second=e.snapshot(snap);completed=[r['value'] for r in second['records'].values() if not r['deleted'] and r['value'].get('state')=='completed']
        self.assertTrue(completed);self.assertTrue(all(t['observation_proof']['observed_cells']==2 for t in completed))
        snap['stamp']=11.;full=e.snapshot(snap,full=True)
        self.assertTrue(all(r['value']['observation_proof']['stamp']==10.5 for r in full['records'].values() if not r['deleted'] and r['value'].get('state')=='completed'))


class LeasePublisherTests(unittest.TestCase):
    def fixture(self):
        sent=[];p=LeasePublisher(lambda r,text:sent.append((r,json.loads(text))))
        route=dict(schema=2,frame='world',mode='ROUTE',robot=1,allocation_session='s',task='t',version=7,dispatch_id=3,scopes=[{'x':1}],path=[[0,0],[2,0]])
        p.commit({1:route},{1:100.,2:100.},0.,100.);return p,sent,route
    def test_expensive_owner_cycle_keeps_fresh_same_contract(self):
        p,sent,route=self.fixture()
        for i in range(1,18):
            if i==7:p.health({1:100.7,2:100.7},.7)
            p.tick(i*.1,100.+i*.1)
        last=sent[-1][1];self.assertGreater(last['command_seq'],1);self.assertAlmostEqual(last['stamp'],101.7)
        for key in ('task','version','dispatch_id','scopes','path'):self.assertEqual(last[key],route[key])
        self.assertLessEqual(p.stats()['max_publish_gap_s'],.100001)
    def test_dead_authority_cannot_renew_motion_forever(self):
        p,sent,_=self.fixture();n=len(sent);self.assertFalse(p.tick(1.3,101.3));self.assertEqual(len(sent),n)
    def test_stale_validated_source_or_mission_stop_suppresses_motion(self):
        p,sent,_=self.fixture();p.health({1:100.,2:100.},4.)
        self.assertFalse(p.tick(4.,104.));p.health({1:104.,2:104.},4.)
        self.assertFalse(p.tick(4.1,104.1,False));self.assertEqual(len(sent),1)
    def test_stop_nonce_and_order_are_never_replaced_by_old_route(self):
        p,sent,_=self.fixture();stop=dict(mode='STOP',robot=1,allocation_session='s',stop_id='s/stop/9',request_ids=['q'],path=[])
        p.commit({1:stop},{},.2,100.2,False);p.tick(8.,108.,False)
        self.assertTrue(all(v['mode']=='STOP' and v['stop_id']=='s/stop/9' and v['request_ids']==['q'] for _,v in sent[1:]))
        self.assertEqual([v['command_seq'] for _,v in sent],[1,2,3])
    def test_caller_mutation_and_clock_reversal_cannot_change_live_contract(self):
        p,sent,route=self.fixture();route['path'][1][0]=999
        p.tick(.1,100.1);self.assertEqual(sent[-1][1]['path'][1][0],2)
        self.assertFalse(p.tick(.2,99.))

    def test_runtime_clock_is_resampled_after_delayed_publication_lock(self):
        clock=[0.,100.];sent=[];p=LeasePublisher(lambda r,text:sent.append(text),clocks=lambda:tuple(clock))
        p.commit({1:self.fixture()[2]},{1:100.,2:100.},0.,100.)
        clock[:]=[4.,104.]
        self.assertFalse(p.tick(.1,100.1));self.assertEqual(len(sent),1)

    def test_renewal_prevents_spurious_lease_expiry_but_dead_owner_still_trips_fence(self):
        f=VelocityFence(1);f.phase='stopped';clock=[0.,100.]
        p=LeasePublisher(lambda r,text:f.receive_command(json.loads(text),clock[0],clock[1]))
        route=self.fixture()[2];p.commit({1:route},{1:100.,2:100.},0.,100.)
        token='s/1/7/3';events=[]
        for i in range(1,37):
            now=i*.1;clock[:]=[now,100.+now]
            if i==7:p.health({1:100.7,2:100.7},.7)
            p.tick(now,100.+now)
            f.receive_permit(dict(token=token,issuer='executor',permit_seq=i,allow=True),now)
            f.receive_odom(100.+now,(.4*now,0.,0.),(.4,0.),now,100.+now);f.receive_raw(.4,0.,now)
            output,new=f.tick(now);events+=new
            if i==17:self.assertEqual(output,(.4,0.));self.assertEqual(f.phase,'running')
        self.assertEqual(f.phase,'tripped');self.assertIn('COORDINATOR_TIMEOUT',[e['reason'] for e in events])


if __name__=='__main__':unittest.main()
