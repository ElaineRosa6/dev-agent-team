# Sprint Team Plugin 实施计划

> 记录时间：2026-05-21  
> 项目前提：本仓库本身就是 Claude Code 插件项目，`sprint-team-plugin/` 是插件主体。  
> 目标：把现有“文档约定型工作流”推进为“可执行、可校验、可恢复、可审计”的插件系统。

---

## 一、当前判断

### 1. 项目定位

本项目是一个面向 Claude Code 的循环迭代研发团队插件。它通过 Commands、Agents、Skills、Hooks、Scripts 组合出 6 个研发角色和 5 阶段 Sprint 工作流。

核心角色：

| 角色 | 职责 |
|------|------|
| 产品架构师 | 需求澄清、MVP 边界、架构切片 |
| 安全切片规划师 | 变更拆分、依赖排序、回滚方案 |
| 代码审查专家 | 四维度代码审查 |
| 架构审计师 | 架构合理性、业务闭环、完成度审计 |
| 自动修复工程师 | 按审查报告做受限修复 |
| 运维管家 | 迭代启动、收尾、归档、总结 |

目标流程：

```text
/sprint-start
  -> 阶段零：迭代启动
  -> 阶段一：架构规划 + 安全切片
  -> 阶段二：代码实现（当前由人类完成）
/sprint-review
  -> 阶段三：代码审查 + 架构审计
/sprint-fix（如需）
  -> 阶段四：修复规划 + 自动修复 + 回归审查
/sprint-close
  -> 阶段五：迭代收尾
```

### 2. 当前成熟度

现状可以概括为：

```text
设计完成度高，执行闭环不足。
```

已经存在：

- 完整角色设定
- 工作流文档
- 插件目录骨架
- command 文档
- agent/skill 定义
- hooks 配置
- guard/validator/state-sync 脚本
- sprint 状态文件
- 深度 QA 和风险分析文档

尚未真正落地：

- 编排引擎 `run_sprint.py`
- 可执行状态机
- 失败恢复
- 超时、重试、降级
- trace_id 链路追踪
- 结构化事件日志
- 白名单权限引擎
- 测试/lint/build 验证闭环
- prompt/agent/skill 单一来源管理

---

## 二、设计原则

### 1. 插件主体优先

既然本仓库本身就是插件项目，后续实现应以 `sprint-team-plugin/` 为主目录。

建议定位：

```text
sprint-team-plugin/     插件运行时主体
docs/                   项目分析、设计、实施记录
sprints/                示例/开发态状态与配置，可作为插件默认模板来源
scripts/                开发辅助脚本，逐步减少或迁移
```

长期目标：

- 运行时脚本只保留在 `sprint-team-plugin/scripts/`
- 根目录 `scripts/` 不再和插件脚本重复
- 插件安装后应能独立运行，不依赖根目录重复文件

### 2. 控制平面先于智能能力

先做可靠的 runner、状态机、日志和权限，再做项目感知、棕地入口、健康评分等高级能力。

原因：

- 没有状态机，Agent 行为无法恢复
- 没有日志，失败无法定位
- 没有权限白名单，自动化越强风险越高
- 没有测试验证，自动修复只是 LLM 自评

### 3. 文档约定必须下沉为硬逻辑

已有文档中的规则不能只停留在 prompt 层。需要进入配置、脚本和测试。

示例：

| 文档约定 | 应落地位置 |
|----------|------------|
| 角色只能写指定目录 | `permissions.json` + `permission-guard.py` |
| 阶段顺序固定 | `workflow.json` + runner |
| 阶段失败可重试 | `sprint-state.json` + runner |
| 修复必须验证 | `code-validator.py` + runner |
| 紧急通道必须补审查 | state mode + runner gate |

### 4. LLM 负责意图翻译，传统代码负责硬判断

安全切片、架构审计、自动修复都涉及逻辑判断。应避免把所有判断交给 LLM。

建议分工：

- LLM：解释需求、总结报告、生成候选计划
- 脚本：状态流转、依赖检查、路径权限、输出结构校验、测试执行
- 人类：架构门控、高风险修复确认、紧急模式确认

---

## 三、目标架构

### 1. 推荐目录结构

