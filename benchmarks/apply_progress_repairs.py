"""Repair native planner defects, without adding another exploration planner."""
from pathlib import Path
import argparse,difflib
p=argparse.ArgumentParser();p.add_argument('method',choices=['fael','gbp2','all']);a=p.parse_args()
root=Path('/opt/stgplanner/benchmarks');archive=Path('/mnt/d/STGPlanner/benchmarks/progress_repairs');archive.mkdir(exist_ok=True)
def edit(method,relative,transform):
    path=root/(method+'_ws/src')/relative
    backup=archive/(method+'__'+relative.replace('/','__')+'.before')
    if not backup.exists():backup.write_bytes(path.read_bytes())
    original=backup.read_text();updated=transform(original)
    assert updated!=original,relative
    applied=backup.with_suffix('.after')
    permitted={original,updated}
    if applied.exists():permitted.add(applied.read_text())
    if path.read_text() not in permitted:
        raise RuntimeError('Native source has unrelated edits; refusing to overwrite: '+str(path))
    if path.read_text()!=updated:path.write_text(updated)
    applied.write_text(updated)
    patch=''.join(difflib.unified_diff(original.splitlines(True),updated.splitlines(True),fromfile='a/'+relative,tofile='b/'+relative))
    (archive/(method+'__'+relative.replace('/','__')+'.patch')).write_text(patch)
    print(method,relative,flush=True)
def frontier(s):
    s=s.replace('frontier_depth_ == changedCellCode.getDepth() && history_frontier_cells_.count(changedCellCode)==0','frontier_depth_ == changedCellCode.getDepth()')
    s=s.replace('                            history_frontier_cells_.insert(changedCellCode);','                            // Frontier validity is reversible; never permanently blacklist it.')
    needle='''        map_.resetChangeDetection();

        findPlaneLocalFrontier();'''
    assert needle in s
    s=s.replace(needle,'''        map_.resetChangeDetection();
        // A cell can become frontier when an adjacent cell changes. Its own
        // probability need not change after saturation, so inspect neighbours.
        CodeUnorderSet affected = changed_cell_codes_;
        for (const auto& code : changed_cell_codes_) {
            if (code.getDepth() != frontier_depth_) continue;
            auto neighbours = get_XY_NeighborCell(code, frontier_depth_);
            affected.insert(neighbours.begin(), neighbours.end());
        }
        changed_cell_codes_.swap(affected);

        findPlaneLocalFrontier();''')
    return s
def viewpoints(s):
    start=s.index('            if (term.first.distanceXY(current_position_) < sample_dist_ / 2) {')
    end=s.index('            if (term.second.size()<viewpoint_gain_thre_)',start)
    s=s[:start]+'''            // Reaching a viewpoint is not proof that its unknown neighbours
            // were observed. Only the occupancy map can retire a frontier.
'''+s[end:]
    needle='''                for (const auto &point: representative_points_) {
                    sensor_point.x() = point.x();'''
    assert needle in s
    s=s.replace(needle,'''                for (const auto &point: representative_points_) {
                    // The tour selector excludes viewpoints within 1m. Do not
                    // let such a point monopolise frontier assignments: attach
                    // to another observable viewpoint without deleting cells.
                    if (point.distanceXY(current_position_) <= 1.0) continue;
                    sensor_point.x() = point.x();''')
    return s
