from pathlib import Path
folder=Path('D:/STGPlanner/codex/outputs')
for name in ('FAEL成功与GBP2未完成阶段总结','Scene4探索停滞修复报告','Scene4基线算法对比报告','STGPlanner部署报告'):
    path=folder/(name+'.html')
    text='\n'.join(line.rstrip() for line in path.read_text(encoding='utf-8').splitlines()).rstrip()+'\n'
    path.write_text(text,encoding='utf-8',newline='\n')
print('Normalized generated HTML whitespace; report content unchanged.')
