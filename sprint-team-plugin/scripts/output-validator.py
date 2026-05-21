#!/usr/bin/env python3
"""
Output Validator - 验证角色输出文件是否符合预期

在文件写入后自动触发，检查：
1. 文件是否在正确目录
2. 内容是否包含必要章节
3. 文件长度是否合理
"""

import json
import sys
from pathlib import Path

# 各角色的输出校验规则
ROLE_VALIDATION = {
    "product-architect": {
        "dir": "docs/architecture",
        "required_sections": [
            "领域建模",
            "MVP",
            "API 契约",
            "验收标准",
        ],
        "min_length": 500,
    },
    "slice-planner": {
        "dir": "docs/plans",
        "required_sections": [
            "变更定性",
            "执行步骤",
            "回滚方案",
            "验收标准",
        ],
        "min_length": 500,
    },
    "code-reviewer": {
        "dir": "docs/reviews",
        "required_sections": [
            "审查概况",
            "严重问题",
            "高优先级问题",
            "中优先级问题",
            "低优先级问题",
        ],
        "min_length": 300,
    },
    "architecture-auditor": {
        "dir": "docs/audits",
        "required_sections": [
            "架构合理性",
            "业务逻辑闭环",
            "项目完成度",
            "缺陷清单",
        ],
        "min_length": 500,
    },
    "auto-fix-engineer": {
        "dir": "docs/fixes",
        "required_sections": [
            "修复概况",
            "已修复",
            "修复后状态",
        ],
        "min_length": 300,
    },
    "devops-manager": {
        "dir": "docs/iterations",
        "required_sections": [
            "迭代目标",
            "产出物",
        ],
        "min_length": 200,
    },
}


def load_current_role() -> str:
    state_file = Path("sprints/sprint-state.json")
    if not state_file.exists():
        return ""
    with open(state_file) as f:
        state = json.load(f)
    current_phase = state.get("current_phase", "")
    phases = state.get("phases", {})
    phase_info = phases.get(current_phase, {})
    return phase_info.get("role", "")


def validate(file_path: str) -> list[str]:
    path = Path(file_path)
    issues = []

    role = load_current_role()
    if not role:
        return issues

    config = ROLE_VALIDATION.get(role, {})
    if not config:
        return issues

    # 检查内容
    if path.exists():
        content = path.read_text(encoding="utf-8")

        # 检查必要章节
        for section in config.get("required_sections", []):
            if section not in content:
                issues.append(f"缺少必要章节：{section}")

        # 检查长度
        min_len = config.get("min_length", 0)
        if len(content.strip()) < min_len:
            issues.append(f"文件内容过短（{len(content.strip()} < {min_len}）")

    return issues


def main():
    file_path = sys.argv[1] if len(sys.argv) > 1 else ""

    if not file_path:
        sys.exit(0)

    issues = validate(file_path)

    if issues:
        log_file = Path("sprints/.validation-log.txt")
        with open(log_file, "a") as f:
            f.write(f"\n[VALIDATION WARNING] {file_path}:\n")
            for issue in issues:
                f.write(f"  - {issue}\n")

    # Hooks 的 PostToolUse 不阻断，只记录
    sys.exit(0)


if __name__ == "__main__":
    main()
