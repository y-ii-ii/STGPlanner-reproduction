from pathlib import Path
import hashlib,json,re,shutil,subprocess

base=Path('D:/STGPlanner')
repo=base/'catkin_ws/src/STGPlanner'
task=Path(__file__).resolve().parents[1]
upstream='59b41451f7b80ba09a9bcbaf44b58141cd6f9de8'
tag='repro-baseline-2026-10-26'
def git(*args):
    return subprocess.check_output(['git','-C',str(repo),*args],text=True,encoding='utf-8').strip()
def copy(src,dst):
    dst.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(src,dst)

assert git('rev-parse','HEAD')==upstream,'Expected the original upstream HEAD before preparing the baseline.'
result=json.loads((base/'logs/planner_completion/long_verification_summary.json').read_text())
assert result['passed'] and len(result['checks'])==16 and all(result['checks'].values())

ignore=repo/'.gitignore'
extra='''
# Local environments, generated products, and credentials
/build/
/devel/
/install/
/logs/
/downloads/
/models/
/wsl/
/backups/
**/__pycache__/
*.py[cod]
*.vhd
*.vhdx
*.iso
*.tar
*.tar.gz
*.zip
*.bag
*.db3
.env
.env.*
*.pem
*.key
'''
ignore.write_text(ignore.read_text().rstrip()+'\n'+extra,encoding='utf-8')
attributes=repo/'.gitattributes'
attributes.write_text(attributes.read_text().rstrip()+'''\n*.md text eol=lf
*.json text eol=lf
*.jsonl text eol=lf
*.ps1 text eol=crlf
*.cmd text eol=crlf
*.png binary
*.jpg binary
''',encoding='utf-8')

deployment=repo/'deployment'
for file in (base/'scripts').iterdir():
    if file.is_file():copy(file,deployment/'scripts'/file.name)
for name in ('Start-STGPlanner.cmd','Stop-STGPlanner.cmd','Start-STGPlanner.ps1','Stop-STGPlanner.ps1'):
    copy(base/name,deployment/'windows'/name)

docs=repo/'docs'
for name in ('STGPlanner部署报告.md','STGPlanner部署报告.html','runtime_trajectory.png','long_run_metrics.png','RViz修复验证结果.json','长时间运行验证结果.json'):
    copy(task/'outputs'/name,docs/name)
for file in (task/'outputs/screenshots').iterdir():
    if file.is_file():copy(file,docs/'screenshots'/file.name)
docs.joinpath('UPSTREAM_README.md').write_text(git('show',upstream+':README.md')+'\n',encoding='utf-8')

selected={
    'environment.txt':'environment/environment.txt',
    'installed-packages.tsv':'environment/installed-packages.tsv',
    'model_checksums.txt':'environment/model_checksums.txt',
    'gazebo_models_commit.txt':'environment/gazebo_models_commit.txt',
    'runtime_headless.json':'deployment-tests/runtime_headless.json',
    'runtime_headless.trajectory.csv':'deployment-tests/runtime_headless.trajectory.csv',
    'runtime_gui.json':'deployment-tests/runtime_gui.json',
    'gui_node_health.json':'deployment-tests/gui_node_health.json',
    'paper_comparison.json':'paper-comparison.json',
    'build.log':'build/full-build.log',
    'planner_completion/build.log':'build/lifecycle-fixes-build.log',
    'rviz_repair/build.log':'build/rviz-fixes-build.log',
    'rviz_repair/verification_summary.json':'rviz/verification_summary.json',
    'rviz_repair/model_validation.json':'rviz/model_validation.json',
    'rviz_repair/tf_after.json':'rviz/tf_after.json',
    'rviz_repair/markers_after.json':'rviz/markers_after.json',
    'planner_completion/long_runtime.json':'scene4-final/long_runtime.json',
    'planner_completion/long_runtime.events.jsonl':'scene4-final/long_runtime.events.jsonl',
    'planner_completion/long_runtime.metrics.jsonl':'scene4-final/long_runtime.metrics.jsonl',
    'planner_completion/long_runtime.exit':'scene4-final/long_runtime.exit',
    'planner_completion/long_verification_summary.json':'scene4-final/verification_summary.json',
    'planner_completion/isolated_regression.json':'scene4-final/isolated_regression.json',
    'planner_completion/long_exploration.log':'scene4-final/exploration.log',
    'planner_completion/qt_capture_metadata.json':'scene4-final/qt_capture_metadata.json',
    'planner_completion/baseline/old_threshold_stdout.log':'diagnosis/old_threshold_stdout.log',
    'planner_completion/baseline/old_completion_sequence.txt':'diagnosis/old_completion_sequence.txt',
    'planner_completion/first_long_before_stop_fix/audit_review.json':'diagnosis/first_long_audit_review.json',
    'planner_completion/first_long_before_stop_fix/long_runtime.json':'diagnosis/first_long_before_stop_fix.json',
}
for src,dst in selected.items():
    assert (base/'logs'/src).is_file(),src
    copy(base/'logs'/src,repo/'evidence'/dst)
