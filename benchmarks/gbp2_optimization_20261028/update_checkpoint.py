"""Update the current handoff from a real lock/result, not from assumed runtime state."""
import argparse
import datetime
import json
import re
from pathlib import Path
parser=argparse.ArgumentParser();parser.add_argument('trial');parser.add_argument('--stage',choices=['running','ended'],required=True)
args=parser.parse_args();root=Path('D:/STGPlanner');out=root/'codex/outputs/gbp2_optimization_20261028'
catalog=json.loads(Path(__file__).with_name('trial_catalog.json').read_text(encoding='utf-8'))
registered=next(row for row in catalog if row['trial']==args.trial)
lock=json.loads((root/'codex/SIMULATION_LOCK.json').read_text(encoding='utf-8'))
assert lock['trial']==args.trial
folder=root/'benchmarks/results'/args.trial
now=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat()
if args.stage=='running':
    assert lock['runtime_active']
    headline='GBP2 '+args.trial+'运行中；独占仿真，期间不得编译或并行启动'
    detail='当前运行'+args.trial+f"，原生前沿资格阈值{registered['threshold']:g}、名义输入帧距地高度{registered['height']:g}m；独立新场景、公共95%与2400秒上限。"
    if (folder/'events.jsonl').exists():
        events=[json.loads(line) for line in (folder/'events.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
        native_end=next((row for row in events if row['kind']=='native_homing_ended'),None)
        start=next((row for row in events if row['kind']=='exploration_start'),None)
        if native_end is not None and start is not None:
            detail+=f"原生已在{native_end['sim']-start['sim']:.3f}秒返航结束，仍按完整上限保持观察。"
    additional='运行前配置与实际空闲检查、源码/两库、共享适配及配置指纹保存到preflight；只有本会话控制WSL/ROS/Gazebo。后续按conditional_followup_plan.v2.json分支，在本轮完整结束并验收/清理后才执行，不能因运行中暂时面积更好就宣称成功。'
    record={'trial':args.trial,'stage':'running','parameters':registered,'lock':lock,'updated_at':now}
else:
    assert not lock['runtime_active']
    result=json.loads((folder/'result.json').read_text(encoding='utf-8'))
    validation=json.loads((out/(args.trial+'_validation.json')).read_text(encoding='utf-8'))
    assert validation['protocol_checks_passed']
    headline='GBP2 '+args.trial+'完整结束并已验收；下一步按预定方案执行'
    detail=(args.trial+f"完整观察{result['sim_time_s']:.3f}秒、覆盖{result['coverage_fraction']*100:.6f}%、路程{result['distance_m']:.3f}m；公共95%"+
            ('达到。' if result['area_m2']>7400.5 else '未达到。'))
    if result.get('native_finish_sim_s') is not None:detail+=f"原生{result['native_finish_sim_s']:.3f}秒返航结束，与公共完成分别记录。"
    additional=f"{validation['check_count']}项协议/版本/数据/传感器/停车检查通过，原生地图SHA和归属清理通过。原始结果在benchmarks/results/{args.trial}，诊断在codex/outputs/gbp2_optimization_20261028。下一步仍以v2计划和实际锁为准；无用户暂停请求。"
    record={'trial':args.trial,'stage':'ended','summary':validation['summary'],'updated_at':now}
limits_path=root/'codex/GBP2_EXPERIMENT_LIMITS.json'
if limits_path.exists():
    limits=json.loads(limits_path.read_text(encoding='utf-8'))
    if limits['new_experiments_blocked']:
        headline='GBP2已达用户本轮3次上限；'+('当前最后一次仍在收尾' if args.stage=='running' else '实验停止，仅离线收尾')
        detail+=' 本轮新增正式试验上限3次（10/11/12），后续1.5%与全部复测取消。'
        additional='用户最新次数限制覆盖旧v1/v2条件方案。后续仅验收、清理、恢复已测试配置、离线报告/交接与私有备份；新实验入口已加硬拦截，不自动修改算法或增加试验。'
        record['experiment_limits']=limits
status=root/'codex/STATUS.md';text=status.read_text(encoding='utf-8')
text=re.sub(r'更新时间：[^。]+。','更新时间：'+now+'。',text,count=1)
text=re.sub(r'## 当前状态：[^\n]+','## 当前状态：'+headline,text,count=1)
paragraph='Scene4四算法基线阶段仍为已完成；2026-10-28用户明确恢复GBP2后续优化。'+detail+' TARE保持已验证原版，FAEL成功数据保留，均不重跑。历史暂停/运行叙述只说明当时状态；最新章节和SIMULATION_LOCK优先。'
text,count=re.subn(r'(?s)(## 当前状态：[^\n]+\n\n).*?(\n\n\| 运行 \|)',lambda match:match[1]+paragraph+match[2],text,count=1)
assert count==1,'Current handoff format changed; inspect before editing'
text+='\n## '+args.trial+' '+args.stage+'检查点\n\n'+detail+'\n\n'+additional+'\n'
status.write_text(text,encoding='utf-8',newline='\n')
(out/'live_checkpoint.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(detail)
