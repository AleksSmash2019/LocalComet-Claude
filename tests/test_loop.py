"""GR-01 Phase 5 - characterization tests for core.loop.run_loop.

Offline: route/plan/execute/ask_llm are monkeypatched (no LLM, no agents run).
core.loop imports core.executor (which imports 17 agents with heavy deps), so we
inject fake agent modules before import, same pattern as the executor tests.

These tests deliberately cover the two broad `except Exception` paths (step failure
and review failure) with arbitrary exception types (RuntimeError) - which is why the
broad excepts CANNOT be safely narrowed to json/parse types without changing
behavior. Narrowing is therefore intentionally NOT applied in Phase 5 (documented).
"""
import importlib
import sys
import types

import pytest

AGENTS = [
    "browser_agent", "code_agent", "file_agent", "operator_agent", "project_agent",
    "research_agent", "windows_agent", "system_agent", "workspace_agent",
    "diagnostics_agent", "history_agent", "maintenance_agent", "self_edit_agent",
    "gpt_agent", "chatgpt_relay_agent", "stability_agent", "automation_agent",
    "gpt_browser_agent",
]


@pytest.fixture
def loopmod():
    keys = [f"agents.{n}" for n in AGENTS] + ["core.executor", "core.loop"]
    saved = {k: sys.modules.get(k) for k in keys}
    for n in AGENTS:
        m = types.ModuleType(f"agents.{n}")
        m.handle = lambda action, plan: "fake"
        sys.modules[f"agents.{n}"] = m
    sys.modules.pop("core.executor", None)
    sys.modules.pop("core.loop", None)
    L = importlib.import_module("core.loop")
    yield L
    for k, v in saved.items():
        if v is None:
            sys.modules.pop(k, None)
        else:
            sys.modules[k] = v


def _wire(L, monkeypatch, review, route="system", plan=None, result="R"):
    monkeypatch.setattr(L, "route", lambda t: route)
    monkeypatch.setattr(L, "plan", lambda t, r: plan if plan is not None else {"tool": "none"})
    monkeypatch.setattr(L, "execute", lambda p: result)
    monkeypatch.setattr(L, "ask_llm", lambda s, u, **k: review)


def test_immediate_done(loopmod, monkeypatch):
    _wire(loopmod, monkeypatch, '{"done": true, "message": "Готово"}')
    assert loopmod.run_loop("task") == "Готово"


def test_done_default_message(loopmod, monkeypatch):
    _wire(loopmod, monkeypatch, '{"done": true}')
    assert loopmod.run_loop("task") == "Готово"


def test_done_custom_message(loopmod, monkeypatch):
    _wire(loopmod, monkeypatch, '{"done": true, "message": "Всё сделано"}')
    assert loopmod.run_loop("task") == "Всё сделано"


def test_review_code_fences_stripped(loopmod, monkeypatch):
    _wire(loopmod, monkeypatch, '```json\n{"done": true, "message": "OK"}\n```')
    assert loopmod.run_loop("task") == "OK"


def test_step_exception_returns_error(loopmod, monkeypatch):
    monkeypatch.setattr(loopmod, "route", lambda t: (_ for _ in ()).throw(RuntimeError("nope")))
    monkeypatch.setattr(loopmod, "ask_llm", lambda *a, **k: '{"done": true}')
    result = loopmod.run_loop("task")
    assert result.startswith("Шаг упал с ошибкой:") and "nope" in result


def test_review_exception_returns_partial(loopmod, monkeypatch):
    _wire(loopmod, monkeypatch, "unused")
    monkeypatch.setattr(loopmod, "ask_llm", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("review boom")))
    assert loopmod.run_loop("task") == "Задача выполнена частично, но проверка результата сломалась."


def test_no_next_step_stops(loopmod, monkeypatch):
    _wire(loopmod, monkeypatch, '{"done": false}')
    assert loopmod.run_loop("task") == "Остановлено: нет следующего шага."


def test_empty_next_step_stops(loopmod, monkeypatch):
    _wire(loopmod, monkeypatch, '{"done": false, "next_step": ""}')
    assert loopmod.run_loop("task") == "Остановлено: нет следующего шага."


def test_max_steps_reached(loopmod, monkeypatch):
    _wire(loopmod, monkeypatch, '{"done": false, "next_step": "keep going"}')
    assert loopmod.run_loop("task", max_steps=3) == "Остановлено: достигнут лимит шагов."


def test_multistep_then_done(loopmod, monkeypatch):
    seq = iter(['{"done": false, "next_step": "step2"}', '{"done": true, "message": "Fin"}'])
    _wire(loopmod, monkeypatch, "x")
    monkeypatch.setattr(loopmod, "ask_llm", lambda *a, **k: next(seq))
    assert loopmod.run_loop("task", max_steps=5) == "Fin"


def test_done_not_boolean_true_is_not_done(loopmod, monkeypatch):
    _wire(loopmod, monkeypatch, '{"done": "yes"}')
    assert loopmod.run_loop("task") == "Остановлено: нет следующего шага."
