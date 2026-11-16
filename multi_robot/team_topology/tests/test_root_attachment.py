import unittest
from team_topology.exporter import LocalExporter
from team_topology.graph import GraphStore
from team_topology.allocator import Coordinator

class RootAttachmentTests(unittest.TestCase):
    def test_nearest_isolated_anchor_does_not_strand_reachable_task(self):
        value={'frame':'world','stamp':1.,'pose':[.5,.5],
            'grid':{'width':5,'height':1,'resolution':1.,'origin':[0,0],'data':[0,0,0,0,-1]},
            'nodes':[{'id':0,'p':[.5,.5]},{'id':3,'p':[3.5,.5]}],'edges':[]}
        store=GraphStore();store.apply(LocalExporter(1,'root').snapshot(value))
        command=Coordinator(robots=(1,)).plan(store,1.)[1]
        self.assertEqual(command['mode'],'ROUTE');self.assertEqual(command['cost_m'],3.)
    def test_disconnected_free_island_still_cannot_bid(self):
        value={'frame':'world','stamp':1.,'pose':[.5,.5],
            'grid':{'width':5,'height':1,'resolution':1.,'origin':[0,0],'data':[0,100,0,0,-1]},
            'nodes':[{'id':0,'p':[.5,.5]},{'id':3,'p':[3.5,.5]}],'edges':[]}
        store=GraphStore();store.apply(LocalExporter(1,'blocked').snapshot(value))
        self.assertEqual(Coordinator(robots=(1,)).plan(store,1.)[1]['mode'],'WAIT')
