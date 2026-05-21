#!/usr/bin/env python3
"""
Artifact Validator - 验证产物文件的存在性、结构、长度

检查：
1. 文件是否在正确目录
2. 内容是否包含必要章节
3. 文件长度是否合理
4. 文件名是否符合规则

exit 0 = 通过
exit 1 = 失败
"""

import json
import sys
from pathlib import Path


ARTIFACT_CONFIGS = {
    "zero": {
        "dir": "docs/iterations",
        "pattern": "*.md",
        "min_count": 0,
    },
    "one_architect": {
        "dir": "docs/architecture",
        "pattern": "*.md",
        "min_count": 1,
        "required_sections": ["领域建模", "MVP", "API 契约", "验收标准"],
        "min_length": 500,
    },
    "one_planner": {
        "dir": "docs/plans",
        "pattern": "*.md",
        "min_count": 1,
        "required_sections": ["变更定性", "执行步骤", "回滚方案", "验收标准"],
        "min_length": 500,
    },
    "three_review": {
        "dir": "docs/reviews",
        "pattern": "*.md",
        "min_count": 1,
        "required_sections": ["审查概况", "严重问题", "高优先级问题", "低优先级问题"],
        "min_length": 300,
    },
    "three_audit": {
        "dir": "docs/audits",
        "pattern": "*.md",
        "min_count": 1,
        "required_sections": ["架构合理性", "业务逻辑闭环", "项目完成度", "缺陷清单"],
        "min_length": 500,
    },
    "four_fix_plan": {
        "dir": "docs/plans",
        "pattern": "*.md",
        "min_count": 1,
        "required_sections": ["执行步骤", "回滚方案"],
        "min_length": 300,
    },
    "four_fix_execute": {
        "dir": "docs/fixes",
        "pattern": "*.md",
        "min_count": 1,
        "required_sections": ["修复概况", "已修复", "修复后状态"],
        "min_length": 200,
    },
    "five_summary": {
        "dir": "docs/iterations",
        "pattern": "*.md",
        "min_count": 1,
        "required_sections": ["迭代目标", "产出物"],
        "min_length": 200,
    },
}


def validate_artifacts(phase_id: str) -> list[str]:
    config = ARTIFACT_CONFIGS.get(phase_id)
    if not config:
        return [f"阶段 {phase_id} 无产物配置"]

    issues = []
    artifact_dir = Path(config["dir"])
    pattern = config.get("pattern", "*.md")
    min_count = config.get("min_count", 0)

    if min_count == 0:
        return []

    if not artifact_dir.exists():
        issues.append(f"目录 {artifact_dir} 不存在")
        return issues

    files = list(artifact_dir.glob(pattern))
    if len(files) < min_count:
        issues.append(f"{artifact_dir}/{pattern} 文件数不足（需要 {min_count}，实际 {len(files)}）")
        return issues

    for f in files:
        try:
            content = f.read_text(encoding="utf-8")
        except Exception as e:
            issues.append(f"无法读取 {f}: {e}")
            continue

        content_stripped = content.strip()
        min_length = config.get("min_length", 0)
        if len(content_stripped) < min_length:
            issues.append(f"{f.name} 内容过短（{len(content_stripped)} < {min_length}）")

        for section in config.get("required_sections", []):
            if section not in content:
                issues.append(f"{f.name} 缺少必要章节：{section}")

    return issues


def validate_file(file_path: str) -> list[str]:
    path = Path(file_path)
    issues = []
    if not path.exists():
        issues.append(f"文件不存在：{file_path}")
        return issues
    if not path.suffix == ".md":
        return []
    content = path.read_text(encoding="utf-8")
    if not content.strip():
        issues.append(f"{path.name} 内容为空")
    return issues


def main():
    phase_id = sys.argv[1] if len(sys.argv) > 1 else ""
    file_path = sys.argv[2] if len(sys.argv) > 2 else ""

    if not phase_id and not file_path:
        print("用法: artifact_validator <phase_id> [file_path]")
        sys.exit(1)

    issues = []
    if phase_id:
        issues = validate_artifacts(phase_id)
    if file_path:
        issues.extend(validate_file(file_path))

    if issues:
        for i in issues:
            print(f"[VALIDATION ERROR] {i}", file=sys.stderr)
        sys.exit(1)
    else:
        print("OK: 产物校验通过")
        sys.exit(0)


if __name__ == "__main__":
    main()
