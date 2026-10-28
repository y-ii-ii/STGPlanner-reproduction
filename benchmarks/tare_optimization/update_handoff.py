"""Record the newly authorized TARE follow-up without reopening GBP2."""
import datetime
import json
import re
from pathlib import Path

root = Path('D:/STGPlanner')
now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat()
path = root / 'codex/STATUS.md'
text = path.read_text(encoding='utf-8')
text = re.sub(r'## 当前状态：[^\n]+', '## 当前状态：用户授权TARE优化验证；GBP2继续暂停，既有Scene4基线阶段保留完成', text, count=1)
text += '''
## 2026-10-28 TARE优化后续（最新授权）

用户明确要求优化TARE并自主执行终端命令。本轮由原算法会话独占仿真和代码。运行前实际/proc及11311/11345检查均无活动运行。先用原配置执行tare_audit_control_20261028_01，1600s上限、公共95%与2m/s不变；只加独立订阅诊断，未改TARE算法或参数。后续根据日志选定单独优化方案，并使用新运行名。GBP2继续暂停，FAEL成功数据不重跑。旧基线formal_tare_01及所有历史原始结果保持不变。

新增工作工具在codex/work/tare_optimization，交付和预检在codex/outputs/tare_optimization_20261028。监督器冻结原生TARE源码/二进制及公共适配与配置，结束后按运行目录清理并核查端口。该后续优化不撤销2026-10-27已归档的四算法基线阶段完成状态。
'''
path.write_text(text, encoding='utf-8', newline='\n')
path = root / 'codex/RUNBOOK.md'
text = path.read_text(encoding='utf-8')
text = text.replace('> Scene4四算法基线测试已阶段性完成；GBP2后续测试保持用户暂停。当前只维护报告/归档；下列启动命令仅为未来明确恢复后的参考，不自动执行。',
                    '> Scene4四算法基线已阶段性完成。2026-10-28用户另授权TARE优化测试，当前仅本会话控制；GBP2继续暂停。下列旧GBP2命令仍不是执行授权。')
path.write_text(text, encoding='utf-8', newline='\n')
print('TARE follow-up authorization and handoff recorded at ' + now)
