import datetime
import json
from pathlib import Path
root=Path('D:/STGPlanner');now=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat()
text=f'''# STGPlanner 最新交接状态

更新时间：{now}。本文件覆盖旧聊天及history中的过时运行描述。

## 当前状态：本轮恢复验证和收益审计已结束，GBP2仍未完成95%

用户已在“STGPlanner 报告与论文对照”明确解除暂停并授权继续测试。本轮算法/长测会话01a17c85-9d73-7573-885c-a95dbbc4abbf独占WSL、代码和状态写入；报告会话01a17c85-a03f-7170-8f21-68dd9119e2d2只读审计。当前没有活动长测或已安排的自动续跑。

| 运行 | 仿真秒 | 面积比例 | 里程(m) | 分类 |
|---|---:|---:|---:|---|
| repair_formal_fael_01 | 1017.008 | 95.3366% | 1351.931 | 已达到公共95%，本轮未重跑 |
| repair_formal_gbp2_06 | 1082.027 | 54.153530% | 1179.247 | 用户中止，未完成95% |
| repair_formal_gbp2_07 | 2400.018 | 54.964827% | 2389.938 | 完整限时失败 |
| diagnostic_gbp2_gain_08 | 1400.018 | 41.415148% | 1535.363 | pilot/diagnostic限时，非正式重复 |
| repair_formal_gbp2_09 | 2400.007 | 56.338896% | 2413.450 | 完整限时失败 |

09面积4388.80m²，墙钟2412.783秒，1600.551秒时已是56.338896%，最后100秒新增0m²。原生未自然结束；finish_reason=sim_time_limit。375条原生本地选路日志均包含有效前沿，但后期反复在右侧中部运动，最长近静止仅3.017秒。**资格修复已生效，探索问题尚未解决。**
09停车确认、零指令、漂移与传感器检查通过；44,141,149字节的poststop_native_map.vxblx已保存，SHA256 cb24b46f3bd8e3158572335df7a0283439423e4c0755db13a3eb2cfa082a1224。08三份原生地图也保留。08/09监督器结束时按结果目录归属清理进程并复核11311/11345，记录无残留。09离线11312探针退出码0，脚本带所属roscore清理trap；最后一次额外WSL ps复核被用户拒绝，因此未执行，不冒称额外复核已通过。07曾有所属ROS/Gazebo残留，已在08之前核实归属后重启专用发行版清除；07无原生地图收尾快照，poststop_map_capture.json记有服务已关闭错误。

## 本轮结论、修改和验证

- 四种方法无条件共用movement.launch→path_execution/localPlanner/pathFollower。运行实参maxSpeed=2.0；autonomySpeed=3.0经代码截断后不代表3m/s。09的11项运行版本核对通过：仅rrg源码相对07改变，已加载GB库匹配冻结09，3个公共控制二进制、原生时间模型2/1m/s、采样2000及前沿阈值0.01未变。原0.2是原生时间模型，与实际低层速度上限分开；05完整失败也表明校准不能单独解决41%停滞。
- 08只加日志，实际228条本地选择中72条路径无有效前沿，58条在其他路径有前沿时仍获选。09修复为仅让可行且含有效非悬空前沿的路径竞争最佳局部路径；不可行路径不保留frontier_exists标志。沿用已有全局回退，不加新visited规则、真值目标或公共覆盖反馈。实际评分块5个受控用例及转换幂等性共6项检查通过，18包编译成功。
- 09结果211项协议/数据检查全部通过，exploration_goals_passed=false。06分类为user_interrupted，7项真实存档/元数据检查通过；不将06作为完整观测，也不将健康通过或单次跨平台当作95%或论文五次统计复现。
- 09附加速度/动作记录器最初因Python消息包路径缺失而未启动；主测试器覆盖、里程和健康数据持续存在。补充动作首条在相对688.131秒，之前无补充速度/动作采样；原错误日志及passive_audit_attachment.json保留。passive_speed_audit的audit_start_absolute_sim=0是初始无效时钟，不能用作全程采样起点。附加后采样最大线速度指令2.0m/s；物理里程计小量超调与指令上限分开。
- 最终原生地图48次只读重放：按投影感知高度24组中2组仍是前沿，按平地实测感知高度0.456m查询24组中13组是前沿；未知样本XY投影均100%落在公共已知平面，加权未知样本分别84.49%/87.70%位于2m以上。这是查询级三维残余收益分布，不是新面积指标，也不是历史收益重建或唯一因果证明；公共平面图只用于离线诊断，未输入规划器。
- 旧03冻结地图138组5°/2°垂直采样对照未支持“改成2°即可消除残余收益”，未据此改正式设置。论文v4 IV-A统一修改版[25] FALCO和2m/s；Table I中GBP2四场景均用>号报告时间、标准差为横杠，Scene4为>1600s/>1560m，正文提到后期远点往返。不能假称论文所有GBP2试验完整完成，也不能仅凭表断言崩溃。作者各基线适配细节未核实。

## 目录、版本及本地交付

- 项目根D:/STGPlanner；实际Git根D:/STGPlanner/catkin_ws/src/STGPlanner。私有远端y-ii-ii/STGPlanner-reproduction，分支fix/fael-gbp2-progress；本轮父提交59eba6c，新本地代码/证据检查点以git log为准。本轮未推送、未新建最终标签。
- 保留main/repro-baseline-2026-10-26=dfc712982891f29c266083d7efad72ad48e730a2；benchmark/scene4-baselines及scene4-baselines-2026-10-27=9dec3c45184259a0d68e3dfe066040966d807aed。
- 专用WSL STGPlanner-Ubuntu20；实际编译源码/opt/stgplanner/benchmarks/*_ws/src，主环境/opt/stgplanner/catkin_ws。当前原生库/源码及benchmarks/progress_repairs对应09，不能当作07版本。preflight_repair_formal_gbp2_09/baseline07_progress_repairs保留07源码/补丁，trial07_validation.json保留07验收。
- 新工具在codex/work，主要为path_frontier_repair.py、test_path_frontier_selection.py、run_outcome.py、prepare_formal_09.py、run_formal_trial.py及原生收益探针。部署工具D:/STGPlanner/benchmarks。修改D盘上游克隆不会自动改变/opt编译副本。
- 原始结果benchmarks/results/各独立运行目录；06的user_pause.json/interruption.json不改，旧基线和中间失败均保留。progress_trials.json在09结果前固定选择；08单列diagnostic_runs，不混作重复。
- 本地报告codex/outputs/Scene4探索停滞修复报告.md/.html，曲线scene4_progress_curves.png、地图scene4_progress_maps.png，验证Scene4修复长测结果.json；旧部署/基线报告入口已更新。图片已人工查看。07阶段报告、验证和图另存codex/outputs/trial07_review。
- 只读证据：codex/outputs/运动执行与速度审计_2026-10-27.md、preflight_repair_formal_gbp2_07、diagnostic_gbp2_gain_08_setup、path_frontier_selection_regression、gbp_sampling_probe_07、gbp_stagnation_probe_09。正式证据归档到Git的evidence/scene4-progress-fix，源码/报告由本会话统一写入。
- 原始大对话工作区C:/Users/Administrator/Documents/Codex/2026-10-26/add-windowscapability-online-name-openssh-server-9仍保留；其outputs已复制到codex/outputs，不依赖整段聊天接续。

## 下一阶段

先基于09保存地图审计感知自由空间更新、原生预测收益与实际可获得观测的一致性，再决定是否有新的实现修复依据。当前证据不足以宣称唯一根因或通过调整高度范围/阈值解决问题；任何收益范围或策略变化必须另列新实验，不覆盖07/08/09。
后续试验使用新运行名（可从10开始，须先检查冲突）、新manifest/config；不能从已结束进程的时间点续算。运行前读SIMULATION_LOCK并核对真实进程，取得单一控制权，禁止并行重编译/占用11311/11345。FAEL无需因迁移或本轮GBP2失败重跑。
最终修复标签scene4-progress-fix-2026-10-27、远程发布/克隆验收及最终ZIP/bundle尚未执行；不得称已经发布或全部修复完成。本轮只做本地检查点，不扩大原有发布授权。
'''
(root/'codex/STATUS.md').write_text(text,encoding='utf-8',newline='\n')
for path in (root/'AGENTS.md',root/'catkin_ws/src/STGPlanner/AGENTS.md'):
    lines=path.read_text(encoding='utf-8').splitlines()
    lines=[('- 项目暂停或恢复以用户最新明确授权及状态文件为准。用户已于2026-10-27明确恢复，本轮完整验证结束，当前无活动长测。不因打开新会话自动启动测试；运行前核对仿真锁和实际进程。' if line.startswith('- 当前项目由用户主动暂停。') else line) for line in lines]
    path.write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n')
