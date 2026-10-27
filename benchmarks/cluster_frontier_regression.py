"""Execute the full extracted native clustered-gain function on a two-node fixture."""
from pathlib import Path
import subprocess,json
root=Path('/mnt/d/STGPlanner/benchmarks')
native=Path('/opt/stgplanner/benchmarks/gbp2_ws/src/gbplanner/src/rrg.cpp')
scratch=Path('/opt/stgplanner/benchmarks/core_regression');scratch.mkdir(exist_ok=True)
stub=r'''
#include <vector>
#include <list>
#include <unordered_map>
#include <algorithm>
#include <chrono>
#include <iostream>
#define START_TIMER(x)
#define GET_ELAPSED_TIME(x) 0
#define ROS_INFO_COND(...)
namespace ros{struct Time{};}
enum class VertexType{kUnvisited,kFrontier};
struct Gain{bool is_frontier=false;};
struct Vertex{int id;bool is_leaf_vertex=true;int state=0;Gain vol_gain;VertexType type=VertexType::kUnvisited;};
struct Graph{std::unordered_map<int,Vertex*> vertices_map_;int getNumVertices(){return vertices_map_.size();}
void getNearestVertices(int*,double,std::vector<Vertex*>* out){for(auto v:vertices_map_)out->push_back(v.second);}};
struct Params{double clustering_radius=.5;bool use_ray_model_for_volumetric_gain=true;};
struct Stat{double compute_exp_gain_time=0;};
struct Rrg{Graph* local_graph_;Params planning_params_;Stat a,b;Stat* stat_=&a;Stat* stat_chrono_=&b;bool frontier=true;
void computeVolumetricGainRayModel(int&,Gain& g,bool,bool){g.is_frontier=frontier;}
void computeVolumetricGain(int&,Gain& g,bool){g.is_frontier=frontier;}
void computeExplorationGain(bool,bool);
};
'''
def execute(label,text,frontier):
    start=text.index('void Rrg::computeExplorationGain(bool only_leaf_vertices, bool clustering)')
    body=text[start:text.index('\n}\n',start)+3]
    main='''int main(){Vertex a,b;a.id=0;b.id=1;Graph g;g.vertices_map_={{0,&a},{1,&b}};Rrg r;r.local_graph_=&g;r.frontier=FRONTIER;r.computeExplorationGain(false,true);int gain=0,type=0;for(auto v:g.vertices_map_){gain+=v.second->vol_gain.is_frontier;type+=v.second->type==VertexType::kFrontier;}std::cout<<gain<<" "<<type;}'''.replace('FRONTIER','true' if frontier else 'false')
    p=scratch/(label+'.cpp');p.write_text(stub+body+main)
    subprocess.run(['g++','-std=c++17',str(p),'-o',str(p.with_suffix(''))],check=True)
    return list(map(int,subprocess.check_output([str(p.with_suffix(''))],text=True).split()))
before=(root/'progress_repairs/gbp2__gbplanner__src__rrg.cpp.before').read_text()
after=native.read_text()
old=execute('cluster_original',before,True);new=execute('cluster_fixed',after,True);zero=execute('cluster_zero',after,False)
checks={'original_cluster_gain_type_mismatch_reproduced':old==[2,1],
        'fixed_all_cluster_frontiers_preserved':new==[2,2],
        'zero_gain_cluster_does_not_invent_frontiers':zero==[0,0]}
value={'passed':all(checks.values()),'checks':checks,'counts_gain_frontiers_and_typed_frontiers':{'original':old,'fixed':new,'nonfrontier':zero},'note':'Full actual extracted clustered-gain function; graph neighbourhood and gain responses controlled. Proves an implementation inconsistency, not full exploration success.'}
(root/'cluster_frontier_regression.json').write_text(json.dumps(value,indent=2));print(json.dumps(value,indent=2))
if not value['passed']:raise SystemExit(1)
