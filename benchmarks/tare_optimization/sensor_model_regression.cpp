// Exercise the actual native LiDARModel with the physical VLP16 ray endpoints.
#include <lidar_model/lidar_model.h>
#include <cmath>
#include <iostream>

int main() {
  int visible = 0;
  lidar_model_ns::LiDARModel::setCloudDWZResol(0.3);
  for (int angle = -15; angle <= 15; angle += 2) {
    lidar_model_ns::LiDARModel model;
    pcl::PointXYZI point;
    const double elevation = angle * M_PI / 180.0;
    point.x = 12.0 * std::cos(elevation);
    point.y = 0.0;
    point.z = 12.0 * std::sin(elevation);
    model.UpdateCoverage(point);
    const bool observed = model.CheckVisibility(point, 0.3);
    visible += observed;
    std::cout << angle << " " << observed << "\n";
  }
  std::cout << "visible_physical_rays " << visible << "\n";
  return visible == 16 ? 0 : 2;
}