def rapid(s):
    s=s.replace('''        getSuitableTourPoints(current_position);''','''        // Selection of global viewpoints must use this iteration's roadmap.
        planGraphConstruct(road_graph_->graph_, plan_graph_);
        plan_graph_.updateKdtree();
        getSuitableTourPoints(current_position);''',1)
    s=s.replace('if (plan_graph_.getPointId(item, item_id) && current_point_id != item_id)','if (graph.getPointId(item, item_id) && current_point_id != item_id)')
    needle='''            std::vector<int> ids;
            for (int i = 0; i < tour_points_num; ++i) {
                ids.push_back(i);
            }'''.replace('ids;\n','ids; \n')
    assert needle in s
    s=s.replace(needle,'''            std::vector<int> ids;
            ids.push_back(0);
            for (int i = 1; i < tour_points_num; ++i) {
                // Infinite-cost, unreachable targets are not a valid tour.
                if (path_matrix[0][i].size() >= 2) ids.push_back(i);
            }
            if (ids.size() < 2) {
                ROS_WARN("PROGRESS_DIAGNOSTIC no connected tour candidate");
                return false;
            }''')
    needle='''                for (int i = 0; i < max_unity_way.size() - 1; i++) {
                    tsp_path.insert'''
    assert needle in s
    s=s.replace(needle,'''                for (int i = 0; i < max_unity_way.size() - 1; i++) {
                    if (path_matrix[max_unity_way[i]][max_unity_way[i+1]].size() < 2) {
                        path_segments_.clear();
                        ROS_WARN("PROGRESS_DIAGNOSTIC disconnected optimized tour");
                        return false;
                    }
                    tsp_path.insert''')
    return s
def diagnostic(s):
    needle='''        planner_->Initialize(elements_->current_position_);
        preprocess_inited_ = true;'''
    assert needle in s
    return s.replace(needle,'''        planner_->Initialize(elements_->current_position_);
        ROS_INFO_THROTTLE(5, "FAEL_PROGRESS frontiers=%zu candidates=%zu tours=%zu roadmap=%zu",
            elements_->frontier_map_->global_frontier_cells_.size(),
            elements_->viewpoint_manager_->candidate_viewpoints_.size(),
            planner_->tour_points_.size(), elements_->road_map_->graph_.getAllVertices().size());
        preprocess_inited_ = true;''')
def rays(s):
    assert s.count('      height, width);')==2
    s=s.replace('      height, width);','      width, height);')
    # The cache is indexed (x,y). The final horizontal sample has no x+1.
    s=s.replace('x < width)', 'x + 1 < width)').replace('x < width && y > 0)', 'x + 1 < width && y > 0)')
    return s

def sensing_frame(s):
    helpers='''
// BEGIN_GAIN_SENSOR_FRAME
static StateVec gainSensingState(const StateVec& projected, bool ground,
                                double robot_height, double projection_height) {
  StateVec sensing = projected;
  if (ground) sensing[2] += robot_height - projection_height;
  return sensing;
}
static Eigen::Vector3d gainSensorOrigin(const StateVec& sensing,
                                      const Eigen::Vector3d& body_offset) {
  Eigen::Matrix3d yaw = Eigen::AngleAxisd(sensing[3], Eigen::Vector3d::UnitZ()).toRotationMatrix();
  return sensing.head(3) + yaw * body_offset;
}
// END_GAIN_SENSOR_FRAME

'''
    needle='Rrg::Rrg(const ros::NodeHandle& nh, const ros::NodeHandle& nh_private)'
    assert needle in s
    s=s.replace(needle,helpers+needle,1)
    for name in ['computeVolumetricGainRayModel','computeVolumetricGainRayModelNoBound']:
        start=s.index('void Rrg::'+name+'(');end=s.index('\n}\n',start)+3
        body=s[start:end]
        needle='    Eigen::Vector3d origin(state[0], state[1], state[2]);'
        assert body.count(needle)==1
        body=body.replace(needle,'''    // Ground roadmap points are projected to max_ground_height. Predict
    // observations at the physical odometry/sensor reference height instead.
    StateVec sensor_state = gainSensingState(state,
        robot_params_.type == RobotType::kGroundRobot,
        planning_params_.robot_height, planning_params_.max_ground_height);
    Eigen::Vector3d origin = gainSensorOrigin(sensor_state,
        sensor_params_.sensor[sensor_name].center_offset);''')
        assert 'getFrustumEndpoints(state,' in body
        body=body.replace('getFrustumEndpoints(state,','getFrustumEndpoints(sensor_state,')
        body=body.replace('visualizeRays(state,','visualizeRays(sensor_state,')
        s=s[:start]+body+s[end:]
    start=s.index('double Rrg::projectSample(');end=s.index('\n}\n',start)+3
    body=s[start:end]
    assert 'return ground_dist + tsdf_dist;' in body and 'return ray_len;' in body
    body=body.replace('return ground_dist + tsdf_dist;',
        'return (start.z() - point.z()) + tsdf_dist - delta.z();')
    body=body.replace('return ray_len;', 'return ray_len - delta.z();')
    s=s[:start]+body+s[end:]
    import re
    s,n=re.subn(r'time_to_target \+ planning_params_\.auto_homing_enable\s*\? time_to_home\s*: 0',
        'time_to_target + (planning_params_.auto_homing_enable ? time_to_home : 0.0)',s)
    assert n==2,('global time budget expressions',n)
    return s

