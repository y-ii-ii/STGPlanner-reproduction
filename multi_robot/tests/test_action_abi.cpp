#include <control_planner_interface/ExplorerPlannerAction.h>
#include <control_planner_interface/VehicleExecuteAction.h>
#include "control_planner_interface/execution_lease.h"
#include <ros/serialization.h>
#include <cassert>
#include <iostream>
#include <vector>
template<class T>T roundtrip(const T& value){
 auto size=ros::serialization::serializationLength(value);std::vector<uint8_t> data(size);
 ros::serialization::OStream out(data.data(),size);ros::serialization::serialize(out,value);
 T decoded;ros::serialization::IStream in(data.data(),size);ros::serialization::deserialize(in,decoded);return decoded;
}
int main(){
 control_planner_interface::ExplorerPlannerResult result;
 result.execution_lease=R"({"schema":2,"allocation_session":"s","robot":1,"task":"t","version":2,"dispatch_id":3,"command_seq":4,"stamp":1})";
 auto planned=roundtrip(result);assert(planned.execution_lease==result.execution_lease);
 control_planner_interface::VehicleExecuteGoal goal;goal.execution_lease=planned.execution_lease;
 auto executed=roundtrip(goal);auto lease=interface::readExecutionLease(executed.execution_lease);
 assert(lease.token()=="s/1/2/3");
 control_planner_interface::VehicleExecuteResult stopped;stopped.finish=true;
 stopped.stop_proof=R"({"source":"velocity_gate","status":"STOPPED","robot":1,"allocation_session":"s","stop_id":"n","request_ids":["r"],"fresh_samples":5,"stationary_s":0.6,"zero_s":0.8})";
 auto ack=roundtrip(stopped);
 assert(ack.finish&&interface::stoppedProofMatches(ack.stop_proof,"r",1,"s"));
 assert(!interface::stoppedProofMatches(ack.stop_proof,"old",1,"s"));
 std::cout<<"4 real ROS-action serialization checks passed without ros::init or a master\n";
}
