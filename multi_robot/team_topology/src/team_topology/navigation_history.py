"""Keep own verified navigation connections when the current local STG prunes.

This is graph history, not occupancy fusion. Shared edges retain their sampled
known-free paths; every retained segment is revalidated on the author's own map.
Degree-two compression removes redundant vertices while preserving branches,
cycles and current task entrances. It is not a DTW implementation.
"""
import hashlib
from collections import defaultdict
from .graph import wire


class NavigationHistory:
    def __init__(self):
        self.segments=set();self.lattice=None

    def update(self, grid, records, builder):
        lattice=(grid.resolution,grid.origin)
        if self.lattice is not None and lattice!=self.lattice:raise ValueError('history lattice changed')
        self.lattice=lattice
        for e in list(records.values()):
            if e['kind']!='edge':continue
            cells=[grid.cell(p) for p in e['path']]
            for a,b in zip(cells,cells[1:]):
                if sum(abs(x-y) for x,y in zip(a,b))!=1:continue
                if grid.state(a)==0 and grid.state(b)==0:self.segments.add(tuple(sorted((a,b))))
        # New obstacles/unknown invalidate history. Never retain an old free
        # certificate merely because it once helped connect the two robots.
        self.segments={s for s in self.segments if all(grid.state(u)==0 for u in s)}
        adj=defaultdict(set)
        for a,b in self.segments:adj[a].add(b);adj[b].add(a)
        anchors={u for u,v in adj.items() if len(v)!=2}
        # Current roots/task portals are already path-sample vertices in the
        # receiver's Navigation index. Forcing them as compression endpoints
        # would rewrite long history edges whenever a robot moved one cell.
        # An all-degree-two ring needs two anchors to retain its two routes.
        pending=set(adj)
        while pending:
            seed=min(pending);component={seed};todo=[seed];pending.remove(seed)
            while todo:
                for q in adj[todo.pop()]:
                    if q in pending:pending.remove(q);component.add(q);todo.append(q)
            if len(component&anchors)<2:anchors.update((min(component),max(component)))
        def node(u):
            key=builder.key('node','history_%d_%d'%u)
            records[key]=dict(kind='node',p=grid.xy(u),role='history');return key
        used=set()
        for start in sorted(anchors):
            for nxt in sorted(adj[start]):
                segment=tuple(sorted((start,nxt)))
                if segment in used:continue
                used.add(segment);path=[start,nxt];previous,cur=start,nxt
                while cur not in anchors:
                    q=next(p for p in adj[cur] if p!=previous)
                    used.add(tuple(sorted((cur,q))));path.append(q);previous,cur=cur,q
                a,b=node(start),node(cur)
                # A cycle/parallel alternative must not overwrite another route
                # between the same endpoints. Hash the canonical sampled path.
                canonical=min(path,list(reversed(path)))
                digest=hashlib.sha256(wire(canonical).encode()).hexdigest()[:20]
                key=builder.key('edge','history_'+digest)
                records[key]=dict(kind='edge',a=a,b=b,path=[grid.xy(p) for p in path],
                                  resolution=grid.resolution,evidence='known_free')
