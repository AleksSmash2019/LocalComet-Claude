"""Tests for json.loads fallback behavior in planner, goal_manager, observer, task_planner.

Verifies that invalid JSON from LLM does not crash the application and returns
safe fallback values instead.
"""
import importlib

import pytest

planner = importlib.import_module("core.planner")
goal_manager = importlib.import_module("next.goal_manager")
observer = importlib.import_module("next.observer")
task_planner = importlib.import_module("next.task_planner")


def _llm(monkeypatch, module, response):
    monkeypatch.setattr(module, "ask_llm", lambda *a, **kw: response)


class TestPlannerJsonFallback:
    def test_invalid_json_returns_safe_plan(self, monkeypatch):
        monkeypatch.setattr(planner, "natural_command_plan", lambda *a: None)
        monkeypatch.setattr(planner, "_browser_direct_plan", lambda *a: None)
        monkeypatch.setattr(planner, "_voice_direct_plan", lambda *a: None)
        _llm(monkeypatch, planner, "not json [[[")
        result = planner.plan("test command", "system")
        assert result["tool"] == "none"
        assert result["action"] == "answer"
        assert "text" in result

    def test_valid_json_still_works(self, monkeypatch):
        monkeypatch.setattr(planner, "natural_command_plan", lambda *a: None)
        monkeypatch.setattr(planner, "_browser_direct_plan", lambda *a: None)
        monkeypatch.setattr(planner, "_voice_direct_plan", lambda *a: None)
        _llm(monkeypatch, planner, '{"tool": "system", "action": "help"}')
        result = planner.plan("help", "system")
        assert result["tool"] == "system"
        assert result["action"] == "help"


class TestGoalManagerJsonFallback:
    def test_invalid_json_returns_fallback(self, monkeypatch):
        _llm(monkeypatch, goal_manager, "not json [[[")
        result = goal_manager.analyze_goal("my goal")
        assert result["goal"] == "my goal"
        assert result["type"] == "unknown"
        assert result["success_criteria"] == []

    def test_valid_json_still_works(self, monkeypatch):
        _llm(monkeypatch, goal_manager, '{"goal": "test", "type": "research", "success_criteria": ["done"]}')
        result = goal_manager.analyze_goal("test")
        assert result["goal"] == "test"
        assert result["type"] == "research"


class TestObserverJsonFallback:
    def test_invalid_json_returns_empty_observation(self, monkeypatch):
        _llm(monkeypatch, observer, "garbage output ###")
        result = observer.observe_page("some page text")
        assert result["summary"] == ""
        assert result["good"] == []
        assert result["problems"] == []
        assert result["score"] == 0

    def test_valid_json_still_works(self, monkeypatch):
        _llm(monkeypatch, observer, '{"summary": "ok", "good": ["a"], "problems": [], "score": 8}')
        result = observer.observe_page("page")
        assert result["summary"] == "ok"
        assert result["score"] == 8


class TestTaskPlannerJsonFallback:
    def test_invalid_json_returns_empty_list(self, monkeypatch):
        _llm(monkeypatch, task_planner, "broken {{{ json")
        result = task_planner.create_tasks("do something")
        assert result == []

    def test_valid_json_still_works(self, monkeypatch):
        _llm(monkeypatch, task_planner, '{"tasks": ["step 1", "step 2"]}')
        result = task_planner.create_tasks("do something")
        assert result == ["step 1", "step 2"]
