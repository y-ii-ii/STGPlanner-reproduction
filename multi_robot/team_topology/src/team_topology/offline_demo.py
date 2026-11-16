"""Small synthetic end-to-end fixture; no robot or simulator is run."""
import json
from .exporter import LocalExporter
from .graph import GraphStore, Navigation, wire
from .allocator import Coordinator


def snapshot(robot):
    width, height = 13, 7
    data = [100] * (width*height)
    # Two local observations of the same corridor, overlapping in its middle.
    known_x = range(1, 8) if robot == 1 else range(5, 12)
    for x in known_x:
        data[4*width+x] = 0
    branch_x = 3 if robot == 1 else 9
    for y in (2,3):
        data[y*width+branch_x]=0
    for y in (0,1):
        data[y*width+branch_x]=-1
    points = [[float(x)+.5,4.5] for x in known_x]
    nodes = [{"id":i,"p":p} for i,p in enumerate(points)]
    return {"frame":"world","stamp":1.,
        "pose": [1.5,4.5] if robot==1 else [11.5,4.5],
        "grid":{"width":width,"height":height,"origin":[0,0],"resolution":1.,"data":data},
        "nodes":nodes,"edges":[[i,i+1] for i in range(len(nodes)-1)]}


def run():
    store=GraphStore();exporters={r:LocalExporter(r,"demo") for r in (1,2)}
    initial_bytes=0
    for r in (1,2):
        packet=wire(exporters[r].snapshot(snapshot(r)))
        initial_bytes+=len(packet.encode())+4
        store.apply(json.loads(packet))
    coordinator=Coordinator()
    plans=coordinator.plan(store,1.)
    assert all(c['mode']=='ROUTE' for c in plans.values())
    assert plans[1]['task']!=plans[2]['task']
    assert plans[1]['path'][-1][0]==3.5
    assert plans[2]['path'][-1][0]==9.5
    nav=Navigation(store)
    peer_route=nav.route(exporters[1].delta.key('node','root'),
                         exporters[2].delta.key('node','root'))
    assert peer_route is not None
    assert any(e.startswith('2/') for e in peer_route['edges'])
    heartbeat_bytes=0
    for r in (1,2):
        value=snapshot(r);value['stamp']=2.
        packet=wire(exporters[r].snapshot(value))
        assert not json.loads(packet)['records']
        heartbeat_bytes+=len(packet.encode())+4
        store.apply(json.loads(packet))
    # Complete robot 1's locally observed task; robot 2's task remains pending.
    value=snapshot(1);value['stamp']=3.
    for y in (0,1):value['grid']['data'][y*13+3]=0
    store.apply(json.loads(wire(exporters[1].snapshot(value))))
    completed=[k for k,t in store.live('task').items() if t['state']=='completed']
    assert completed and all(k.startswith('1/') for k in completed)
    return {'fixture':'synthetic_two_branches_not_Scene4',
        'initial_commands':plans,'interrobot_route_cost_m':peer_route['cost'],
        'interrobot_route_contains_peer_edge':True,
        'initial_serialized_bytes_two_publications':initial_bytes,
        'unchanged_heartbeat_bytes_two_publications':heartbeat_bytes,
        'completed_observation_tasks':completed,'raw_map_transferred':False,
        'new_simulations':0,'new_T95':None}


if __name__=='__main__':
    print(json.dumps(run(),ensure_ascii=False,indent=2))
