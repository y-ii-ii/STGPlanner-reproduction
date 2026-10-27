
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
  double best_gain = 0;
  int best_path_id = 0;
  int num_leaf_vertices = leaf_vertices.size();
  bool frontier_exists = false;
  std::vector<int> negative_edge_leafs;
  std::vector<Eigen::Vector3d> inadmissible_negative_edges;
  for (int i = 0; i < num_leaf_vertices; ++i) {
    int id = leaf_vertices[i]->id;
    std::vector<Vertex*> path;
    local_graph_->getShortestPath(id, local_graph_rep_, true, path);
    int path_size = path.size();
    int num_unknown_voxels = 0;
    if (path_size > 1) {
      // At least 2 vertices: root + leaf.
      double path_gain = 0;
      double lambda = planning_params_.path_length_penalty;
      bool inadmissible_edge = false;
      for (int ind = 0; ind < path_size; ++ind) {
        Vertex* v_id = path[ind];
        double path_length =
            local_graph_->getShortestDistance(v_id->id, local_graph_rep_);
        double vol_gain =
            v_id->vol_gain.gain *
            exp(-v_id->is_hanging * planning_params_.hanging_vertex_penalty);

        if (ind > 0 && robot_params_.type == RobotType::kGroundRobot) {
          double inclination =
              edge_inclinations_[path[ind]->id][path[ind - 1]->id];
          Eigen::Vector3d segment =
              path[ind]->state.head(3) - path[ind - 1]->state.head(3);
          if ((path[ind]->state(2) - path[ind - 1]->state(2)) <
              -map_manager_->getResolution()) {
            // Negative slope
            if (inclination > planning_params_.max_negative_inclination ||
                (std::atan2(std::abs(segment(2)), segment.head(2).norm()) >
                    planning_params_.max_negative_inclination)) {
              path_gain = 0.0;
              negative_edge_leafs.push_back(leaf_vertices[i]->id);
              inadmissible_negative_edges.push_back(
                  path[ind - 1]->state.head(3));
              inadmissible_negative_edges.push_back(path[ind]->state.head(3));
              inadmissible_edge = true;
            }
          }
        }
        if (!inadmissible_edge) {
          path_gain += vol_gain * exp(-lambda * path_length);
          v_id->vol_gain.accumulative_gain = path_gain;
          num_unknown_voxels += v_id->vol_gain.num_unknown_voxels;
          if (v_id->vol_gain.is_frontier && !v_id->is_hanging)
            frontier_exists = true;
        }
      }
      if (inadmissible_edge) {
        continue;
      }

      // Compare with exploring direction to penalty not-forward paths.
      double lambda2 = planning_params_.path_direction_penalty;
      std::vector<Eigen::Vector3d> path_list;
      local_graph_->getShortestPath(id, local_graph_rep_, true, path_list);
      double fw_ratio =
          Trajectory::computeDistanceBetweenTrajectoryAndDirection(
              path_list, exploring_direction_, 0.2, true);
      path_gain *= exp(-lambda2 * fw_ratio);

      if (path_gain > best_gain) {
        best_gain = path_gain;
        best_path_id = id;
      }
    }
  }

  return {best_path_id,best_gain,frontier_exists};
}
Result REPAIRED(Graph* local_graph_,std::vector<Vertex*> leaf_vertices,std::map<int,std::map<int,double>> edge_inclinations_){
 int local_graph_rep_=0;Planning planning_params_;Robot robot_params_;Map map;Map* map_manager_=&map;double exploring_direction_=0;
  double best_gain = 0;
  int best_path_id = 0;
  int num_leaf_vertices = leaf_vertices.size();
  bool frontier_exists = false;
  std::vector<int> negative_edge_leafs;
  std::vector<Eigen::Vector3d> inadmissible_negative_edges;
  for (int i = 0; i < num_leaf_vertices; ++i) {
    int id = leaf_vertices[i]->id;
    std::vector<Vertex*> path;
    local_graph_->getShortestPath(id, local_graph_rep_, true, path);
    int path_size = path.size();
    int num_unknown_voxels = 0;
    if (path_size > 1) {
      // At least 2 vertices: root + leaf.
      double path_gain = 0;
      double lambda = planning_params_.path_length_penalty;
      bool inadmissible_edge = false;
      bool path_has_frontier = false;
      for (int ind = 0; ind < path_size; ++ind) {
        Vertex* v_id = path[ind];
        double path_length =
            local_graph_->getShortestDistance(v_id->id, local_graph_rep_);
        double vol_gain =
            v_id->vol_gain.gain *
            exp(-v_id->is_hanging * planning_params_.hanging_vertex_penalty);

        if (ind > 0 && robot_params_.type == RobotType::kGroundRobot) {
          double inclination =
              edge_inclinations_[path[ind]->id][path[ind - 1]->id];
          Eigen::Vector3d segment =
              path[ind]->state.head(3) - path[ind - 1]->state.head(3);
          if ((path[ind]->state(2) - path[ind - 1]->state(2)) <
              -map_manager_->getResolution()) {
            // Negative slope
            if (inclination > planning_params_.max_negative_inclination ||
                (std::atan2(std::abs(segment(2)), segment.head(2).norm()) >
                    planning_params_.max_negative_inclination)) {
              path_gain = 0.0;
              negative_edge_leafs.push_back(leaf_vertices[i]->id);
              inadmissible_negative_edges.push_back(
                  path[ind - 1]->state.head(3));
              inadmissible_negative_edges.push_back(path[ind]->state.head(3));
              inadmissible_edge = true;
            }
          }
        }
        if (!inadmissible_edge) {
          path_gain += vol_gain * exp(-lambda * path_length);
          v_id->vol_gain.accumulative_gain = path_gain;
          num_unknown_voxels += v_id->vol_gain.num_unknown_voxels;
          if (v_id->vol_gain.is_frontier && !v_id->is_hanging)
            path_has_frontier = true;
        }
      }
      if (inadmissible_edge) {
        continue;
      }
      // An inadmissible path must not keep the local-frontier flag alive.
      frontier_exists = frontier_exists || path_has_frontier;

      // Compare with exploring direction to penalty not-forward paths.
      double lambda2 = planning_params_.path_direction_penalty;
      std::vector<Eigen::Vector3d> path_list;
      local_graph_->getShortestPath(id, local_graph_rep_, true, path_list);
      double fw_ratio =
          Trajectory::computeDistanceBetweenTrajectoryAndDirection(
              path_list, exploring_direction_, 0.2, true);
      path_gain *= exp(-lambda2 * fw_ratio);

      // Residual non-frontier gain must not displace an exploratory path.
      if (path_has_frontier && path_gain > best_gain) {
        best_gain = path_gain;
        best_path_id = id;
      }
    }
  }

  // END_LOCAL_FRONTIER_ELIGIBILITY

  return {best_path_id,best_gain,frontier_exists};
}

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
