"""GR-01 Phase 3 - characterization tests for core.executor.execute().

core.executor imports 17 agent modules at import time, several of which pull heavy
Windows/browser deps (playwright, pyautogui) absent in the offline sandbox. We
inject lightweight fake agent modules (each exposing handle(action, plan)) into
sys.modules before importing core.executor, so we can characterize the dispatch
table (tool -> agent) and the structural plan handling without those deps.
"""
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

TOOL_AGENT = {
    "system": "system_agent", "diagnostics": "diagnostics_agent",
    "history": "history_agent", "maintenance": "maintenance_agent",
    "self_edit": "self_edit_agent", "gpt": "gpt_agent",
    "chatgpt_relay": "chatgpt_relay_agent", "stability": "stability_agent",
    "automation": "automation_agent", "gpt_browser": "gpt_browser_agent",
    "workspace": "workspace_agent", "browser": "browser_agent",
    "file": "file_agent", "files": "file_agent",
    "code": "code_agent", "codegen": "code_agent",
    "project": "project_agent", "research": "research_agent",
    "operator": "operator_agent", "windows": "windows_agent",
}


@pytest.fixture(scope="module")
def execute():
    keys = [f"agents.{n}" for n in AGENTS] + ["core.executor"]
    saved = {k: sys.modules.get(k) for k in keys}
    for n in AGENTS:
        mod = types.ModuleType(f"agents.{n}")
        mod.handle = (lambda agent: (lambda action, plan: {"agent": agent, "action": action, "plan": plan}))(n)
        sys.modules[f"agents.{n}"] = mod
    sys.modules.pop("core.executor", None)
    import core.executor as ex
    yield ex.execute
    for k, v in saved.items():
        if v is None:
            sys.modules.pop(k, None)
        else:
            sys.modules[k] = v


@pytest.mark.parametrize("tool,agent", sorted(TOOL_AGENT.items()))
def test_dispatch_routes_to_agent(execute, tool, agent):
    plan = {"tool": tool, "action": "go"}
    assert execute(plan) == {"agent": agent, "action": "go", "plan": plan}


def test_none_plan(execute):
    assert execute(None) == "Executor: пустой план."


def test_int_plan(execute):
    assert execute(123) == "Executor: неправильный формат плана: 123"


def test_str_plan(execute):
    assert execute("str") == "Executor: неправильный формат плана: str"


def test_empty_dict_no_tool(execute):
    assert execute({}) == "Executor: неизвестный инструмент. План: {}"


def test_dict_no_tool_with_action(execute):
    assert execute({"action": "x"}) == "Executor: неизвестный инструмент. План: {'action': 'x'}"


def test_empty_tool_string_is_falsy(execute):
    assert execute({"tool": "", "action": "x"}) == "Executor: неизвестный инструмент. План: {'tool': '', 'action': 'x'}"


def test_tool_none_returns_text(execute):
    assert execute({"tool": "none", "text": "hi"}) == "hi"


def test_tool_none_defaults_ok(execute):
    assert execute({"tool": "none"}) == "OK"


def test_tool_none_empty_text_kept(execute):
    assert execute({"tool": "none", "text": ""}) == ""


def test_unknown_tool(execute):
    assert execute({"tool": "zzz"}) == "Executor: неизвестный инструмент: zzz"


def test_actions_not_list(execute):
    assert execute({"actions": "nope"}) == "Executor: поле actions должно быть списком."


def test_actions_list_numbered(execute):
    plan = {"actions": [{"tool": "none", "text": "a"}, {"tool": "none", "text": "b"}]}
    assert execute(plan) == "1. a\n2. b"


def test_top_level_list_numbered(execute):
    assert execute([{"tool": "none", "text": "a"}, {"tool": "none", "text": "b"}]) == "1. a\n2. b"


def test_empty_list(execute):
    assert execute([]) == ""


def test_single_item_list(execute):
    assert execute([{"tool": "none", "text": "solo"}]) == "1. solo"


def test_three_item_numbering(execute):
    plan = [{"tool": "none", "text": "a"}, {"tool": "none", "text": "b"}, {"tool": "none", "text": "c"}]
    assert execute(plan) == "1. a\n2. b\n3. c"


def test_list_with_non_dict_element(execute):
    assert execute([123]) == "1. Executor: неправильный формат плана: 123"


def test_nested_actions_single(execute):
    assert execute({"actions": [{"tool": "none", "text": "x"}]}) == "1. x"


def test_actions_dispatch_to_agent(execute):
    result = execute({"actions": [{"tool": "system", "action": "s"}]})
    assert result.startswith("1. ") and "system_agent" in result


def test_chatgpt_relay_apply_reaches_agent(execute):
    result = execute({"tool": "chatgpt_relay", "action": "apply"})
    assert result == {"agent": "chatgpt_relay_agent", "action": "apply", "plan": {"tool": "chatgpt_relay", "action": "apply"}}
