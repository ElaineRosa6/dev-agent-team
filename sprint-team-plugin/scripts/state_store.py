#!/usr/bin/env python3
"""
State Store - Sprint 状态持久化存储

负责读取、写入、更新 sprint-state.json。
提供状态查询和修改的原子操作。
"""

import json
import shutil
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Optional


class StateStore:
    def __init__(self, state_path: str = "sprints/sprint-state.json"):
        self.state_path = Path(state_path)

    def load(self) -> dict:
        if not self.state_path.exists():
            raise FileNotFoundError(f"状态文件不存在: {self.state_path}")
        with open(self.state_path, encoding="utf-8") as f:
            return json.load(f)

    def save(self, state: dict) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        backup_path = self.state_path.with_suffix(".json.bak")
        if self.state_path.exists():
            shutil.copy2(self.state_path, backup_path)
        with open(self.state_path, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)

    def get_sprint_id(self) -> str:
        return self.load().get("sprint_id", "")

    def get_status(self) -> str:
        return self.load().get("status", "unknown")

    def get_current_phase(self) -> str:
        return self.load().get("current_phase", "")

    def get_current_role(self) -> str:
        state = self.load()
        phase_id = state.get("current_phase", "")
        phases = state.get("phases", {})
        phase_info = phases.get(phase_id, {})
        return phase_info.get("role", "")

    def get_phase(self, phase_id: str) -> Optional[dict]:
        state = self.load()
        return state.get("phases", {}).get(phase_id)

    def get_phase_status(self, phase_id: str) -> str:
        phase = self.get_phase(phase_id)
        return phase.get("status", "unknown") if phase else "unknown"

    def set_phase_status(self, phase_id: str, status: str, reason: str = "") -> None:
        state = self.load()
        phases = state.get("phases", {})
        if phase_id not in phases:
            raise ValueError(f"未知阶段: {phase_id}")
        phases[phase_id]["status"] = status
        now = datetime.now(timezone.utc).isoformat()
        if status == "running":
            phases[phase_id]["started_at"] = now
        elif status == "completed":
            phases[phase_id]["completed_at"] = now
            phases[phase_id]["gate_check"] = True
        elif status == "failed":
            phases[phase_id]["failed_at"] = now
            phases[phase_id]["failure_reason"] = reason
            phases[phase_id]["retry_count"] = phases[phase_id].get("retry_count", 0) + 1
        state["phases"] = phases
        self.save(state)

    def set_current_phase(self, phase_id: str) -> None:
        state = self.load()
        if phase_id not in state.get("phases", {}):
            raise ValueError(f"未知阶段: {phase_id}")
        state["current_phase"] = phase_id
        self.save(state)

    def set_sprint_status(self, status: str) -> None:
        state = self.load()
        state["status"] = status
        self.save(state)

    def add_artifact(self, phase_id: str, artifact_path: str) -> None:
        state = self.load()
        phases = state.get("phases", {})
        if phase_id in phases:
            artifacts = phases[phase_id].get("artifacts", [])
            if artifact_path not in artifacts:
                artifacts.append(artifact_path)
            phases[phase_id]["artifacts"] = artifacts
            state["phases"] = phases
            self.save(state)

    def increment_retry(self, phase_id: str) -> int:
        state = self.load()
        phases = state.get("phases", {})
        if phase_id not in phases:
            raise ValueError(f"未知阶段: {phase_id}")
        retry_count = phases[phase_id].get("retry_count", 0) + 1
        phases[phase_id]["retry_count"] = retry_count
        state["phases"] = phases
        self.save(state)
        return retry_count

    def can_retry(self, phase_id: str, max_retries: int = 2) -> bool:
        phase = self.get_phase(phase_id)
        if not phase:
            return False
        return phase.get("retry_count", 0) < max_retries

    def add_log(self, message: str, extra: Optional[dict] = None) -> None:
        state = self.load()
        entry: dict[str, Any] = {
            "time": datetime.now(timezone.utc).isoformat(),
            "message": message,
        }
        if extra:
            entry.update(extra)
        state.setdefault("logs", []).append(entry)
        self.save(state)

    def set_decision(self, key: str, value: Any) -> None:
        state = self.load()
        state.setdefault("decisions", {})[key] = value
        self.save(state)

    def get_decision(self, key: str, default: Any = None) -> Any:
        return self.load().get("decisions", {}).get(key, default)

    def set_output(self, key: str, value: str) -> None:
        state = self.load()
        state.setdefault("outputs", {})[key] = value
        self.save(state)

    def set_context(self, key: str, value: Any) -> None:
        state = self.load()
        state.setdefault("context", {})[key] = value
        self.save(state)

    def get_all_phases_summary(self) -> list[dict]:
        state = self.load()
        result = []
        for phase_id, phase_info in state.get("phases", {}).items():
            result.append({
                "id": phase_id,
                "name": phase_info.get("name", ""),
                "role": phase_info.get("role", ""),
                "status": phase_info.get("status", "pending"),
            })
        return result
