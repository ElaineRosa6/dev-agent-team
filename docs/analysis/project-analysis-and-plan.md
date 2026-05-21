# Sprint Team 项目分析与改进计划

> 记录时间：2026-05-21
> 核心前提：大模型和 Agent 必然会在某些具体问题上出错翻车，这是系统特性而非 Bug。所有设计必须基于"翻车也翻不死"的原则。

---

## 一、项目现状

### 项目定位

基于 Claude Code CLI 的多 Agent 编排系统，模拟完整软件研发团队。6 个角色协作实现从需求到交付的循环迭代开发流程。

### 核心组件

| 组件 | 文件 | 作用 |
|------|------|------|
| 状态机 | `sprints/sprint-state.json` | 管理流程阶段、角色、产物状态 |
| 编排引擎 | `sprint-team-plugin/scripts/run_sprint.py` | 调度角色、校验输出、门控确认 |
| Prompt 模板 | `sprints/prompts/*.md` | 6 个角色的工作指令 |
| 权限配置 | `sprints/config/permissions.json` | 限制每个角色的操作范围 |
| 插件系统 | `sprint-team-plugin/` | Commands + Agents + Skills + Hooks |
| Guard 脚本 | `scripts/*.py` | 权限拦截、命令拦截、输出校验 |

### 6 个角色

| 角色 | 阶段 | 可写范围 |
|------|------|---------|
| 产品架构师 | 阶段一 | `docs/architecture/` (只写 Markdown) |
| 安全切片规划师 | 阶段一/四 | `docs/plans/` (只写 Markdown) |
| 代码审查专家 | 阶段三 | `docs/reviews/` (读源码、写报告) |
| 架构审计师 | 阶段三 | `docs/audits/` (读项目、写报告) |
| 自动修复工程师 | 阶段二/四 | `docs/fixes/` + 代码 (唯一可改代码的角色) |
| 运维管家 | 阶段零/五 | `docs/iterations/` (只写 Markdown) |

### 5 阶段工作流

```
阶段零(迭代启动) → 阶段一(架构规划) → 阶段二(代码实现-人类) →
阶段三(代码审查) → [有P0/P1?] → 是: 阶段四(安全修复) → 阶段五(迭代收尾)
                                      → 否: 直接阶段五
```

---

## 二、发现的问题与缺口

### 问题 1：没有项目感知层

**现状**：所有角色 Prompt 的输入变量（`{{REQUIREMENTS}}`、`{{CONTEXT}}`、`{{TECH_STACK}}`）都需要用户手动提供。Agent 不会自动扫描项目结构、识别技术栈、理解已有代码。

**表现**：给一个已经开发了一半的项目，Agent 像新同事一样完全依赖用户喂上下文。

### 问题 2：多轮迭代中债务堆积

**缺口**：
- `sprint-state.json` 只有当期阶段状态，没有跨迭代问题追踪
- P2/P3 问题被无限推迟，永不清算
- 没有"技术债务账本"机制

### 问题 3：LLM 随机性导致的错误累积

**缺口**：
- 没有基线快照对比，无法检测 N 轮迭代后的系统漂移
- 没有模型错误检测（伪实现、半完成函数、错误注释）
- 没有健康评分系统来决定是否需要稳定性迭代

### 问题 4：缺少棕地（Brownfield）入口

**现状**：所有 prompt 都假设从零开始。`/sprint-start` 会询问用户需求，不会先扫描项目现状。

**需求**：给一个已有项目 + 问题清单，Agent 应该能自动：
1. 扫描项目理解现状
2. 对比用户描述的问题 + 自主发现的问题
3. 做问题分类、依赖分析、优先级排序
4. 输出修复规划

---

## 三、"必然翻车"前提下的 8 个脆弱点

### 脆弱点 1：没有任何超时和重试机制

**现状**：Hook 脚本直接 `python3 scripts/xxx.py`，没有超时。Guard 脚本挂了没有 fallback。

**翻车场景**：Guard 脚本因 Python 环境问题 hang 住 → 整个 Claude Code 会话被卡死 → 静默死亡。

