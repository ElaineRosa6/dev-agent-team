#!/usr/bin/env python3
"""
Event Log - 结构化事件日志

为每次阶段执行、guard拦截、校验失败生成带 trace_id 的 JSONL 日志。
日志文件存储在 sprints/logs/ 目录下。
"""

import hashlib
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path


def generate_trace_id(sprint_id: str, phase: str, role: str) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    short = uuid.uuid4().hex[:6]
    return f"{sprint_id}:{phase}:{role}:{ts}:{short}"


def write_event(event_type: str, **kwargs) -> str:
    sprint_id = kwargs.pop("sprint_id", "unknown")
    phase = kwargs.pop("phase", "")
    role = kwargs.pop("role", "")

    trace_id = generate_trace_id(sprint_id, phase, role)

    entry = {
        "trace_id": trace_id,
        "sprint_id": sprint_id,
        "phase": phase,
        "role": role,
        "event": event_type,
        "status": kwargs.pop("status", event_type),
        "time": datetime.now(timezone.utc).isoformat(),
    }
    entry.update(kwargs)

    log_dir = Path("sprints/logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / "events.jsonl"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    return trace_id


def write_guard_event(sprint_id: str, guard_type: str, blocked_action: str,
                      reason: str, role: str = "", phase: str = "") -> str:
    return write_event(
        "guard_blocked",
        sprint_id=sprint_id,
        phase=phase,
        role=role,
        guard_type=guard_type,
        blocked_action=blocked_action,
        reason=reason,
        status="blocked",
    )


def write_allow_event(sprint_id: str, guard_type: str, action: str,
                      role: str = "", phase: str = "") -> str:
    return write_event(
        "guard_allowed",
        sprint_id=sprint_id,
        phase=phase,
        role=role,
        guard_type=guard_type,
        action=action,
        status="allowed",
    )


def write_validation_event(sprint_id: str, phase: str, file_path: str,
                           issues: list, passed: bool,
                           role: str = "") -> str:
    return write_event(
        "validation_result",
        sprint_id=sprint_id,
        phase=phase,
        role=role,
        file_path=file_path,
        issues=issues,
        status="passed" if passed else "failed",
    )


def get_sprint_events(sprint_id: str = None) -> list[dict]:
    log_file = Path("sprints/logs/events.jsonl")
    if not log_file.exists():
        return []
    events = []
    with open(log_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                if sprint_id and entry.get("sprint_id") != sprint_id:
                    continue
                events.append(entry)
            except json.JSONDecodeError:
                continue
    return events


def load_sprint_id() -> str:
    state_file = Path("sprints/sprint-state.json")
    if not state_file.exists():
        return "unknown"
    try:
        with open(state_file, encoding="utf-8") as f:
            state = json.load(f)
        return state.get("sprint_id", "unknown")
    except (json.JSONDecodeError, OSError):
        return "unknown"


def count_guard_blocks(sprint_id: str = None) -> int:
    events = get_sprint_events(sprint_id)
    return sum(1 for e in events if e.get("status") == "blocked")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法: python3 event_log.py <summary|write_event>")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "summary":
        events = get_sprint_events()
        block_count = sum(1 for e in events if e.get("status") == "blocked")
        print(f"总事件数: {len(events)}")
        print(f"被拦截次数: {block_count}")
    elif cmd == "write_event":
        trace_id = write_event("manual_test", sprint_id="test", phase="demo", role="test")
        print(f"事件已写入, trace_id: {trace_id}")
    else:
        print(f"未知命令: {cmd}")
        sys.exit(1)
