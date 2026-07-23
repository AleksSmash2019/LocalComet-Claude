"""GR-01 Phase 3 - characterization tests for core.planner.

Offline: ask_llm is mocked (no network); voice/natural/browser-direct paths need
no LLM. natural_command_plan is stubbed to None where we exercise later branches,
so tests isolate the branch under test.
"""
import importlib

import pytest

planner = importlib.import_module("core.planner")


@pytest.mark.parametrize("text,expected", [
    ("voice status", {"tool": "system", "action": "voice_status"}),
    ("voice test", {"tool": "system", "action": "voice_test"}),
    ("voice speak привет мир", {"tool": "system", "action": "voice_speak", "text": "привет мир"}),
    ("voice last report", {"tool": "system", "action": "voice_last_report"}),
    ("hello", None),
    ("just talking", None),
])
def test_voice_direct_plan(text, expected):
    assert planner._voice_direct_plan(text) == expected


@pytest.mark.parametrize("text,expected", [
    ("browser: открой сайт", "открой сайт"),
    ("браузер найди кофе", "найди кофе"),
    ("no prefix here", "no prefix here"),
    ("browser", ""),
])
def test_strip_browser_prefix(text, expected):
    assert planner._strip_browser_prefix(text) == expected


@pytest.mark.parametrize("text,markers,expected", [
    ("open the site now", ["the site"], "now"),
    ("nothing matches", ["xyz"], ""),
    ("a then b then c", ["then"], "b then c"),
])
def test_extract_after(text, markers, expected):
    assert planner._extract_after(text, markers) == expected


def test_plan_voice_direct():
    assert planner.plan("voice status", "system") == {"tool": "system", "action": "voice_status"}


def test_plan_voice_speak_carries_text():
    assert planner.plan("voice speak тест", "system") == {
        "tool": "system", "action": "voice_speak", "text": "тест"}


def test_plan_voice_short_circuits_before_llm(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("ask_llm must not be called for a voice command")
    monkeypatch.setattr(planner, "ask_llm", boom)
    assert planner.plan("voice test", "system") == {"tool": "system", "action": "voice_test"}


def test_plan_browser_direct_branch(monkeypatch):
    monkeypatch.setattr(planner, "natural_command_plan", lambda user: None)
    monkeypatch.setattr(planner, "_browser_direct_plan", lambda user: {"tool": "browser", "action": "open"})
    assert planner.plan("open something", "browser") == {"tool": "browser", "action": "open"}


def _llm(monkeypatch, answer):
    monkeypatch.setattr(planner, "natural_command_plan", lambda user: None)
    monkeypatch.setattr(planner, "_browser_direct_plan", lambda user: None)
    monkeypatch.setattr(planner, "ask_llm", lambda system, user: answer)


def test_plan_llm_offline_returns_answer(monkeypatch):
    _llm(monkeypatch, planner.format_llm_offline_message())
    assert planner.plan("do something", "system") == {
        "tool": "none", "action": "answer", "text": planner.format_llm_offline_message()}


def test_plan_llm_valid_json(monkeypatch):
    _llm(monkeypatch, '{"tool": "system", "action": "help"}')
    assert planner.plan("do something", "system") == {"tool": "system", "action": "help"}


def test_plan_llm_strips_code_fences(monkeypatch):
    _llm(monkeypatch, '```json\n{"tool": "x", "action": "y"}\n```')
    assert planner.plan("do something", "system") == {"tool": "x", "action": "y"}


def test_plan_llm_repairs_single_quotes(monkeypatch):
    _llm(monkeypatch, "{'tool': 'x', 'action': 'y'}")
    assert planner.plan("do something", "system") == {"tool": "x", "action": "y"}


def test_plan_llm_repairs_trailing_comma(monkeypatch):
    _llm(monkeypatch, '{"tool": "x", "action": "y",}')
    assert planner.plan("do something", "system") == {"tool": "x", "action": "y"}


def test_plan_unknown_route_reaches_llm_when_no_direct(monkeypatch):
    _llm(monkeypatch, '{"tool": "none", "action": "answer"}')
    assert planner.plan("qwerty asdf", "unknown") == {"tool": "none", "action": "answer"}