### 脆弱点 2：Guard 是脆弱的黑名单模式

**现状**：
- `command-guard.py` 只拦截 15 个硬编码的危险命令
- `delete-guard.py` 只拦截 6 个删除命令
- `permission-guard.py` 只做路径前缀匹配

**翻车场景**：模型生成 `shutil.rmtree()` 或 `cat /dev/null > file` → Guard 只检查 Bash 命令，不检查代码执行 → 绕过了。

**本质**：黑名单模式注定有遗漏。这是"假定不会翻车"的思维。

### 脆弱点 3：output-validator 只校验"有没有"，不校验"对不对"

**现状**：检查文件包含必要章节标题 + 长度超过最小值。不检查内容质量、不检查伪实现、不检查代码能否编译。PostToolUse exit(0) 不阻断，只写日志。

**翻车场景**：模型生成 5000 字废话报告，包含所有必要章节 → 校验通过 → 校验失败被吞掉了。

### 脆弱点 4：状态机没有错误恢复

**现状**：只有 `pending/completed/skipped` 三种状态，没有 `failed` 状态，没有错误原因记录，没有重试计数。

**翻车场景**：某阶段执行一半崩溃 → 状态永远卡在 `pending` → 下次启动不知道是"没做"还是"做失败了"。

### 脆弱点 5：没有 trace_id，没有链路追踪

**现状**：`sprint-state.json` 的 `logs` 是空数组。没有 trace 机制。不知道产物是哪个角色哪次调用生成的。

**翻车场景**：发现架构计划写错了 → 不知道是第几次调用出的错 → 无法复现 → 无法根因分析。

### 脆弱点 6：Agent 间是逻辑隔离，不是物理隔离

**现状**：6 个角色共享同一个 Claude Code 会话。权限靠 Guard 脚本拦截，所有角色在同一进程上下文。

**翻车场景**：角色 A 的错误假设污染后续所有角色 → 没有会话隔离 → 一个跑飞，全盘跑飞。

### 脆弱点 7：Prompt 是散落文件，没有版本化管理

**现状**：`sprints/prompts/*.md` 和 `sprint-team-plugin/agents/*.md` 各有一份，内容可能不一致。没有版本号、没有校验和、没有变更日志。

**翻车场景**：改了 Prompt 忘了同步插件版本 → 两种行为不一致 → 无法回退 → 无法 A/B 测试。

### 脆弱点 8：没有强制的迭代比例分配

**现状**：工作流文档建议了迭代节奏，但不是强制约束。没有机制阻止连续 10 轮只做新功能。没有"债务上限"。

**翻车场景**：业务压力下永远做新功能 → 技术债务指数增长 → 系统在某次迭代后突然不可维护。

---

## 四、防御式架构改造建议

### 改造 1：超时 + 重试退避 + 降级

```
所有 LLM 调用：
  timeout: 600s
  retries: 3
  backoff: exponential (30s → 60s → 120s)
  fallback: 返回结构化错误 → "能力边界，转人工"

所有 Guard 脚本：
  timeout: 5s
  fallback: 超时/崩溃 → 默认 DENY（宁可误拦不可漏放）
```

### 改造 2：白名单 + 能力边界声明

反转策略，从黑名单改为白名单：

```
每个角色声明自己的能力边界：

产品架构师：
  CAN_DO: ["读取项目结构", "输出 Markdown 架构文档"]
  CANNOT_DO: ["修改代码", "执行命令", "删除文件"]
  CAPABILITY_BOUNDARY: "只理解架构，不验证代码可实现性"

安全切片规划师：
  CAN_DO: ["读取架构计划", "输出执行切片"]
  CANNOT_DO: ["直接修改代码", "执行命令"]
  CAPABILITY_BOUNDARY: "只规划步骤，不判断代码质量"

白名单之外的操作，默认 DENY。不再依赖黑名单的完整性。
```

### 改造 3：质量校验而非存在性校验

