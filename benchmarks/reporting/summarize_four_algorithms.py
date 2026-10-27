"""Read existing Scene4 results and compare with verified paper v4 Table I."""
import datetime
import hashlib
import json
from pathlib import Path

root=Path('D:/STGPlanner');out=root/'codex/outputs'
specs=[
 ('STGPlanner','本机基线01','formal_stgp_01',779.8,17.2,1194.0,12.9,.015,1.53),
 ('TARE','本机基线01','formal_tare_01',1018.6,82.3,1640.0,135.3,.338,1.61),
 ('FAEL','原生修复01','repair_formal_fael_01',1033.9,149.8,1420.3,128.4,.119,1.37),
 ('GBP2','原生修复09','repair_formal_gbp2_09',1600,None,1560,None,.465,.97),
]
rows=[];records=[]
for name,version,trial,pt,ptstd,pd,pdstd,pr,ps in specs:
    source=root/'benchmarks/results'/trial/'result.json'
    result=json.loads(source.read_text())
    assert result['protocol_revision']==3
    assert result['area_threshold_m2']==7400.5
    success=result['finish_reason']=='coverage_threshold'
    assert result['validation']['reached_common_threshold']==success
    assert all(result['validation'][key] for key in ('stop_ack','parked_command_zero','parking_drift_under_0_1m','sensor_stream_live'))
    paper_time=f'{pt:.1f}±{ptstd:.1f}' if ptstd is not None else '>1600（Std —）'
    paper_distance=f'{pd:.1f}±{pdstd:.1f}' if pdstd is not None else '>1560（Std —）'
    local_time=f"{result['sim_time_s']:.3f}"+('（限时）' if not success else '')
    rows.append(f"| {name}（{version}） | {paper_time} → {local_time} | {paper_distance} → {result['distance_m']:.3f} | {pr:.3f} → {result['runtime_native_s_summary']['mean']:.4f} | {ps:.2f} → {result['average_speed_m_s']:.3f} | {result['coverage_fraction']*100:.4f}% | {'达到公共95%' if success else '限时未达95%'} |")
    records.append({'algorithm':name,'local_version':version,'trial':trial,'source_result':str(source),
       'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
       'paper':{'exploration_time_s':pt,'exploration_time_std_s':ptstd,'path_length_m':pd,'path_length_std_m':pdstd,'censored_lower_bounds':ptstd is None,'runtime_s':pr,'average_speed_m_s':ps},
       'local':{key:result[key] for key in ('sim_time_s','wall_time_s','distance_m','coverage_fraction','average_speed_m_s','finish_reason')},
       'local_native_runtime_mean_s':result['runtime_native_s_summary']['mean'],
       'descriptive_difference_from_paper_mean':{'exploration_time_percent':(result['sim_time_s']/pt-1)*100,'path_length_percent':(result['distance_m']/pd-1)*100} if success else None})
header='| 算法（本地版本） | 探索时间(s)：论文 → 本地 | 路径长度(m)：论文 → 本地 | 平均规划耗时(s)：论文 → 本地 | 平均速度(m/s)：论文 → 本地 | 本地覆盖指标 | 本地判定 |\n|---|---:|---:|---:|---:|---:|---|'
table=header+'\n'+'\n'.join(rows)
text='''# Scene4四种算法与论文数据汇总

**Scene4基线测试已阶段性完成。当前结果：STGPlanner、TARE、修复后的FAEL达到本地公共95%阈值；最新GBP2完整限时运行未达95%。GBP2后续测试保持用户暂停，本汇总没有启动新测试。**

下表每个“论文 → 本地”单元格左侧来自[论文v4 Table I的Scene4](https://arxiv.org/html/2412.13664v4)，右侧来自已保存的原始result.json。论文为每方法五次测试的统计；本地为表内所列版本的一次正式观测，不能作为同条件五次统计复现。

'''+table+'''

## 口径与结论

- 本地成功定义为公共观察器的已知平面面积/7790m²达到95%（面积>7400.5m²），并通过停车和传感器验收；不是算法自然结束或严格可达区域100%覆盖。论文未提供可直接对应的本地覆盖比例，故不填造论文覆盖率。
- GBP2的2400.007秒、2413.450米是限时观测窗口及其部分探索轨迹，不是完成时间/完整覆盖路径。论文的>1600和>1560同样不是准确完成值；Std横杠表示未提供，不能单独断言成功或崩溃，因此不计算GBP2相对论文的完成性能差。
- FAEL使用修复后的01运行，GBP2使用最新修复/校准后的09运行；两者含本地实现改动，不能与未经改动的上游/作者配置画等号。原FAEL1600秒41.2775%、原GBP2 1600秒41.1789%及全部中间失败/中止数据均保留，未用后续结果覆盖。
- 规划耗时按各代码原生统计范围：STGPlanner/FAEL为IterationTime，TARE为/runtime分项和，GBP2为服务回调内部稳态时钟。统计边界、CPU和负载不同，不能据此宣称跨论文的计算效率排名。本地速度是里程/探索仿真时长，含转向、等待及停滞，不是2m/s速度上限。
- 完成运行的单次数值对照：STGPlanner时间比论文均值低2.53%、路径低0.54%；FAEL时间低1.63%、路径低4.81%；TARE时间高25.40%、路径高9.23%。这些是描述性差值，不证明改进/退化或统计显著性。

## 原始结果选择

STGPlanner：formal_stgp_01；TARE：formal_tare_01；FAEL：repair_formal_fael_01；GBP2：repair_formal_gbp2_09。均在D:/STGPlanner/benchmarks/results下，源文件SHA和精确数值另存同名JSON。

详细部署/原始基线见[Scene4基线算法对比报告](Scene4基线算法对比报告.html)，FAEL/GBP2修复及未解决问题见[探索停滞修复报告](Scene4探索停滞修复报告.html)。本表是已保存数据的汇总，不是新增实验或重新验证。
'''
stem='Scene4四算法与论文对比汇总'
(out/(stem+'.md')).write_text(text,encoding='utf-8',newline='\n')
(out/(stem+'.json')).write_text(json.dumps({'generated_at':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),'paper_url':'https://arxiv.org/html/2412.13664v4','scene':'Scene4','paper_repeats':5,'local_observations_per_version':1,'records':records},ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(table)
