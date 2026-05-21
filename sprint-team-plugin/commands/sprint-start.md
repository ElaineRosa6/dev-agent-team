---
name: sprint-start
description: 启动新一轮 Sprint 迭代，从阶段零开始完整研发流程
---

启动新一轮 Sprint 迭代。

## 执行步骤

### 1. 初始化状态
读取 `sprints/sprint-state.json`，如果不存在则从 `sprints/sprint-state.json.template` 复制。

### 2. 收集需求
向用户询问本轮迭代的需求描述，包括：
- 核心业务目标
- 功能清单
- 技术约束（如有）
- 上一轮遗留问题（如有）

### 3. 阶段零：迭代启动（运维管家）
加载运维管家角色，执行：
- 确认迭代目标
- 记录参与角色
- 准备输入材料

输出到 `docs/iterations/iteration-{N}-start.md`

### 4. 阶段一：架构规划
#### 4.1 产品架构师
加载产品架构师角色，根据需求输出：
- MVP 边界圈定
- API 契约定义
- 演进式架构落地切片计划

输出到 `docs/architecture/architecture-plan.md`

#### 4.2 安全切片规划师
加载安全切片规划师角色，根据架构计划输出：
- 变更定性
- 安全执行切片计划（步骤 1→N）
- 每个步骤的回滚方案

输出到 `docs/plans/execution-plan.md`

### 5. 门控确认
打印架构计划和执行计划摘要，等待用户确认：
- 用户输入 `y`：进入阶段二
- 用户输入 `n`：返回修改架构计划

### 6. 更新状态
更新 `sprints/sprint-state.json`：
- `phase_status.zero = "completed"`
- `phase_status.one_architect = "completed"`
- `phase_status.one_planner = "completed"`
- `phase_status.two_implementation = "pending"`

## 输出文档规范

所有文档使用 Markdown 格式，保存到 `docs/` 目录下对应子目录。

## 现在开始

请询问用户本轮迭代的需求是什么。
