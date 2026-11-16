import random
import unittest
from team_topology.grid import Grid
from team_topology.tasks import TaskTracker
from team_topology.exporter import LocalExporter


class CompletenessTests(unittest.TestCase):
    def test_every_observed_free_unknown_neighbor_pair_is_represented(self):
        for seed in range(12):
            rng=random.Random(seed)
            g=Grid(13,11,.5,(-2.,-1.),[rng.choice([-1,0,100]) for _ in range(143)])
            tasks=[t for t in TaskTracker().update(g).values() if t['state']=='pending']
            for y in range(g.height):
                for x in range(g.width):
                    u=(x,y)
                    if g.state(u)!=-1:continue
                    for portal in g.neighbors(u):
                        if g.state(portal)==0:
                            self.assertTrue(any(u in t['cells'] and portal in t['portal_members'] for t in tasks),
                                            (seed,u,portal))
            for t in tasks:
                self.assertTrue(all(g.state(p)==-1 for p in t['cells']))
                self.assertTrue(all(g.state(p)==0 for p in t['portal_members']))

    def test_published_packet_mutation_does_not_corrupt_cached_export(self):
        exp=LocalExporter(1,'immutable')
        snap={'frame':'world','stamp':1.,'pose':[.5,.5],
              'grid':{'width':3,'height':1,'resolution':1,'origin':[0,0],'data':[0,-1,-1]},
              'nodes':[],'edges':[]}
        first=exp.snapshot(snap)
        key=exp.delta.key('node','root')
        first['records'][key]['value']['p']=[999,999]
        snap['stamp']=2.
        second=exp.snapshot(snap,full=True)
        self.assertEqual(tuple(second['records'][key]['value']['p']),(.5,.5))


if __name__=='__main__':unittest.main()