def lidar_geometry(s):
    marker='else if (type == SensorType::kLidar) {'
    cursor=0;changed=0
    while True:
        start=s.find(marker,cursor)
        if start<0:break
        end=s.index('\n  }',start)+4
        body=s[start:end]
        needle='double x = max_range * cos(dh);'
        if needle in body:
            body=body.replace(needle,'double x = max_range * cos(dv) * cos(dh);')
            body=body.replace('double y = max_range * sin(dh);','double y = max_range * cos(dv) * sin(dh);')
            s=s[:start]+body+s[end:];changed+=1;end=start+len(body)
        cursor=end
    assert changed==2,('lidar endpoint generators',changed)
    return s

def homing_accessor(s):
    needle='class Rrg {\n public:\n'
    assert needle in s
    return s.replace(needle,needle+'''  // End condition is distinct from a normal global repositioning path.
  bool isHomingEngaged() const { return homing_engaged_; }

''',1)

def homing_service(s):
    helper='''
// BEGIN_NATIVE_GLOBAL_STATUS
static int nativeGlobalResponseStatus(bool homing) {
  return homing ? planner_msgs::planner_srv::Response::kHoming
                : planner_msgs::planner_srv::Response::kRepositioning;
}
// END_NATIVE_GLOBAL_STATUS

'''
    assert 'namespace explorer {\n' in s
    s=s.replace('namespace explorer {\n','namespace explorer {\n'+helper,1)
    needle='''  rrg_->reset();
  Rrg::GraphStatus status = rrg_->buildGraph();'''
    assert needle in s
    s=s.replace(needle,'''  if (rrg_->isHomingEngaged()) {
    res.path = rrg_->getHomingPath(req.header.frame_id);
    res.status = nativeGlobalResponseStatus(true);
    return true;
  }
  rrg_->reset();
  Rrg::GraphStatus status = rrg_->buildGraph();''',1)
    needle='res.status = planner_msgs::planner_srv::Response::kRepositioning;'
    assert s.count(needle)==1
    return s.replace(needle,'res.status = nativeGlobalResponseStatus(rrg_->isHomingEngaged());')
if a.method in ['fael','all']:
    edit('fael','planner/src/perception/ufomap.cpp',frontier)
    edit('fael','planner/src/preprocess/viewpoint_manager.cpp',viewpoints)
    edit('fael','planner/src/rapid_cover_planner/rapid_cover_planner.cpp',rapid)
    edit('fael','planner/src/topo_planner/topo_planner.cpp',diagnostic)
if a.method in ['gbp2','all']:
    edit('gbp2','planner_common/src/voxblox/voxblox_alt_impl.cpp',rays)
    edit('gbp2','gbplanner/src/rrg.cpp',sensing_frame)
    edit('gbp2','planner_common/src/params.cpp',lidar_geometry)
    edit('gbp2','gbplanner/include/gbplanner/rrg.h',homing_accessor)
    edit('gbp2','gbplanner/src/gbplanner.cpp',homing_service)
