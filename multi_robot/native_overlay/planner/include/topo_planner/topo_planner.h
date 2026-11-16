
#ifndef ROBO_PLANNER_WS_TOPO_PLANNER_H
#define ROBO_PLANNER_WS_TOPO_PLANNER_H

#include <ros/ros.h>
#include <tf/tf.h>
#include <tf/transform_listener.h>
#include <geometry_msgs/Pose.h>
#include <nav_msgs/Odometry.h>
#include <actionlib/server/simple_action_server.h>
#include <control_planner_interface/ExplorerPlannerAction.h>
#include <control_planner_interface/PlannerMsgs.h>
#include <std_msgs/String.h>
#include <std_msgs/Float64MultiArray.h>
#include "rapid_cover_planner/execution_grid.h"
#include "rapid_cover_planner/topology_route_gate.h"

#include <message_filters/subscriber.h>
#include <message_filters/sync_policies/approximate_time.h>
#include <message_filters/sync_policies/exact_time.h>
#include <message_filters/time_synchronizer.h>

#include <pcl/point_types.h>
#include <pcl/point_cloud.h>
#include <pcl/filters/voxel_grid.h>
#include <pcl_conversions/pcl_conversions.h>
#include <pcl_ros/impl/transforms.hpp>
#include <pcl/common/common.h>

#include "preprocess/preprocess.h"
#include "rapid_cover_planner/rapid_cover_planner.h"
#include "heri_graph_cover_planner/heri_graph_cover_planner.h"

namespace topo_planner{

    class TopoPlanner{
    public:
        typedef actionlib::SimpleActionServer<control_planner_interface::ExplorerPlannerAction> ExplorerPlannerServer;

        ros::NodeHandle nh_;
        ros::NodeHandle nh_private_;

        ros::Subscriber explore_finish_sub_;

        ros::Publisher iteration_time_pub_;
        ros::Publisher native_catalog_pub_,native_status_pub_;
        double last_native_catalog_=-1e9;
        // Opt-in isolated topology mode; historical launches default to false.
        bool topology_enabled_=false;
        int topology_robot_=1;
        ros::Publisher topology_snapshot_pub_,topology_feedback_pub_;
        ros::Subscriber topology_command_sub_;
        std::mutex topology_mutex_;
        std::string topology_session_,topology_task_,topology_mode_="WAIT";
        unsigned long topology_command_seq_=0,topology_version_=0;
        double topology_command_stamp_=0,last_topology_snapshot_=-1e9;
        std::vector<rapid_cover_planner::TopologyPoint> topology_route_;
        void initializeTopology();
        void publishTopologySnapshot();
        void topologyCommand(const std_msgs::String::ConstPtr&);
        void topologyPlanning(control_planner_interface::ExplorerPlannerResult&);
        bool execution_repair_enabled_=true;
        ros::Publisher execution_grid_pub_;ros::Subscriber execution_feedback_sub_;
        double last_execution_grid_=-1e9,raw_execution_x_=0,raw_execution_y_=0;
        unsigned long execution_projections_=0,execution_rejections_=0;
        std::string execution_status_="UNCHANGED";
        void initializeExecutionRepair();
        void executionFeedback(const std_msgs::Float64MultiArray::ConstPtr&);
        rapid_cover_planner::ExecutionGrid executionGrid();
        void publishExecutionGrid();
        void repairExecutionPath(control_planner_interface::ExplorerPlannerResult&);
        void publishNativeCatalog();
        void publishNativeStatus(int iteration,const control_planner_interface::ExplorerPlannerResult&result);


        ExplorerPlannerServer planner_action_server_;
        int planner_goal_id_;

        ros::Timer preprocess_timer_;
        ros::Timer msgs_timer_;
        bool preprocess_inited_;

        ros::Publisher topo_planner_msgs_pub_;

        preprocess::Preprocess::Ptr elements_;

        std::string each_ufomap_update_txt_name_;
        double sum_ufomap_update_time_;
        int ufomap_update_num_ = 0;

        std::string each_topo_update_text_name_;
        double sum_topo_update_time_;
        int topo_update_num_ = 0;

        heri_graph_cover_planner::HeriGraphCoverPlanner::Ptr planner_;

        TopoPlanner(ros::NodeHandle &nh, ros::NodeHandle &nh_private);

        void plannerCallback(const control_planner_interface::ExplorerPlannerGoalConstPtr &goal);

        std::vector<geometry_msgs::Pose> wayPoseGeneration(rapid_cover_planner::Path &path);

        bool isExplorationFinish();

        bool isCurrentGoalScanned();

        void topo_planner_msgs_publish();

        void explorationFinishCallback(const std_msgs::BoolConstPtr &finish);

    };
}

#endif