runbook=root/'codex/RUNBOOK.md';content=runbook.read_text(encoding='utf-8')
content=content.replace('--name repair_formal_gbp2_07','--name repair_formal_gbp2_10')
content=content.replace('禁止覆盖06。','禁止覆盖任何已有运行（尤其06/07/08/09）；示例10也须先检查名称是否已占用。')
runbook.write_text(content,encoding='utf-8',newline='\n')
lock={'state':'idle','owner_thread':'01a17c85-9d73-7573-885c-a95dbbc4abbf','trial':'repair_formal_gbp2_09',
    'updated_at':now,'runtime_active':False,'phase':'complete_observation_unmet_95','finish_reason':'sim_time_limit',
    'result_path':'D:/STGPlanner/benchmarks/results/repair_formal_gbp2_09','common_threshold_reached':False,
    'extra_final_process_check':'not_run_user_denied',
    'note':'Formal09 cleanup verified owned processes and11311/11345 free; offline replay exited0 with cleanup trap. Extra final WSL ps check denied by user and not retried. No new long run scheduled; check actual processes before next ownership claim.'}
(root/'codex/SIMULATION_LOCK.json').write_text(json.dumps(lock,indent=2)+'\n',encoding='utf-8',newline='\n')
print('Updated concise final handoff, resume guidance and idle simulation lock.')
