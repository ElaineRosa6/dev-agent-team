---
name: sprint-close
description: 迭代收尾，清理、记录、归档、输出迭代总结
---

进入阶段五：迭代收尾。

## 执行步骤

### 1. 读取状态
读取 `sprints/sprint-state.json`，确认当前状态。

### 2. 运维管家：迭代收尾
加载运维管家角色，执行：

#### 2.1 垃圾文件清理
- 扫描项目，列出清理清单
- 确认后执行清理
- 确认项目仍可正常构建

#### 2.2 工作记录
- 记录本轮迭代所有工作内容
- 汇总所有产出物路径

#### 2.3 迭代总结
输出到 `docs/iterations/iteration-{N}-summary.md`，包含：
- 迭代目标回顾
- 产出物清单
- 成果统计
- 遗留问题及处理计划
- 下一轮迭代建议
- 经验教训

#### 2.4 文档归档
- 确认所有文档已归档到正确目录
- 更新 sprint-state.json 中的 outputs 字段

### 3. 更新状态
- `phase_status.five_summary = "completed"`
- `status = "completed"`

### 4. 询问
询问用户是否开始下一轮迭代。

## 现在开始

读取当前迭代状态，然后执行收尾流程。
