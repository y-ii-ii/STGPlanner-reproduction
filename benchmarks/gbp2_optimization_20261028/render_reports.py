"""Render local Markdown reports to self-contained HTML and normalize whitespace."""
import re
import subprocess
from pathlib import Path
out=Path('D:/STGPlanner/codex/outputs')
for name in ['GBP2优化测试报告','Scene4四算法与论文对比汇总','代码目录说明']:
    target=out/(name+'.html')
    subprocess.run(['pandoc',str(out/(name+'.md')),'--standalone','--embed-resources',
                    '--css',str(out/'scene4_table_style.css'),'--resource-path',str(out),
                    '--metadata','title='+name,'-o',str(target)],check=True)
    html=target.read_text(encoding='utf-8')
    html=re.sub(r'[ \t]+(?=\n)','',html)
    target.write_text(html,encoding='utf-8',newline='\n')
print('Three self-contained HTML reports rendered.')
