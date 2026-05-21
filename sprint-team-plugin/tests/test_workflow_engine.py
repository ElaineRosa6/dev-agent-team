#!/usr/bin/env python3
"""
Tests for WorkflowEngine and StateStore
"""

import json
import os
import sys
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from state_store import StateStore
from workflow_engine import WorkflowEngine


def create_test_state(tmpdir: str) -> str:
    state = {
        "sprint_id": "sprint-test",
        "status": "initialized",
        "mode": "normal",
        "current_phase": "zero",
        "current_role": None,
        "iteration": 1,
        "phases": {
            "zero": {
                "name": "迭代启动",
                "role": "devops-manager",
                "status": "pending",
                "started_at": None,
                "completed_at": None,
                "failed_at": None,
                "failure_reason": None,
                "retry_count": 0,
                "max_retries": 2,
                "gate_check": False,
                "output_validated": False,
                "artifacts": [],
            },
            "one_architect": {
                "name": "架构规划",
                "role": "product-architect",
                "status": "pending",
                "started_at": None,
                "completed_at": None,
                "failed_at": None,
                "failure_reason": None,
                "retry_count": 0,
                "max_retries": 2,
                "gate_check": False,
                "output_validated": False,
                "artifacts": [],
            },
            "one_planner": {
                "name": "安全切片",
                "role": "slice-planner",
                "status": "pending",
                "started_at": None,
                "completed_at": None,
                "failed_at": None,
                "failure_reason": None,
                "retry_count": 0,
                "max_retries": 2,
                "gate_check": False,
                "output_validated": False,
                "artifacts": [],
            },
            "five_summary": {
                "name": "迭代收尾",
                "role": "devops-manager",
                "status": "pending",
                "started_at": None,
                "completed_at": None,
                "failed_at": None,
                "failure_reason": None,
                "retry_count": 0,
                "max_retries": 2,
                "gate_check": False,
                "output_validated": False,
                "artifacts": [],
            },
        },
        "context": {},
        "outputs": {},
        "decisions": {},
        "logs": [],
    }
    state_path = os.path.join(tmpdir, "sprint-state.json")
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    return state_path


def create_test_workflow(tmpdir: str) -> str:
    workflow = {
        "version": "1.0.0",
        "phases": [
            {
                "id": "zero",
                "name": "迭代启动",
                "role": "devops-manager",
                "required_artifacts": [],
                "gate_required": False,
                "next_phases": ["one_architect"],
            },
            {
                "id": "one_architect",
                "name": "架构规划",
                "role": "product-architect",
                "required_artifacts": [
                    {
                        "dir": "docs/architecture",
                        "pattern": "*.md",
                        "min_count": 1,
                        "required_sections": ["MVP"],
                        "min_length": 100,
                    }
                ],
                "gate_required": True,
                "next_phases": ["one_planner"],
            },
            {
                "id": "one_planner",
                "name": "安全切片",
                "role": "slice-planner",
                "required_artifacts": [],
                "gate_required": False,
                "next_phases": ["five_summary"],
            },
            {
                "id": "five_summary",
                "name": "迭代收尾",
                "role": "devops-manager",
                "required_artifacts": [],
                "gate_required": False,
                "next_phases": [],
            },
        ],
        "decision_points": {},
    }
    workflow_path = os.path.join(tmpdir, "workflow.json")
    with open(workflow_path, "w", encoding="utf-8") as f:
        json.dump(workflow, f, ensure_ascii=False, indent=2)
    return workflow_path


class TestStateStore:
    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.state_path = create_test_state(self.tmpdir)
        self.store = StateStore(self.state_path)

    def teardown_method(self):
        shutil.rmtree(self.tmpdir)

    def test_load(self):
        state = self.store.load()
        assert state["sprint_id"] == "sprint-test"

    def test_get_current_phase(self):
        assert self.store.get_current_phase() == "zero"

    def test_get_current_role(self):
        assert self.store.get_current_role() == "devops-manager"

    def test_get_phase_status(self):
        assert self.store.get_phase_status("zero") == "pending"
        assert self.store.get_phase_status("nonexistent") == "unknown"

    def test_set_phase_status_running(self):
        self.store.set_phase_status("zero", "running")
        assert self.store.get_phase_status("zero") == "running"
        assert self.store.get_phase("zero")["started_at"] is not None

    def test_set_phase_status_completed(self):
        self.store.set_phase_status("zero", "running")
        self.store.set_phase_status("zero", "completed")
        assert self.store.get_phase_status("zero") == "completed"
        assert self.store.get_phase("zero")["completed_at"] is not None

    def test_set_phase_status_failed(self):
        self.store.set_phase_status("zero", "running")
        self.store.set_phase_status("zero", "failed", "test error")
        assert self.store.get_phase_status("zero") == "failed"
        assert self.store.get_phase("zero")["failure_reason"] == "test error"
        assert self.store.get_phase("zero")["retry_count"] == 1

    def test_can_retry(self):
        self.store.set_phase_status("zero", "running")
        self.store.set_phase_status("zero", "failed", "err")
        assert self.store.can_retry("zero")
        self.store.set_phase_status("zero", "running")
        self.store.set_phase_status("zero", "failed", "err")
        assert not self.store.can_retry("zero")

    def test_add_log(self):
        self.store.add_log("test message", {"key": "value"})
        state = self.store.load()
        assert len(state["logs"]) == 1
        assert state["logs"][0]["message"] == "test message"

    def test_backup_on_save(self):
        self.store.save(self.store.load())
        assert Path(self.state_path + ".bak").exists()


