"""Checkpoint the first candidate and the unchanged independent repeat."""
import json
import re
from pathlib import Path
root = Path('D:/STGPlanner')
folder = root / 'benchmarks/results/tare_sensor_model_20261028_01'
result = json.loads((folder / 'result.json').read_text(encoding='utf-8'))
assert all(result['validation'].values())
assert json.loads((folder / 'freeze_validation.json').read_text(encoding='utf-8'))['all_frozen_files_unchanged']
assert all(json.loads((folder / 'runtime_cleanup.json').read_text(encoding='utf-8'))['ports_free'].values())
path = root / 'codex/STATUS.md'
text = path.read_text(encoding='utf-8')
text = re.sub(r'## 当前状态：[^\n]+', '## 当前状态：TARE感知模型候选01成功，冻结同版本02独立确认中；GBP2暂停', text, count=1)
text += '''
## TARE候选01完整结果与02确认

tare_sensor_model_20261028_01：976.461s、1474.461m、95.0757381%，六项验收全通过、冻结文件无变化，运行归属清理及11311/11345空闲通过。相对新原配置对照996.477s/1490.842m，仅减少时间2.01%、里程1.10%，远小于旧/新原配置之间的波动，不能据此宣称稳定优化。

已按预定规则启动同一冻结源码/二进制/配置的独立新图tare_sensor_model_20261028_02，上限仍1600s，不增加任何参数调整或重编译。运行期间本会话独占ROS/Gazebo与原生工作空间，GBP2继续暂停。完成02后比较全部结果，决定候选保留或恢复原生版本，再生成报告、归档与私有备份。
'''
path.write_text(text, encoding='utf-8', newline='\n')
print('Independent candidate confirmation recorded')
