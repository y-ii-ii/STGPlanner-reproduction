
#include "control_planner_interface/control_planner_interface.h"


namespace interface {

    ControlPlannerInterface::ControlPlannerInterface(ros::NodeHandle &nh, ros::NodeHandle &nh_private,
                                                     std::shared_ptr<PCIManager> &pci_manager)
            : nh_(nh), nh_private_(nh_private), pci_manager_(pci_manager),
              planner_client_(nh_, "topo_planner", true) {

        odometry_sub_ = nh_.subscribe("odometry",1, &ControlPlannerInterface::odometryCallback, this);

        if (!loadParams()) {
            ROS_ERROR("control planner interface can not load params. Shut down ROS node.");
            ros::shutdown();
        }
        ROS_INFO("control planner interface construct");
    }

    bool ControlPlannerInterface::loadParams() {

        const std::string &ns = ros::this_node::getName();

        frame_id_ = "world";
        if (!ros::param::get(ns + "/frame_id", frame_id_)) {
            ROS_WARN("No frame_id specified. Looking for %s. Default is 'world'.",
                     (ns + "/frame_id").c_str());
        }

        pci_manager_->setFrameId(frame_id_);

        if (!pci_manager_->loadParams(ns)) return false;

        return true;
    }

    void ControlPlannerInterface::odometryCallback(const nav_msgs::OdometryConstPtr &odom) {
        current_pose_ = odom->pose.pose;
        pci_manager_->setCurrentPose(current_pose_);

        pose_is_ready_ = true;
    }

    bool ControlPlannerInterface::init() {
        pose_is_ready_ = false;

        ros::Rate rr(1);
        while (!pose_is_ready_) {
            ROS_WARN("Waiting for odometry.");
            ros::spinOnce();
            rr.sleep();
        }

        if (!pci_manager_->initialize()) return false;

        return true;
    }

    void ControlPlannerInterface::goToWayPose(geometry_msgs::Pose &pose) {
        pci_manager_->goToWaypoint(pose);
    }

    bool ControlPlannerInterface::isGoalReached() {
        return pci_manager_->isGoalReached();
    }

    void ControlPlannerInterface::cancelCurrentGoal() {
        pci_manager_->cancelCurrentGoal();
    }

    void ControlPlannerInterface::executePath(const  std::vector<control_planner_interface::Path> &path_segments) {
        std::vector<geometry_msgs::Pose> modified_path;
        pci_manager_->executePath(path_segments,modified_path);
    }

    bool ControlPlannerInterface::callForPlanner(const int &iteration_id,
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

    void ControlPlannerInterface::stopMove() {
        pci_manager_->stopMove();
    }
}