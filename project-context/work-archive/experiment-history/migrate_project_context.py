"""Save the user-paused task and seed concise context for new project chats."""
from pathlib import Path
import datetime,gzip,hashlib,json,shutil
task=Path(__file__).resolve().parents[1]
project=Path('D:/STGPlanner');context=project/'codex';repo=project/'catkin_ws/src/STGPlanner';bench=project/'benchmarks'
for d in [context,context/'work',context/'outputs',context/'history',repo/'project-context']:
    d.mkdir(parents=True,exist_ok=True)
now=datetime.datetime.now().astimezone().isoformat();trial=bench/'results/repair_formal_gbp2_06';result=json.loads((trial/'result.json').read_text())
pause={'saved_at':now,'state':'paused_by_user','reason':'用户要求先暂停项目，迁移到STGPlanner项目并配置跨会话交接。','trial':'repair_formal_gbp2_06','sim_time_s':result['sim_time_s'],'coverage_fraction':result['coverage_fraction'],'distance_m':result['distance_m'],'reached_common_threshold':False,'result_finish_reason':result['finish_reason'],'intentional_native_stop':True,'resume_requires_fresh_trial':True,'native_runtime_stopped':True,'validation':result['validation']}
(trial/'user_pause.json').write_text(json.dumps(pause,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
(context/'PAUSED.json').write_text(json.dumps(pause,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
agents='''# STGPlanner 项目协作规则

- 先读最新状态与恢复清单：D:/STGPlanner/codex/STATUS.md、RUNBOOK.md。不要默认读取整段旧聊天或历史归档。
- 当前项目由用户主动暂停。除非用户后续明确恢复，不启动仿真、修改算法或继续长测；可回答问题及维护交接文件。
- 本项目目录D:/STGPlanner不是Git根。实际Git仓库在D:/STGPlanner/catkin_ws/src/STGPlanner；不要在D盘项目根执行git init。
- 私有仓库y-ii-ii/STGPlanner-reproduction；当前修复分支fix/fael-gbp2-progress。保留main及两个历史基线标签。
- 部署工具D:/STGPlanner/benchmarks；WSL发行版STGPlanner-Ubuntu20。真正编译的FAEL/GBP2源码在WSL /opt/stgplanner/benchmarks/*_ws/src，修改D盘上游克隆不会自动改变二进制。
- 多会话不假定互相知道聊天内容。每个实质阶段结束更新STATUS.md的结果、改动文件、验证与下一步；不以巨型聊天复制代替交接。
- 同时只允许一个会话控制这套WSL/ROS/Gazebo。运行前读SIMULATION_LOCK.json并核对实际进程；更新归属。其他会话不得终止发行版、占用11311/11345、重编译正在用的原生库。
- 同一Git工作目录只允许一个会话写代码/切分支/提交；并行代码任务使用独立Git工作树。报告会话读取已落盘数据，最终报告写入由一个会话完成。
- 原始基线与失败/用户中止数据不可覆盖。新测试必须新目录名；95%公共阈值、原生结束、限时、用户暂停分别报告，不把健康验收或单次试验当作论文统计复现。
- 项目内中间脚本用codex/work，交付用codex/outputs。历史原始会话工作区及其outputs仍保留，路径见STATUS.md。
'''
(project/'AGENTS.md').write_text(agents,encoding='utf-8',newline='\n')
repoagents=agents.replace('D:/STGPlanner/codex/STATUS.md、RUNBOOK.md','project-context/STATUS.md、project-context/RUNBOOK.md')
(repo/'AGENTS.md').write_text(repoagents,encoding='utf-8',newline='\n')
status=f'''# STGPlanner 最新交接状态

更新时间：{now}。本文件覆盖旧聊天及history中所有“仍在运行”的历史描述。

## 当前状态：用户主动暂停

用户最新要求：先暂停算法项目；迁入已创建的STGPlanner项目，配置短会话交接。
已将“部署并测试 STGPlanner”对话迁入项目，侧栏按项目分组。项目ID bd16d030-19af-4456-a6f4-fecde2256511。
GBP2第六轮已按用户要求停止原生启动器，公共测试器执行停车并保存结果；随后专用WSL发行版已停止。没有活动长测。

- 第六轮repair_formal_gbp2_06：{result['sim_time_s']:.3f}仿真秒，{result['coverage_fraction']*100:.6f}%，{result['area_m2']:.2f}m²，{result['distance_m']:.3f}m。
- **已突破原41%平台并进入右侧；尚未完成95%。** 本轮被用户中止，不能声称完整2400秒试验或算法自然结束。
- 原始finish_reason是{result['finish_reason']}，源于有记录的人工关闭原生启动器。interruption.json和user_pause.json说明用户暂停；停车确认、零指令、漂移和传感器检查均通过。
- 不能从1082秒精确续跑：进程内图和仿真状态已结束。恢复时使用新的运行名（建议repair_formal_gbp2_07）从相同初始条件重测；保留06为用户中止证据。

## 目录和版本

- 项目根：D:/STGPlanner；Git根：D:/STGPlanner/catkin_ws/src/STGPlanner。
- 私有远程：https://github.com/y-ii-ii/STGPlanner-reproduction，分支fix/fael-gbp2-progress。
- 最近已推送的算法代码检查点e2b5d2d（聚类前沿类型修复）；之前14925ee（返航契约）、11afc7d（几何修复）。迁移交接另有后续提交，读取git log核实。
- 保留main/repro-baseline-2026-10-26=dfc712982891f29c266083d7efad72ad48e730a2；benchmark/scene4-baselines和scene4-baselines-2026-10-27=9dec3c45184259a0d68e3dfe066040966d807aed。
- 最终修复标签scene4-progress-fix-2026-10-27尚未创建；最终报告、远程克隆验收和最终ZIP/bundle尚未完成，不得冒称已发布。
- WSL：STGPlanner-Ubuntu20（root，Ubuntu20/ROS Noetic）；WSL磁盘在D盘。原生编译副本/opt/stgplanner/benchmarks/fael_ws和gbp2_ws，主环境/opt/stgplanner/catkin_ws。
- 部署脚本、配置、回归和原始结果D:/STGPlanner/benchmarks；新会话工具和报告副本D:/STGPlanner/codex/work、outputs。
- 原始会话工作区：{task.as_posix()}；原outputs保留，迁移时也复制到项目codex/outputs，旧文件不删除。

## 已确认结果和修复

- FAEL原1600秒41.2775%，约415秒后停滞；修复前沿生命周期、XY邻格更新、近点分配一致性、路网更新和不可达2-opt后，repair_formal_fael_01在1017.008s达到95.3366%，1351.931m，停车验收通过。
- GBP2原1600秒41.1789%、1945.54m；01/02中间诊断主动停止，03完整2400.032s仍41.7582%；04修复返航契约后855.756s原生结束，仅41.3186%，后续主动诊断停止；05完整2400.014s仍41.4049%、2343.532m，2116.081s原生返航结束。
- GBP2原生修复：73x6射线缓存维度/末列越界；投影点到物理感知高度及外参；旁侧地面射线漏扣0.5m；LiDAR球坐标超程12.3954->12m；时间预算三元表达式优先级；返航IDL状态2正确传播和适配器仅执行一次返航；聚类收益复制后同步邻节点前沿类型（旧受控用例收益前沿2/类型1，修复2/2）。
- 显式配置校准：采样节点500->2000、边/循环上限4倍，时间模型2/1m/s，原生前沿比例0.05->0.01。公共95%完成阈值不变。这些是本地工程改动，不能称论文原始参数复现。
- 通道冻结地图诊断排除了地面缺失与AdaptiveObb挡住通道。500/2000节点原生服务分别0/3、3/3给出通道前进；125个自由观察点原生前沿比例0.05下0个、0.01下16个有效。它们均为离线诊断，05完整失败已证明其单独不足以完成全程。
- 06与05相比只加聚类类型同步修复；采样随机，单次全程差异不能独立证明该修复的因果贡献。06确已突破41%，但被用户暂停，必须重新完整验证。
- 回归：射线5、FAEL2、感知坐标3、几何/预算10、适配器契约10、前沿校准5、聚类3。对应JSON在benchmarks。最近编译18包通过。

## 公共协议与证据

Scene4独立观察器已知平面面积/7790m²，.4m栅格、12m截断；完成面积>7400.5m²。这不是100%可达区覆盖。机器人映射预热5秒后前进3米再计时。控制器/地形固定；返航、公共完成、时间上限分开记录。公共协议revision3，GBP适配器revision1。
源码/二进制指纹progress_repairs/manifest.json；原生修复9个文件、3个库。driver和gbp2.yaml的允许变更及原始SHA在trial_repairs/manifest.json。每轮native_source_manifest、adapter_config_manifest和配置随结果保存。06还有live_rosparams.yaml确认实际0.01/2000。
06附加只读passive_frontier_audit.jsonl，早期submitted_controller_path标签实际是局部localPlanner的/path候选，不是GBP全局下发路径；后续标签已更正并节流。不要用这些局部候选统计里程或当作原生全局路径。

## 恢复后优先事项

1. 先读RUNBOOK.md；按用户新目标决定是否恢复GBP2，不自动启动。
2. 06改为用户中止的中间证据；07为新正式运行，运行前固定progress_trials.json。当前分析/报告脚本仍选择06，**它们是待整理草稿，不能直接生成“最终完成”报告**。
3. 完整运行后核验原始result、源代码/二进制和实际参数，区别健康检查通过与探索达95%。FAEL结果不需因迁移重复跑。
4. 更新analyze_progress.py对用户中止分类的验收；当前最终分支仅接受coverage_threshold/sim_time_limit，因此06会失败，不能靠放宽最终完成标准糊弄。
5. 生成曲线/地图，人工查看图片；make_progress_report.py、update_progress_docs.py、pandoc更新3份报告。修订模板的最终运行名/中止描述。旧基线原始结果保留。
6. stage_progress.py归档代码/新证据/报告，凭据模式检查、diff --check，提交推送；再建最终标签，verify_progress_remote.py及verify_progress_clone.py核对旧refs、私有性、全部文件SHA；最后bundle和package_progress.py。这些交付尚未执行。

## 多会话约定

主协调/长测会话独占WSL和代码写入；报告会话可读结果/处理独立草稿；新功能会话需独立Git工作树，不能随意切换共享分支。
新会话只加载本文件及当次涉及源码，按需查RUNBOOK/history。每阶段更新本文件，避免长聊天不断追加。
'''
runbook='''# 新会话恢复与协作清单

## 新会话怎么开始

在STGPlanner项目中创建一个**全新会话**，不要复制完整旧聊天。首条可直接粘贴：

> 请先读取D:/STGPlanner/AGENTS.md、D:/STGPlanner/codex/STATUS.md和RUNBOOK.md，只汇报当前状态与本会话负责范围，暂不启动仿真。

用户明确恢复后，实验会话可用：

> 恢复GBP2验证。先读取项目交接文件，保留06用户中止数据，为新一轮分配新运行名，完整验证95%目标后再更新报告和私有分支。

建议按任务开短会话：①算法与长测；②报告与论文对照；③后续新功能。多开本身不会把会话变成共享完整记忆。共享依据是文件、Git、原始结果和简短阶段交接。不要同时让几个会话操作同一仿真、同一代码文件或切同一个工作目录的分支。

## 启动前核对

```powershell
Get-Content D:/STGPlanner/codex/STATUS.md
Get-Content D:/STGPlanner/codex/SIMULATION_LOCK.json
git -C D:/STGPlanner/catkin_ws/src/STGPlanner status --short
git -C D:/STGPlanner/catkin_ws/src/STGPlanner log -4 --oneline
wsl.exe --list --running
```

当前用户已暂停，不要为了执行上述清单自动启动WSL。恢复后检查实际进程，确认没有其他会话持有仿真；再把锁记录state设为running、owner_thread和trial设为本会话。结束后更新为idle/paused，并写结果路径。锁文件是协作约定，不是操作系统强制互斥。

## 用户明确恢复后的长测示例

无需因迁移重新安装。先确认最新代码、原生编译指纹和配置，必要时再编译。每次采用新目录，禁止覆盖06。

```powershell
git -C D:/STGPlanner/catkin_ws/src/STGPlanner branch --show-current
# 修改源码后才按需重建；正在长测时不得执行：
wsl.exe -d STGPlanner-Ubuntu20 -u root -- bash /mnt/d/STGPlanner/benchmarks/build_progress_repairs.sh gbp2
# 必须先确认本专用发行版没有别的会话正在使用，才能终止并重启：
wsl.exe --terminate STGPlanner-Ubuntu20
wsl.exe -d STGPlanner-Ubuntu20 -u root -- bash /mnt/d/STGPlanner/benchmarks/run_benchmark.sh gbp2 --name repair_formal_gbp2_07 --limit 2400
```

运行前固定选择并保存manifest/config。运行后看result.json、metrics.jsonl、events.jsonl、known_plane_cells.csv、原生日志和停车验收，不能只看是否生成路径。06不能从1082秒原地续算正式试验。

## 报告工具位置

D:/STGPlanner/codex/work保留最新未发布工具草稿，D:/STGPlanner/benchmarks有已部署工具。旧对话脚本的相对路径已随codex/work和codex/outputs迁入；使用前读STATUS中的待办，不要无条件批量运行。

完成新正式运行且整理选择文件后：Linux执行analyze_progress.py、plot_progress.py；Windows执行make_progress_report.py --output D:/STGPlanner/codex/outputs，更新旧报告入口，pandoc生成独立HTML；stage_progress.py归档。正式发布前核查模板不再写06为最终完成，所有验证通过。

## 每次交接写什么

只补必要信息：目标/暂停或运行状态、当前分支与提交、修改文件、测试命令与结果、正在运行的PID/试验名、未解决问题、下一步。状态以最新文件和实际进程为准；历史文件不是当前运行指令。

## 官方依据

AGENTS.md用于持久项目指导，官方说明：https://learn.chatgpt.com/docs/agent-configuration/agents-md 。本项目用短AGENTS加独立状态文件，避免将全部实验历史塞入自动加载上下文。迁入项目不能扩大单会话上下文或保证不发生其他中断。
'''
for name,text in [('STATUS.md',status),('RUNBOOK.md',runbook)]:
    (context/name).write_text(text,encoding='utf-8',newline='\n')
    (repo/'project-context'/name).write_text(text,encoding='utf-8',newline='\n')
lock={'state':'paused_by_user','owner_thread':'01a1762b-5903-7a30-b807-9a6950c931be','trial':'repair_formal_gbp2_06','updated_at':now,'runtime_active':False,'note':'No automatic resume; a new explicit user request can resume. Check real processes before claiming ownership.'}
(context/'SIMULATION_LOCK.json').write_text(json.dumps(lock,indent=2),encoding='utf-8',newline='\n')
(repo/'project-context/PAUSED.json').write_text(json.dumps(pause,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
guide='''# STGPlanner项目迁移与多会话使用说明

已将“部署并测试 STGPlanner”迁入已有STGPlanner项目（D盘），侧栏按项目分组。代码、WSL环境和历史结果原路径不变，避免搬动编译环境。项目根已建立简短AGENTS.md；codex/STATUS.md记录最新事实，RUNBOOK.md给出恢复命令和多会话规则；原Git仓库也保存了可版本回滚的交接副本。

改善主要来自**分任务开新的短会话，并通过文件/Git交接**。把原来的长对话移入项目并不会缩短历史，也不会扩大单会话上下文；多个会话不能默认知道彼此的完整聊天。官方AGENTS.md说明：https://learn.chatgpt.com/docs/agent-configuration/agents-md 。

以后打开左侧STGPlanner项目，点新建会话，首条可输入：

> 先读取D:/STGPlanner/AGENTS.md、D:/STGPlanner/codex/STATUS.md和RUNBOOK.md，按最新状态接手本会话任务，暂不启动仿真。

建议分为算法长测、报告论文对照、后续新功能三个主题。当前已按用户要求暂停，不自动创建并启动新的实验任务。需要恢复时，在实验会话明确说“恢复GBP2完整验证”；原长对话留作历史查询即可。

一套WSL/ROS/Gazebo同一时间由一个会话控制；共享Git目录一次只允许一个会话写入/切分支，独立代码工作采用不同工作树。状态文件和锁记录提供协调，不是强制文件锁。

暂停前GBP2第六轮已突破41%，在1082.027仿真秒达到54.153530%，1179.247米；因用户暂停结束，停车检查通过，尚未达到95%。下次须新开完整试验，不能把本轮当作完整2400秒长测或自然完成。最新正式部署报告尚待恢复验证后更新，本次只完成项目迁移和交接配置。

项目内路径：

- 最新交接：D:/STGPlanner/codex/STATUS.md
- 恢复与协作：D:/STGPlanner/codex/RUNBOOK.md
- 当前暂停记录：D:/STGPlanner/codex/PAUSED.json
- 工具草稿/报告副本：D:/STGPlanner/codex/work、outputs
- 真正Git仓库：D:/STGPlanner/catkin_ws/src/STGPlanner
- 最新试验：D:/STGPlanner/benchmarks/results/repair_formal_gbp2_06

原会话工作区和交付全部保留；项目内复制的文件有SHA256迁移清单，不重新安装、不重建场景、不删除旧证据。
'''
(task/'outputs/STGPlanner项目迁移说明.md').write_text(guide,encoding='utf-8',newline='\n')
history=task/'work/PROGRESS_RESUME.md'
if history.exists():
    (context/'history/PRE_MIGRATION.md').write_text('# 历史归档，非当前指令\n\n其中活动进程、权限和待办均可能过期。当前事实只看../STATUS.md。\n\n'+history.read_text(encoding='utf-8'),encoding='utf-8',newline='\n')
    history.write_text('# 当前交接已迁移\n\n用户已主动暂停。请读D:/STGPlanner/codex/STATUS.md与RUNBOOK.md。旧内容仅作为D:/STGPlanner/codex/history/PRE_MIGRATION.md归档，不是当前指令。\n',encoding='utf-8',newline='\n')
copied={}
for source_folder,dest_folder in [(task/'work',context/'work'),(task/'outputs',context/'outputs')]:
    for p in source_folder.iterdir():
        if p.is_file() and (source_folder.name=='outputs' or p.suffix.lower() in ['.py','.sh','.cpp','.ps1','.json','.md','.css','.cmd','.txt']):
            dest=dest_folder/p.name;shutil.copy2(p,dest)
            expected=hashlib.sha256(p.read_bytes()).hexdigest();assert hashlib.sha256(dest.read_bytes()).hexdigest()==expected
            copied[dest.relative_to(project).as_posix()]={'source':str(p),'sha256':expected,'bytes':dest.stat().st_size}
manifest={'copied_at':now,'project_id':'bd16d030-19af-4456-a6f4-fecde2256511','project_root':str(project),'original_workspace_preserved':True,'file_count':len(copied),'files':copied}
(context/'migration_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
(task/'outputs/STGPlanner项目迁移校验.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
# Copy latest staged source-tool drafts; do not generate or label a final test report.
stage=(task/'work/stage_progress.py').read_text(encoding='utf-8')
exec(stage[:stage.index('\ndef gz(')],{'__file__':str(task/'work/stage_progress.py')})
dest=repo/'evidence/scene4-progress-fix/repair_formal_gbp2_06';dest.mkdir(exist_ok=True)
for name in ['result.json','metrics.jsonl','events.jsonl','trajectory.csv','coverage.ufo','interruption.json','user_pause.json','native_source_manifest.json','adapter_config_manifest.json','native_config.yaml','benchmark_trial.py','live_rosparams.yaml']:
    if (trial/name).exists():shutil.copy2(trial/name,dest/name)
for name in ['native_planner.log','known_plane_cells.csv','passive_frontier_audit.jsonl']:
    if (trial/name).exists():
        with (trial/name).open('rb') as src,(dest/(name+'.gz')).open('wb') as raw,gzip.GzipFile(filename='',fileobj=raw,mode='wb',mtime=0) as gz:shutil.copyfileobj(src,gz)
p=repo/'benchmarks/progress_repairs/README.md';s=p.read_text(encoding='utf-8')
s=s.replace('Latest run06 was selected before its outcome and is undergoing real2400s\nverification. Final claims must follow its recorded result. Prior failures remain.',
    'Run06 was stopped at the user request to pause the project:1082.027simulated\nseconds,54.153530%,1179.247m. It crossed the old41% plateau but did not reach95%.\nThis is a user-interrupted attempt, not a completed2400s or native-finished run.\nRead project-context/STATUS.md before resuming. Final release remains pending.')
p.write_text(s,encoding='utf-8',newline='\n')
print(json.dumps({'copied_files':len(copied),'all_copy_hashes_verified':True,'paused_trial':pause},ensure_ascii=False,indent=2))
