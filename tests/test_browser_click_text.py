"""Characterization test: browser_agent click_text routing.

Proves that action=="click_text" is handled by the FIRST block (line ~302)
which wraps result in _friendly_browser_action_result, and that no second
handler is reachable.

Uses careful sys.modules cleanup to avoid polluting the agents package
namespace (test_executor.py injects fake agents via sys.modules).
"""
import sys

import pytest


@pytest.fixture
def browser_env(monkeypatch, tmp_path):
    import core.state as st
    monkeypatch.setattr(st, "STATE_FILE", tmp_path / "state.json")

    saved_mod = sys.modules.pop("agents.browser_agent", None)
    saved_attr = None
    import agents
    if hasattr(agents, "browser_agent"):
        saved_attr = agents.browser_agent
        delattr(agents, "browser_agent")

    import agents.browser_agent as ba

    calls = []
    monkeypatch.setattr(
        ba, "click_by_text",
        lambda text: calls.append(("click_by_text", text)) or f"clicked: {text}"
    )

    yield ba, calls

    sys.modules.pop("agents.browser_agent", None)
    if hasattr(agents, "browser_agent"):
        delattr(agents, "browser_agent")
    if saved_mod is not None:
        sys.modules["agents.browser_agent"] = saved_mod
    if saved_attr is not None:
        agents.browser_agent = saved_attr


def test_click_text_returns_friendly_result(browser_env):
    ba, calls = browser_env
    result = ba.handle("click_text", {"text": "YouTube"})
    assert result == "clicked: YouTube"
    assert calls == [("click_by_text", "YouTube")]


def test_click_text_saves_state(browser_env):
    ba, calls = browser_env
    import core.state as st
    ba.handle("click_text", {"text": "Search"})
    assert st.get_value("last_browser_action") == "click_text"
    assert "clicked: Search" in st.get_value("last_browser_result", "")


def test_click_text_empty_text(browser_env):
    ba, calls = browser_env
    result = ba.handle("click_text", {})
    assert result == "clicked: "
    assert calls == [("click_by_text", "")]
