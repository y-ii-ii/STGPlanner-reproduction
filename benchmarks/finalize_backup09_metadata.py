import datetime
import json
import re
import shutil
from pathlib import Path
root=Path('D:/STGPlanner');repo=root/'catkin_ws/src/STGPlanner';out=root/'codex/outputs'
remote=json.loads((out/'私有仓库备份验证.json').read_text(encoding='utf-8'))
clone=json.loads((out/'私有仓库克隆恢复核验.json').read_text(encoding='utf-8'))
assert remote['private'] and remote['remote_head_matches_local']
assert remote['remote_commit']==clone['commit'] and clone['all_recorded_hashes_passed']
sha=clone['commit'];now=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat()
status=root/'codex/STATUS.md';text=status.read_text(encoding='utf-8')
text=re.sub(r'更新时间：[^。]+。','更新时间：'+now+'。',text,count=1)
text=text.replace('本次备份待推送核验；不创建“全部修复完成”标签，main及历史基线保持不变。',
    f'本次代码/证据内容提交{sha}已推送并通过私有性、远端提交及克隆SHA核验；随后元数据提交记录本次验收。未创建“全部修复完成”标签，main及历史基线保持不变。')
text+='''\n## 本次私有备份验收\n\n'''+f'''- 内容检查点：{sha}，fix/fael-gbp2-progress，远端私有性已确认。
- 从远端独立克隆恢复，522项记录文件SHA全部匹配，09原生地图解压SHA匹配，工作树干净，历史基线标签保留。
- 内容结论仍为FAEL本地成功、GBP2未达95%；GBP2后续测试保持用户暂停，不自动续跑。
- 验收记录见project-context/BACKUP_VERIFIED.json、docs/私有仓库备份说明.md；本地记录在codex/outputs/私有仓库备份验证.json和私有仓库克隆恢复核验.json。
- 本文所记录的是内容提交，随后仅增加验收/交接元数据；最终分支HEAD以git log及远端最终核对为准。
'''
status.write_text(text,encoding='utf-8',newline='\n')
lockpath=root/'codex/SIMULATION_LOCK.json';lock=json.loads(lockpath.read_text())
lock.update(state='paused_by_user',runtime_active=False,phase='private_backup_verified_gbp2_paused',updated_at=now,
    backup_content_commit=sha,note='User paused further GBP2 tests. Result/code private backup verified by remote commit and fresh clone hashes; no simulation or automatic continuation scheduled.')
lockpath.write_text(json.dumps(lock,indent=2)+'\n',encoding='utf-8',newline='\n')
receipt={'content_commit':sha,'repository':'y-ii-ii/STGPlanner-reproduction','branch':'fix/fael-gbp2-progress',
 'private':True,'content_verification':remote,'fresh_clone_verification':clone,
 'decision':'FAEL reached95% locally; GBP2 did not. Further GBP2 tests paused by user.',
 'note':'This receipt is a follow-up metadata commit; its own commit SHA is available in git log. No fully-fixed tag created.'}
(repo/'project-context/BACKUP_VERIFIED.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
note=f'''# 私有仓库结果备份说明

内容提交：[{sha[:7]}](https://github.com/y-ii-ii/STGPlanner-reproduction/commit/{sha})

仓库：y-ii-ii/STGPlanner-reproduction（已核实私有），分支fix/fael-gbp2-progress。

- FAEL：1017.008仿真秒达到95.3366%，停车与传感器检查通过。
- GBP2最新09：完整2400.007仿真秒、56.338896%，未达到95%；原始失败、中止、诊断数据和代码修改全部保留。
- 211项协议/数据检查通过不等于探索成功。工程单次结果不冒充论文五次统计复现。
- 远端内容提交与本地一致；独立克隆的522项记录文件SHA全部匹配，44MB原生地图的解压SHA也匹配。
- main、历史基线分支及两个历史基线标签保持不变；不创建“全部修复完成”标签。
- 用户已暂停GBP2后续测试，无活动长测或自动续跑。潜在剩余原因仅作为交接事项。

本说明随后的元数据提交仅记录验收，不改变上述内容证据。完整机器记录见[BACKUP_VERIFIED.json](../project-context/BACKUP_VERIFIED.json)。
'''
(out/'私有仓库备份说明.md').write_text(note,encoding='utf-8',newline='\n')
(repo/'docs/私有仓库备份说明.md').write_text(note,encoding='utf-8',newline='\n')
for name in ('STATUS.md','RUNBOOK.md','SIMULATION_LOCK.json'):shutil.copy2(root/'codex'/name,repo/'project-context'/name)
for name in ('verify_remote_clone09.py','verify_index09.py','normalize_reports09.py','finalize_backup09_metadata.py'):
    (repo/'benchmarks'/name).write_text((root/'codex/work'/name).read_text(encoding='utf-8'),encoding='utf-8',newline='\n')
print(json.dumps({'content_commit':sha,'receipt_written':True,'GBP2_paused':True}))
