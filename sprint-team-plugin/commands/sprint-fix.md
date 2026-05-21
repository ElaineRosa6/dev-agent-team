---
name: sprint-fix
description: 审查发现 P0/P1 问题，进入安全修复阶段
---

进入阶段四：安全修复。

## 执行步骤

### 1. 读取状态和报告
- 读取 `sprints/sprint-state.json`
- 读取 `docs/reviews/code-review.md`
- 读取 `docs/audits/architecture-audit.md`

### 2. 安全切片规划师：修复规划
加载安全切片规划师角色，根据审查报告：
- 汇总所有待修复问题
- 识别问题间依赖关系
- 设计兼容策略（防腐层/双写/Feature Toggle）
- 输出修复执行切片计划

输出到 `docs/plans/fix-plan.md`

### 3. 自动修复工程师：修复执行
加载自动修复工程师角色，按修复计划：
- 阶段零：定位问题，探测环境
- 阶段一：高可信度快速修复（P1/P2 明确 Bug）
- 阶段二：需运行测试验证的修复
- 阶段三：仅评估不修复（架构级问题）
- 阶段四：明确跳过
- 运行构建/测试/lint 验证

输出到 `docs/fixes/fix-report.md`

### 4. 回归审查
加载代码审查专家角色，对修复后代码回归审查：
- 确认原问题是否解决
- 确认是否引入新问题

输出到 `docs/reviews/regression-review.md`

### 5. 决策
- 回归通过 → 进入阶段五
- 发现新问题 → 重新规划修复

### 6. 更新状态
更新 `sprints/sprint-state.json`

## 现在开始

读取审查报告，然后开始修复规划。
