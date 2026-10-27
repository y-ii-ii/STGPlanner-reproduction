from pathlib import Path
import argparse,datetime,json
root=Path('D:/STGPlanner/benchmarks')
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=root/'progress_report');a=p.parse_args()
out=a.output;out.mkdir(parents=True,exist_ok=True)
v=json.loads((root/'progress_report/progress_validation.json').read_text())
lines=['# Scene4 探索停滞修复与长测报告','',f"更新日期：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}（本机时间）",'',
'本报告延续《Scene4基线算法对比报告》，保留原始 1600 秒失败结果，新增 FAEL、GBP2 原生源码修复后的真实仿真测试。结果来自同一台电脑的公开 Scene4；每种修复版本仅完成一次正式运行。', '',
'## 1. 实测结论','',
'| 方法 | 修复前覆盖指标 | 修复后覆盖指标 | 修复后仿真时间(s) | 修复后墙钟时间(s) | 修复后里程(m) | 停止原因 |',
'|---|---:|---:|---:|---:|---:|---|']
for method in ['fael','gbp2']:
    b=v['results'][method]['before'];a=v['results'][method]['after']
    lines.append(f"| {method.upper()} | {b['coverage_fraction']*100:.3f}% | {a['coverage_fraction']*100:.3f}% | {a['sim_time_s']:.3f} | {a['wall_time_s']:.3f} | {a['distance_m']:.3f} | {'达到统一95%门槛' if a['finish_reason']=='coverage_threshold' else '2400秒限时，未完成'} |")
lines+=['','覆盖指标始终为独立公共观察器记录的已知平面面积 / 7790 m²，停止条件为面积 > 7400.5 m²。它包含已知空闲及占据栅格，是项目的名义面积比例，不能等同于真实可达区域 100% 覆盖。限时结果不能当作完成时间。','',
'![修复前后实际覆盖曲线](scene4_progress_curves.png)','',
'### 与原来1600秒预算的同期比较','',
'| 方法 | 旧版1600秒指标 | 修复版1600秒附近观测或提前完成结果 | 对应仿真时刻(s) |',
'|---|---:|---:|---:|']
for method in ['fael','gbp2']:
    b=v['results'][method]['before'];a=v['results'][method]['after'];c=a['checkpoint_1600']
    ratio=c['coverage_fraction'] if c else a['coverage_fraction'];t=c['sim_s'] if c else a['sim_time_s']
    lines.append(f"| {method.upper()} | {b['coverage_fraction']*100:.3f}% | {ratio*100:.3f}%{'（提前完成）' if a['completed_before_1600'] else ''} | {t:.3f} |")
