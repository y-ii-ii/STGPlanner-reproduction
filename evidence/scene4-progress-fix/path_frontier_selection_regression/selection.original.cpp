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

