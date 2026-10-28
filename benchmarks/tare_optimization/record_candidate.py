"""Record successful native fixture/build and the fresh candidate trial."""
import json
import re
from pathlib import Path
root = Path('D:/STGPlanner')
out = root / 'codex/outputs/tare_optimization_20261028'
fixture = out / 'sensor_model_regression'
assert (fixture / 'baseline_v2.exitcode').read_text().strip() == '2'
assert (fixture / 'candidate.exitcode').read_text().strip() == '0'
assert 'visible_physical_rays 14' in (fixture / 'baseline_v2.log').read_text()
assert 'visible_physical_rays 16' in (fixture / 'candidate.log').read_text()
path = root / 'codex/STATUS.md'
text = path.read_text(encoding='utf-8')
text = re.sub(r'## 当前状态：[^\n]+', '## 当前状态：TARE传感器模型对齐正式候选01正在验证；GBP2继续暂停', text, count=1)
text += '''
## TARE感知模型候选01已通过启动前验收

原生TARE工作空间编译成功（1包，88.8s，无警告/失败）；实际LiDARModel相同16束物理射线用例由旧版14/16改为16/16，±15°端点均识别。其余规划逻辑、配置、公共执行链未修改，仍关闭方向惯性。新图正式试验tare_sensor_model_20261028_01，上限1600s，95%公共规则不变，独立订阅记录与冻结/停车验收同对照。候选尚无性能结论，不能把感知用例通过当成探索成功或优化有效。
'''
path.write_text(text, encoding='utf-8', newline='\n')
print('Candidate preflight evidence and ongoing handoff recorded')
