"""Checkpoint complete10 and the preregistered intermediate-threshold11."""
import datetime
import json
import re
from pathlib import Path
root=Path('D:/STGPlanner');out=root/'codex/outputs/gbp2_optimization_20261028'
validation=json.loads((out/'gbp2_default_frontier_20261028_10_validation.json').read_text(encoding='utf-8'))
assert validation['protocol_checks_passed'] and not validation['summary']['public95_reached']
plan={'trial':'gbp2_frontier03_20261028_11','fixed_before_outcome':True,
      'single_change_from09':{'SensorParams/VLP16/frontier_percentage_threshold':[.01,.03]},
      'limit_s':2400,'native_sources_binaries':'same09','public_threshold_m2':7400.5,'speed_limit_m_s':2,
      'samples':2000,'gain_objective':'native3D','independent_fresh_scene':True,
      'reason':'Prespecified intermediate after10 native early end40.4724%. No public-plane feedback or uniform-ray change.',
      'diagnostic_addition':'After common stop only, serialize the final native graph as well as map; saved gain flag is not internal active vertex type.'}
target=out/'trial11_plan.json';assert not target.exists()
target.write_text(json.dumps(plan,indent=2)+'\n',encoding='utf-8',newline='\n')
path=root/'codex/STATUS.md';text=path.read_text(encoding='utf-8')
text=re.sub(r'## 当前状态：[^\n]+','## 当前状态：GBP2对照10完整失败并已验收；准备独立3%阈值对照11',text,count=1)
now=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat()
text=re.sub(r'更新时间：[^。]+。','更新时间：'+now+'。',text,count=1)
text+='''
## GBP2对照10完整结果与独立对照11

gbp2_default_frontier_20261028_10完整观察2400.040秒，3152.80m²/40.4724005%，794.006m；原生707.079秒返航结束，此后1692.961秒未重启规划、未增加面积。公共结束分类sim_time_limit，原生结束与95%分开记录。46项协议/数据/版本/传感器/停车/原生地图SHA检查通过，公共95%失败。原生地图31,463,517字节、SHA256 382fd470d356cc02f5db6b9208dfeffcd5c9d21c1a882f06fb60fc1d8b0d3698；所属进程清理和端口复核通过。

结束后两次原生地图只读网格诊断：09/10中分别有180/122个局部包围盒自由的4米网格原点；1%阈值分别保留21/31个前沿、3%保留1/7个、10%均为0。该诊断不证明这些原点存在连通可达路径，不读公共平面图。均匀与非均匀射线结果接近，不据此调整正式射线模型。09未知样本81.85%、10未知样本68.14%投影到原生已知低层列，属于原生三维残余收益分布诊断。

TF核对：归一化world下sensor_z约0.456003、点云帧z约0.455703，差0.3mm；Gazebo原始world传感器z约0.5192属于不同原点，不能据此宣称TF错误。地面投影再换回感知高度仍有待验证的量化/参考高度偏差，尚无因果或性能结论。历史成功平面图均在GBP2全局XY边界内，不支持简单扩大边界作为修复。

按预定方案部署gbp2_frontier03_20261028_11：唯一原生参数相对09改为frontier_percentage_threshold=0.03，原生09代码/两库、三维收益、采样2000、12m、2m/s、95%和2400秒保持不变，独立新场景。新增只在公共停止后保存原生全局图，不改规划与运动。运行时以SIMULATION_LOCK.json为准，期间不得重编译或启动第二套ROS/Gazebo。TARE/FAEL不重跑。
'''
path.write_text(text,encoding='utf-8',newline='\n');print('10 checkpoint and fixed11 plan saved.')
