"""Update report/evidence tooling for the last confirmed diagnosis and run selection."""
from pathlib import Path
task=Path(__file__).resolve().parent
p=task/'make_progress_report.py';s=p.read_text(encoding='utf-8')
s=s.replace('原生收益权重、传感器参数、空间边界与前沿判定阈值均保留，公共95%门槛不变。','原生收益权重、感知范围和空间边界保留；传感器前沿比例随后按下述证据调整，公共95%门槛不变。')
s=s.replace('最终GBP2数据使用所有缺陷修复、返航契约修复及上述采样/时间模型配置的全新运行 `repair_formal_gbp2_04`，选择在结果产生前固定于progress_trials.json。不同版本的失败尝试保留，不当作同版本重复或挑选最优成绩。',
'''第四轮修正返航契约后仍在约855.756s原生结束，覆盖约41.319%，停车保持超过8分钟后主动停止诊断。第五轮将原生传感器前沿比例0.05调为0.01：冻结地图中125个无碰撞通道观察点，原阈值下0个有效，新阈值下16个有效；出口(18.5,66,0.456)有275个未知单元，原生判断门槛分别为1296和260。这个参数是原生候选前沿判断比例，不是公共95%覆盖门槛。离线证据提示出口可保留，但不能代替全程验证。第五轮实际完整跑满2400.014s（墙钟2413.895s），仅3225.44m²、41.405%，2343.532m；2116.081s返航结束后保持停车，未再请求探索。它证明该配置校准仍不足以突破平台。','',
'### 聚类收益与前沿类型不同步','',
'进一步审查发现computeExplorationGain的聚类分支把收益复制给邻近节点后，将它们移出待处理列表，却只给代表节点更新前沿类型。后续addFrontiers按类型筛选，因此部分有前沿收益的节点不会进入全局前沿候选。提取完整原生函数进行两节点受控回归：原版收益前沿2个、类型前沿1个；修复后两者均为2个；零收益用例仍均为0。修复同步复制节点的类型，不改变收益计算或碰撞检查。这证明实现不一致，不能单凭回归断言它解释全部停滞。','',
'最终GBP2选用加入上述聚类同步修复的全新运行 `repair_formal_gbp2_06`，其余参数与第五轮相同，选择在结果产生前固定于progress_trials.json。不同版本的失败尝试保留，不当作同版本重复或挑选最优成绩。''')
s=s.replace("'## 4. 后期稳定性、真实地图和验收','',", "'## 4. 后期稳定性、真实地图和验收',''," )
needle="'## 5. 与论文Scene4的关系','',"
s=s.replace(needle,"'### 各次GBP2诊断运行（全部保留）','',\n'| 运行 | 仿真秒 | 面积指标 | 里程(m) | 结束说明 |',\n'|---|---:|---:|---:|---|']\nfor item in v['intermediate_diagnostics']['intermediate_attempts']:\n    r=item['result'];lines.append(f\"| {r['trial']} | {r['sim_time_s']:.3f} | {r['coverage_fraction']*100:.3f}% | {r['distance_m']:.3f} | {'有记录的主动诊断停止' if item['intentional_stop'] else '2400秒限时未完成'} |\")\nlines+=['',\n"+needle)
s=s.replace("'wsl.exe -d STGPlanner-Ubuntu20 -u root -- python3 /mnt/d/STGPlanner/benchmarks/trial_contract_regression.py',", "'wsl.exe -d STGPlanner-Ubuntu20 -u root -- python3 /mnt/d/STGPlanner/benchmarks/trial_contract_regression.py',\n'wsl.exe -d STGPlanner-Ubuntu20 -u root -- python3 /mnt/d/STGPlanner/benchmarks/cluster_frontier_regression.py',")
p.write_text(s,encoding='utf-8',newline='\n')
p=task/'stage_progress.py';s=p.read_text(encoding='utf-8')
s=s.replace("'offline_rrg_probe.py','run_offline_rrg_probe.sh']", "'offline_rrg_probe.py','run_offline_rrg_probe.sh','validate_frontier_calibration.py','cluster_frontier_regression.py']")
s=s.replace("'adapter_config_manifest.json']", "'adapter_config_manifest.json','native_config.yaml','benchmark_trial.py']")
s=s.replace("'protocol_manifest.json','progress_trials.json']", "'protocol_manifest.json','progress_trials.json','gbp_corridor_gain.json','frontier_calibration_validation.json','cluster_frontier_regression.json']")
s=s.replace("'repair_formal_gbp2_04.err',", "'repair_formal_gbp2_04.err','repair_formal_gbp2_05.err','repair_formal_gbp2_06.err','progress_build_gbp2_cluster_stdout.log','progress_build_gbp2_cluster_stderr.log','corridor_gain_probe.log','corridor_gain_probe.err',")
p.write_text(s,encoding='utf-8',newline='\n')
print('Updated report and evidence tooling.')
