---
name: sprint-status
description: 查看当前 Sprint 状态、阶段进度和产出物
---

查看当前 Sprint 状态。

## 执行步骤

### 1. 读取状态
读取 `sprints/sprint-state.json`

### 2. 显示状态摘要

```
## Sprint 状态

Sprint ID: {sprint_id}
迭代轮次: {iteration}
总体状态: {status}
当前阶段: {current_phase}

## 阶段进度

| 阶段 | 名称 | 角色 | 状态 | 产出 |
|------|------|------|------|------|
| zero | 迭代启动 | 运维管家 | {status} | {artifacts} |
| one_architect | 架构规划 | 产品架构师 | {status} | {artifacts} |
| one_planner | 安全切片 | 安全切片规划师 | {status} | {artifacts} |
| two_implementation | 代码实现 | 人类 | {status} | {artifacts} |
| three_review | 代码审查 | 代码审查专家 | {status} | {artifacts} |
| three_audit | 架构审计 | 架构审计师 | {status} | {artifacts} |
| four_fix_plan | 修复规划 | 安全切片规划师 | {status} | {artifacts} |
| four_fix_execute | 修复执行 | 自动修复工程师 | {status} | {artifacts} |
| four_regression | 回归审查 | 代码审查专家 | {status} | {artifacts} |
| five_summary | 迭代收尾 | 运维管家 | {status} | {artifacts} |

## 决策点

- 阶段一已批准: {phase_one_approved}
- 需要修复: {needs_fix}
- 修复回归通过: {fix_regression_passed}

## 产出物

- 架构计划: {architecture_plan}
- 执行计划: {execution_plan}
- 代码审查: {code_review}
- 架构审计: {architecture_audit}
- 修复报告: {fix_report}
- 迭代总结: {iteration_summary}
```

### 3. 下一步建议

根据当前状态给出下一步操作建议。

## 现在开始

读取状态文件并显示。
