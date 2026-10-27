"""Scoped native path/frontier eligibility repair; public protocol is untouched."""

def repair_local_frontier_selection(source):
    marker='// BEGIN_LOCAL_FRONTIER_ELIGIBILITY'
    if marker in source:
        assert 'if (path_has_frontier && path_gain > best_gain)' in source
        assert 'frontier_exists = frontier_exists || path_has_frontier;' in source
        return source
    start=source.index('  double best_gain = 0;',source.index('// Gain evaluation for valid paths'))
    end=source.index('  if (planning_params_.auto_global_planner_enable)',start)
    body=source[start:end]
    assert body.count('      bool inadmissible_edge = false;')==1
    body=body.replace('      bool inadmissible_edge = false;',
        '      bool inadmissible_edge = false;\n      bool path_has_frontier = false;')
    old='''          if (v_id->vol_gain.is_frontier && !v_id->is_hanging)
            frontier_exists = true;'''
    assert body.count(old)==1
    body=body.replace(old,'''          if (v_id->vol_gain.is_frontier && !v_id->is_hanging)
            path_has_frontier = true;''')
    old='''      if (inadmissible_edge) {
        continue;
      }
'''
    assert body.count(old)==1
    body=body.replace(old,old+'''      // An inadmissible path must not keep the local-frontier flag alive.
      frontier_exists = frontier_exists || path_has_frontier;
''')
    assert body.count('      if (path_gain > best_gain) {')==1
    body=body.replace('      if (path_gain > best_gain) {', '''      // Residual non-frontier gain must not displace an exploratory path.
      if (path_has_frontier && path_gain > best_gain) {''')
    source=source[:start]+'  '+marker+'\n'+body+'  // END_LOCAL_FRONTIER_ELIGIBILITY\n\n'+source[end:]
    needle='    best_vertex_ = local_graph_->getVertex(path[0]);'
    assert source.count(needle)==1
    telemetry='''    // Selection diagnostics use native graph states; no additional planning.
    std::vector<Vertex*> diagnostic_path;
    local_graph_->getShortestPath(best_path_id, local_graph_rep_, true, diagnostic_path);
    int diagnostic_frontiers = 0;
    for (auto* vertex : diagnostic_path)
      if (vertex->vol_gain.is_frontier && !vertex->is_hanging) ++diagnostic_frontiers;
    auto* diagnostic_leaf = local_graph_->getVertex(best_path_id);
    auto* diagnostic_root = local_graph_->getVertex(0);
    ROS_INFO("GBP_DIAGNOSTIC_SELECTED root_x=%.6f root_y=%.6f root_z=%.6f root_yaw=%.6f root_unknown=%d leaf_x=%.6f leaf_y=%.6f leaf_z=%.6f leaf_yaw=%.6f leaf_unknown=%d leaf_frontier=%d path_frontiers=%d any_frontier=%d gain=%.6f",
      diagnostic_root->state[0], diagnostic_root->state[1], diagnostic_root->state[2], diagnostic_root->state[3], diagnostic_root->vol_gain.num_unknown_voxels,
      diagnostic_leaf->state[0], diagnostic_leaf->state[1], diagnostic_leaf->state[2], diagnostic_leaf->state[3], diagnostic_leaf->vol_gain.num_unknown_voxels,
      diagnostic_leaf->vol_gain.is_frontier, diagnostic_frontiers, frontier_exists, best_gain);
'''
    return source.replace(needle,telemetry+needle)