```
output-validator.py 增强：

1. 内容质量检查：
   - 检测"伪实现"模式：pass、TODO、raise NotImplementedError
   - 检测"废话"模式：连续空行、重复段落、占位符文本
   - 检测报告是否只列问题没有修复建议

2. 代码检查（针对 auto-fix-engineer）：
   - 修改后的代码是否能通过编译/lint
   - 测试是否通过
   - 是否引入了新的 import

3. 校验失败必须阻断（而非只写日志）：
   - PreToolUse 校验：exit(2) 阻断
   - PostToolUse 校验：标记 failed 状态，暂停流程
```

### 改造 4：状态机增加失败恢复

```json
{
  "phases": {
    "three_review": {
      "status": "failed",
      "failure_reason": "LLM timeout after 600s",
      "retry_count": 2,
      "max_retries": 3,
      "last_error": "...",
      "failed_at": "2026-05-21T10:30:00Z",
      "gate_check": false
    }
  }
}

状态流转：
  pending → running → completed
  pending → running → failed → retry → running → ...
  failed (retry_count >= max_retries) → escalated (转人工)
```

### 改造 5：全链路 trace_id

```
每次角色调用生成 trace_id：
  sprint-001:three_review:20260521-103000:uuid-abc123

每个 trace 记录：
  {
    "trace_id": "...",
    "sprint_id": "sprint-001",
    "phase": "three_review",
    "role": "code-reviewer",
    "prompt_file": "sprints/prompts/code-reviewer.md",
    "prompt_hash": "sha256:...",
    "input_summary": "代码审查：3 个文件，约 500 行",
    "output_file": "docs/reviews/code-review.md",
    "output_hash": "sha256:...",
    "started_at": "...",
    "completed_at": "...",
    "status": "completed|failed|timeout",
    "retry_count": 0,
    "model_used": "claude-sonnet-4-6",
    "tokens_used": 12000
  }

存储：sprints/logs/traces/sprint-001-traces.jsonl
```

### 改造 6：会话隔离 + 单点不崩溃

```
每个角色独立会话：
  - 产品架构师完成后，只输出产物文件
  - 安全切片规划师启动新会话，只读产物文件，不继承前一个角色的上下文
  - 上下文传递靠文件，不靠会话记忆

故障隔离：
  - 某个角色跑飞 → 只影响该阶段产物
  - 后续阶段可以检测到产物质量不合格 → 暂停
  - 不会雪崩到整个 sprint
```

### 改造 7：Prompt 版本化管理

```
sprints/prompts/
├── .prompt-versions.json     # 版本索引
├── product-architect/
│   ├── v1.0.0.md
│   └── v1.1.0.md
└── slice-planner/
    └── v1.0.0.md

.prompt-versions.json:
{
  "product-architect": {
    "current": "v1.1.0",
    "history": [
      { "version": "v1.0.0", "date": "2026-05-21", "change": "初始版本" },
      { "version": "v1.1.0", "date": "2026-05-25", "change": "修复了过度设计倾向" }
    ]
  }
}
```

---

## 五、翻车指标与可观测性埋点

### 翻车指标（Crash Metrics）

| 指标 | 计算方式 | 告警阈值 | 含义 |
|------|---------|---------|------|
| **人工介入率** | 人工确认或干预次数 / 总阶段数 | > 30% | 系统自主性不足 |
| **幻觉拦截率** | Guard 拦截的越权或无效输出 / 总输出数 | 趋势上升 | 模型输出质量下降 |
| **工具失败率** | Guard 脚本超时或报错次数 / 总调用次数 | > 5% | 基础设施不可靠 |
| **降级触发率** | fallback 到转人工的次数 / 总调用次数 | > 10% | LLM 能力边界被频繁触碰 |
| **阶段重试率** | 某个阶段需要重试的次数 / 总阶段数 | > 20% | 该阶段 Prompt 或约束不足 |
| **债务超期率** | 超 3 轮未修复的问题数 / 总问题数 | > 15% | 技术债务失控 |
| **基线漂移度** | 当前架构 vs 基线架构的差异指标 | 持续上升 | 架构在迭代中渐行渐远 |
| **伪实现检出率** | 发现伪实现 / 审查代码量 | > 5% | 模型在"假装完成" |

