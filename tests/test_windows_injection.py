"""Negative test: H-01 — shell injection via app name in windows.open_app.

Proves that arbitrary strings passed as app names are rejected by the
allowlist and never reach subprocess execution.
"""
from unittest.mock import patch, MagicMock

import pytest


class TestWindowsOpenAppInjection:
    def test_unknown_app_rejected_not_executed(self):
        """An app name not in APP_COMMANDS must be rejected, not executed."""
        with patch("modules.windows.subprocess.Popen") as mock_popen:
            from modules.windows import open_app
            result = open_app("calc & whoami")

        mock_popen.assert_not_called()
        assert "не найдено" in result or "Access denied" in result.lower() or "разреш" in result

    def test_shell_metacharacters_rejected(self):
        """Shell metacharacters in app name must not reach Popen."""
        payloads = [
            "notepad; calc",
            "calc | whoami",
            "$(whoami)",
            "calc.exe & net user",
            "start http://evil.com",
        ]
        with patch("modules.windows.subprocess.Popen") as mock_popen:
            from modules.windows import open_app
            for payload in payloads:
                result = open_app(payload)
                assert "не найдено" in result or "разреш" in result, (
                    f"Payload {payload!r} was not rejected: {result}"
                )

        mock_popen.assert_not_called()

    def test_allowlisted_app_uses_list_args(self):
        """A valid app must be launched with list args, no shell."""
        with patch("modules.windows.subprocess.Popen") as mock_popen:
            with patch("modules.windows.time.sleep"):
                with patch("modules.windows.set_value"):
                    from modules.windows import open_app
                    result = open_app("calc")

        mock_popen.assert_called_once_with(["calc"])
        assert "Открыл" in result

    def test_allowlisted_app_no_shell_kwarg(self):
        """Popen must not receive shell=True for allowlisted apps."""
        with patch("modules.windows.subprocess.Popen") as mock_popen:
            with patch("modules.windows.time.sleep"):
                with patch("modules.windows.set_value"):
                    from modules.windows import open_app
                    open_app("chrome")

        call_kwargs = mock_popen.call_args[1] if mock_popen.call_args[1] else {}
        assert call_kwargs.get("shell") is not True
        call_args = mock_popen.call_args[0][0]
        assert isinstance(call_args, list)
