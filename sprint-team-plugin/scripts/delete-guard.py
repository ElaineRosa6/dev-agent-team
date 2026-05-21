#!/usr/bin/env python3
"""
Delete Guard - 拦截文件删除操作

exit 0 = 放行
exit 2 = 阻断
"""

import sys

FORBIDDEN_COMMANDS = [
    "rm ",
    "rmdir ",
    "unlink ",
    "del ",
    "git rm",
    "git clean",
]


def main():
    command = sys.argv[1] if len(sys.argv) > 1 else ""

    if not command:
        sys.exit(0)

    command_lower = command.lower()

    for forbidden in FORBIDDEN_COMMANDS:
        if command_lower.startswith(forbidden.lower()) or f" {forbidden.lower()}" in command_lower:
            print(f"\n[DELETE BLOCKED] 禁止删除操作：{command}", file=sys.stderr)
            sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
