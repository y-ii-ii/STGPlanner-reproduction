from pathlib import Path
import hashlib,json,subprocess
task=Path(__file__).resolve().parents[1]
out=task/'outputs'
info=json.loads((out/'GitHub上传验证.json').read_text(encoding='utf-8'))
clone=task/'work/github-offline-restore-check'
def git(*args):return subprocess.check_output(['git','-C',str(clone),*args],text=True).strip()
assert git('rev-parse','HEAD')==info['commit']
assert git('rev-list','-n','1',info['baseline_tag'])==info['commit']
manifest=json.loads((clone/'baseline_manifest.json').read_text(encoding='utf-8'))
assert all(hashlib.sha256((clone/name).read_bytes()).hexdigest()==digest for name,digest in manifest['assets'].items())
info['offline_restore_verified']=True
info['offline_bundle_sha256']=hashlib.sha256((out/'STGPlanner-verified-baseline.bundle').read_bytes()).hexdigest()
(out/'GitHub上传验证.json').write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf-8')
report=f'''# GitHub 上传与回滚说明

私有仓库：[{info['repository']}]({info['url']})

- 主分支：`main`
- 已验证固定标签：`{info['baseline_tag']}`
- 基线提交：`{info['commit']}`
- 保留的上游提交：`{info['upstream_commit']}`
- 远端检查：{info['remote_files']} 个文件；主分支与标签指向一致；最终 16 项运行检查证据存在且通过。
- 全新克隆验证：91 个部署/报告/证据资产的 SHA256 一致。
- 已从离线 bundle 实际克隆，并再次核对提交、标签与 91 个资产，恢复检查通过。

## 本机目录与远端

源码目录：`D:\\STGPlanner\\catkin_ws\\src\\STGPlanner`

`origin` 指向你的私有仓库，`upstream` 保留原作者仓库。上传内容包括完整上游源码与历史、本机修复、部署/启动/测试脚本、报告、截图和选定原始证据。WSL 虚拟磁盘、模型下载缓存和编译产物留在本机；依赖与模型按版本清单及安装脚本重建。

## 后续修改

在新分支上修改，小步提交并推送；当前基线标签保持不动。仓库中的 `docs/版本控制与回滚.md` 给出了完整流程。

## 回到当前已验证版本

先停止运行；有未提交且需要保留的文件时先使用 `git stash push -u` 保存。

```powershell
& 'D:\\STGPlanner\\Stop-STGPlanner.cmd'
Set-Location D:\\STGPlanner\\catkin_ws\\src\\STGPlanner
git status
git fetch origin --tags
# 如有本地未提交修改，先保存后再切换
git switch -c recovery/scene4-baseline {info['baseline_tag']}
& .\\deployment\\install-local-tools.ps1
wsl.exe -d STGPlanner-Ubuntu20 -u root -- bash /mnt/d/STGPlanner/scripts/build.sh
& 'D:\\STGPlanner\\Start-STGPlanner.cmd'
```

恢复分支不会删除后续提交。若同名恢复分支已存在，使用新的名称。切换源码后需同步外部 `D:\\STGPlanner\\scripts` 并重新构建，才能使实际运行入口与恢复版本一致。

## 离线备份

同目录的 `STGPlanner-verified-baseline.bundle` 保存完整 Git 历史、主分支和固定标签，可在没有网络时克隆到一个新的空目录检查。它保存代码与部署资料，不包含整个 WSL 系统磁盘。

SHA256：`{info['offline_bundle_sha256']}`
'''
(out/'GitHub上传与回滚说明.md').write_text(report,encoding='utf-8')
print(json.dumps({'remote_verified':True,'offline_restore_verified':True,'commit':info['commit'],'assets_checked':len(manifest['assets'])},indent=2))
