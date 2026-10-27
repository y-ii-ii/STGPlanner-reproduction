"""Compile the exact production scoring block with controlled graph fixtures."""
import hashlib
import json
import subprocess
from pathlib import Path
from path_frontier_repair import repair_local_frontier_selection

root=Path('/mnt/d/STGPlanner'); out=root/'codex/outputs/path_frontier_selection_regression'
out.mkdir(exist_ok=True)
baseline=out/'native_before_selection_repair.cpp'
if not baseline.exists():
    archived=root/'catkin_ws/src/STGPlanner/evidence/scene4-progress-fix/path_frontier_selection_regression/native_before_selection_repair.cpp'
    candidate=archived if archived.exists() else root/'benchmarks/progress_repairs/gbp2__gbplanner__src__rrg.cpp.after'
    if '// BEGIN_LOCAL_FRONTIER_ELIGIBILITY' in candidate.read_text():
        candidate=root/'benchmarks/progress_repairs/gbp2__gbplanner__src__rrg.cpp.before'
    baseline.write_text(candidate.read_text())
native=baseline.read_text()
start=native.index('  double best_gain = 0;',native.index('// Gain evaluation for valid paths'))
end=native.index('  if (planning_params_.auto_global_planner_enable)',start)
original=native[start:end]
full_repaired=repair_local_frontier_selection(native)
assert repair_local_frontier_selection(full_repaired)==full_repaired
repaired_start=full_repaired.index('  double best_gain = 0;',full_repaired.index('// Gain evaluation for valid paths'))
repaired_end=full_repaired.index('  if (planning_params_.auto_global_planner_enable)',repaired_start)
repaired=full_repaired[repaired_start:repaired_end]
(out/'selection.original.cpp').write_text(original)
(out/'selection.repaired.cpp').write_text(repaired)
header=r'''
#include <Eigen/Dense>
#include <vector>
#include <map>
#include <cmath>
#include <iostream>
enum class RobotType {kGroundRobot,kAirRobot};
struct Gain {double gain=0,accumulative_gain=0;int num_unknown_voxels=0;bool is_frontier=false;};
struct Vertex {int id; Eigen::Vector4d state=Eigen::Vector4d::Zero(); Gain vol_gain;bool is_hanging=false;};
struct Graph {
  std::map<int,Vertex> vertices;std::map<int,std::vector<int>> paths;
  void getShortestPath(int id,int,bool,std::vector<Vertex*>& result){for(int vertex:paths[id])result.push_back(&vertices[vertex]);}
  void getShortestPath(int id,int,bool,std::vector<Eigen::Vector3d>& result){for(int vertex:paths[id])result.push_back(vertices[vertex].state.head(3));}
  double getShortestDistance(int,int){return 0;}
};
struct Planning {double path_length_penalty=0,path_direction_penalty=0,hanging_vertex_penalty=1,max_negative_inclination=.5;};
struct Robot {RobotType type=RobotType::kGroundRobot;};
struct Map {double getResolution(){return .2;}};
struct Trajectory {static double computeDistanceBetweenTrajectoryAndDirection(const std::vector<Eigen::Vector3d>&,double,double,bool){return 0;}};
struct Result {int id;double gain;bool frontier;};
Result ORIGINAL(Graph* local_graph_,std::vector<Vertex*> leaf_vertices,std::map<int,std::map<int,double>> edge_inclinations_){
 int local_graph_rep_=0;Planning planning_params_;Robot robot_params_;Map map;Map* map_manager_=&map;double exploring_direction_=0;
'''
tail='  return {best_path_id,best_gain,frontier_exists};\n}\n'
program=header+original+tail+header[header.index('Result ORIGINAL('):].replace('ORIGINAL','REPAIRED')+repaired+tail
program+=r'''
int main(){
  bool first=true;std::cout<<"{\"cases\":[";
  auto run=[&](const char* name, Graph& graph,std::vector<int> leaves,std::map<int,std::map<int,double>> slopes,int expected_old,int expected_new,bool expected_frontier){
    std::vector<Vertex*> ptrs;for(int id:leaves)ptrs.push_back(&graph.vertices[id]);
    Result old=ORIGINAL(&graph,ptrs,slopes),fixed=REPAIRED(&graph,ptrs,slopes);
    bool pass=old.id==expected_old && fixed.id==expected_new && fixed.frontier==expected_frontier;
    if(!first)std::cout<<",";first=false;
    std::cout<<"{\"name\":\""<<name<<"\",\"original_id\":"<<old.id<<",\"repaired_id\":"<<fixed.id<<",\"original_frontier_exists\":"<<(old.frontier?"true":"false")<<",\"repaired_frontier_exists\":"<<(fixed.frontier?"true":"false")<<",\"passed\":"<<(pass?"true":"false")<<"}";
    if(!pass)exit(2);
  };
  Graph graph;
  for(int id=0;id<6;id++){graph.vertices[id].id=id;graph.vertices[id].state<<id,0,.7,0;}
  graph.paths[1]={0,1};graph.paths[2]={0,2};
  graph.vertices[1].vol_gain.gain=200;graph.vertices[2].vol_gain.gain=100;graph.vertices[2].vol_gain.is_frontier=true;
  run("nonfrontier_score_cannot_displace_frontier_path",graph,{1,2},{},1,2,true);
  graph.vertices[2].vol_gain.is_frontier=false;
  run("no_frontier_does_not_emit_positive_local_path",graph,{1,2},{},1,0,false);
  graph.vertices[1].vol_gain.is_frontier=true;graph.vertices[2].vol_gain.is_frontier=true;
  run("highest_valid_frontier_score_preserved",graph,{1,2},{},1,1,true);
  graph.vertices[1].is_hanging=true;
  run("hanging_frontier_not_eligible",graph,{1,2},{},2,2,true);
  graph.vertices[1].is_hanging=false;graph.vertices[2].vol_gain.is_frontier=false;
  graph.paths[3]={0,1,3};graph.vertices[3].state[2]=-.3;graph.vertices[3].vol_gain.gain=300;
  run("inadmissible_frontier_does_not_suppress_global_fallback",graph,{3,2},{{3,{{1,1.0}}}},2,0,false);
  std::cout<<"]}\n";
}
'''
source=out/'actual_selection_regression.cpp';binary=out/'actual_selection_regression'
source.write_text(program)
subprocess.run(['g++','-O0','-std=c++17','-I/usr/include/eigen3',str(source),'-o',str(binary)],check=True)
data=json.loads(subprocess.check_output([str(binary)],text=True))
data.update(passed=all(case['passed'] for case in data['cases']),source_scope='Exact production path-scoring block; controlled paths/gains/inclinations; no ROS or simulated motion.',
    baseline_native_sha256=hashlib.sha256(native.encode()).hexdigest())
data['checks']={case['name']:case['passed'] for case in data['cases']}
data['checks']['transformation_idempotent']=repair_local_frontier_selection(full_repaired)==full_repaired
(out/'result.json').write_text(json.dumps(data,indent=2)+'\n')
print(json.dumps(data,indent=2))
