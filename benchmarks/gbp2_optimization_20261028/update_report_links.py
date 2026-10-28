"""Update local report entries while preserving the preselected four-method table."""
import datetime
import json
from pathlib import Path
root=Path('D:/STGPlanner');out=root/'codex/outputs';work=out/'gbp2_optimization_20261028'
summary=json.loads((work/'summary.json').read_text(encoding='utf-8'));decision=summary['decision']
assert decision['phase_complete']
path=out/'Scene4四算法与论文对比汇总.md';text=path.read_text(encoding='utf-8')
assert 'GBP2后续原生参数试验' not in text
first,rest=text.split('\n',1)
notice='> **2026-10-28 GBP2后续：** '+decision['conclusion']+' 完整结果见[GBP2优化测试报告](GBP2优化测试报告.html)。原四算法主表仍保留预选基线，全部新试验在下方补充，不挑最好一次替换历史GBP2行。\n\n'
text=first+'\n\n'+notice+rest.lstrip()
text=text.replace('**Scene4基线测试已阶段性完成。当前结果：STGPlanner、TARE、修复后的FAEL达到本地公共95%阈值；最新GBP2完整限时运行未达95%。GBP2后续测试保持用户暂停，本汇总没有启动新测试。**',
    '**Scene4基线测试已阶段性完成。主表预选版本中，STGPlanner、TARE、修复后的FAEL达到本地公共95%，GBP2修复09完整限时未达95%。用户于2026-10-28恢复的GBP2后续另列；最新状态见上方及优化报告。**')
text=text.replace('FAEL使用修复后的01运行，GBP2使用最新修复/校准后的09运行；','主表FAEL使用修复后的01运行，GBP2保持该阶段预选修复09；后续参数试验另列。')
text=text.replace('本表是已保存数据的汇总，不是新增实验或重新验证。','原主表保持预选结果；下方补充表只汇总已落盘的后续试验。')
text+='\n## GBP2后续原生参数试验（全部已完成运行）\n\n'
text+='| 运行 | 原生前沿阈值 | 名义距地高度(m) | 完整观察(s) | 原生结束(s) | 覆盖 | 路程(m) | 公共95% |\n|---|---:|---:|---:|---:|---:|---:|---|\n'
compact=[]
for record in summary['records']:
    d=record['result'];end=d.get('native_finish_sim_s');end_text=f'{end:.3f}' if end is not None else '未结束'
    text+=f"| {record['trial']} | {record['threshold']:g} | {record['height']:g} | {d['sim_time_s']:.3f} | {end_text} | {d['coverage_fraction']*100:.4f}% | {d['distance_m']:.3f} | {'达到' if d['area_m2']>7400.5 else '未达到'} |\n"
    compact.append({'trial':record['trial'],'frontier_threshold':record['threshold'],'robot_height_m':record['height'],
        **{k:d.get(k) for k in ['sim_time_s','distance_m','area_m2','coverage_fraction','finish_reason','native_finished','native_finish_sim_s']}})
text+='\n'+decision['conclusion']+' 原生提前返航与公共95%分开报告；未完成试验的观察时长不是完成时间。新试验保留工程修复09的原生源码与两库，参数和统计边界见[完整GBP2报告](GBP2优化测试报告.html)。\n'
path.write_text(text,encoding='utf-8',newline='\n')
path=out/'Scene4四算法与论文对比汇总.json';data=json.loads(path.read_text(encoding='utf-8'))
data['followups_updated_at']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat()
data['baseline_records_preserved']=True
data.setdefault('followups',{})['gbp2_optimization_20261028']={'report':'GBP2优化测试报告.html','conclusion':decision['conclusion'],'records':compact}
path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
guide=out/'代码目录说明.md';text=guide.read_text(encoding='utf-8')
text+='\n## 2026-10-28后续工具\n\nTARE工具在`codex/work/tare_optimization`，GBP2工具在`codex/work/gbp2_optimization_20261028`；两个目录各有README逐文件说明。Git对应`benchmarks/tare_optimization`与`benchmarks/gbp2_optimization_20261028`。GBP2本轮包括单参数配置、运行监督、被动记录、冻结地图诊断、URDF几何审计、报告/交接与私有备份；历史已执行record/prepare不能无条件重跑。当前原生部署和结果以最新STATUS及GBP2优化报告为准。\n'
guide.write_text(text,encoding='utf-8',newline='\n')
print('Local four-method baseline preserved; complete GBP2 follow-up and tool entries added.')
