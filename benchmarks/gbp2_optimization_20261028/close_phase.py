"""Close the three-trial phase at the user's hard limit; never schedule another run."""
import datetime
import json
from pathlib import Path
root=Path('D:/STGPlanner');out=root/'codex/outputs/gbp2_optimization_20261028'
limits=json.loads((root/'codex/GBP2_EXPERIMENT_LIMITS.json').read_text(encoding='utf-8'))
cap=json.loads((out/'experiment_limit_validation.json').read_text(encoding='utf-8'))
assert limits['new_experiments_blocked'] and limits['max_new_formal_trials']==3 and cap['new_experiment_guard_rejects']
baseline=json.loads((root/'benchmarks/results/repair_formal_gbp2_09/result.json').read_text(encoding='utf-8'))
records=[]
for name in limits['counted_trials']:
    value=json.loads((out/(name+'_validation.json')).read_text(encoding='utf-8'))
    assert value['protocol_checks_passed'] and not value['summary']['public95_reached']
    records.append(value)
assert len(records)==3 and max(r['summary']['coverage_fraction'] for r in records)<baseline['coverage_fraction']
deployment=json.loads((out/'deployment_state.json').read_text(encoding='utf-8'))
assert deployment['reference_trial']=='repair_formal_gbp2_09' and deployment['runtime_idle_verified']
value={'phase_complete':True,'end_reason':'explicit_user_experiment_cap','max_new_formal_trials':3,
    'completed_trials':limits['counted_trials'],'no_new_experiments':True,'cancelled_plans':limits['cancelled'],
    'public95_reached':False,'new_configuration_area_improvement_demonstrated':False,
    'conclusion':'本轮新增正式试验限额3次（10/11/12）已用完，三次均未达公共95%，也未提高历史修复09的56.338896%覆盖。按用户限制停止GBP2优化，不再测试或修改算法。当前配置下GBP2存在明显覆盖停滞，不作为Scene4达95%的成功基线。',
    'deployment_text':'已恢复历史修复09的可追溯已测试配置（前沿0.01、名义高度0.456m），原生源码及两库仍与09一致；该配置仍明确标为未达95%。全部候选before/after、失败数据和校准依据保留，不将较差候选作为默认性能优化。',
    'interpretation':'本轮证据显示两种失效表现：低阈值保留残余三维收益，局部往返且全局回退受阻；提高至3%/10%后则在约40%覆盖时耗尽合格前沿并返航。几何名义高度校准虽缩小平地参考高度差，本次覆盖仍只有28.5350%，没有解决停滞；单次结果不能证明该校准在所有条件下必然降低性能。原生3D收益、前沿资格和全局回退与二维公共完整覆盖不等价。工程上按当前Scene4适配不足归档；这些有限观测不能证明GBP2在所有此类场景理论上都无法成功，也不能排除尚未核实的适配因素。',
    'next_step':'不再启动1.5%阈值、复测、地图重放或新源码优化。仅完成离线结果整理、交接及私有备份；保留STGPlanner/TARE/FAEL已成功基线与GBP2未达标对照。今后若用户另行明确恢复，必须先设新的有限次数和停止条件，不能自动扩展本轮限制。',
    'experiment_checks':sum(r['check_count'] for r in records)}
target=out/'phase_decision.json';assert not target.exists()
target.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
path=root/'codex/SIMULATION_LOCK.json';lock=json.loads(path.read_text(encoding='utf-8'));assert not lock['runtime_active']
lock.update(state='idle',phase='gbp2_user_limit_reached_offline_closeout',gbp2_followup='capped_at_user_limit',
    max_new_formal_trials=3,used_new_formal_trials=3,new_experiments_blocked=True,
    updated_at=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),
    note='User cap reached; only offline closeout/restore/backup. No new ROS/Gazebo, probe, repeat, or optimization.')
path.write_text(json.dumps(lock,indent=2)+'\n',encoding='utf-8',newline='\n')
with (root/'codex/RUNBOOK.md').open('a',encoding='utf-8',newline='\n') as handle:
    handle.write('\n## 最新硬限制：GBP2本轮最多3次，已停止\n\n10/11/12三次已完整结束且未达95%，没有覆盖改善。用户限制覆盖旧v1/v2方案：1.5%、全部复测、新ROS/Gazebo/地图重放与算法修改均取消。权威限制codex/GBP2_EXPERIMENT_LIMITS.json；新入口guard_new_experiment.py拒绝继续。仅离线收尾、恢复已测试09配置、报告/交接及私有备份。不得以旧“恢复测试”章节自动续跑。\n')
print(json.dumps(value,ensure_ascii=False,indent=2))