```text
dev-agent-team/
├── sprint-team-plugin/
│   ├── .claude-plugin/
│   │   └── plugin.json
│   ├── commands/
│   │   ├── sprint-start.md
│   │   ├── sprint-review.md
│   │   ├── sprint-fix.md
│   │   ├── sprint-close.md
│   │   ├── sprint-status.md
│   │   ├── brownfield-start.md        # P2 新增
│   │   └── sprint-health.md           # P2 新增
│   ├── agents/
│   ├── skills/
│   ├── hooks/
│   │   └── hooks.json
│   ├── scripts/
│   │   ├── run_sprint.py              # P0 新增
│   │   ├── workflow_engine.py         # P0 新增
│   │   ├── state_store.py             # P0 新增
│   │   ├── event_log.py               # P1 新增
│   │   ├── permission-guard.py
│   │   ├── command-guard.py
│   │   ├── delete-guard.py
│   │   ├── artifact-validator.py      # 替代/拆分 output-validator
│   │   ├── quality-validator.py       # P1 新增
│   │   ├── code-validator.py          # P1 新增
│   │   ├── sprint-state-sync.py
│   │   ├── project-scanner.py         # P2 新增
│   │   ├── baseline-snapshot.py       # P2 新增
│   │   └── health-calculator.py       # P2 新增
│   ├── templates/
│   │   ├── sprint-state.json.template
│   │   ├── permissions.json
│   │   └── workflow.json              # P0 新增
│   └── tests/
│       ├── test_workflow_engine.py
│       ├── test_permission_guard.py
│       ├── test_artifact_validator.py
│       └── fixtures/
├── docs/
│   └── analysis/
├── sprints/
│   ├── sprint-state.json             # 开发态/示例状态
│   ├── config/
│   ├── prompts/
│   └── logs/
└── scripts/
    └── dev-only 工具，逐步清理重复脚本
```

### 2. 单一来源策略

当前存在多份角色定义：

- 根目录 `01-产品架构师.md` 等
- `sprints/prompts/*.md`
- `sprint-team-plugin/agents/*.md`
- `sprint-team-plugin/skills/*/SKILL.md`

建议短期保留现状，但新增同步规则：

```text
插件运行时以 sprint-team-plugin/agents 和 sprint-team-plugin/skills 为准。
根目录角色文档视为历史参考，后续归档到 docs/reference/。
sprints/prompts 用作开发态 prompt 模板，最终应与插件模板合并。
```

中期目标：

```text
sprint-team-plugin/roles/
  product-architect.md
  slice-planner.md
  code-reviewer.md
  architecture-auditor.md
  auto-fix-engineer.md
  devops-manager.md
```

再由脚本生成 agents/skills 或由 agents/skills 引用 roles 内容。

---

## 四、分阶段实施计划

## Phase 0：可运行性修复

目标：修复当前会直接导致插件脚本不可用的问题。

优先级：P0  
预计耗时：0.5 天

### 任务

1. 修复两份 `output-validator.py` 的语法错误
2. 修复 `sprint-state-sync.py` 的 docs 路径拼接错误
3. 修复 `hooks.json` 中 `CLUADE_TOOL_INPUT` 拼写错误
4. 修正 `README.md` 中 Commands 数量错误
5. 明确根目录 `scripts/` 与插件 `scripts/` 的关系

### 验收标准

```text
python3 -m py_compile sprint-team-plugin/scripts/*.py
python3 -m py_compile scripts/*.py
```

全部通过。

---

## Phase 1：最小控制平面

目标：实现最小可用 runner，让工作流从文档约定变成可执行状态机。

优先级：P0  
预计耗时：1.5 天

### 任务

1. 新增 `sprint-team-plugin/scripts/run_sprint.py`
2. 新增 `sprint-team-plugin/scripts/workflow_engine.py`
3. 新增 `sprint-team-plugin/scripts/state_store.py`
4. 新增 `sprint-team-plugin/templates/workflow.json`
5. 扩展 `sprint-state.json.template`

### 最小状态模型

```json
{
  "sprint_id": "sprint-001",
  "status": "initialized",
  "mode": "normal",
  "current_phase": "zero",
  "phases": {
    "zero": {
      "status": "pending",
      "role": "devops-manager",
      "started_at": null,
      "completed_at": null,
      "failed_at": null,
      "failure_reason": null,
      "retry_count": 0,
      "max_retries": 2,
      "artifacts": []
    }
  }
}
```

### 状态流转

```text
pending -> running -> completed
running -> failed
failed -> retrying -> running
failed -> escalated
pending -> skipped
```

### runner 第一版能力

- 读取状态
- 读取 workflow 配置
- 显示当前阶段
- 校验阶段是否可执行
- 标记阶段 running/completed/failed
- 记录失败原因
- 检查必需产物是否存在
- 给出下一阶段建议

第一版不强求自动调用 Claude。先把状态推进做实。

### 验收标准

- 可以通过命令推进一个模拟 Sprint
- 任意阶段失败后状态中有失败原因
- 重新执行时能识别当前阶段
- 缺少必需产物时不能标记完成

---

## Phase 2：权限白名单与 Guard 重构

目标：把 guard 从硬编码黑名单升级为配置驱动白名单。

优先级：P0  
预计耗时：1 天

