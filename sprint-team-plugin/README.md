# sprint-team-plugin

循环迭代研发团队 Agent 团队 Plugin，适用于 Claude Code。

## 组件

| 组件 | 说明 |
|------|------|
| Commands (5) | `/sprint-start` `/sprint-review` `/sprint-fix` `/sprint-close` `/sprint-status` |
| Agents (6) | 产品架构师、安全切片规划师、代码审查专家、架构审计师、自动修复工程师、运维管家 |
| Skills (6) | 各角色工作流指令，自动加载 |
| Hooks (5) | 权限拦截、危险命令拦截、删除拦截、输出校验、状态同步 |
| Scripts (5) | Python 编排引擎和 Hook 脚本 |

## 安装

### 方式一：本地安装

```bash
cd /path/to/project
/plugin install /path/to/sprint-team-plugin
```

### 方式二：Git 仓库安装

```bash
/plugin install git@github.com:your-org/sprint-team-plugin.git
```

## 使用

### 启动迭代

```
/sprint-start
```

### 代码完成后触发审查

```
/sprint-review
```

### 进入修复阶段

```
/sprint-fix
```

### 迭代收尾

```
/sprint-close
```

### 查看状态

```
/sprint-status
```

## 目录结构

```
sprint-team-plugin/
├── .claude-plugin/
│   └── plugin.json          # 插件配置
├── commands/
│   ├── sprint-start.md      # 启动迭代
│   ├── sprint-review.md     # 代码审查
│   ├── sprint-fix.md        # 修复阶段
│   ├── sprint-close.md      # 迭代收尾
│   └── sprint-status.md     # 查看状态
├── agents/
│   ├── product-architect.md
│   ├── slice-planner.md
│   ├── code-reviewer.md
│   ├── architecture-auditor.md
│   ├── auto-fix-engineer.md
│   └── devops-manager.md
├── skills/
│   ├── product-architect/SKILL.md
│   ├── slice-planner/SKILL.md
│   ├── code-reviewer/SKILL.md
│   ├── architecture-auditor/SKILL.md
│   ├── auto-fix-engineer/SKILL.md
│   └── devops-manager/SKILL.md
├── hooks/
│   └── hooks.json
└── scripts/
    ├── run_sprint.py          # 编排引擎
    ├── permission-guard.py    # 权限拦截
    ├── command-guard.py       # 危险命令拦截
    ├── delete-guard.py        # 删除拦截
    ├── output-validator.py    # 输出校验
    └── sprint-state-sync.py   # 状态同步
```

## 工作流

```
/sprint-start → 阶段零→一 → 门控确认 → 代码实现 → 
/sprint-review → 阶段三 → 决策 → 
/sprint-fix（如需）→ 阶段四 → 回归审查 → 
/sprint-close → 阶段五 → 迭代总结
```

## Hooks 说明

| Hook | 触发时机 | 作用 |
|------|---------|------|
| permission-guard | Write/Edit 前 | 检查角色权限，越权写入则阻断 |
| command-guard | Bash 前 | 拦截危险命令 |
| delete-guard | Bash 前 | 拦截删除操作 |
| output-validator | Write/Edit 后 | 验证输出文件内容，记录到日志 |
| sprint-state-sync | Bash 后 | 自动同步产出物到状态文件 |

## 权限隔离

| 角色 | 可写目录 | 禁止操作 |
|------|---------|---------|
| 产品架构师 | docs/architecture/ | 修改代码、删除文件 |
| 安全切片规划师 | docs/plans/ | 修改代码、删除文件 |
| 代码审查专家 | docs/reviews/ | 修改代码 |
| 架构审计师 | docs/audits/ | 修改代码 |
| 自动修复工程师 | docs/fixes/ + 代码 | 删除文件、引入新依赖 |
| 运维管家 | docs/iterations/ | 删除代码文件 |
