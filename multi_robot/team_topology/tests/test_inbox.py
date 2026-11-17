import threading
import unittest
from team_topology.inbox import AuthorityInbox
from team_topology.execution import ExecutionSupervisor
from test_execution import wish
from test_stop_delivery import proof

class InboxTests(unittest.TestCase):
 def test_stop_ack_is_serviced_before_busy_graph_and_planner_lane(self):
  q=AuthorityInbox();s=ExecutionSupervisor([1],'s');c=s.commands({1:wish()},0.,0.)[1]
  for i in range(1000):
   q.put('topology',{'seq':i},10,.1);q.put('feedback',{'status':'ACCEPTED'},20,.1)
  q.put('feedback',proof(c),100,.7)
  events=q.feedback(normal_limit=0)
  self.assertEqual(len(events),1);self.assertTrue(s.feedback(events[0][1],.8))
  self.assertEqual(s.commands({1:wish()},.9,.9)[1]['mode'],'ROUTE')
  self.assertEqual(q.stats()['topology_pending'],1000)

 def test_topology_fifo_and_tombstones_are_never_silently_dropped(self):
  q=AuthorityInbox()
  for i in range(1000):q.put('topology',{'seq':i,'deleted':i%2==0},4,0.)
  self.assertEqual([q.packet()[1]['seq'] for _ in range(1000)],list(range(1000)))
  self.assertIsNone(q.packet())

 def test_capability_bytes_counted_without_authority_work(self):
  q=AuthorityInbox();q.put('feedback',{'status':'TRAFFIC_CAPABILITY'},123,0.)
  self.assertEqual(q.feedback(),[]);self.assertEqual(q.stats()['feedback_received_bytes'],123)

 def test_normal_budget_cannot_consume_critical_budget(self):
  q=AuthorityInbox()
  for i in range(5):q.put('feedback',{'status':'ACCEPTED','i':i},1,0.)
  q.put('feedback',{'status':'STOP_REQUEST'},1,1.)
  events=q.feedback(2)
  self.assertEqual([v['status'] for _,v in events],['STOP_REQUEST','ACCEPTED','ACCEPTED'])
  self.assertEqual(q.stats()['normal_pending'],3)

 def test_concurrent_callback_producers_do_not_lose_ack_messages(self):
  q=AuthorityInbox()
  def send(r):
   for i in range(100):q.put('feedback',{'status':'STOPPED','robot':r,'i':i},10,0.)
  threads=[threading.Thread(target=send,args=(r,)) for r in (1,2)]
  for t in threads:t.start()
  for t in threads:t.join()
  events=q.feedback(0);self.assertEqual(len(events),200);self.assertEqual(len({(v['robot'],v['i']) for _,v in events}),200)
  self.assertEqual(q.stats()['feedback_received_bytes'],2000)

if __name__=='__main__':unittest.main()
