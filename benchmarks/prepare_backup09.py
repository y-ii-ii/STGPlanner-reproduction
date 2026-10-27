"""Freeze the user's stop decision and preserve every existing evidence blob."""
import datetime
import gzip
import json
import subprocess
from pathlib import Path

root=Path('D:/STGPlanner');repo=root/'catkin_ws/src/STGPlanner';out=root/'codex/outputs'
git=['git','-c','safe.directory='+str(repo),'-C',str(repo)]
modified=subprocess.check_output(git+['diff','--name-only','-z','--','evidence/scene4-progress-fix']).decode().split('\0')
preserved=[]
for name in filter(None,modified):
    if name=='evidence/scene4-progress-fix/progress_trials.json':continue
    old=subprocess.check_output(git+['show','HEAD:'+name]);path=repo/name;current=path.read_bytes()
    same_payload=(gzip.decompress(old)==gzip.decompress(current)) if name.endswith('.gz') else old==current
    if not same_payload and name.endswith('.json'):
        try:same_payload=json.loads(old)==json.loads(current)
        except (ValueError,UnicodeError):pass
    alternate=None
    if not same_payload:
        alternate=path.with_name(path.name[:-3]+'.postrun-complete.gz') if name.endswith('.gz') else path.with_name(path.stem+'.postrun-complete'+path.suffix)
        assert not alternate.exists() or alternate.read_bytes()==current
        alternate.write_bytes(current)
    path.write_bytes(old)
    preserved.append({'original':name,'old_bytes_restored':True,'payload_unchanged':same_payload,
        'additional_complete_copy':alternate.relative_to(repo).as_posix() if alternate else None})
(out/'原始证据保留核对.json').write_text(json.dumps(preserved,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')

now=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat()
status=root/'codex/STATUS.md';text=status.read_text(encoding='utf-8')
text=text.replace('## 当前状态：本轮恢复验证和收益审计已结束，GBP2仍未完成95%',
    '## 当前状态：用户暂停GBP2后续测试，整理已完成结果并备份私有仓库')
text=text.replace('当前没有活动长测或已安排的自动续跑。','当前没有活动长测或已安排的自动续跑。用户最新要求：GBP2先不继续测；整理FAEL成功与GBP2未达95%的结论、保留数据和修改、更新报告/交接并备份私有仓库。未经用户明确恢复，不继续GBP2测试或算法修改。')
text=text.replace('本轮未推送、未新建最终标签。','本次备份待推送核验；不创建“全部修复完成”标签，main及历史基线保持不变。')
start=text.index('## 下一阶段')
text=text[:start]+'''## 后续安排与备份边界

用户已明确要求GBP2先不继续测试。本次只整理报告、证据、代码及私有Git备份，不启动新仿真、不修改算法、不安排续跑。FAEL成功定义为本地一次完整运行达到公共95%并通过停车/传感器验收；GBP2最新09为完整2400秒限时、56.338896%，探索未完成。两者均不冒充论文五次统计复现。
潜在的感知自由空间/原生收益一致性问题仅作未解决事项留存；待用户明确恢复后才接续，新实验须新名称及单一仿真控制权。06保持用户中止分类，07/09保持完整限时失败，08单列诊断。
备份目标为私有仓库fix/fael-gbp2-progress分支，保留main及两个历史基线标签。本次不创建scene4-progress-fix-2026-10-27“全部修复完成”标签。远程备份验收另存codex/outputs/私有仓库备份验证.json；未完成的验证不得冒称通过。
'''
import re
text=re.sub(r'更新时间：[^。]+。','更新时间：'+now+'。',text,count=1)
status.write_text(text,encoding='utf-8',newline='\n')
runbook=root/'codex/RUNBOOK.md';text=runbook.read_text(encoding='utf-8')
notice='> 当前用户已暂停GBP2后续测试。本次仅整理FAEL成功/GBP2未达95%的结果并备份；以下启动命令只是用户未来明确恢复后的参考，不自动执行。\n\n'
if notice not in text:text=text.replace('# 新会话恢复与协作清单\n\n','# 新会话恢复与协作清单\n\n'+notice,1)
text=text.replace('当前由算法与长测会话','本轮由算法与长测会话')
runbook.write_text(text,encoding='utf-8',newline='\n')
for path in (root/'AGENTS.md',repo/'AGENTS.md'):
    lines=path.read_text(encoding='utf-8').splitlines()
    for index,line in enumerate(lines):
        if line.startswith('- 项目暂停或恢复以'):
            lines[index]='- 项目暂停或恢复以用户最新明确授权及状态文件为准。用户已暂停GBP2后续测试，当前仅整理结果与备份；除非用户明确恢复，不启动新GBP2测试或继续算法修改。FAEL成功结果保留，不自动重跑。'
    path.write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n')
lock_path=root/'codex/SIMULATION_LOCK.json';lock=json.loads(lock_path.read_text())
lock.update(state='paused_by_user',runtime_active=False,phase='results_archival_private_backup',updated_at=now,
    note='User paused further GBP2 tests and authorized result/code/report preservation and private repository backup only. No simulation or automatic continuation scheduled.')
lock_path.write_text(json.dumps(lock,indent=2)+'\n',encoding='utf-8',newline='\n')
report=out/'Scene4探索停滞修复报告.md';text=report.read_text(encoding='utf-8')
notice='> **本次整理结论：FAEL本地一次完整运行达到95.3366%，GBP2最新完整2400秒运行仅56.338896%，未达到95%。用户已暂停GBP2后续测试；保留全部基线、失败、中止数据及源码修改，按当前分支备份到私有仓库。此备份不表示全部问题已修复，也不代表论文五次统计复现。**\n\n'
if notice not in text:text=text.replace('# Scene4 探索停滞修复与长测报告\n\n','# Scene4 探索停滞修复与长测报告\n\n'+notice,1)
text=text.replace('最终固定标签、远程上传验收和Git备份bundle尚未完成；本报告不表示已发布。','用户已授权将本次成功/未完成结果及代码备份到当前私有分支，远程提交一致性与证据SHA验收单独记录；不创建“全部修复完成”标签。')
text=text.replace('最终ZIP/bundle和上传验收尚待独立完成。','私有分支备份及本地Git bundle验证另见备份记录；不将备份视为探索目标已完成。')
text=text.replace('最终发布、标签及ZIP/bundle仍未执行。','本次只备份成功/未完成的真实结果，不创建全部修复完成标签。')
report.write_text(text,encoding='utf-8',newline='\n')
for name in ('STGPlanner部署报告.md','Scene4基线算法对比报告.md'):
    path=out/name;text=path.read_text(encoding='utf-8')
    if notice not in text:
        first,rest=text.split('\n',1);text=first+'\n\n'+notice+rest
    path.write_text(text,encoding='utf-8',newline='\n')
readme=repo/'README.md';text=readme.read_text(encoding='utf-8')
if notice not in text:
    first,rest=text.split('\n',1);text=first+'\n\n'+notice+rest
readme.write_text(text,encoding='utf-8',newline='\n')
print(json.dumps({'old_evidence_files_preserved':len(preserved),'additional_complete_versions':sum(bool(x['additional_complete_copy']) for x in preserved),'GBP2_tests_paused':True}))
