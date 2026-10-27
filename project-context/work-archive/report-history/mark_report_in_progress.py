from pathlib import Path
import shutil
task=Path(__file__).resolve().parents[1]
message='更新进行中：首轮长测发现结束后仍可能输出转向命令，停车链路已修复；最终报告将在第二轮严格长测完成后重新生成。以下是上一版记录，暂不作为最终验收。'
md=task/'outputs/STGPlanner部署报告.md'
md.write_text('> **'+message+'**\n\n'+md.read_text(encoding='utf-8'),encoding='utf-8')
html=task/'outputs/STGPlanner部署报告.html'
html.write_text(html.read_text(encoding='utf-8').replace('<body>','<body><p style="padding:16px;background:#fff1d6;border:1px solid #cc9332">'+message+'</p>',1),encoding='utf-8')
shutil.copy2(md,'D:/STGPlanner/部署报告.md')
shutil.copy2(html,'D:/STGPlanner/部署报告.html')
