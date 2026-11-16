
#include "control_planner_interface/pci_vehicle.h"
#include "control_planner_interface/execution_lease.h"

namespace interface {

    PCIVehicle::PCIVehicle(const ros::NodeHandle &nh, const ros::NodeHandle &nh_private) : PCIManager(nh, nh_private),
                                                                                           vehicle_execute_client_(nh_,
                                                                                                                   "vehicle_execute",
                                                                                                                   true),
                                                                                           vehicle_stop_client_(nh_,
                                                                                                                "vehicle_stop",
                                                                                                                true),
                                                                                           n_seq_(0) {

        ROS_INFO("pci vehicle construct");

    }

    bool PCIVehicle::loadParams(const std::string ns) {
        nh_private_.param("team/topology_enabled",topology_mode_,false);
        nh_private_.param("team/robot_id",topology_robot_,1);
        return true;
    }

    bool PCIVehicle::initialize() {
        pci_status_ = PCIStatus::kReady;

        return true;
    }

    void PCIVehicle::setCurrentPose(const geometry_msgs::Pose &pose) {
        current_pose_.position.x = pose.position.x;
        current_pose_.position.y = pose.position.y;
        current_pose_.position.z = pose.position.z;
        current_pose_.orientation.x = pose.orientation.x;
        current_pose_.orientation.y = pose.orientation.y;
        current_pose_.orientation.z = pose.orientation.z;
        current_pose_.orientation.w = pose.orientation.w;
    }

    void PCIVehicle::setFrameId(const std::string &frame_id) {
        frame_id_ = frame_id;
    }

    bool PCIVehicle::executePath(const std::vector<control_planner_interface::Path> &path_segments,
                                 std::vector<geometry_msgs::Pose> &modified_path) {

        n_seq_++;
        control_planner_interface::VehicleExecuteGoal path_goal;
        path_goal.header.seq = n_seq_;
        path_goal.header.stamp = ros::Time::now();
        path_goal.header.frame_id = frame_id_;
        path_goal.paths = path_segments;
        if(topology_mode_){
            try{readExecutionLease(execution_lease_);}catch(const std::exception&){return false;}
            if(stop_fault_||!vehicle_execute_client_.isServerConnected())return false;
            path_goal.execution_lease=execution_lease_;
        }
        vehicle_execute_client_.sendGoal(path_goal);
        ros::spinOnce();

        return true;
    }

    bool PCIVehicle::goToWaypoint(const geometry_msgs::Pose &pose) {
        control_planner_interface::Path path;
        path.path.push_back(current_pose_);
        path.path.push_back(pose);
        std::vector<control_planner_interface::Path> path_segments;
        path_segments.push_back(path);
        std::vector<geometry_msgs::Pose> modified_path;
        executePath(path_segments,modified_path);

        return true;
    }

    bool PCIVehicle::isGoalReached() {
        if (vehicle_execute_client_.getState() == actionlib::SimpleClientGoalState::SUCCEEDED)
            return true;
        else {
            return false;
        }
    }

    void PCIVehicle::cancelCurrentGoal() {
        vehicle_execute_client_.cancelGoal();
    }

    void PCIVehicle::stopMove() {
        control_planner_interface::VehicleExecuteGoal goal;
        goal.paths.clear();
        if(topology_mode_){
            vehicle_execute_client_.cancelGoal();
            ExecutionLease lease;lease.robot=topology_robot_;
            try{if(!execution_lease_.empty())lease=readExecutionLease(execution_lease_);}catch(const std::exception&){}
            std::string request="pci/"+std::to_string(ros::WallTime::now().toNSec())+"/"+std::to_string(++n_seq_);
            boost::property_tree::ptree p;p.put("request_id",request);
            std::ostringstream out;boost::property_tree::write_json(out,p,false);goal.execution_lease=out.str();
            vehicle_stop_client_.sendGoal(goal);
            double began=executionMonotonicNow();
            while(ros::ok()&&!vehicle_stop_client_.getState().isDone()&&executionMonotonicNow()-began<7.5)
                ros::WallDuration(.02).sleep();
            auto result=vehicle_stop_client_.getResult();
            stop_fault_=!(vehicle_stop_client_.getState()==actionlib::SimpleClientGoalState::SUCCEEDED&&result&&result->finish
                &&stoppedProofMatches(result->stop_proof,request,int(lease.robot),lease.session));
            if(stop_fault_){vehicle_stop_client_.cancelGoal();pci_status_=PCIStatus::kError;}
            else pci_status_=PCIStatus::kReady;
            return;
        }
        vehicle_stop_client_.sendGoal(goal);
    }
}