lines+=['','1600 秒检查点取每秒记录中首次达到或超过 1600 秒的样本；提前完成时使用终点。新增 2400 秒上限是为了观察后期稳定性，不能把多给的时间直接算作修复收益。','',
'## 2. FAEL：问题链条与修复','',
'旧版在约415秒后不再扩展，最终1600秒指标41.278%，累计571.34m。原生节点仍存活，存在前沿和候选观察点，却持续输出空路线，因此不能解释为正常探索完成。','',
'1. `findPlaneLocalFrontier` 用 `history_frontier_cells_` 永久排除曾经出现过的前沿。与此同时，观察点靠近机器人时会直接从全局前沿集中删除其关联栅格，即使未知邻域仍然存在。二者组合会丢失尚未探索的边界。修复为根据当前占据图更新有效性，不再以“历史出现过”永久屏蔽，也不以“已靠近观察点”作为删除边界的依据。',
'2. 原检测只检查自身发生变化的栅格。某个自由栅格的概率饱和后，其邻域变化不会触发重新检查。修复为将变化栅格的四个 XY 邻格加入检测集合。',
'3. 近于1m的观察点会获得前沿归属，但路线选择又排除这些观察点，导致边界被无法选中的点占用。修复为在前沿分配阶段保持同一距离约束，允许其他可观测点接手。',
'4. 全局观察点筛选使用上一轮规划图；当前点连接函数混用了成员图和传入图。修复为先同步当前路网，按传入图查询编号。',
'5. 不可达点以巨大代价进入原生2-opt，可能产生空首段或断裂路线。修复为仅将与当前点连通的候选送入2-opt，并拒绝优化结果中的空连接段。保留原生候选生成、地图搜索和优化器，没有另写探索策略。','',
'新增 `FAEL_PROGRESS` 日志记录前沿数、候选数、路线目标数和路网顶点数，便于区分“节点存活”和“仍在有效探索”。','',
'## 3. GBP2：为什么会反复探索','',
'旧版1600秒仍移动了1945.54m，但覆盖指标只有41.179%。日志中局部收益持续存在，而全局图前沿计数始终为0：局部规划反复访问已有区域，缺少可靠的全局转移目标。单看非空路径数量会误判为正常进展。','',
'确认当前编译启用 `RAY_CAST_METHOD=1`。`voxblox_alt_impl.cpp` 的两个扫描函数将射线缓存分配成 `(height,width)`，随后却按 `(x,y)` 访问。原生公开接口实测此次采样为73×6、438个端点（角度浮点循环包含一条水平边界射线）。Release关闭Eigen断言后，这些射线的缓存位置发生严重别名重叠，破坏收益及前沿估计。另外，写入 `x+1` 时仅检查 `x<width`，最后一列缺少边界保护。','',
'修复为按 `(width,height)` 分配，并在所有相邻列写入前使用 `x+1<width`。保持原来的采样、收益权重、传感器范围和完成阈值。使用从原生源码提取的表达式和实测73×6维度进行C++/Eigen回归：旧分配复现335个冲突单元，修复后为0；旧末列条件触发断言，修复后正常退出；438个端点与宽×高一致。早期72×6示例的330个冲突并非最终实测维度，最终验收已按原生宽高重做。修复后的600秒功能试运行中，全局前沿计数恢复为非零；该试运行不是正式重复统计。','',
'### 缓存修复后仍存在的问题：收益射线高度与真实传感器不一致','',
'仅修缓存的中间运行 `repair_formal_gbp2_01` 在1121.225s仍只有41.756%（3252.8m²），却已经行驶1470.78m。为继续排障，主动关闭该运行的原生规划器，由公共测试器执行停车和数据落盘。结果中的 `process_exit:native_planner` 是本次有记录的人工诊断停止，不是自然完成或未说明的崩溃；`interruption.json`、原生候选点和当时源码指纹随数据保留。','',
'继续定位到地面规划图采用 `max_ground_height=0.7m` 投影，而物理激光/里程计参考高度为 `robot_height=0.456m`。捕获到的规划图点z范围约0.520—0.699m，受地面估计影响，并非恒为0.7m。原收益函数直接把规划图z当作传感器z，预测的观测高度与车辆到达后的实际观测不一致。','',
'保存原生TSDF地图后，在31个实际访问过的位置重放同一组射线：以0.7m计算，未知单元平均251.387；以0.456m计算，平均136.710，前者约为1.84倍。这些位置在两种高度下都未被判为前沿；该证据证明收益偏差存在，不能单凭它声称解释了全部循环。地图快照、访问坐标、原生重放程序及原始计数均保留，未把未观测的三维单元直接清零。','',
'新增修复把地面规划点换算到 `robot_height` 感知参考高度，再同时计算射线起点和端点；起点也正确应用随朝向旋转的传感器外参。两个实际启用的射线收益函数都接入该转换，空中机器人分支不作地面高度换算。独立回归从实际源码提取所用函数，验证高度换算、不修改输入、空中分支、旋转外参及两个原生调用点。地图、控制器、收益权重和95%阈值保持原样。最终GBP2结果使用全新运行 `repair_formal_gbp2_02`；中间失败尝试不混入正式重复统计。','',
'## 4. 后期稳定性、真实地图和验收','',
'![修复前后最终已知地图与实际轨迹](scene4_progress_maps.png)','',
'图中浅灰为已知自由栅格，深色为已知占据栅格，白色为未知；轨迹来自实际里程计。左右运行时长以子图标注为准。图像是记录数据的可复现绘图，不是伪造的RViz截图。','',
'| 方法 | 旧版最长近静止时段(s) | 修复版最长近静止时段(s) | 修复版非空/空规划数 | 拒绝断裂路线数 |',
'|---|---:|---:|---:|---:|']
for method in ['fael','gbp2']:
    b=v['results'][method]['before'];a=v['results'][method]['after']
    lines.append(f"| {method.upper()} | {b['longest_near_stationary_sim_s']:.3f} | {a['longest_near_stationary_sim_s']:.3f} | {a['nonempty_plans']} / {a['empty_plans']} | {a['rejected_disconnected_paths']} |")