class TestWorkflowEngine:
    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.state_path = create_test_state(self.tmpdir)
        self.workflow_path = create_test_workflow(self.tmpdir)
        self.engine = WorkflowEngine(
            workflow_path=self.workflow_path,
            state_path=self.state_path,
        )

    def teardown_method(self):
        shutil.rmtree(self.tmpdir)

    def test_get_next_suggested_phase_initial(self):
        self.engine.store.set_current_phase("zero")
        next_phase = self.engine.get_next_suggested_phase()
        assert next_phase == "zero"

    def test_start_phase(self):
        ok, msg = self.engine.start_phase("zero")
        assert ok
        assert self.engine.store.get_phase_status("zero") == "running"

    def test_cannot_start_completed_phase(self):
        self.engine.start_phase("zero")
        self.engine.store.set_phase_status("zero", "completed")
        ok, msg = self.engine.start_phase("zero")
        assert not ok

    def test_complete_phase_without_artifacts(self):
        self.engine.start_phase("zero")
        ok, msg = self.engine.complete_phase("zero")
        assert ok

    def test_complete_phase_with_missing_artifacts(self):
        import os as _os
        _cwd = _os.getcwd()
        _os.chdir(self.tmpdir)
        try:
            engine = WorkflowEngine(
                workflow_path=self.workflow_path,
                state_path=self.state_path,
            )
            engine.start_phase("one_architect")
            ok, msg = engine.complete_phase("one_architect")
            assert not ok
        finally:
            _os.chdir(_cwd)

    def test_complete_phase_with_valid_artifacts(self):
        import os as _os
        _cwd = _os.getcwd()
        _os.chdir(self.tmpdir)
        try:
            engine = WorkflowEngine(
                workflow_path=self.workflow_path,
                state_path=self.state_path,
            )
            docs_dir = os.path.join(self.tmpdir, "docs", "architecture")
            os.makedirs(docs_dir)
            content = "# Test\n\n## MVP\n\n" + "x" * 200
            with open(os.path.join(docs_dir, "plan.md"), "w") as f:
                f.write(content)
            engine.start_phase("one_architect")
            missing = engine._check_required_artifacts("one_architect")
            assert len(missing) == 0
        finally:
            _os.chdir(_cwd)

    def test_fail_and_retry(self):
        self.engine.start_phase("zero")
        self.engine.fail_phase("zero", "test")
        assert self.engine.store.get_phase_status("zero") == "failed"
        ok, msg = self.engine.retry_phase("zero")
        assert ok
        assert self.engine.store.get_phase_status("zero") == "running"

    def test_max_retries_exceeded(self):
        self.engine.start_phase("zero")
        for _ in range(3):
            self.engine.fail_phase("zero", "err")
            if self.engine.store.can_retry("zero"):
                self.engine.retry_phase("zero")
        ok, msg = self.engine.retry_phase("zero")
        assert not ok
        assert "最大重试" in msg

    def test_skip_phase(self):
        ok, msg = self.engine.skip_phase("one_planner")
        assert ok
        assert self.engine.store.get_phase_status("one_planner") == "skipped"

    def test_cannot_skip_running_phase(self):
        self.engine.start_phase("zero")
        ok, msg = self.engine.skip_phase("zero")
        assert not ok

    def test_invalid_transition(self):
        ok, msg = self.engine.complete_phase("zero")
        assert not ok

    def test_sprint_summary(self):
        summary = self.engine.get_sprint_summary()
        assert summary["sprint_id"] == "sprint-test"
        assert len(summary["phases"]) == 4


def run_tests():
    tests = TestStateStore()
    methods = [m for m in dir(tests) if m.startswith("test_")]
    passed = 0
    failed = 0
    for method_name in methods:
        tests.setup_method()
        try:
            getattr(tests, method_name)()
            print(f"  PASS: {method_name}")
            passed += 1
        except Exception as e:
            print(f"  FAIL: {method_name} - {e}")
            failed += 1
        finally:
            tests.teardown_method()

    tests = TestWorkflowEngine()
    methods = [m for m in dir(tests) if m.startswith("test_")]
    for method_name in methods:
        tests.setup_method()
        try:
            getattr(tests, method_name)()
            print(f"  PASS: {method_name}")
            passed += 1
        except Exception as e:
            print(f"  FAIL: {method_name} - {e}")
            failed += 1
        finally:
            tests.teardown_method()

    print(f"\n{passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
