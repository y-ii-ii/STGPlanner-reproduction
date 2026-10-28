"""Record the frozen single-native-parameter experiment while it is running."""
import re
from pathlib import Path
root=Path('D:/STGPlanner');path=root/'codex/STATUS.md';text=path.read_text(encoding='utf-8')
text=re.sub(r'## 当前状态：[^\n]+','## 当前状态：GBP2上游默认前沿参数10%正式对照运行中；TARE/FAEL不重跑',text,count=1)
text+='''
## GBP2正式单参数对照10

已启动gbp2_default_frontier_20261028_10，完整2400s上限、新场景；仅SensorParams/VLP16/frontier_percentage_threshold从0.01恢复上游默认0.1。09代码、原生两库、采样2000、感知范围12m、运动上限2m/s、原生全局回退、三维射线收益和公共95%保持不变。此原生“前沿资格比例”不等于公共95%完成门槛。

监督器与独立只读订阅器在codex/work/gbp2_optimization_20261028；完整预检/配置/源码指纹保存到新运行的preflight。已修正辅助订阅的环境路径与仿真时钟等待，记录动作/命令、实际参数和加载库，结束时仅请求保存原生地图，并按所属目录清理进程。运行期间不编译原生库。

检验1%是否让高处残余三维未知收益维持局部前沿、阻止有效全局切换。若阈值提高造成原生过早结束，仍按原生结束/公共95%/完整限时分别报告，绝不把返航或健康验收当探索成功。后续中间阈值或地面收益变体须另建新名、固定方案，不使用公共覆盖图给规划器选目标。
'''
path.write_text(text,encoding='utf-8',newline='\n');print('GBP2 trial10 running handoff updated')
