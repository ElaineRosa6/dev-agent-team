#!/usr/bin/env python3
"""
Permission Guard - 拦截越权文件写入

检查 Claude 尝试写入的文件是否在允许范围内。
exit 0 = 放行
exit 2 = 阻断
"""

import json
import sys
import os
from pathlib import Path

# 角色权限配置
ROLE_PERMISSIONS = {
    "product-architect": {
        "allowed_dirs": ["docs/architecture"],
        "allowed_extensions": [".md"],
    },
    "slice-planner": {
        "allowed_dirs": ["docs/plans"],
        "allowed_extensions": [".md"],
    },
    "code-reviewer": {
        "allowed_dirs": ["docs/reviews"],
        "allowed_extensions": [".md"],
    },
    "architecture-auditor": {
        "allowed_dirs": ["docs/audits"],
        "allowed_extensions": [".md"],
    },
    "auto-fix-engineer": {
        "allowed_dirs": ["docs/fixes"],
        "allowed_extensions": [".md", ".py", ".js", ".ts", ".go", ".rs", ".java"],
    },
    "devops-manager": {
        "allowed_dirs": ["docs/iterations"],
        "allowed_extensions": [".md"],
    },
}

# 禁止写入的文件和目录
FORBIDDEN_PATHS = [
    ".git",
    ".env",
    "node_modules",
    "vendor",
    ".claude",
]

FORBIDDEN_EXTENSIONS = [".key", ".pem", ".secret", ".env"]


def load_current_role() -> str:
    """从 sprint-state.json 读取当前角色"""
    state_file = Path("sprints/sprint-state.json")
    if not state_file.exists():
        return ""
    with open(state_file) as f:
        state = json.load(f)
    current_phase = state.get("current_phase", "")
    phases = state.get("phases", {})
    phase_info = phases.get(current_phase, {})
    return phase_info.get("role", "")


def check_permission(file_path: str) -> tuple[bool, str]:
    """检查文件写入权限"""
    path = Path(file_path)

    # 检查禁止路径
    for forbidden in FORBIDDEN_PATHS:
        if forbidden in str(path):
            return False, f"禁止写入禁止路径：{forbidden}"

    # 检查禁止扩展名
    if path.suffix in FORBIDDEN_EXTENSIONS:
        return False, f"禁止写入文件类型：{path.suffix}"

    # 获取当前角色
    role = load_current_role()
    if not role:
        return True, "无角色约束，放行"

    # 获取角色权限
    perms = ROLE_PERMISSIONS.get(role, {})
    if not perms:
        return True, f"角色 {role} 无约束，放行"

    # 检查扩展名
    allowed_ext = perms.get("allowed_extensions", [])
    if allowed_ext and path.suffix not in allowed_ext:
        return False, f"角色 {role} 不允许写入 {path.suffix} 文件"

    # 检查目录
    allowed_dirs = perms.get("allowed_dirs", [])
    if allowed_dirs:
        allowed = any(str(path).startswith(d) for d in allowed_dirs)
        if not allowed:
            return False, f"角色 {role} 不允许写入 {path}"

    return True, "权限检查通过"


def main():
    file_path = sys.argv[1] if len(sys.argv) > 1 else ""

    if not file_path:
        sys.exit(0)

    allowed, reason = check_permission(file_path)

    if allowed:
        sys.exit(0)
    else:
        print(f"\n[PERMISSION DENIED] {reason}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