for name in ('iteration_time.txt','time_distance_volume.txt','trajectory.txt'):
    copy(base/'logs/planner_completion/long_run_statistics'/name,repo/'evidence/scene4-final/statistics'/name)

(deployment/'install-local-tools.ps1').write_text('''$ErrorActionPreference = 'Stop'
$StgRepositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$StgExpectedRoot = 'D:\\STGPlanner\\catkin_ws\\src\\STGPlanner'
if ($StgRepositoryRoot.TrimEnd('\\') -ne $StgExpectedRoot) {
    throw "Clone this repository into $StgExpectedRoot before installing the fixed-path deployment tools."
}
$StgScriptDirectory = 'D:\\STGPlanner\\scripts'
New-Item -ItemType Directory -Force -Path $StgScriptDirectory | Out-Null
Copy-Item -Path (Join-Path $PSScriptRoot 'scripts\\*') -Destination $StgScriptDirectory -Force
Copy-Item -Path (Join-Path $PSScriptRoot 'windows\\*') -Destination 'D:\\STGPlanner' -Force
Write-Host 'Deployment tools synchronized from the current checked-out Git revision.'
''',encoding='utf-8')

(repo/'README.md').write_text(f'''# STGPlanner Scene4 复现基线

基于 [Haochen-Niu/STGPlanner](https://github.com/Haochen-Niu/STGPlanner) 的公开代码，保留其 Git 历史、作者信息及各文件原有许可声明。上游基线：`{upstream}`。原始项目说明和论文引用见 [UPSTREAM_README](docs/UPSTREAM_README.md)。

本仓库用于保存本机已验证版本，后续在分支上逐步修改，并通过固定标签回到当前基线。

## 已验证范围

- Windows 11 + D 盘独立 WSL2 Ubuntu 20.04，ROS Noetic / Gazebo 11。
- 28 个 Catkin 包构建成功；实际运行公开代码提供的 Scene4。
- 修复编译依赖、CRLF、场景模型、TF、空 Marker、结束期间误报超时与停车链路。
- 最终完整观察 1200.1 秒，16 项生命周期检查全部通过；3646 次成功且非空规划，项目累计距离约 1214.97 米。
- 默认以项目指标超过名义地图面积的 95% 停止；不代表真实可达区域 100% 覆盖。
- 只完成 Scene4 功能复现；其他论文场景、基线方法和同配置五轮统计尚未复现。

## 入口

- [完整部署报告](docs/STGPlanner部署报告.md) / [单文件 HTML 报告](docs/STGPlanner部署报告.html)
- [版本控制与回滚](docs/版本控制与回滚.md)
- [最终验证结果](evidence/scene4-final/verification_summary.json)
- [论文 Scene4 对照](evidence/paper-comparison.json)
- [部署脚本](deployment/scripts/) / [Windows 启停入口](deployment/windows/)

## 当前机器启动

```powershell
& 'D:\\STGPlanner\\Start-STGPlanner.cmd'
# 停止专用发行版中的项目
& 'D:\\STGPlanner\\Stop-STGPlanner.cmd'
```

从仓库恢复运行脚本（尤其在切换旧版本后）：

```powershell
Set-Location D:\\STGPlanner\\catkin_ws\\src\\STGPlanner
& .\\deployment\\install-local-tools.ps1
wsl.exe -d STGPlanner-Ubuntu20 -u root -- bash /mnt/d/STGPlanner/scripts/build.sh
```

新电脑应先克隆到上述固定路径，再按照部署报告导入 Ubuntu、安装依赖、复制部署工具和构建。报告中历史上游克隆命令仅说明原部署过程，恢复此复现版本应克隆本仓库，而非重新拉取未经修复的上游。

## 版本约定

固定基线标签：`{tag}`。`main` 保存可运行版本；新修改先开独立分支，完成有意义的检查后提交和推送。回滚方法见对应文档。

仓库包含完整上游源码、修复、部署脚本、报告、截图与选定测试证据。WSL 虚拟磁盘、APT/模型下载缓存、编译产物和密钥不进入 Git；模型由脚本从固定上游提交重新下载。
''',encoding='utf-8')

