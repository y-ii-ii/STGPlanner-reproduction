from pathlib import Path
import json,sys,time,statistics
sys.path.insert(0,sys.argv[1]);from team_topology.graph import GraphStore
p=Path('/mnt/d/STGPlanner/benchmarks/results/topology_dispatch_scene4_20261117_04_dual/topology_deltas.jsonl')
full={}
with p.open('rb') as f:
 start=max(0,p.stat().st_size-8*1024*1024);f.seek(start)
 if start:f.readline()
 for l in f:
  d=json.loads(l)
  if d.get('full'):full[d['author']]=d
assert len(full)==2
store=GraphStore()
for d in full.values():store.apply(d)
dig=store.digest();dur=[];initial_records=len(store.records)
for i in range(100):
 author=sorted(full)[i%2];d=full[author];d=dict(d,records={},full=False,seq=store.sequences[author]+1,state=dict(d['state'],stamp=d['state']['stamp']+i*.1))
 began=time.monotonic();store.apply(d);store.digest();dur.append(time.monotonic()-began)
assert store.digest()==dig
result=dict(no_ros_or_physics=True,source='last full packets of preserved dispatch04; 100 synthetic state-only heartbeats',records=initial_records,nodes=len(store.live('node')),edges=len(store.live('edge')),digest=dig,median_s=statistics.median(dur),max_s=max(dur),sum_s=sum(dur),iterations=len(dur))
Path(sys.argv[2]).write_text(json.dumps(result,indent=2));print(json.dumps(result))
