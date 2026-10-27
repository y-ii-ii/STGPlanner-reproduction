from pathlib import Path
import json
import shutil
import zipfile

task = Path(__file__).resolve().parents[1]
base = Path('D:/STGPlanner')
out = task/'outputs'
for mode in ('headless', 'gui'):
    data = json.loads((base/f'logs/runtime_{mode}.json').read_text(encoding='utf-8'))
    assert data['passed'] and all(data['checks'].values())
shutil.copy2(base/'logs/runtime_trajectory.png', out/'runtime_trajectory.png')
readme = '''STGPlanner 部署材料

本机运行目录：D:\\STGPlanner
启动：双击 D:\\STGPlanner\\Start-STGPlanner.cmd
停止：双击 D:\\STGPlanner\\Stop-STGPlanner.cmd

完整部署步骤、问题与修复、测试数值详见 STGPlanner部署报告.md。
scripts/ 为实际使用的 Linux 安装、修复、构建、启动和测试脚本。
源码的完整重建修复入口是 patch_deployment.py；deploy-fixes.patch 用于审阅已跟踪文件的差异。
source/.gitattributes 是新增的换行规则，修复脚本也会自动创建它。
models/ 不打包大型贴图，install_assets.sh 会从 OSRF 官方仓库指定提交下载。
logs/ 包含真实测试结果、轨迹、环境/依赖清单、模型校验值及构建/运行日志。

本包不包含完整 Git 仓库、WSL 虚拟磁盘或 Ubuntu 安装镜像；这些已保留在本机 D 盘。
'''
archive = out/'STGPlanner部署材料.zip'
with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    z.writestr('使用说明.txt', readme)
    z.write(out/'STGPlanner部署报告.md', 'STGPlanner部署报告.md')
    z.write(out/'runtime_trajectory.png', 'runtime_trajectory.png')
    z.write(out/'RViz修复验证结果.json', 'RViz修复验证结果.json')
    z.write(out/'长时间运行验证结果.json', '长时间运行验证结果.json')
    z.write(out/'long_run_metrics.png', 'long_run_metrics.png')
    if (out/'STGPlanner部署报告.html').exists():
        z.write(out/'STGPlanner部署报告.html', 'STGPlanner部署报告.html')
    for p in sorted((out/'screenshots').glob('*')):
        if p.is_file():
            z.write(p,'screenshots/'+p.name)
    for filename in ('Start-STGPlanner.cmd', 'Stop-STGPlanner.cmd',
                     'Start-STGPlanner.ps1', 'Stop-STGPlanner.ps1'):
        z.write(base/filename, filename)
    for p in sorted((base/'scripts').iterdir()):
        if p.is_file():
            z.write(p, 'scripts/'+p.name)
    for p in sorted((base/'logs').rglob('*')):
        if not p.is_file():
            continue
        rel = p.relative_to(base/'logs')
        if rel.parts[0] in ('ros',) or p.suffix == '.png' or p.name.endswith('.progress.json'):
            continue
        z.write(p, 'logs/'+rel.as_posix())
    z.write(base/'catkin_ws/src/STGPlanner/.gitattributes', 'source/.gitattributes')
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    print('Archive: {} files, {:.2f} MiB'.format(len(z.namelist()), archive.stat().st_size/1024**2))
shutil.copy2(archive, base/'部署材料.zip')
print('Deliverables verified.')
