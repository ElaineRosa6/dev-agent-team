# 用户指令记忆

本文件记录了用户的指令、偏好和教导，用于在未来的交互中提供参考。

## 格式

### 用户指令条目

- Date: [YYYY-MM-DD]
- Context: [提及的场景或时间]
- Instructions:
  - [用户教导或指示的内容，逐行描述]

### 项目知识条目

- Date: [YYYY-MM-DD]
- Context: Agent 在执行 [具体任务描述] 时发现
- Category: [运维部署|构建编译|排错调试|工作流协作|环境配置]
- Instructions:
  - [具体的知识点，逐行描述]

## 条目

### 项目知识: Sprint Team Plugin 构建编译方式
- Date: 2026-05-21
- Context: Agent 在执行 Sprint Team Plugin Phase 0-5 实施时发现
- Category: 构建编译
- Instructions:
  - 所有脚本编译检查: `python3 -m py_compile sprint-team-plugin/scripts/*.py`
  - 运行全部测试: `python3 sprint-team-plugin/tests/test_workflow_engine.py` && `python3 sprint-team-plugin/tests/test_phase2_3_4.py`
  - Runner 验证: `python3 sprint-team-plugin/scripts/run_sprint.py status` && `python3 sprint-team-plugin/scripts/run_sprint.py next --dry-run`

### 项目知识: Sprint Team Plugin 架构与目录约定
- Date: 2026-05-21
- Context: Agent 在执行 Sprint Team Plugin 实施时发现
- Category: 工作流协作
- Instructions:
  - 插件主体在 `sprint-team-plugin/` 目录下
  - `scripts/` 根目录是开发辅助脚本，逐步向 `sprint-team-plugin/scripts/` 收敛
  - `sprints/` 目录存放开发态状态文件和配置模板
  - `templates/` 存放插件模板(permissions.json, workflow.json, sprint-state.json.template)
  - 测试文件放在 `sprint-team-plugin/tests/`
