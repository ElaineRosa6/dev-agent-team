---
name: sprint-review
description: 代码实现完成后，触发代码审查和架构审计
---

代码实现完成，触发阶段三：代码审查。

## 执行步骤

### 1. 读取状态
读取 `sprints/sprint-state.json`，确认当前处于阶段二完成状态。

### 2. 阶段三：代码审查
#### 2.1 代码审查专家
加载代码审查专家角色，执行四维度扫描：
- 功能性 Bug（边界、异常、并发、类型、资源）
- 安全性（注入、认证、数据泄露、依赖）
- 代码质量（坏味道、设计原则、性能、可读性）
- 业务逻辑（场景遗漏、一致性、时序）

输出到 `docs/reviews/code-review.md`

#### 2.2 架构审计师
加载架构审计师角色，结合审查报告执行：
- 架构合理性评估
- 业务逻辑闭环诊断
- 项目完成度盘点
- 缺陷清单（P0/P1/P2）

输出到 `docs/audits/architecture-audit.md`

### 3. 决策
分析审查和审计报告：
- 发现 P0/P1 问题 → 提示进入阶段四修复
- 无严重问题 → 直接进入阶段五收尾

### 4. 更新状态
更新 `sprints/sprint-state.json`：
- `phase_status.three_review = "completed"`
- `phase_status.three_audit = "completed"`
- `decisions.needs_fix = true/false`

## 现在开始

探索当前项目代码，然后执行四维度代码审查。
