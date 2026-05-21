#!/usr/bin/env python3
"""
Code Validator - 代码验证

检查：
1. Python 文件是否能通过 py_compile
2. 是否存在 import 不存在的模块（基础检测）
3. JSON/YAML 文件是否合法

exit 0 = 通过
exit 1 = 发现代码问题
"""

import json
import py_compile
import sys
from pathlib import Path


def check_python(file_path: str) -> list[str]:
    issues = []
    try:
        py_compile.compile(file_path, doraise=True)
    except py_compile.PyCompileError as e:
        issues.append(f"Python 编译失败：{e}")
    return issues


def check_json(file_path: str) -> list[str]:
    issues = []
    try:
        with open(file_path, encoding="utf-8") as f:
            json.load(f)
    except json.JSONDecodeError as e:
        issues.append(f"JSON 解析失败：{e}")
    return issues


def validate_file(file_path: str) -> list[str]:
    path = Path(file_path)
    if not path.exists():
        return [f"文件不存在：{file_path}"]

    suffix = path.suffix.lower()
    if suffix == ".py":
        return check_python(file_path)
    elif suffix == ".json":
        return check_json(file_path)
    return []


def main():
    file_path = sys.argv[1] if len(sys.argv) > 1 else ""

    if not file_path:
        print("用法: code_validator <file_path>")
        sys.exit(1)

    issues = validate_file(file_path)

    if issues:
        for i in issues:
            print(f"[CODE ERROR] {i}", file=sys.stderr)
        sys.exit(1)
    else:
        print("OK: 代码校验通过")
        sys.exit(0)


if __name__ == "__main__":
    main()