lines+=['','近静止按相邻约1秒样本XY位移 < 0.03m累计；这是诊断指标，不能单独证明卡死。', '',
f"数据和接口验收：**{'通过' if v['protocol_checks_passed'] else '未全部通过'}**，共 {len(v['checks'])} 项；探索目标验收：**{'全部达到统一门槛' if v['exploration_goals_passed'] else '仍有未达到统一门槛的运行，不能宣称全部修复完成'}**。具体布尔结果见 `Scene4修复长测结果.json`。检查包含传感器活性、原生节点存活、停止动作确认、停车零指令与漂移、地图文件、轨迹单调性、源代码/二进制指纹，以及公共协议和当前实际配置的逐文件校验。", '',
'独立FAEL回归直接调用实际编译库中的前沿类，验证历史前沿可重新激活，以及仅邻格变化时自由栅格会被重新检查。独立测试使用11312端口与墙钟，避免结束仿真后暂停的 `/clock` 干扰测试。公共UFOMap实现保持不变，测试按已有聚合查询语义构造完整自由栅格组。','',
'## 5. 与论文Scene4的关系','',
'论文表格：FAEL探索时间1033.9±149.8s、路径1420.3±128.4m；GBP2为>1600s、>1560m。论文数字是原作者实验条件下的统计。本报告的修复版本含新增本地源码改动，采用公共机器人、控制器、12m内部感知范围及统一观察器。每方法仅1次正式运行，不能宣称复现了论文均值、标准差、方法排名或严格同条件速度。编译和独立诊断探针曾在FAEL早期运行阶段执行，计算耗时更不宜用于论文级性能比较。','',
'正式运行期间执行过独立回归、地图快照及诊断探针，可能造成短暂资源占用，因此这些结果主要用于功能与稳定性验证。FAEL原生辅助txt会在对象构造时重置，回归脚本现已增加“FAEL进程必须停止”的检查；本报告使用独立覆盖观察器、里程计、ROS运行时消息及节点日志作为正式证据，不采用该辅助txt作为统计来源。','',
'本次重点验证原先的停滞和反复访问问题能否消除，论文完整性能评测还需要作者完整场景配置和多次重复。Scene1—3仍未从公开仓库获得；没有自造场景冒充论文场景。','',
'## 6. 目录、版本及重建命令','',
'- 项目：`D:\\STGPlanner`；基线工具与运行证据：`D:\\STGPlanner\\benchmarks`。',
'- 原生编译副本：WSL中的 `/opt/stgplanner/benchmarks/fael_ws` 和 `gbp2_ws`，它们位于D盘WSL虚拟磁盘。',
'- 精确上游版本见 `benchmarks/sources.lock.json`：FAEL `a180b4129efe8fa3b27e877cb3417d1189b622ee`；GBP2 `gbplanner2` 分支 `7301b5350915cf3a4055072ad559842db37b4ca9`。',
'- 补丁、修复前后源码及SHA256见 `benchmarks/progress_repairs/manifest.json`；没有把WSL虚拟磁盘、密钥、下载缓存或编译目录提交到Git。','',
'已有本机环境恢复本分支工具后执行：','',
'```powershell',
'Set-Location D:\\STGPlanner\\catkin_ws\\src\\STGPlanner',
'git switch fix/fael-gbp2-progress',
'Copy-Item -Path .\\benchmarks\\* -Destination D:\\STGPlanner\\benchmarks -Recurse -Force',
'wsl.exe -d STGPlanner-Ubuntu20 -u root -- bash /mnt/d/STGPlanner/benchmarks/build_progress_repairs.sh fael',
'wsl.exe -d STGPlanner-Ubuntu20 -u root -- bash /mnt/d/STGPlanner/benchmarks/build_progress_repairs.sh gbp2',
'```','',
'新电脑先按主部署报告准备WSL、ROS和STGPlanner，按旧对比报告安装锁定版本的基线，再执行上述新增修复脚本。脚本拒绝覆盖不属于已记录修复的本地改动，避免误伤后续开发。单独重测时必须换新的目录名，并先结束上一个专用仿真实例：','',
'```powershell',
'wsl.exe --terminate STGPlanner-Ubuntu20',
'wsl.exe -d STGPlanner-Ubuntu20 -u root -- bash /mnt/d/STGPlanner/benchmarks/run_benchmark.sh fael --name repair_fael_repeat_02 --limit 2400',
'# 完成后终止专用发行版，再运行另一方法',
'wsl.exe --terminate STGPlanner-Ubuntu20',
'wsl.exe -d STGPlanner-Ubuntu20 -u root -- bash /mnt/d/STGPlanner/benchmarks/run_benchmark.sh gbp2 --name repair_gbp2_repeat_02 --limit 2400',
'```','',
'回归与数据验收（后两条需本报告对应的两组正式结果仍在本机）：','',
'```powershell',
'wsl.exe -d STGPlanner-Ubuntu20 -u root -- python3 /mnt/d/STGPlanner/benchmarks/ray_cache_regression.py',
'wsl.exe -d STGPlanner-Ubuntu20 -u root -- bash /mnt/d/STGPlanner/benchmarks/run_fael_frontier_regression.sh',
'wsl.exe -d STGPlanner-Ubuntu20 -u root -- python3 /mnt/d/STGPlanner/benchmarks/gain_frame_regression.py',
'wsl.exe -d STGPlanner-Ubuntu20 -u root -- python3 /mnt/d/STGPlanner/benchmarks/analyze_progress.py',
'wsl.exe -d STGPlanner-Ubuntu20 -u root -- python3 /mnt/d/STGPlanner/benchmarks/plot_progress.py',
'```','',
'收益高度诊断可在保留原始快照和坐标文件后，通过 `run_gbp_gain_probe.sh` 在独立11312端口重放。若从私有仓库恢复，先解压 `evidence/scene4-progress-fix/gbp_gain_snapshot.vxblx.gz` 到 `D:\\STGPlanner\\benchmarks\\gbp_gain_snapshot.vxblx`，并复制同目录的 `gbp_gain_positions.txt`；脚本会加载已锁定的GBP2配置。该程序只查询保存地图，不生成或执行探索路径。','',
'## 7. 私有仓库与回滚','',
'私有仓库：[y-ii-ii/STGPlanner-reproduction](https://github.com/y-ii-ii/STGPlanner-reproduction)，本次分支 `fix/fael-gbp2-progress`，固定标签 `scene4-progress-fix-2026-10-27`。实际提交与上传验证见 `Scene4修复GitHub上传验证.json`。原 `main`、`repro-baseline-2026-10-26`、`benchmark/scene4-baselines` 和 `scene4-baselines-2026-10-27` 保留。','',
'回滚时先保留未提交改动，再切换到目标标签，并恢复相应部署工具。仅切Git分支不会自动恢复 `/opt` 中已编译的原生副本。要回到旧基线，须将本次归档的 `.before` 按 `manifest.json` 的 method/relative 路径还原到各自 `/opt/..._ws/src`，再按旧构建命令编译。不要继续调用新增修复脚本，否则会重新应用修复。详细操作见 `rollback_progress_repairs.py --help`，默认只检查，指定 `--apply` 才恢复。','',
'回到修复前的多算法基线（不是最初STGPlanner单算法main）：','',
'```powershell',
'wsl.exe --terminate STGPlanner-Ubuntu20',
'wsl.exe -d STGPlanner-Ubuntu20 -u root -- python3 /mnt/d/STGPlanner/benchmarks/rollback_progress_repairs.py --apply',
'wsl.exe -d STGPlanner-Ubuntu20 -u root -- bash -lc "source /opt/stgplanner/catkin_ws/devel/setup.bash; cd /opt/stgplanner/benchmarks/fael_ws; catkin build planner --no-deps -j2 -p1"',
'wsl.exe -d STGPlanner-Ubuntu20 -u root -- bash -lc "source /opt/ros/noetic/setup.bash; cd /opt/stgplanner/benchmarks/gbp2_ws; catkin build gbplanner -j2 -p1"',
'git -C D:\\STGPlanner\\catkin_ws\\src\\STGPlanner switch --detach scene4-baselines-2026-10-27',
'```','',
'交付包含新增报告、曲线、原始结果、压缩原生日志、修复前后源代码、补丁和完整Git备份bundle；旧版报告及数据另行保留，可逐项追溯。','']
(out/'Scene4探索停滞修复报告.md').write_text('\n'.join(lines),encoding='utf-8',newline='\n')
(out/'Scene4修复长测结果.json').write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
print(out/'Scene4探索停滞修复报告.md')
