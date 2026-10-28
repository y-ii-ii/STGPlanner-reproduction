"""Record the native early end while preserving the full observation protocol."""
import datetime
from pathlib import Path
root = Path('D:/STGPlanner')
path = root/'codex/STATUS.md'
text = path.read_text(encoding='utf-8')
old = 'Scene4四算法工程基线测试已按用户最新要求阶段性关闭。STGPlanner、TARE及修复FAEL达到公共95%；GBP2修复09完整限时未达95%，保持暂停。当前无活动长测或自动续跑安排；本轮只更新报告、交接与私有备份、整理工作文件，未启动ROS、仿真或重新编译。后续只有用户明确授权新范围才恢复测试。'
assert old in text
text = text.replace(old, 'Scene4四算法基线阶段仍为已完成；用户于2026-10-28明确恢复GBP2后续优化。当前仅本会话持有WSL/ROS/Gazebo与共享代码写入权。GBP2单参数对照10正在按完整2400秒协议观察，原生约707.079秒已返航结束，覆盖40.4724005%，公共95%未达。TARE已完成后续验证并恢复原版，FAEL成功数据保留，均不重跑。历史各节中的“暂停/无运行”只描述其当时状态；以下最新GBP2章节及锁文件优先。', 1)
text += '''
## GBP2对照10原生提前结束检查点

10%前沿资格阈值在约707.079秒触发native_homing_ended；覆盖3152.80m²/40.4724005%，约793.997m。原生日志为局部连续四次无前沿、全局图无合格前沿后调用HOMING，任务时间预算尚余约2930秒。尚未到完整2400秒观察上限，不冒称最终验收或原生完成95%。仍按预设协议停车观察，不重启规划、不编译、不并行启动仿真；结束后保存原生地图、验收及清理进程。

已预设下一轮独立新图frontier_percentage_threshold=0.03，其他原生代码/两库/采样2000/三维收益/公共95%/2m/s/2400秒不变；只有10完整结束并确认实际进程/端口空闲后才部署。高阈值提前删去全局前沿与低阈值追逐残余三维收益存在权衡；当前观测不证明GBP2必然无法完成Scene4。
'''
now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat()
lines = text.splitlines()
lines[2] = '更新时间：'+now+'。本文件覆盖旧聊天及history中的过时运行描述。'
path.write_text('\n'.join(lines)+'\n', encoding='utf-8', newline='\n')
runbook = root/'codex/RUNBOOK.md'
with runbook.open('a', encoding='utf-8', newline='\n') as handle:
    handle.write('''
## 当前GBP2恢复优化（2026-10-28，覆盖上方旧暂停状态）

用户已明确恢复GBP2优化，TARE/FAEL不重跑。首先看STATUS最新GBP2章节和SIMULATION_LOCK.json；gbp2_default_frontier_20261028_10正在完整2400秒观察，原生约707.079秒返航且公共覆盖40.4724%，仍不等于探索成功。当前仿真及共享代码仅归原算法会话所有，其他会话不得启动/停止或重编译。

当前工具集中codex/work/gbp2_optimization_20261028；run_trial.sh启动固定协议，run_gbp2_trial.py冻结指纹并按所属结果目录清理，observe_and_save.py只读订阅及结束后保存原生地图。assert_idle.py核对实际/proc、端口与锁；prepare_frontier.py仅空闲后部署预设单阈值，保存before/after。下一预设值0.03，必须新运行名。analyze_running.py读取进度/原生选点日志；compare_plane_maps.py仅离线对比历史成功运行重叠，绝不可给规划器输入这些平面图。不要重跑旧prepare或历史恢复脚本。
''')
print('Current GBP2 native early-end checkpoint recorded; trial remains running.')
