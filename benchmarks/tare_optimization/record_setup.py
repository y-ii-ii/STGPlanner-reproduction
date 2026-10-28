"""Handoff checkpoint after the unchanged control, before candidate simulation."""
import datetime
import json
import re
from pathlib import Path

root = Path('D:/STGPlanner')
now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat()
path = root / 'codex/STATUS.md'
text = path.read_text(encoding='utf-8')
text = re.sub(r'## 当前状态：[^\n]+', '## 当前状态：TARE原配置对照已完成，传感器模型对齐候选正在编译；GBP2暂停', text, count=1)
text += '''
## TARE新对照与候选源码检查点

原配置tare_audit_control_20261028_01已完成：996.477s、1490.842m、95.0901155%，六项健康/停车验收全通过；原生源码、二进制和公共适配冻结检查无变化，运行归属清理及11311/11345空闲检查通过。原生二进制SHA与evidence/scene4-baselines/runtime_linkage.txt完全一致。旧formal_tare_01保留，不能把未改算法的新对照改善归到优化候选名下。

原生实际LiDARModel的16束物理角度用例baseline_v2只识别14束，±15°两端点均不可见。最初仅开方向惯性的计划未运行；运行中该触发计数为0，改为独立测试实际VLP16感知模型对齐，方案见experiment_plan.sensor_model_v2.json。

对照结束后已保存原始TARE二进制和两份原生源码before/after/patch，应用全视场24→30°、角栅格包含两端点、视点评估半视场12→15°及其派生阈值的变更，正在WSL原生tare_ws编译。候选仅为已确认感知适配差异的实验，不证明性能提高；惯性仍关闭，范围12m、公共95%、2m/s和1600s均不改。当前没有活动仿真，但本会话仍独占该原生工作空间；未经协调不得另起仿真或构建。

下一步：原生构建成功→同一16束实际模型用例须全部通过→tare_sensor_model_20261028_01新图正式试验；拟采用时须独立02复测。任何候选失败也保留。编译辅助测试曾遇pkg-config缺失和缺少原生misc_utils静态链接，已改用真实CMake编译/链接设置；这些是辅助用例构建调整，不是算法运行失败。
'''
path.write_text(text, encoding='utf-8', newline='\n')
path = root / 'codex/SIMULATION_LOCK.json'
lock = json.loads(path.read_text(encoding='utf-8'))
lock.update(state='preparing', phase='tare_sensor_model_building', native_build_active=True, runtime_active=False, updated_at=now)
path.write_text(json.dumps(lock, indent=2) + '\n', encoding='utf-8', newline='\n')
print('TARE source/build handoff recorded')