### 可观测性埋点

```
sprints/logs/
├── traces/          # 全链路 trace 日志
│   └── sprint-{N}-traces.jsonl
├── guard/           # Guard 拦截日志
│   └── sprint-{N}-guard.log
├── metrics/         # 翻车指标快照
│   └── sprint-{N}-metrics.json
└── incidents/       # 翻车事件记录
    └── incident-{YYYYMMDD}-{nn}.md

每个埋点记录什么：

1. traces/*.jsonl（每次角色调用）
   - trace_id, sprint_id, phase, role
   - prompt_hash, output_hash
   - started_at, completed_at, status
   - retry_count, error_message

2. guard/*.log（每次 Guard 拦截）
   - timestamp, guard_type, blocked_action
   - role, phase, reason
   - 是否误判（人工标注）

3. metrics/*.json（每轮迭代结束快照）
   - 所有翻车指标的当前值
   - 趋势对比（vs 上一轮）

4. incidents/*.md（每次翻车事件）
   - 时间、阶段、角色
   - 翻车描述
   - 根因分析
   - 修复措施
   - 新增的防护约束（代码化）
```

---

## 六、计划新增的 8 个组件（功能增强）

### P0（核心必需）

| # | 组件 | 解决问题 | 简述 |
|---|------|---------|------|
| 1 | **项目感知层** | 问题 1 | 自动扫描项目结构、识别技术栈、提取核心模块、估算完成度 |
| 2 | **技术债务账本** | 问题 2 | 跨迭代追踪 deferred 问题，超期自动升级优先级 |
| 3 | **棕地入口流程** | 问题 4 | 从"已有项目 + 问题清单"启动修复工作流 |

### P1（重要增强）

| # | 组件 | 解决问题 | 简述 |
|---|------|---------|------|
| 4 | **基线快照系统** | 问题 3 | 每轮迭代结束自动记录系统状态，下轮启动时对比漂移 |
| 5 | **模型错误猎犬** | 问题 3 | 专门检测 LLM 幻觉：伪实现、导入不存在模块、签名不匹配等 |
| 6 | **健康评分系统** | 问题 3 | 综合评分决定是否需要"稳定性迭代"，健康分 < 60 禁止新功能 |
| 7 | **问题切入点分析** | 问题 4 | 对问题做依赖图分析、风险评级、改动半径评估、修复排序 |
| 8 | **棕地审查入口** | 问题 4 | `/brownfield-start` 命令，接受项目和问题清单，自动扫描 + 规划 |

---

## 七、当前最紧迫的技术债务及还债计划

### 债务清单（按紧迫性排序）

| # | 债务项 | 风险等级 | 症状 | 根因 |
|---|--------|---------|------|------|
| D-001 | Guard 是黑名单模式，注定遗漏 | **P0** | 模型可绕过拦截执行危险操作 | 策略错误：应该用白名单 |
| D-002 | 校验只检查存在性不检查质量 | **P0** | 伪实现、废话报告通过校验 | 校验规则不完整 |
| D-003 | 无超时、无重试、无降级 | **P0** | 任何 hang 都会导致整个会话死锁 | 基础设施缺失 |
| D-004 | 无 trace 链路，无法根因分析 | **P1** | 翻车后无法复现和定位 | 可观测性缺失 |
| D-005 | 状态机无失败状态和恢复 | **P1** | 中途崩溃后状态不一致 | 状态模型不完整 |
| D-006 | Prompt 散落无版本管理 | **P1** | 改了不知道、无法回退 | 配置即代码未落实 |
| D-007 | 角色间无会话隔离 | **P1** | 一个跑飞全盘跑飞 | 架构耦合 |
| D-008 | 无强制迭代比例约束 | **P2** | 债务可以无限堆积 | 流程缺乏硬约束 |
| D-009 | 两份 Prompt 目录可能不一致 | **P2** | `sprints/prompts/` vs `sprint-team-plugin/agents/` | 重复定义 |

### 还债计划

