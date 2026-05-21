#!/usr/bin/env python3
"""
Delete Guard - 拦截文件删除操作

exit 0 = 放行
exit 2 = 阻断
"""

import json
import sys
from pathlib import Path

from event_log import write_guard_event, load_sprint_id

BUILTIN_COMMANDS = [
    "rm ",
    "rmdir ",
    "unlink ",
    "del ",
    "git rm",
    "git clean",
]


def _load_sprint_id() -> str:
    state_file = Path("sprints/sprint-state.json")
    if not state_file.exists():
        return "unknown"
    try:
        with open(state_file, encoding="utf-8") as f:
            return json.load(f).get("sprint_id", "unknown")
    except (json.JSONDecodeError, OSError):
        return "unknown"


def main():
    command = sys.argv[1] if len(sys.argv) > 1 else ""

    if not command:
        sys.exit(0)

    command_lower = command.lower()
    sprint_id = _load_sprint_id()

    for forbidden in BUILTIN_COMMANDS:
        f_lower = forbidden.lower()
        if command_lower.startswith(f_lower) or f" {f_lower}" in command_lower:
            write_guard_event(
                sprint_id, "delete-guard", command, f"禁止删除命令: {forbidden.strip()}"
            )
            print(f"\n[DELETE BLOCKED] 禁止删除操作：{command}", file=sys.stderr)
            sys.exit(2)

    write_guard_event(sprint_id, "delete-guard", command, "-", status="allowed")
    sys.exit(0)


if __name__ == "__main__":
    main()
