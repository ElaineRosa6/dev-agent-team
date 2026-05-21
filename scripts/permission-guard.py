#!/usr/bin/env python3
"""
Permission Guard - 拦截越权文件写入

从 permissions.json 读取角色权限白名单，检查文件写入是否被允许。
路径经过规范化处理，防止前缀匹配绕过。

exit 0 = 放行
exit 2 = 阻断
"""

import json
import os
import sys
from pathlib import Path


PERMISSION_CONFIGS = [
    "sprints/config/permissions.json",
    "sprint-team-plugin/templates/permissions.json",
]

FORBIDDEN_EXTENSIONS = [".key", ".pem", ".secret"]


def _resolve_config_path() -> Path:
    for config_path in PERMISSION_CONFIGS:
        p = Path(config_path)
        if p.exists():
            return p
    return Path(PERMISSION_CONFIGS[0])


def _normalize_path(file_path: str) -> Path:
    resolved = Path(os.path.normpath(os.path.abspath(file_path)))
    return resolved


def _is_under(path: Path, prefix: Path) -> bool:
    try:
        path.relative_to(prefix)
        return True
    except ValueError:
        return False


def _match_glob(filename: str, pattern: str) -> bool:
    from fnmatch import fnmatch
    return fnmatch(filename, pattern)


def load_permissions() -> dict:
    config_path = _resolve_config_path()
    if not config_path.exists():
        return {}
    try:
        with open(config_path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def load_current_role() -> str:
    state_file = Path("sprints/sprint-state.json")
    if not state_file.exists():
        return ""
    try:
        with open(state_file, encoding="utf-8") as f:
            state = json.load(f)
    except (json.JSONDecodeError, OSError):
        return ""
    current_phase = state.get("current_phase", "")
    phases = state.get("phases", {})
    phase_info = phases.get(current_phase, {})
    return phase_info.get("role", "")


def check_permission(file_path: str, tool_input: str = "") -> tuple[bool, str]:
    resolved = _normalize_path(file_path)
    filename = resolved.name

    config = load_permissions()
    global_restrict = config.get("global_restrictions", {})

    for forbidden_dir_name in global_restrict.get("forbidden_dirs", []):
        if forbidden_dir_name in resolved.parts:
            return False, f"禁止写入禁止路径：{forbidden_dir_name}"

    for forbidden_file_pattern in global_restrict.get("forbidden_files", []):
        if _match_glob(filename, forbidden_file_pattern):
            return False, f"禁止写入禁止文件：{forbidden_file_pattern}"

    if resolved.suffix in FORBIDDEN_EXTENSIONS:
        return False, f"禁止写入敏感文件类型：{resolved.suffix}"

    role = load_current_role()
    if not role:
        return True, "无当前角色约束，放行"

    permissions = config.get("permissions", {})
    if role not in permissions:
        known = ", ".join(permissions.keys())
        return False, f"未知角色 {role}，拒绝访问（已知角色：{known}）"

    perms = permissions[role]

    allowed_ext = perms.get("allowed_file_extensions", [])
    if allowed_ext and resolved.suffix not in allowed_ext:
        return False, f"角色 {role} 不允许写入 {resolved.suffix} 文件"

    allowed_dirs = perms.get("allowed_dirs", [])
    if allowed_dirs:
        matched = False
        for d in allowed_dirs:
            d_resolved = Path(os.path.normpath(os.path.abspath(d)))
            if d_resolved == resolved or _is_under(resolved, d_resolved):
                matched = True
                break
        if not matched:
            return False, f"角色 {role} 不允许写入 {file_path}（允许目录：{allowed_dirs}）"

    max_size = perms.get("max_file_size_kb", None)
    if max_size and os.path.exists(resolved):
        size_kb = os.path.getsize(resolved) / 1024
        if size_kb > max_size:
            return False, f"文件大小 {size_kb:.0f}KB 超过限制 {max_size}KB"

    if role == "auto-fix-engineer":
        restricted = perms.get("restricted_dirs", [])
        for restricted_dir in restricted:
            if restricted_dir in resolved.parts:
                return False, f"auto-fix-engineer 禁止写入受限目录：{restricted_dir}"

    return True, "权限检查通过"


def main():
    file_path = sys.argv[1] if len(sys.argv) > 1 else ""
    tool_input = sys.argv[2] if len(sys.argv) > 2 else ""

    if not file_path:
        sys.exit(0)

    allowed, reason = check_permission(file_path, tool_input)

    if allowed:
        sys.exit(0)
    else:
        print(f"\n[PERMISSION DENIED] {reason}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
