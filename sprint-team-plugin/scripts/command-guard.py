#!/usr/bin/env python3
"""
Command Guard - 拦截危险命令

从 permissions.json 的全局限制中读取危险命令模式，结合内置黑名单进行拦截。
exit 0 = 放行
exit 2 = 阻断
"""

import json
import sys
from pathlib import Path

from event_log import write_guard_event, load_sprint_id

BUILTIN_PATTERNS = [
    "rm -rf",
    "rm -f",
    "rmdir",
    "drop database",
    "drop table",
    "truncate",
    "git push --force",
    "git reset --hard",
    "chmod 777",
    "mkfs",
    "fdisk",
    "dd if=",
    "shutdown",
    "reboot",
    "poweroff",
]


def load_forbidden_commands() -> list[str]:
    config_paths = [
        "sprints/config/permissions.json",
        "sprint-team-plugin/templates/permissions.json",
    ]
    for p in config_paths:
        try:
            with open(p, encoding="utf-8") as f:
                config = json.load(f)
            return config.get("global_restrictions", {}).get("forbidden_commands", [])
        except (FileNotFoundError, json.JSONDecodeError):
            continue
    return []


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

    all_patterns = BUILTIN_PATTERNS + load_forbidden_commands()
    for pattern in all_patterns:
        if pattern.lower() in command_lower:
            write_guard_event(sprint_id, "command-guard", command, f"危险命令: {pattern}")
            print(f"\n[COMMAND BLOCKED] 危险命令：{pattern}", file=sys.stderr)
            sys.exit(2)

    write_guard_event(sprint_id, "command-guard", command, "-", status="allowed")
    sys.exit(0)


if __name__ == "__main__":
    main()
