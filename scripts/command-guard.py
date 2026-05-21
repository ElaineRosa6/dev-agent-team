#!/usr/bin/env python3
"""
Command Guard - 拦截危险命令

exit 0 = 放行
exit 2 = 阻断
"""

import sys

FORBIDDEN_PATTERNS = [
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

def main():
    command = sys.argv[1] if len(sys.argv) > 1 else ""

    if not command:
        sys.exit(0)

    command_lower = command.lower()

    for pattern in FORBIDDEN_PATTERNS:
        if pattern.lower() in command_lower:
            print(f"\n[COMMAND BLOCKED] 危险命令：{pattern}", file=sys.stderr)
            sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
