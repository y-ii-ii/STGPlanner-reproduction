from pathlib import Path
import shutil

root=Path('/mnt/d/STGPlanner/catkin_ws/src/STGPlanner')
backup=Path('/mnt/d/STGPlanner/logs/planner_completion/source_before')
backup.mkdir(parents=True,exist_ok=True)
def update(rel,old,new):
    path=root/rel
    text=path.read_text()
    if new in text:return
    if old not in text:raise RuntimeError('Unexpected source: '+rel)
    dest=backup/rel
    dest.parent.mkdir(parents=True,exist_ok=True)
    if not dest.exists():shutil.copy2(path,dest)
    path.write_text(text.replace(old,new))

header='stgp_planner/control_planner_interface/include/control_planner_interface/control_planner_interface.h'
update(header,'#include <thread>','#include <thread>\n#include <functional>')
update(header,'bool callForPlanner(const int &iteration_id, std::vector<control_planner_interface::Path> &path_segments);',
       'bool callForPlanner(const int &iteration_id, std::vector<control_planner_interface::Path> &path_segments,\n                            const std::function<bool()> &stop_requested = {});')
source='stgp_planner/control_planner_interface/src/control_planner_interface.cpp'
path=root/source
text=path.read_text()
begin=text.index('    bool ControlPlannerInterface::callForPlanner(')
end=text.index('    void ControlPlannerInterface::stopMove()',begin)
new='''    bool ControlPlannerInterface::callForPlanner(const int &iteration_id,
            std::vector<control_planner_interface::Path> &path_segments,
            const std::function<bool()> &stop_requested) {
        control_planner_interface::ExplorerPlannerGoal goal;
        goal.iteration_id = iteration_id;
        path_segments.clear();
        ROS_INFO("call for the path to explore..");
        planner_client_.sendGoal(goal);
        const ros::WallTime started = ros::WallTime::now();
        // Pump completion callbacks while waiting. A normal coverage stop can
        // close the planner before its active action sends a result.
        while (ros::ok()) {
            ros::spinOnce();
            if (stop_requested && stop_requested()) {
                planner_client_.cancelGoal();
                ROS_INFO("Planner request %d interrupted by exploration completion signal after %.3f wall seconds.",
                         iteration_id, (ros::WallTime::now() - started).toSec());
                return false;
            }
            const auto state = planner_client_.getState();
            if (state.isDone()) {
                const auto result = planner_client_.getResult();
                if (state == actionlib::SimpleClientGoalState::SUCCEEDED && result) {
                    path_segments = result->paths;
                    ROS_INFO("the path get.");
                    return true;
                }
                ROS_WARN("Planner request %d ended with state %s: %s", iteration_id,
                         state.toString().c_str(), state.getText().c_str());
                return false;
            }
            if ((ros::WallTime::now() - started).toSec() >= 60.0) {
                planner_client_.cancelGoal();
                ROS_ERROR("Planner request %d timed out after 60 wall seconds (state %s).",
                          iteration_id, state.toString().c_str());
                return false;
            }
            ros::WallDuration(0.02).sleep();
        }
        planner_client_.cancelGoal();
        return false;
    }

'''
update(source,text[begin:end],new)
explorer='stgp_planner/exploration_manager/src/explorer.cpp'
update(explorer,'interface_(interface), iteration_num_(0) {',
       'interface_(interface), iteration_num_(0), exploration_finished_(false) {')
update(explorer,'ROS_WARN("the iteration is out time or aborted");',
       'if (!exploration_finished_ && ros::ok())\n                        ROS_WARN("Planner request did not succeed; retrying the next iteration.");')
update(explorer,'return interface_->callForPlanner(iteration_num, path_segments);',
       'return interface_->callForPlanner(iteration_num, path_segments, [this]() { return exploration_finished_; });')
update(explorer,'exploration_finished_ = msg->is_exploration_finished;',
       'exploration_finished_ = exploration_finished_ || msg->is_exploration_finished;')

stats='stgp_planner/visualization_tools/src/exploration_data.cpp'
update(stats,'ROS_INFO("max volume threshold is reach...");',
       'ros::param::set(ros::this_node::getName() + "/finish_reason", "coverage_threshold");\n            ROS_INFO("EXPLORATION_STOP reason=coverage_threshold metric=%.6f map_area=%.6f threshold=%.6f ratio=%.6f",\n                     known_space_volume, max_volume, 0.95 * max_volume, known_space_volume / max_volume);')
update(stats,'ROS_INFO("max time is reach...");',
       'ros::param::set(ros::this_node::getName() + "/finish_reason", "time_limit");\n            ROS_WARN("EXPLORATION_STOP reason=time_limit elapsed=%.6f limit=%.6f", time_second - system_init_time, max_time);')
execution='stgp_planner/robot_move/path_execution/src/path_execution.cpp'
update(execution,'advertise<std_msgs::Bool>("stop_move", 1);',
       'advertise<std_msgs::Bool>("stop_move", 1, true);')
path=root/execution
text=path.read_text()
begin=text.index('    void PathExecution::stopMoveCallback(')
end=text.index('    bool PathExecution::isStopped()',begin)
new='''    void PathExecution::stopMoveCallback(const control_planner_interface::VehicleExecuteGoalConstPtr &stop_goal) {
        ROS_INFO("start stop ...");
        const ros::WallTime started = ros::WallTime::now();
        while (ros::ok() && (ros::WallTime::now() - started).toSec() < 7.0) {
            std_msgs::Bool stop;
            stop.data = true;
            stop_move_pub_.publish(stop);
            if ((ros::WallTime::now() - started).toSec() >= 2.0 && isStopped()) {
                ROS_INFO("stop move finished; follower stop remains latched.");
                stop_move_server_.setSucceeded();
                return;
            }
            ros::WallDuration(0.1).sleep();
        }
        ROS_ERROR("Robot did not settle within the stop deadline.");
        stop_move_server_.setAborted();
    }

'''
update(execution,text[begin:end],new)
update(execution,'        if (!global_path_to_follow_.empty()) {',
       '        std_msgs::Bool resume;\n        resume.data = false;\n        stop_move_pub_.publish(resume);\n        if (!global_path_to_follow_.empty()) {')
update(execution,'        if ((dist / odom_delta_t) < stop_vel_thres_',
       '        if (odom_delta_t <= 0.0) return false;\n        if ((dist / odom_delta_t) < stop_vel_thres_')
follower='stgp_planner/robot_move/cmu_planner/local_planner/src/pathFollower.cpp'
update(follower,'int safetyStop = 0;',
       'int safetyStop = 0;\nbool pathExecutionStop = false;\nvoid pathExecutionStopHandler(const std_msgs::Bool::ConstPtr &stop) {\n    pathExecutionStop = stop->data;\n}')
update(follower,'    ros::Subscriber subStop = nh.subscribe<std_msgs::Int8>("/stop", 5, stopHandler);',
       '    ros::Subscriber subStop = nh.subscribe<std_msgs::Int8>("/stop", 5, stopHandler);\n    ros::Subscriber subExecutionStop = nh.subscribe<std_msgs::Bool>("/path_execution_node/stop_move", 1, pathExecutionStopHandler);')
update(follower,'            if (safetyStop >= 2) vehicleYawRate = 0;',
       '            if (safetyStop >= 2) vehicleYawRate = 0;\n            if (pathExecutionStop) {\n                vehicleSpeed = 0;\n                vehicleYawRate = 0;\n            }')
print('Completion responsiveness, action diagnostics and follower stop repaired; coverage threshold remains 0.95.')
