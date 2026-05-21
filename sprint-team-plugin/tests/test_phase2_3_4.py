#!/usr/bin/env python3
"""
Tests for Permission Guard, Artifact Validator, Quality Validator, and Event Log
"""

import importlib.util
import json
import os
import sys
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


def _load_module(name):
    path = Path(__file__).parent.parent / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


class TestPermissionGuard:
    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()
        os.chdir(self.tmpdir)
        os.makedirs("sprints")
        os.makedirs("sprint-team-plugin/templates")
        self._write_config()
        self._write_state()
        mod = _load_module("permission-guard")
        self.check_permission = mod.check_permission

    def teardown_method(self):
        os.chdir(self.old_cwd)
        shutil.rmtree(self.tmpdir)

    def _write_config(self):
        config = {
            "permissions": {
                "product-architect": {
                    "allowed_dirs": ["docs/architecture"],
                    "allowed_file_extensions": [".md"],
                    "max_file_size_kb": 512,
                },
                "auto-fix-engineer": {
                    "allowed_dirs": ["docs/fixes"],
                    "allowed_file_extensions": [".md", ".py"],
                    "restricted_dirs": ["node_modules", ".git"],
                },
            },
            "global_restrictions": {
                "forbidden_dirs": [".git", "node_modules"],
                "forbidden_files": [".env", "*.key"],
            }
        }
        with open("sprint-team-plugin/templates/permissions.json", "w") as f:
            json.dump(config, f)

    def _write_state(self, phase="zero", role="product-architect"):
        state = {
            "sprint_id": "test",
            "current_phase": phase,
            "phases": {
                "zero": {"role": role, "status": "pending"},
                "four_fix_execute": {"role": "auto-fix-engineer", "status": "pending"},
            },
        }
        with open("sprints/sprint-state.json", "w") as f:
            json.dump(state, f)

    def test_allowed_write_correct_dir(self):
        ok, msg = self.check_permission("docs/architecture/plan.md")
        assert ok

    def test_denied_write_wrong_dir(self):
        ok, msg = self.check_permission("src/code.py")
        assert not ok

    def test_denied_forbidden_dir(self):
        ok, msg = self.check_permission(".git/config")
        assert not ok

    def test_denied_forbidden_file(self):
        ok, msg = self.check_permission(".env")
        assert not ok

    def test_denied_wrong_extension(self):
        ok, msg = self.check_permission("docs/architecture/data.json")
        assert not ok

    def test_auto_fix_engineer_restricted_dirs(self):
        self._write_state("four_fix_execute", "auto-fix-engineer")
        ok, msg = self.check_permission("docs/fixes/node_modules/x.js")
        assert not ok

    def test_auto_fix_engineer_allowed(self):
        self._write_state("four_fix_execute", "auto-fix-engineer")
        ok, msg = self.check_permission("docs/fixes/fix.py")
        assert ok

    def test_no_role_allows(self):
        self._write_state("zero", "")
        ok, msg = self.check_permission("anything/at/all.js")
        assert ok


class TestArtifactValidator:
    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()
        os.chdir(self.tmpdir)
        self.m = _load_module("artifact-validator")
        self.validate = self.m.validate_artifacts

    def teardown_method(self):
        os.chdir(self.old_cwd)
        shutil.rmtree(self.tmpdir)

    def test_missing_dir(self):
        issues = self.validate("one_architect")
        assert len(issues) >= 1

    def test_valid_artifacts(self):
        os.makedirs("docs/architecture")
        content = "# Plan\n\n## 领域建模\n\n## MVP\n\n## API 契约\n\n## 验收标准\n\n"
        content += "x" * 500
        with open("docs/architecture/plan.md", "w") as f:
            f.write(content)
        issues = self.validate("one_architect")
        assert len(issues) == 0

    def test_missing_section(self):
        os.makedirs("docs/architecture")
        with open("docs/architecture/plan.md", "w") as f:
            f.write("# Plan\n\n内容")
        issues = self.validate("one_architect")
        assert any("缺少" in i for i in issues)


class TestQualityValidator:
    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()
        os.chdir(self.tmpdir)
        self.m = _load_module("quality-validator")
        self.check = self.m.check_quality

    def teardown_method(self):
        os.chdir(self.old_cwd)
        shutil.rmtree(self.tmpdir)

    def test_clean_file(self):
        with open("clean.md", "w") as f:
            f.write("# 标题\n\n这是一段干净的Markdown内容。\n没有TODO也没有占位符。\n")
        issues = self.check("clean.md")
        assert len(issues) == 0

    def test_detects_todo(self):
        with open("todo.md", "w") as f:
            f.write("# TODO: 需要完成这个功能\n")
        issues = self.check("todo.md")
        assert any("TODO" in i for i in issues)


class TestEventLog:
    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()
        os.chdir(self.tmpdir)
        os.makedirs("sprints/logs", exist_ok=True)
        self.m = _load_module("event_log")
        self.write = self.m.write_event
        self.get_events = self.m.get_sprint_events

    def teardown_method(self):
        os.chdir(self.old_cwd)
        shutil.rmtree(self.tmpdir)

    def test_write_and_read_event(self):
        tid = self.write("phase_start", sprint_id="test", phase="zero", role="test")
        assert ":" in tid
        events = self.get_events()
        assert len(events) >= 1

    def test_filter_by_sprint_id(self):
        self.write("a", sprint_id="sprint-1")
        self.write("b", sprint_id="sprint-2")
        events = self.get_events("sprint-1")
        assert all(e.get("sprint_id") == "sprint-1" for e in events)


def run_tests():
    classes = [TestPermissionGuard, TestArtifactValidator, TestQualityValidator, TestEventLog]
    passed = 0
    failed = 0
    for cls in classes:
        instance = cls()
        for method_name in sorted(m for m in dir(instance) if m.startswith("test_")):
            instance.setup_method()
            try:
                getattr(instance, method_name)()
                print(f"  PASS: {cls.__name__}.{method_name}")
                passed += 1
            except Exception as e:
                print(f"  FAIL: {cls.__name__}.{method_name} - {e}")
                failed += 1
            finally:
                instance.teardown_method()

    print(f"\n{passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
