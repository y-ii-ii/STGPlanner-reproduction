# 验证证据

`scene4-final/` 是停车与超时修复后完成的最终单轮 20 分钟观察，16 项检查通过。项目累计距离与采集窗口里程计距离口径不同，见报告说明。

`diagnosis/first_long_before_stop_fix.json` 是较早的诊断轮次：虽然旧版 13 项检查标记 passed，复核发现残余角速度命令，故不作为最终停车验收；`first_long_audit_review.json` 明确记录了该限制。

`build/`、`rviz/`、`deployment-tests/`、`environment/` 分别保存构建、RViz/TF/Marker、原部署运行和环境证据。部分历史文件包含当时机器路径或话题名，这是运行记录，不是跨机器默认配置。
