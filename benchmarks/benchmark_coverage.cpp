#include <ros/ros.h>
#include <std_msgs/Float64.h>
#include <std_msgs/Bool.h>
#include <perception/ufomap.h>
#include <fstream>
#include <mutex>

class CoverageObserver : public perception::Ufomap {
public:
  CoverageObserver(ros::NodeHandle& nh,ros::NodeHandle& priv,const std::string& output)
      : Ufomap(nh,priv),output_(output) {
    // Keep the upstream mapping and plane-count definition, without serializing
    // the complete 3D map on every publication or sharing diagnostic filenames.
    pub_timer_.stop();write_ufomap_timer_.stop();
    txt_known_name=output_+"/coverage_mapping.tsv";
    txt_frontier_name=output_+"/coverage_frontier.tsv";
    txt_insert_cloud_name=output_+"/coverage_insert.tsv";
    map_txt_name=output_+"/coverage.ufo";
    publisher_=nh.advertise<std_msgs::Float64>("/benchmark/known_area",1,true);
    finish_=nh.subscribe("/benchmark/finish",1,&CoverageObserver::finish,this);
    timer_=priv.createTimer(ros::Duration(1.0),&CoverageObserver::tick,this);
  }
private:
  void updateCount() {
    for(auto it=map_.changesBegin();it!=map_.changesEnd();++it)known_cell_codes_.insert(*it);
    map_.resetChangeDetection();
    knownCellOutput();
  }
  void tick(const ros::TimerEvent&) {
    std::lock_guard<std::mutex> guard(map_mutex_);
    updateCount();
    std_msgs::Float64 message;
    message.data=known_plane_cell_num_*map_.getResolution()*map_.getResolution();
    publisher_.publish(message);
  }
  void finish(const std_msgs::Bool::ConstPtr& message) {
    if(!message->data||saved_)return;
    saved_=true;timer_.stop();
    std::lock_guard<std::mutex> guard(map_mutex_);
    updateCount();
    std::ofstream cells(output_+"/known_plane_cells.csv");
    cells<<"x,y,occupied\n";
    for(const auto& code:known_cell_codes_) {
      auto point=map_.toCoord(code.toKey());
      if(code.getDepth()==0&&point.z()>0&&point.z()<map_.getResolution())
        cells<<point.x()<<","<<point.y()<<","<<map_.isOccupied(code)<<"\n";
    }
    map_.write(output_+"/coverage.ufo");
  }
  std::string output_;
  ros::Publisher publisher_;
  ros::Subscriber finish_;
  ros::Timer timer_;
  bool saved_=false;
};
int main(int argc,char** argv) {
  ros::init(argc,argv,"benchmark_coverage");
  ros::NodeHandle nh,priv("~");
  std::string output;priv.param<std::string>("output_directory",output,"/tmp");
  CoverageObserver observer(nh,priv,output);
  ros::spin();
}
