
#include <ros/ros.h>

#include "topo_planner/topo_planner.h"
#include "utils/fatal_trace.h"


int main(int argc, char** argv){
    // Diagnostic only: retain the original fatal signal and abort this trial.
    utils::installFatalTrace();
    ros::init(argc,argv,"topo_planner_node");
    ros::NodeHandle nh;
    ros::NodeHandle nh_private("~");

    ROS_INFO_STREAM("start planner");

    topo_planner::TopoPlanner planner(nh, nh_private);

    ros::spin();
    return 0;
}
