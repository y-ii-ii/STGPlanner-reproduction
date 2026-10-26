#include <control_planner_interface/control_planner_interface.h>
#include <actionlib/server/simple_action_server.h>
#include <ros/callback_queue.h>
#include <atomic>
#include <fstream>

class NoMotionPCI : public interface::PCIManager {
public:
  using PCIManager::PCIManager;
  bool loadParams(const std::string) override { return true; }
  bool initialize() override { return true; }
  bool goToWaypoint(const geometry_msgs::Pose&) override { return true; }
  bool executePath(const std::vector<control_planner_interface::Path>&, std::vector<geometry_msgs::Pose>&) override { return true; }
  bool isGoalReached() override { return true; }
  void cancelCurrentGoal() override {}
  void stopMove() override {}
  void setCurrentPose(const geometry_msgs::Pose&) override {}
  void setFrameId(const std::string&) override {}
};

int main(int argc,char** argv) {
  ros::init(argc,argv,"stgplanner_completion_regression");
  ros::NodeHandle nh("/completion_regression"),priv("~"),server_nh(nh);
  ros::CallbackQueue server_queue;
  server_nh.setCallbackQueue(&server_queue);
  using Server=actionlib::SimpleActionServer<control_planner_interface::ExplorerPlannerAction>;
  std::atomic<int> mode{0};
  std::unique_ptr<Server> server;
  server.reset(new Server(server_nh,"topo_planner",[&](const control_planner_interface::ExplorerPlannerGoalConstPtr&) {
    control_planner_interface::ExplorerPlannerResult result;
    if (mode==0) {
      control_planner_interface::Path path;path.path.emplace_back();result.paths.push_back(path);
      server->setSucceeded(result);
    } else if (mode==1) server->setAborted(result,"isolated rejection injection");
    else {
      while(ros::ok()&&!server->isPreemptRequested())ros::WallDuration(.01).sleep();
      if(ros::ok())server->setPreempted(result,"isolated cancellation acknowledged");
    }
  },false));
  server->start();
  ros::AsyncSpinner server_spinner(1,&server_queue);server_spinner.start();
  std::shared_ptr<interface::PCIManager> pci=std::make_shared<NoMotionPCI>(nh,priv);
  interface::ControlPlannerInterface client(nh,priv,pci);
  if(!client.planner_client_.waitForServer(ros::Duration(10)))return 2;
  std::vector<control_planner_interface::Path> path;
  const bool success=client.callForPlanner(1,path)&&!path.empty();
  mode=1;
  const auto aborted_start=ros::WallTime::now();
  const bool aborted=!client.callForPlanner(2,path)&&client.planner_client_.getState()==actionlib::SimpleClientGoalState::ABORTED;
  const double aborted_seconds=(ros::WallTime::now()-aborted_start).toSec();
  mode=2;
  bool completion=false;
  auto timer=nh.createWallTimer(ros::WallDuration(.25),[&](const ros::WallTimerEvent&){completion=true;},true);
  const auto completion_start=ros::WallTime::now();
  const bool cancelled=!client.callForPlanner(3,path,[&](){return completion;});
  const double completion_seconds=(ros::WallTime::now()-completion_start).toSec();
  ros::WallDuration(.2).sleep();
  const auto timeout_start=ros::WallTime::now();
  const bool timeout=!client.callForPlanner(4,path);
  const double timeout_seconds=(ros::WallTime::now()-timeout_start).toSec();
  const bool passed=success&&aborted&&aborted_seconds<2&&cancelled&&completion_seconds<1&&timeout&&timeout_seconds>=60&&timeout_seconds<62;
  std::ofstream f("/mnt/d/STGPlanner/logs/planner_completion/isolated_regression.json");
  f<<std::boolalpha<<"{\n\"passed\":"<<passed<<",\n\"succeeded_path\":"<<success<<",\n\"aborted_state_preserved\":"<<aborted<<",\n\"aborted_seconds\":"<<aborted_seconds<<",\n\"completion_cancelled\":"<<cancelled<<",\n\"completion_seconds\":"<<completion_seconds<<",\n\"real_timeout\":"<<timeout<<",\n\"timeout_seconds\":"<<timeout_seconds<<"\n}\n";
  ros::shutdown();server_spinner.stop();return passed?0:1;
}