### 任务

1. `permission-guard.py` 改为读取 `permissions.json`
2. 增加路径规范化，避免简单前缀匹配绕过
3. 增加角色缺失时的默认策略
4. 增加命令白名单能力
5. 对 `auto-fix-engineer` 单独限制可写文件列表

### 默认策略

建议：

```text
无当前角色：
  开发模式可放行，但记录 warning
  插件运行模式默认 deny

未知角色：
  deny

路径不在 allowed_dirs：
  deny

扩展名不在 allowed_file_extensions：
  deny
```

### 验收标准

- 角色配置只改 `permissions.json` 即可生效
- 路径穿越、相对路径、大小写差异都被规范化处理
- 产品架构师无法写代码文件
- 自动修复工程师无法写未授权目录
- 所有阻断事件写入结构化日志

---

## Phase 3：结构化日志与 Trace

目标：让每次阶段执行、guard 拦截、校验失败都有可追踪记录。

优先级：P1  
预计耗时：1 天

### 任务

1. 新增 `event_log.py`
2. 新增 `trace_id` 生成规则
3. runner 写 `sprints/logs/events.jsonl`
4. guard 写 `sprints/logs/guard.jsonl`
5. validator 写 `sprints/logs/validation.jsonl`

### trace_id 格式

```text
{sprint_id}:{phase}:{role}:{timestamp}:{short_uuid}
```

示例：

```text
sprint-001:three_review:code-reviewer:20260521-103000:a1b2c3
```

### 事件格式

```json
{
  "time": "2026-05-21T10:30:00+08:00",
  "trace_id": "sprint-001:three_review:code-reviewer:20260521-103000:a1b2c3",
  "sprint_id": "sprint-001",
  "phase": "three_review",
  "role": "code-reviewer",
  "event": "phase_failed",
  "status": "failed",
  "reason": "missing required artifact docs/reviews/code-review.md"
}
```

### 验收标准

- 任意阶段失败可通过 trace_id 找到相关事件
- guard 拦截次数可被统计
- validation warning 不再只写自由文本

---

## Phase 4：Validator 拆分与质量校验

目标：把“有没有文件”升级为“结构合格 + 内容基本可信 + 代码可验证”。

优先级：P1  
预计耗时：1.5 天

### 任务

1. 将 `output-validator.py` 拆为：
   - `artifact-validator.py`
   - `quality-validator.py`
   - `code-validator.py`
2. artifact validator 检查：
   - 目录
   - 扩展名
   - 必需章节
   - 最小长度
   - 文件名规则
3. quality validator 检查：
   - TODO/占位符
   - 空洞章节
   - 重复段落
   - “后续补充”等无效承诺
   - 只列问题不写建议
4. code validator 检查：
   - 测试命令
   - lint 命令
   - build 命令

### 策略

```text
PostToolUse 不直接阻断 Claude 工具调用，但必须：
  1. 写 validation 事件
  2. 更新 phase validation 状态
  3. runner gate 不允许未通过校验的阶段进入 completed
```

### 验收标准

- 伪报告不能让阶段完成
- 缺少必需章节不能让阶段完成
- 自动修复阶段未运行验证不能标记完成

---

## Phase 5：测试体系

目标：给插件基础设施加最小回归测试，防止脚本和配置漂移。

优先级：P1  
预计耗时：1 天

### 测试范围

```text
sprint-team-plugin/tests/
├── test_workflow_engine.py
├── test_state_store.py
├── test_permission_guard.py
├── test_artifact_validator.py
├── test_event_log.py
└── fixtures/
```

### 必测场景

- 状态合法流转
- 状态非法流转被拒绝
- 阶段失败后可重试
- 角色权限匹配
- 越权路径被拒绝
- 必需章节缺失被识别
- trace 事件写入成功

### 验收标准

```text
python3 -m pytest sprint-team-plugin/tests
```

全部通过。

---

## Phase 6：项目感知与棕地入口

目标：支持已有项目 + 问题清单的入口。

优先级：P2  
预计耗时：2 天

### 任务

1. 新增 `/brownfield-start`
2. 新增 `project-scanner.py`
3. 新增 `issue-analyzer.py` 或对应 agent
4. 新增扫描产物：

```text
docs/project-scan/
  project-map.md
  tech-stack.json
  entrypoints.json
  risk-summary.md
```

### project-scanner 第一版能力

- 扫描目录结构
- 识别语言和框架
- 识别包管理器
- 识别测试命令候选
- 识别入口文件
- 识别高风险目录
- 输出项目摘要

### brownfield-start 流程

```text
用户输入问题清单
  -> project-scanner 生成项目画像
  -> issue-analyzer 分类问题
  -> slice-planner 输出修复切片
  -> 用户 gate
```

