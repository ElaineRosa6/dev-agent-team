# Sprint Orchestrator - 研发团队编排系统

## 架构

```
剧本（Prompt） + 导演（编排器） + 舞台限制（权限隔离） = 可靠的研发团队
```

| 组件 | 职责 | 文件 |
|------|------|------|
| 状态机 | 管理流程状态和产物 | `sprints/sprint-state.json` |
| 编排脚本 | 调度角色、校验输出、门控确认 | `run_sprint.py` |
| Prompt 模板 | 各角色的工作指令 | `sprints/prompts/*.md` |
| 权限配置 | 限制每个角色的操作范围 | `sprints/config/permissions.json` |

## 目录结构

```
├── run_sprint.py                    # 编排脚本（入口）
├── sprints/
│   ├── sprint-state.json            # 状态机
│   ├── prompts/                     # 角色 Prompt 模板
│   │   ├── product-architect.md
│   │   ├── slice-planner.md
│   │   ├── code-reviewer.md
│   │   ├── architecture-auditor.md
│   │   ├── auto-fix-engineer.md
│   │   └── devops-manager.md
│   └── config/
│       └── permissions.json         # 权限配置
└── docs/                            # 输出文档
    ├── architecture/                # 架构计划
    ├── plans/                       # 执行计划
    ├── reviews/                     # 审查报告
    ├── audits/                      # 审计报告
    ├── fixes/                       # 修复报告
    └── iterations/                  # 迭代文档
```

## 使用方式

### 前置条件

1. 安装 Claude Code CLI
2. 确保 Python 3.8+ 可用

### 启动 Sprint

```bash
python run_sprint.py
```

### 流程

```
阶段零(运维管家) → 阶段一(产品架构师→安全切片规划师) → 
阶段二(人类开发) → 阶段三(代码审查专家→架构审计师) → 
阶段四(如需修复) → 阶段五(运维管家)
```

### 每个阶段

1. **构建 Prompt** - 根据状态和角色拼接 Prompt
2. **门控确认** - 打印阶段信息，等待用户输入 y
3. **执行** - 调用 `claude --prompt` 执行
4. **校验** - 检查输出文件是否符合预期
5. **更新状态** - 标记阶段完成，进入下一阶段

### 重置 Sprint

```bash
cp sprints/sprint-state.json.template sprints/sprint-state.json
```

## 状态机流转

```
zero (pending) → one_architect (pending) → one_planner (pending) →
two_implementation (pending) → three_review (pending) → three_audit (pending) →
[决策：有 P0/P1？]
  ├── 是 → four_fix_plan → four_fix_execute → four_regression → five_summary
  └── 否 → five_summary
```

## 权限隔离

每个角色有严格的权限限制：

| 角色 | 可写目录 | 可操作 | 禁止操作 |
|------|---------|--------|---------|
| 产品架构师 | docs/architecture/ | 读、写文档 | 修改代码、删除文件 |
| 安全切片规划师 | docs/plans/ | 读、写文档 | 修改代码、删除文件 |
| 代码审查专家 | docs/reviews/ | 读源码、写文档 | 修改代码 |
| 架构审计师 | docs/audits/ | 读、写文档 | 修改代码 |
| 自动修复工程师 | docs/fixes/ + 代码 | 修改指定文件 | 删除文件、引入新依赖 |
| 运维管家 | docs/iterations/ | 读、写文档 | 删除代码文件 |

## 门控确认

关键节点需要用户确认：

- 阶段一完成后：确认架构计划
- 阶段二：等待人类开发完成
- 阶段三后：确认是否进入修复
- 执行失败时：确认是否重试
- 校验失败时：确认是否继续

## 输出校验

每个角色完成后，脚本自动校验：

1. 文件是否生成在正确目录
2. 文件名是否匹配预期模式
3. 内容是否包含必要章节
4. 文件长度是否合理

校验失败会暂停并等待用户确认。

## 自定义

### 添加新角色

1. 在 `sprints/prompts/` 创建 `<role>.md`
2. 在 `ROLE_OUTPUT_CONFIG` 添加配置
3. 在 `permissions.json` 添加权限配置

### 修改流程

编辑 `PHASE_FLOW` 列表，调整阶段顺序。

### 修改校验规则

编辑 `ROLE_OUTPUT_CONFIG` 中的 `required_sections`。
