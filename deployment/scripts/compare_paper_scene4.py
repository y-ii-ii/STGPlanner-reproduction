from pathlib import Path
import json,os
base=Path('D:/STGPlanner') if os.name=='nt' else Path('/mnt/d/STGPlanner')
folder=base/'logs/planner_completion'
data=json.loads((folder/'long_runtime.json').read_text())
start=next(e['sim_time'] for e in data['events'] if e['kind']=='ros_log' and 'init motion has finished' in e.get('text',''))
end=next(e['sim_time'] for e in data['events'] if e['kind']=='ros_log' and 'exploration process has finished' in e.get('text',''))
sim_seconds=end-start
wall_seconds=data['metrics'][-1]['project_elapsed']
distance=data['metrics'][-1]['reported_distance']
iterations=[float(line.split()[1]) for line in (folder/'long_run_statistics/iteration_time.txt').read_text().splitlines()[1:] if line.strip()]
average=sum(iterations)/len(iterations)
paper={'exploration_seconds':779.8,'exploration_std_seconds':17.2,'distance_m':1194.,'distance_std_m':12.9,'runtime_seconds':.015,'speed_mps':1.53,'trials':5}
result={'paper':paper,'local':{'wall_exploration_seconds':wall_seconds,'ros_sim_exploration_seconds':sim_seconds,'ros_sim_start':start,'ros_sim_end':end,'real_time_factor_during_exploration':sim_seconds/wall_seconds,'reported_distance_m':distance,'odometry_window_distance_m':data['distance_m'],'mean_internal_iteration_seconds':average,'iteration_records':len(iterations),'mean_speed_from_wall_mps':distance/wall_seconds,'mean_speed_from_sim_mps':distance/sim_seconds,'final_trial_only':True},'reference_deltas':{'wall_time_percent':100*(wall_seconds/paper['exploration_seconds']-1),'sim_time_percent':100*(sim_seconds/paper['exploration_seconds']-1),'distance_percent':100*(distance/paper['distance_m']-1),'internal_runtime_ratio':average/paper['runtime_seconds']},'strict_paper_replication':False,'paper_url':'https://arxiv.org/html/2412.13664v1#S4.T1'}
(base/'logs/paper_comparison.json').write_text(json.dumps(result,indent=2))
section='''
### 复现范围与论文表 I 对照

完整克隆并构建了公开仓库的 28 个包，实际运行了 Scene4 的感知、建图、拓扑规划、局部控制和可视化链路，并修复了部署及运行故障。此结论属于“公开代码的 Scene4 功能复现”，并非论文全部实验的独立重复验证。完整源码保留在 `D:\\STGPlanner\\catkin_ws\\src\\STGPlanner`；材料包包含脚本与补丁，没有把完整仓库和 WSL 磁盘重复打包。

论文图 5 / 表 I 包含 Scene1～4；当前公开仓库只提供 Scene4 的 world 与配套参数。本次未运行其他三个论文场景、GBP2/TARE/FAEL 基线，也未按论文要求在相同配置下重复 5 次计算均值和标准差；两轮长测承担排错和验收用途，不能当作同配置的五轮统计。也未逐项证明公开源码与论文所有算法细节完全一致。

论文数字来自 [论文表 I 和实验设置](https://arxiv.org/html/2412.13664v1#S4)，取 Scene4 的 Ours；本机取最终严格长测的单轮记录：

| 指标 | 论文 Scene4 / Ours | 本机最终单轮 | 解释 |
|---|---:|---:|---|
'''
section+='| 探索耗时 | 779.8 ± 17.2 s | 墙钟 {:.2f} s；ROS 仿真 {:.2f} s | 墙钟数值高 {:.2f}%；仿真时长数值相差 {:.2f}%。论文未明确所用统计时钟，不能直接认定严格一致。 |\n'.format(wall_seconds,sim_seconds,result['reference_deltas']['wall_time_percent'],result['reference_deltas']['sim_time_percent'])
section+='| 路径长度 | 1194.0 ± 12.9 m | {:.2f} m | 项目累计距离高 {:.2f}%；数值较接近，但一轮结果不能验证论文均值和标准差。 |\n'.format(distance,result['reference_deltas']['distance_percent'])
section+='| Run time / 规划计算时间 | 0.015 s | 内部迭代均值 {:.5f} s | 约 {:.2f} 倍；采用项目 iteration_time 计时，尚未逐项统一论文计时边界与硬件。 |\n'.format(average,result['reference_deltas']['internal_runtime_ratio'])
section+='| 平均速度 | 1.53 m/s | 按 ROS 仿真时间 {:.3f} m/s；按墙钟 {:.3f} m/s | 由同一累计距离分别除以两种时长推导，不能混用。 |\n'.format(distance/sim_seconds,distance/wall_seconds)
section+='| 统计口径 | 每场景、每方法重复 5 次 | 最终单轮；其余运行用于排错 | 未进行论文级统计复现。 |\n\n'
section+='ROS 时钟由本轮 Explorer 的“init motion has finished”与“exploration process has finished”两条实际事件读取：`{:.3f}` 至 `{:.3f}`；墙钟时间采用项目统计节点 `timeConsumed`，不使用含停车观察的 1200 秒测试总时长。路径采用与该时间窗口对应的项目累计距离；报告中的 {:.2f} 米里程计采集值还包含监测启动后的初始化运动和静止波动，不能替换此处口径。\n\n'.format(start,end,data['distance_m'])
section+='本机运行于 Windows / WSL2，Gazebo 和 RViz 使用 CPU 软件渲染；论文使用 Ubuntu 20.04、i9-10900K，最大运动速度设置为 2 m/s。本机配置的 maxSpeed 同样为 2 m/s，但探索期间 ROS 仿真时间与墙钟时间比约为 {:.3f}，所以渲染/仿真变慢会拉长墙钟耗时。硬件、负载、仿真调度、结束门槛和计时边界尚未全部统一，不能把数值差异单独归因于算法，也不能据此验证论文对其他方法的领先比例。\n\n'.format(sim_seconds/wall_seconds)
section+='结论：Scene4 的功能链路已跑通，路径长度和按仿真时间推导的速度较接近论文；本机墙钟耗时和内部规划计算时间较高。当前证据支持工程部署与功能复现，不支持“论文全部性能结果已复现”。原始对照数据见 `logs/paper_comparison.json`。\n\n'
(base/'logs/paper_comparison_section.md').write_text(section,encoding='utf-8')
print(json.dumps(result,indent=2))
