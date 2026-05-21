#!/usr/bin/env python3
"""
Workflow Engine - Sprint 工作流状态机引擎

读取 workflow.json，驱动阶段流转、校验产物、执行门控。
"""

import json
from pathlib import Path
from typing import Optional

from event_log import write_event, load_sprint_id
from state_store import StateStore


class WorkflowEngine:
    VALID_TRANSITIONS = {
        "pending": ["running"],
        "running": ["completed", "failed"],
        "failed": ["running", "escalated"],
        "completed": [],
        "skipped": [],
        "escalated": ["running"],
    }

    def __init__(
        self,
        workflow_path: str = "sprint-team-plugin/templates/workflow.json",
        state_path: str = "sprints/sprint-state.json",
    ):
        self.workflow_path = Path(workflow_path)
        self.store = StateStore(state_path)
        self._workflow: Optional[dict] = None

    def load_workflow(self) -> dict:
        if self._workflow is None:
            if not self.workflow_path.exists():
                alt = Path("templates/workflow.json")
                if alt.exists():
                    self.workflow_path = alt
                else:
                    raise FileNotFoundError(f"工作流配置不存在: {self.workflow_path}")
            with open(self.workflow_path, encoding="utf-8") as f:
                self._workflow = json.load(f)
        return self._workflow

    def get_phase_config(self, phase_id: str) -> Optional[dict]:
        workflow = self.load_workflow()
        for phase in workflow.get("phases", []):
            if phase["id"] == phase_id:
                return phase
        return None

    def get_all_phases(self) -> list[dict]:
        return self.load_workflow().get("phases", [])

    def get_next_phases(self, phase_id: str) -> list[str]:
        config = self.get_phase_config(phase_id)
        if not config:
            return []
        return config.get("next_phases", [])

    def can_transition(self, phase_id: str, target_status: str) -> tuple[bool, str]:
        current = self.store.get_phase_status(phase_id)
        if current == "unknown":
            return False, f"阶段 {phase_id} 不存在"
        allowed = self.VALID_TRANSITIONS.get(current, [])
        if target_status not in allowed:
            return False, f"阶段 {phase_id} 不允许从 {current} 转换到 {target_status}（允许: {allowed}）"
        return True, ""

    def start_phase(self, phase_id: str) -> tuple[bool, str]:
        can, reason = self.can_transition(phase_id, "running")
        if not can:
            return False, reason
        self.store.set_phase_status(phase_id, "running")
        self.store.set_current_phase(phase_id)
        self.store.set_sprint_status("in_progress")
        self.store.add_log(f"阶段 {phase_id} 开始执行", {"phase": phase_id, "action": "start"})
        config = self.get_phase_config(phase_id)
        role = config.get("role", "") if config else ""
        write_event("phase_start", phase=phase_id, role=role)
        return True, f"阶段 {phase_id} 已启动"

    def complete_phase(self, phase_id: str) -> tuple[bool, str]:
        can, reason = self.can_transition(phase_id, "completed")
        if not can:
            return False, reason
        missing = self._check_required_artifacts(phase_id)
        if missing:
            return False, f"阶段 {phase_id} 缺少必需产物: {', '.join(missing)}"
        self.store.set_phase_status(phase_id, "completed")
        self.store.add_log(f"阶段 {phase_id} 已完成", {"phase": phase_id, "action": "complete"})
        config = self.get_phase_config(phase_id)
        role = config.get("role", "") if config else ""
        write_event("phase_complete", phase=phase_id, role=role)
        return True, f"阶段 {phase_id} 已完成"

    def fail_phase(self, phase_id: str, reason: str = "") -> tuple[bool, str]:
        can, trans_reason = self.can_transition(phase_id, "failed")
        if not can:
            return False, trans_reason
        self.store.set_phase_status(phase_id, "failed", reason=reason)
        self.store.add_log(f"阶段 {phase_id} 失败: {reason}", {"phase": phase_id, "action": "fail", "reason": reason})
        config = self.get_phase_config(phase_id)
        role = config.get("role", "") if config else ""
        write_event("phase_failed", phase=phase_id, role=role, reason=reason)
        return True, f"阶段 {phase_id} 已标记失败"

    def retry_phase(self, phase_id: str) -> tuple[bool, str]:
        phase = self.store.get_phase(phase_id)
        if not phase:
            return False, f"阶段 {phase_id} 不存在"
        if phase.get("status") != "failed":
            return False, f"阶段 {phase_id} 当前状态为 {phase.get('status')}，只有 failed 状态可重试"
        if not self.store.can_retry(phase_id):
            return False, f"阶段 {phase_id} 已达最大重试次数，需人工介入"
        self.store.set_phase_status(phase_id, "running")
        self.store.add_log(f"阶段 {phase_id} 重试", {"phase": phase_id, "action": "retry"})
        write_event("phase_retry", phase=phase_id, role=phase.get("role", ""))
        return True, f"阶段 {phase_id} 重试中"

    def skip_phase(self, phase_id: str) -> tuple[bool, str]:
        phase = self.store.get_phase(phase_id)
        if not phase:
            return False, f"阶段 {phase_id} 不存在"
        current = phase.get("status")
        if current not in ("pending",):
            return False, f"阶段 {phase_id} 当前状态为 {current}，只有 pending 状态可跳过"
        state = self.store.load()
        state["phases"][phase_id]["status"] = "skipped"
        self.store.save(state)
        self.store.add_log(f"阶段 {phase_id} 已跳过", {"phase": phase_id, "action": "skip"})
        write_event("phase_skip", phase=phase_id, role=phase.get("role", ""))
        return True, f"阶段 {phase_id} 已跳过"

    def get_next_suggested_phase(self) -> Optional[str]:
        current_phase = self.store.get_current_phase()
        if not current_phase:
            phases = self.get_all_phases()
            return phases[0]["id"] if phases else None
        current_status = self.store.get_phase_status(current_phase)
        if current_status == "completed":
            next_ids = self.get_next_phases(current_phase)
            if len(next_ids) == 1:
                return next_ids[0]
            if len(next_ids) > 1:
                decision = self.load_workflow().get("decision_points", {}).get(current_phase)
                if decision:
                    if current_phase == "three_audit":
                        needs_fix = self.store.get_decision("needs_fix", False)
                        return decision["true_branch"] if needs_fix else decision["false_branch"]
                return next_ids[0]
            return None
        if current_status == "failed":
            return current_phase
        return current_phase

    def _check_required_artifacts(self, phase_id: str) -> list[str]:
        config = self.get_phase_config(phase_id)
        if not config:
            return [f"阶段 {phase_id} 配置不存在"]
        required = config.get("required_artifacts", [])
        if not required:
            return []
        missing = []
        for artifact in required:
            artifact_dir = Path(artifact["dir"])
            if not artifact_dir.exists():
                missing.append(f"目录 {artifact['dir']} 不存在")
                continue
            pattern = artifact.get("pattern", "*.md")
            files = list(artifact_dir.glob(pattern))
            min_count = artifact.get("min_count", 1)
            if len(files) < min_count:
                missing.append(f"{artifact['dir']}/{pattern} 文件数不足（需要 {min_count}，实际 {len(files)}）")
                continue
            for f in files:
                try:
                    content = f.read_text(encoding="utf-8")
                except Exception:
                    missing.append(f"无法读取 {f}")
                    continue
                min_length = artifact.get("min_length", 0)
                if len(content.strip()) < min_length:
                    missing.append(f"{f.name} 内容过短（{len(content.strip())} < {min_length}）")
                for section in artifact.get("required_sections", []):
                    if section not in content:
                        missing.append(f"{f.name} 缺少章节: {section}")
        return missing

    def get_sprint_summary(self) -> dict:
        state = self.store.load()
        workflow = self.load_workflow()
        phases_summary = []
        for phase_config in workflow.get("phases", []):
            phase_id = phase_config["id"]
            phase_state = state.get("phases", {}).get(phase_id, {})
            phases_summary.append({
                "id": phase_id,
                "name": phase_config.get("name", ""),
                "role": phase_config.get("role", ""),
                "status": phase_state.get("status", "pending"),
                "gate_required": phase_config.get("gate_required", False),
                "gate_check": phase_state.get("gate_check", False),
            })
        return {
            "sprint_id": state.get("sprint_id", ""),
            "status": state.get("status", "unknown"),
            "current_phase": state.get("current_phase", ""),
            "iteration": state.get("iteration", 1),
            "phases": phases_summary,
        }
