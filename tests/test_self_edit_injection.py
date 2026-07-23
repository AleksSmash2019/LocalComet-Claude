"""Negative test: C-01 — shell injection via filename in self_edit py_compile.

Proves that filenames with shell metacharacters or spaces do NOT result in
arbitrary command execution or word-splitting when passed through _run_tests
or project_health py_compile paths.
"""
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture
def fake_root(tmp_path):
    """Create a minimal project root with a .py file containing a space."""
    (tmp_path / "core").mkdir()
    (tmp_path / "core" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "hello world.py").write_text("x = 1\n", encoding="utf-8")
    return tmp_path


class TestSelfEditShellInjection:
    def test_compile_handles_space_in_filename_without_shell(self, fake_root):
        """A file named 'hello world.py' must be passed as one arg, not split."""
        changed = [fake_root / "hello world.py"]

        with patch("modules.self_edit.ROOT_DIR", fake_root):
            from modules.self_edit import _run_tests
            ok, output = _run_tests([], changed)

        assert ok, f"py_compile failed for file with space: {output}"
        assert "hello world.py" in output

    def test_py_compile_uses_list_args_not_shell_string(self, fake_root):
        """Verify subprocess.run is called with a list (no shell interpretation)."""
        calls = []
        original_run = subprocess.run

        def spy_run(cmd, **kwargs):
            calls.append((cmd, kwargs))
            return original_run(cmd, **kwargs)

        changed = [fake_root / "hello world.py"]

        with patch("modules.self_edit.ROOT_DIR", fake_root):
            with patch("modules.self_edit.subprocess.run", side_effect=spy_run):
                from modules.self_edit import _run_tests
                _run_tests([], changed)

        assert len(calls) >= 1, "subprocess.run was not called"
        for cmd, kwargs in calls:
            assert isinstance(cmd, list), (
                f"Expected list args, got string: {cmd!r}"
            )
            assert kwargs.get("shell") is not True, (
                f"shell=True must not be used for py_compile: {cmd!r}"
            )
            assert cmd[0] == sys.executable
            assert cmd[1:3] == ["-m", "py_compile"]
            assert cmd[3] == "hello world.py", (
                f"Filename must be a single arg, got: {cmd[3:]}"
            )

    def test_project_health_compile_no_shell(self, fake_root):
        """project_health py_compile must use list args without shell."""
        calls = []

        def spy_run(cmd, **kwargs):
            calls.append((cmd, kwargs))
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

        with patch("modules.self_edit.ROOT_DIR", fake_root):
            with patch("modules.self_edit.subprocess.run", side_effect=spy_run):
                from modules.self_edit import project_health
                project_health()

        assert len(calls) >= 1, "subprocess.run was not called"
        for cmd, kwargs in calls:
            assert isinstance(cmd, list), (
                f"Expected list args, got string: {cmd!r}"
            )
            assert kwargs.get("shell") is not True, (
                f"shell=True must not be used: {cmd!r}"
            )