(docs/'版本控制与回滚.md').write_text(f'''# 版本控制与回滚

## 基线

- 上游来源：Haochen-Niu/STGPlanner，提交 `{upstream}`。
- 固定已验证版本：标签 `{tag}`，包含源码修复与部署资产。
- 基线之后的修改在独立分支提交；保留标签，不重写或强推覆盖基线。
- 验证范围和数值见部署报告及 `evidence/scene4-final/`。首轮长测发现停车问题，未作为最终停车验收；相应原始数据和复核说明仍保留。

## 开始一次修改

```powershell
Set-Location D:\\STGPlanner\\catkin_ws\\src\\STGPlanner
git status
git switch main
git pull --ff-only origin main
# 将分支名替换为本次具体修改；示例仅用于说明
git switch -c feature/planner-improvement
# 修改、构建并做与改动相匹配的检查后
git add <本次修改的文件>
git commit -m "Describe the concrete change"
git push -u origin feature/planner-improvement
```

## 安全恢复到当前基线

先停止仿真，再保存尚未提交的修改。`stash -u` 保存未跟踪文件，但不包含已忽略的大型缓存和环境镜像。

```powershell
& 'D:\\STGPlanner\\Stop-STGPlanner.cmd'
Set-Location D:\\STGPlanner\\catkin_ws\\src\\STGPlanner
git status
# 有尚未提交且需要保留的文件时执行
git stash push -u -m "Before restoring the Scene4 baseline"
git fetch origin --tags
# 创建恢复分支，不删除后续提交；若同名分支已存在，换一个新名称
git switch -c recovery/scene4-baseline {tag}
# 外部 D:\\STGPlanner\\scripts 也必须同步，不能只恢复源码
& .\\deployment\\install-local-tools.ps1
wsl.exe -d STGPlanner-Ubuntu20 -u root -- bash /mnt/d/STGPlanner/scripts/build.sh
& 'D:\\STGPlanner\\Start-STGPlanner.cmd'
```

恢复分支不会重写 `main`。若只需要撤销后续某个提交，在合适分支执行 `git revert <提交号>` 并重新验证，再推送即可；共享历史避免使用强制推送。

## 依赖与整个 WSL 环境

Git 保存源码与重建脚本，不保存 WSL 磁盘。以后准备大改系统依赖之前，可另外导出本机环境：

```powershell
& 'D:\\STGPlanner\\Stop-STGPlanner.cmd'
New-Item -ItemType Directory -Force D:\\STGPlanner\\backups
wsl.exe --export STGPlanner-Ubuntu20 D:\\STGPlanner\\backups\\before-dependency-change.tar
```

将环境导出保留在本地备份目录，避免将数 GB 镜像加入 Git。Git 回退后应同步部署脚本、重新构建；系统依赖版本变化时还需按环境清单恢复或使用 WSL 备份。
''',encoding='utf-8')

(repo/'evidence/README.md').write_text('''# 验证证据

`scene4-final/` 是停车与超时修复后完成的最终单轮 20 分钟观察，16 项检查通过。项目累计距离与采集窗口里程计距离口径不同，见报告说明。

`diagnosis/first_long_before_stop_fix.json` 是较早的诊断轮次：虽然旧版 13 项检查标记 passed，复核发现残余角速度命令，故不作为最终停车验收；`first_long_audit_review.json` 明确记录了该限制。

`build/`、`rviz/`、`deployment-tests/`、`environment/` 分别保存构建、RViz/TF/Marker、原部署运行和环境证据。部分历史文件包含当时机器路径或话题名，这是运行记录，不是跨机器默认配置。
''',encoding='utf-8')

payload=[]
for folder in (deployment,docs,repo/'evidence'):
    payload.extend(f for f in folder.rglob('*') if f.is_file())
payload.extend(repo/name for name in git('ls-files').splitlines())
payload.extend((repo/'.gitattributes',repo/'.gitignore'))
patterns=[rb'gh[pousr]_[A-Za-z0-9]{30,}',rb'github_pat_[A-Za-z0-9_]{30,}',rb'-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----',rb'AKIA[0-9A-Z]{16}']
findings=[]
for file in set(payload):
    raw=file.read_bytes()
    if len(raw)>45*1024*1024:raise RuntimeError('Unexpected large upload: '+str(file))
    if b'\0' in raw[:2048]:continue
    if any(re.search(p,raw) for p in patterns):findings.append(str(file.relative_to(repo)))
assert not findings,'Potential credentials found; file names only: '+str(findings)
manifest={'upstream_repository':'https://github.com/Haochen-Niu/STGPlanner','upstream_commit':upstream,'baseline_tag':tag,'validation':{'scene':'Scene4','checks':16,'passed':True},'assets':{str(file.relative_to(repo)).replace('\\','/'):hashlib.sha256(file.read_bytes()).hexdigest() for file in sorted(set(payload)) if file.is_file() and any(folder in file.parents for folder in (deployment,docs,repo/'evidence'))}}
(repo/'baseline_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'source_files':len(git('ls-files').splitlines()),'deployment_and_evidence_files':len(manifest['assets']),'credential_patterns_found':len(findings),'payload_bytes':sum(f.stat().st_size for f in set(payload))},indent=2))