```
迭代 N（稳定性迭代）— 强制分配，不做新功能

Phase 1：P0 三项（阻断性风险）— 预计 2 天
├── D-001: Guard 改为白名单模式
│   耗时：0.5 天
│   验证：测试 20 种绕过方式，全部应被拦截
│
├── D-002: 校验规则增强
│   耗时：0.5 天
│   验证：注入 5 份伪实现报告，应全部检出
│
└── D-003: 超时 + 重试 + 降级
    耗时：1 天
    验证：模拟超时、脚本崩溃，系统应降级转人工

Phase 2：P1 四项（可靠性增强）— 预计 3 天
├── D-004: trace 链路
│   耗时：1 天
│   验证：任意翻车事件可通过 trace_id 复现
│
├── D-005: 状态机失败恢复
│   耗时：0.5 天
│   验证：中途 kill 后重启，状态可恢复
│
├── D-006: Prompt 版本化管理
│   耗时：0.5 天
│   验证：可以回退到上一版 Prompt
│
└── D-007: 会话隔离
    耗时：1 天
    验证：角色 A 的上下文不会泄漏到角色 B

Phase 3：P2 两项（流程约束）— 预计 1 天
├── D-008: 迭代比例硬约束
│   耗时：0.5 天
│   验证：连续 3 轮只做新功能 → 第 4 轮强制稳定性迭代
│
└── D-009: Prompt 去重
    耗时：0.5 天
    验证：只保留一份 Prompt，两处引用同一份

总计：6 天（一个完整的稳定性迭代周期）
```

---

## 八、关键设计约束

1. **不改变现有工作流**：新组件是增量增强，不破坏现有 5 阶段流程
2. **状态向后兼容**：`sprint-state.json` 的扩展字段不影响现有逻辑
3. **感知结果可注入**：感知层输出要能注入到各角色的 `{{CONTEXT}}` 变量
4. **债务账本独立**：账本文件独立于状态机，跨 sprint 持久化
5. **基线快照轻量**：只记录关键指标，不复制整个项目
6. **防御优先**：所有改造遵循"翻车也翻不死"原则，不追求"不翻车"

---

## 九、文件规划（计划）

```
dev-agent-team/
├── sprints/
│   ├── sprint-state.json          # 扩展：增加 baseline_hash、health_score 字段
│   ├── config/
│   │   └── permissions.json       # 扩展：新增感知层角色权限
│   ├── prompts/                   # 版本化管理目录
│   │   ├── product-architect/
│   │   │   └── v1.0.0.md
│   │   ├── slice-planner/
│   │   │   └── v1.0.0.md
│   │   ├── project-scanner.md     # 新增：项目感知 Agent Prompt
│   │   └── issue-analyzer.md      # 新增：问题切入点分析 Prompt
│   ├── debt/
│   │   └── ledger.json            # 新增：技术债务账本
│   ├── baselines/
│   │   └── sprint-{N}-baseline.json  # 新增：每轮基线快照
│   └── logs/                      # 新增：可观测性日志
│       ├── traces/
│       ├── guard/
│       ├── metrics/
│       └── incidents/
│
├── sprint-team-plugin/
│   ├── commands/
│   │   ├── /brownfield-start.md   # 新增：棕地入口命令
│   │   └── /sprint-health.md      # 新增：查看健康分
│   ├── agents/
│   │   ├── project-scanner.md     # 新增：项目感知 Agent
│   │   └── issue-analyzer.md      # 新增：问题分析 Agent
│   └── scripts/
│       ├── project-scanner.py     # 新增：项目自动扫描脚本
│       ├── baseline-snapshot.py   # 新增：基线快照脚本
│       ├── hallucination-hunter.py # 新增：模型错误检测脚本
│       └── health-calculator.py   # 新增：健康分计算脚本
│
└── docs/
    ├── baselines/                 # 新增：基线快照存储
    └── debt/                      # 新增：债务账本存储
```

---

## 十、备注

- 用户决定**暂不实施**，先记录分析和计划
- 后续可以分阶段实施：先做 P0 的 3 个组件，再做 P1 的 5 个组件
- 实施前需要确认优先级和范围是否调整
- 所有改造必须遵循"必然翻车"前提，防御优于修补
