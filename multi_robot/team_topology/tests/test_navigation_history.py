import unittest
from team_topology.navigation_history import NavigationHistory
from team_topology.graph import DeltaBuilder,GraphStore,Navigation
from team_topology.grid import Grid


class HistoryTests(unittest.TestCase):
    def records(self,g,cells):
        return {'a':dict(kind='node',p=g.xy(cells[0])), 'b':dict(kind='node',p=g.xy(cells[-1])),
                'e':dict(kind='edge',path=[g.xy(u) for u in cells])}

    def test_corridor_retained_when_local_edge_is_pruned(self):
        g=Grid(8,1,1,(0,0),[0]*8);h=NavigationHistory();b=DeltaBuilder(1,'h')
        first=self.records(g,[(x,0) for x in range(8)]);h.update(g,first,b)
        latest={};h.update(g,latest,b)
        self.assertEqual(sum(v['kind']=='edge' for v in latest.values()),1)
        self.assertEqual(sum(v['kind']=='node' for v in latest.values()),2)
        self.assertEqual(len(next(v for v in latest.values() if v['kind']=='edge')['path']),8)

    def test_new_obstacle_invalidates_old_bridge(self):
        g=Grid(8,1,1,(0,0),[0]*8);h=NavigationHistory();b=DeltaBuilder(1,'h');h.update(g,self.records(g,[(x,0) for x in range(8)]),b)
        blocked=Grid(8,1,1,(0,0),[0,0,0,100,0,0,0,0]);r={};h.update(blocked,r,b)
        self.assertTrue(all(all(blocked.state(blocked.cell(p))==0 for p in e['path']) for e in r.values() if e['kind']=='edge'))
        self.assertEqual(len(h.segments),5)

    def test_ring_keeps_two_routes_between_anchors(self):
        g=Grid(3,3,1,(0,0),[0]*9);cells=[(0,0),(1,0),(2,0),(2,1),(2,2),(1,2),(0,2),(0,1),(0,0)]
        h=NavigationHistory();b=DeltaBuilder(1,'h');h.update(g,self.records(g,cells),b);r={};h.update(g,r,b)
        edges=[e for e in r.values() if e['kind']=='edge'];self.assertEqual(len(edges),2)
        self.assertEqual(len({e['a'] for e in edges}|{e['b'] for e in edges}),2)

    def test_unknown_invalidates_history_and_lattice_change_rejected(self):
        g=Grid(3,1,1,(0,0),[0]*3);h=NavigationHistory();b=DeltaBuilder(1,'h');h.update(g,self.records(g,[(0,0),(1,0),(2,0)]),b)
        r={};h.update(Grid(3,1,1,(0,0),[0,-1,0]),r,b);self.assertFalse(h.segments)
        with self.assertRaises(ValueError):h.update(Grid(3,1,1,(1,0),[0]*3),{},b)


if __name__=='__main__':unittest.main()