### 验收标准

- 对已有项目能生成稳定项目画像
- 问题清单能被分类为 P0/P1/P2/P3
- 输出修复计划前必须经过用户确认

---

## Phase 7：健康评分、债务账本与基线快照

目标：支持跨迭代治理，不让 P2/P3 和架构漂移无限堆积。

优先级：P2  
预计耗时：2 天

### 任务

1. 新增技术债务账本：

```text
sprints/debt/ledger.json
```

2. 新增基线快照：

```text
sprints/baselines/sprint-{N}-baseline.json
```

3. 新增健康评分：

```text
sprints/logs/metrics/sprint-{N}-metrics.json
```

### 健康评分输入

- P0/P1 未解决数
- P2/P3 超期数
- 测试是否通过
- lint 是否通过
- guard 拦截趋势
- validation 失败次数
- 阶段重试次数
- 人工介入次数
- 基线漂移度

### 硬约束建议

```text
health_score < 60:
  禁止进入新功能 sprint
  强制建议稳定性迭代

存在 P0:
  禁止 sprint-close completed

P1 超过 1 轮未处理:
  自动升级为阻断项
```

---

## 五、实施顺序总览

| 阶段 | 优先级 | 目标 | 预计耗时 |
|------|--------|------|----------|
| Phase 0 | P0 | 修复现有脚本可运行性 | 0.5 天 |
| Phase 1 | P0 | 最小 runner + 状态机 | 1.5 天 |
| Phase 2 | P0 | 白名单权限与 guard 重构 | 1 天 |
| Phase 3 | P1 | 结构化日志与 trace | 1 天 |
| Phase 4 | P1 | validator 拆分与质量校验 | 1.5 天 |
| Phase 5 | P1 | 基础测试体系 | 1 天 |
| Phase 6 | P2 | 项目感知与棕地入口 | 2 天 |
| Phase 7 | P2 | 健康评分、债务账本、基线快照 | 2 天 |

总计约 10.5 天。

建议先执行 Phase 0 到 Phase 2，形成一个稳定的插件基础版本。

---

## 六、关键取舍

### 1. 暂不优先做完整自动编排

第一版 runner 不需要自动调用 Claude。先保证状态推进、产物校验、失败恢复可用。

原因：如果一开始就接全自动 LLM 调用，问题会混在一起，难以判断是状态机错误、prompt 错误、权限错误，还是模型输出错误。

### 2. 暂不让自动修复工程师做新功能

自动修复工程师只处理审查报告中的明确问题。新功能实现应未来单独设计“实现工程师”角色，并进入沙盒验证。

### 3. 暂不做仪表盘

先落 JSONL 事件日志和每轮 metrics 文件。仪表盘只有在日志结构稳定后才值得做。

### 4. 不继续扩大重复文档

新增文档应集中在 `docs/analysis/` 或未来 `docs/design/`。角色定义应逐步收敛到插件目录内。

---

## 七、近期可执行清单

### Sprint A：插件基础稳定化

范围：Phase 0 + Phase 1

交付物：

- 修复当前脚本语法和路径问题
- 新增最小 `run_sprint.py`
- 新增 `workflow.json`
- 扩展状态模板
- runner 可推进模拟状态

验收：

```text
python3 -m py_compile sprint-team-plugin/scripts/*.py
python3 sprint-team-plugin/scripts/run_sprint.py status
python3 sprint-team-plugin/scripts/run_sprint.py next --dry-run
```

### Sprint B：权限与日志硬化

范围：Phase 2 + Phase 3

交付物：

- guard 配置化
- 结构化事件日志
- trace_id
- guard/validation 事件 JSONL

验收：

```text
越权写入被拒绝
合法写入被允许
所有拒绝事件可在 logs 中查询
任意 phase 事件带 trace_id
```

### Sprint C：质量门控

范围：Phase 4 + Phase 5

交付物：

- validator 拆分
- 基础测试套件
- 自动修复阶段验证命令接入

验收：

```text
伪报告不能过 gate
缺章节不能过 gate
测试失败不能关闭自动修复阶段
pytest 全部通过
```

---

## 八、完成标准

基础版插件完成标准：

1. 插件安装后 command/agent/skill/hook 路径完整
2. 所有 Python 脚本可通过编译
3. runner 能读取和推进 sprint 状态
4. 阶段失败可记录、重试、升级
5. guard 使用配置驱动权限
6. validator 能阻止不合格产物进入 completed
7. 所有关键动作有结构化日志
8. 自动修复阶段至少能运行配置中的验证命令
9. 基础测试覆盖状态机、权限、校验、日志

达到以上标准后，再进入棕地入口、健康评分、债务账本等增强能力。

