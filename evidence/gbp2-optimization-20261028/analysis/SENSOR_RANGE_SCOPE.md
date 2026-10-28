# LiDAR量程口径核对

2026-10-28从运行10冻结的`live_rosparams.yaml`中提取真实`robot_description`：Gazebo gpu_ray范围0.3–131m，ROS Velodyne插件保留0.9–130m，16条垂直扫描线、±15°、水平1800采样、10Hz。原生GBP2收益`SensorParams/VLP16/max_range=12m`，Voxblox积分`max_ray_length_m=12m`，公共UFOMap`max_range=12m`。

因此，本轮方案中的12m是有效规划/建图/公共评分上限，不能称作物理仿真LiDAR最大量程12m。仿真传感器配置、本地公共观察器和原生建图上限均未在本轮改变。论文给出VLP16视场和统一控制平台，但不能据此冒称已核实作者逐算法每一项有效量程与停止配置。

证据：`sensor_model_audit.json`、`preflight_audit/config/voxblox.yaml`、各运行`preflight/config/gbp2.yaml`与`coverage.yaml`。这项口径澄清不修改任何原始运行数据或物理模型，不构成额外传感器优化试验。
