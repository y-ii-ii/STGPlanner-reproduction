"""Keep the prespecified four-method baseline table and link the newer TARE cohort."""
import hashlib
import json
import shutil
import subprocess
from pathlib import Path
root=Path('D:/STGPlanner');repo=root/'catkin_ws/src/STGPlanner';out=root/'codex/outputs'
stem='Scene4四算法与论文对比汇总'
path=out/(stem+'.md');text=path.read_text(encoding='utf-8');first,rest=text.split('\n',1)
notice='> **2026-10-28 TARE后续：** 新增原配置对照996.477s/1490.842m；感知对齐候选两次976.461s/1474.461m、1060.356s/1546.579m，均达到95%，但未证实稳定性能收益，已恢复原生原配置。完整结果见[TARE优化测试报告](TARE优化测试报告.html)。下表保留2026-10-27预选单次基线，不按最新或最好一次替换历史TARE行。\n\n'
assert notice not in text
path.write_text(first+'\n\n'+notice+rest.lstrip(),encoding='utf-8',newline='\n')
subprocess.run(['pandoc',str(path),'--standalone','--embed-resources','--metadata','title='+stem,'--css',str(out/'scene4_table_style.css'),'-o',str(path.with_suffix('.html'))],cwd=str(out),check=True)
html=path.with_suffix('.html');html.write_text('\n'.join(line.rstrip() for line in html.read_text(encoding='utf-8').splitlines())+'\n',encoding='utf-8',newline='\n')
for suffix in ['.md','.html']:shutil.copy2(out/(stem+suffix),repo/'docs'/(stem+suffix))
manifest=repo/'evidence/scene4-progress-fix/evidence_manifest.json';value=json.loads(manifest.read_text(encoding='utf-8'))
for name in value['files']:value['files'][name]=hashlib.sha256((repo/name).read_bytes()).hexdigest()
manifest.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
shutil.copy2(Path(__file__),repo/'benchmarks/tare_optimization/update_report_links.py')
print('Historical four-method table retained; latest TARE cohort crosslinked')
