#!/usr/bin/env python3
"""
Integration Tests - Guard + Validator + Runner CLI

Tests the complete guard/validator/runner pipeline with proper
state management and CLI interface validation.
"""

import json
import os
import sys
import tempfile
import shutil
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import importlib.util


def _load_module(name):
    path = Path(__file__).parent.parent / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


class TestCommandGuard:
    def setup_method(self):
        self.m = _load_module("command-guard")

    def test_dangerous_rm_blocked(self):
        try:
            sys.argv = ["command-guard.py", "rm -rf /workspace"]
            self.m.main()
            assert False, "Should have exited"
        except SystemExit as e:
            assert e.code == 2

    def test_drop_database_blocked(self):
        try:
            sys.argv = ["command-guard.py", "mysql -e 'DROP DATABASE users'"]
            self.m.main()
            assert False, "Should have exited"
        except SystemExit as e:
            assert e.code == 2

    def test_safe_command_allowed(self):
        try:
            sys.argv = ["command-guard.py", "python3 -m py_compile test.py"]
            self.m.main()
        except SystemExit as e:
            assert e.code == 0

    def test_empty_command_allowed(self):
        try:
            sys.argv = ["command-guard.py", ""]
            self.m.main()
        except SystemExit as e:
            assert e.code == 0

    def test_no_args_allowed(self):
        try:
            sys.argv = ["command-guard.py"]
            self.m.main()
        except SystemExit as e:
            assert e.code == 0


class TestDeleteGuard:
    def setup_method(self):
        self.m = _load_module("delete-guard")

    def test_rm_blocked(self):
        try:
            sys.argv = ["delete-guard.py", "rm file.txt"]
            self.m.main()
            assert False, "Should have exited"
        except SystemExit as e:
            assert e.code == 2

    def test_git_rm_blocked(self):
        try:
            sys.argv = ["delete-guard.py", "git rm -r src/"]
            self.m.main()
            assert False, "Should have exited"
        except SystemExit as e:
            assert e.code == 2

    def test_safe_command_allowed(self):
        try:
            sys.argv = ["delete-guard.py", "git status"]
            self.m.main()
        except SystemExit as e:
            assert e.code == 0

    def test_unlink_blocked(self):
        try:
            sys.argv = ["delete-guard.py", "unlink /etc/passwd"]
            self.m.main()
            assert False, "Should have exited"
        except SystemExit as e:
            assert e.code == 2


class TestArtifactValidator:
    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()
        os.chdir(self.tmpdir)
        self.m = _load_module("artifact-validator")

    def teardown_method(self):
        os.chdir(self.old_cwd)
        shutil.rmtree(self.tmpdir)

    def test_no_config_returns_empty(self):
        issues = self.m.validate_artifacts("nonexistent_phase")
        assert len(issues) == 1

    def test_zero_phase_no_artifacts_needed(self):
        issues = self.m.validate_artifacts("zero")
        assert len(issues) == 0

    def test_one_architect_missing_dir(self):
        issues = self.m.validate_artifacts("one_architect")
        assert any("不存在" in i for i in issues)

    def test_one_architect_valid_with_all_sections(self):
        os.makedirs("docs/architecture")
        content = "# 架构\n\n## 领域建模\ntext\n\n## MVP\ntext\n\n## API 契约\ntext\n\n## 验收标准\ntext\n\n"
        content += "x" * 600
        with open("docs/architecture/plan.md", "w") as f:
            f.write(content)
        issues = self.m.validate_artifacts("one_architect")
        assert len(issues) == 0

    def test_validate_file_nonexistent(self):
        issues = self.m.validate_file("no_such_file.md")
        assert len(issues) >= 1

    def test_validate_file_empty(self):
        with open("empty.md", "w") as f:
            f.write("")
        issues = self.m.validate_file("empty.md")
        assert any("空" in i for i in issues)


class TestQualityValidator:
    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()
        os.chdir(self.tmpdir)
        self.m = _load_module("quality-validator")

    def teardown_method(self):
        os.chdir(self.old_cwd)
        shutil.rmtree(self.tmpdir)

    def test_passes_clean_content(self):
        with open("clean.md", "w") as f:
            f.write("# 干净的文档\n\n这是一段没有问题的内容。\n很完整。\n很好。\n")
        issues = self.m.check_quality("clean.md")
        assert len(issues) == 0

    def test_detects_fixme(self):
        with open("fixme.md", "w") as f:
            f.write("# FIXME: 这里需要重构\n")
        issues = self.m.check_quality("fixme.md")
        assert any("临时" in i for i in issues)

    def test_detects_hack(self):
        with open("hack.md", "w") as f:
            f.write("# HACK: 临时修复方案\n")
        issues = self.m.check_quality("hack.md")
        assert any("临时" in i for i in issues)

    def test_detects_placeholder(self):
        with open("placeholder.md", "w") as f:
            f.write("# TODO: placeholder\n\n这里填写具体内容\n")
        issues = self.m.check_quality("placeholder.md")
        assert any("placeholder" in i.lower() or "TODO" in i for i in issues)

    def test_detects_delay_promise(self):
        with open("delay.md", "w") as f:
            f.write("# 报告\n\n后续再补充详细内容。\n")
        issues = self.m.check_quality("delay.md")
        assert any("延迟" in i or "TODO" in i for i in issues)

    def test_nonexistent_file(self):
        issues = self.m.check_quality("nonexistent.md")
        assert any("不存在" in i for i in issues)


def run_tests():
    classes = [TestCommandGuard, TestDeleteGuard, TestArtifactValidator, TestQualityValidator]
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
            except AssertionError as e:
                print(f"  FAIL: {cls.__name__}.{method_name} - {e}")
                failed += 1
            except SystemExit:
                print(f"  FAIL: {cls.__name__}.{method_name} - unexpected SystemExit")
                failed += 1
            except Exception as e:
                print(f"  FAIL: {cls.__name__}.{method_name} - {e}")
                failed += 1
            finally:
                try:
                    instance.teardown_method()
                except Exception:
                    pass

    print(f"\n{passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
