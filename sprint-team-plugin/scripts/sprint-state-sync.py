#!/usr/bin/env python3
"""
Sprint State Sync - 自动同步状态文件

在 Bash 命令执行后，检查 sprint-state.json 是否需要更新。
自动检测 docs/ 目录下的新文件并记录到状态中。
"""

import json
import sys
from pathlib import Path
from datetime import datetime


def sync():
    state_file = Path("sprints/sprint-state.json")
    if not state_file.exists():
        return

    with open(state_file) as f:
        state = json.load(f)

    # 扫描 docs/ 目录下的新文件
    docs_dir = Path("docs")
    if not docs_dir.exists():
        return

    outputs = state.get("outputs", {})

    # 检查各目录下的最新文件
    file_mapping = {
        "architecture_plan": "docs/architecture",
        "execution_plan": "docs/plans",
        "code_review": "docs/reviews",
        "architecture_audit": "docs/audits",
        "fix_report": "docs/fixes",
        "iteration_summary": "docs/iterations",
    }

    for key, dir_path in file_mapping.items():
        full_path = docs_dir / dir_path
        if full_path.exists():
            md_files = list(full_path.glob("*.md"))
            if md_files:
                latest = max(md_files, key=lambda f: f.stat().st_mtime)
                outputs[key] = str(latest)

    state["outputs"] = state.get("outputs", {})
    for key, value in outputs.items():
        state["outputs"][key] = value

    state["logs"].append({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "message": "状态自动同步",
    })

    with open(state_file, "w") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    sync()
