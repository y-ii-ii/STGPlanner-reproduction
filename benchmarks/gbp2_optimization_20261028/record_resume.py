"""Record explicit user authorization to resume GBP2 after completed TARE work."""
import datetime
import json
import re
import shutil
from pathlib import Path
root=Path('D:/STGPlanner');repo=root/'catkin_ws/src/STGPlanner'
out=root/'codex/outputs/gbp2_optimization_20261028';out.mkdir(exist_ok=True)
now=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat()
audit=json.loads((out/'preflight_audit/audit.json').read_text(encoding='utf-8'))
assert not audit['runtime_processes'] and all(audit['ports_free'].values()) and audit['rrg_matches_formal09']
lock_path=root/'codex/SIMULATION_LOCK.json';old=json.loads(lock_path.read_text(encoding='utf-8'));assert not old['runtime_active']
with (out/'previous_simulation_lock.json').open('x',encoding='utf-8') as handle:handle.write(json.dumps(old,ensure_ascii=False,indent=2)+'\n')
lock={'owner_thread':'01a17c85-9d73-7573-885c-a95dbbc4abbf','method':'gbp2','state':'preparing','runtime_active':False,
      'phase':'gbp2_optimization_preflight','updated_at':now,'gbp2_followup':'resumed_by_user',
      'tare_followup':'complete_original_deployment_restored','note':'User explicitly resumed GBP2 area improvement and mechanism testing. One runtime/code owner. No simulation started yet.'}
lock_path.write_text(json.dumps(lock,indent=2)+'\n',encoding='utf-8',newline='\n')
path=root/'codex/STATUS.md';text=path.read_text(encoding='utf-8');text=re.sub(r'## 当前状态：[^\n]+','## 当前状态：用户已恢复GBP2面积提升与机制验证；TARE后续完成并保持原版',text,count=1)
text+='''
## 2026-10-28 GBP2恢复优化（最新明确授权）

用户在TARE完成后明确要求继续GBP2优化，检验能否提升Scene4探索面积，以及停滞是否与方法本身有关。此次授权解除先前GBP2暂停，仅本会话控制WSL/ROS/Gazebo及共享代码，其他会话不得自动并行运行。

运行前已核对/proc与11311/11312/11345，均无活动仿真/占用。WSL实际GBP2 rrg.cpp与09冻结源码相同，原生库及源码已新快照到codex/outputs/gbp2_optimization_20261028/preflight_audit。Git起点8c55a9a，原始09、失败/用户中止数据、TARE回滚后的原配置及历史基线均保留。

先以冻结09地图/原生接口做收益与可观测性诊断，再固定独立候选、新名称完整试验；公共95%、观察器、物理传感器和2m/s控制上限不变，不输入公共真值目标，不靠延长上限或改停止口径宣称成功。若测试地面导航相关收益适配，将明确标为方法变体，不能算原生GBP2论文复现。有限失败试验不能证明GBP2在该类环境永远无法完成。

工作工具codex/work/gbp2_optimization_20261028，交付codex/outputs/gbp2_optimization_20261028。当前为离线预检，未启动新长测；每轮前读锁和实际进程，结束后按结果目录归属清理并验收停车/传感器。
'''
path.write_text(text,encoding='utf-8',newline='\n')
path=root/'codex/RUNBOOK.md';text=path.read_text(encoding='utf-8');lines=text.splitlines();lines=[('> 2026-10-28用户已明确恢复GBP2面积提升与机制验证；本会话独占运行/代码。TARE后续完成并保持原版。旧历史命令不是其他会话的自动执行授权。' if line.startswith('> Scene4四算法基线已阶段性完成。') else line) for line in lines];path.write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n')
for path in [root/'AGENTS.md',repo/'AGENTS.md']:
    text=path.read_text(encoding='utf-8');text=text.replace('Scene4四算法基线测试已阶段性完成，用户已暂停GBP2后续测试；除非用户明确恢复，不启动新GBP2测试或继续算法修改。FAEL成功结果保留，不自动重跑。','Scene4四算法基线阶段已完成；用户于2026-10-28明确恢复GBP2面积提升与机制验证，由当前会话独占。运行前核对最新STATUS、仿真锁和实际进程，不因新会话自动启动测试。TARE保持已验证原版，FAEL成功结果保留，不自动重跑。');path.write_text(text,encoding='utf-8',newline='\n')
print('GBP2 explicit resume authorization and native baseline preserved.')
