// Geometry-only check on preserved own grids, no ROS or native planner replay.
#include "rapid_cover_planner/body_route.h"
#include <boost/property_tree/ptree.hpp>
#include <boost/property_tree/json_parser.hpp>
#include <fstream>
#include <cassert>
int main(int argc,char**argv){
 boost::property_tree::ptree root;boost::property_tree::read_json(argv[1],root);auto g=root.get_child("grid");
 rapid_cover_planner::ExecutionGrid grid;grid.width=g.get<int>("width");grid.height=g.get<int>("height");grid.resolution=g.get<double>("resolution");
 auto it=g.get_child("origin").begin();grid.x0=(it++)->second.get_value<double>();grid.y0=it->second.get_value<double>();
 for(auto& r:g.get_child("data"))grid.data.push_back(r.second.get_value<int>());
 std::vector<double> p;for(auto&v:root.get_child("body.pose"))p.push_back(v.second.get_value<double>());
 std::vector<rapid_cover_planner::TopologyPoint> reference;
 for(auto&v:root.get_child("reference")){auto t=v.second.begin();double x=(t++)->second.get_value<double>();reference.push_back({x,t->second.get_value<double>()});}
 auto result=rapid_cover_planner::bodyRoute(grid,reference,p[0],p[1],p[2]);
 std::ofstream out(argv[2]);out<<std::setprecision(16)<<"{\"status\":\""<<result.status<<"\",\"method\":\""<<result.method<<"\",\"arc\":"<<result.arc<<",\"expanded\":"<<result.expanded<<",\"poses\":[";
 bool first=true;for(auto v:result.poses){assert(grid.footprint(v.x,v.y,v.yaw,result.margin)==0);if(!first)out<<",";first=false;out<<"["<<v.x<<","<<v.y<<","<<v.yaw<<"]";}out<<"]}";
}
