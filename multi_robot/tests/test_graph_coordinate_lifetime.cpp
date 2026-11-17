// Actual STG vecS storage, without ROS/Gazebo. -DUNSAFE reproduces the old
// borrowed-coordinate pattern under ASan; default copies before graph growth.
#include "utils/node.h"
using namespace utils;
#include "perception/hierarchical_graph.h"
#include <cassert>
perception::LabeledMap graph;
#ifdef UNSAFE
void grow(const cv::Point& coordinate){
#else
void grow(cv::Point coordinate){
#endif
 for(int i=1;i<1024;++i)boost::add_vertex(i,graph);
 volatile int x=coordinate.x;assert(x==13);
}
int main(){boost::add_vertex(0,graph);graph[0].cvPt=cv::Point(13,1);grow(graph[0].cvPt);assert(graph[0].cvPt==cv::Point(13,1));std::cout<<"STG vecS coordinate survives growth by value\n";}
