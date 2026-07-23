"""GR-01 Phase 3 - characterization tests for core.router.route().

These lock the CURRENT routing behavior (including natural_command_route
interception and keyword-list precedence). Offline: route() only does
keyword matching + a state read; no network. Generated from live route()
output, then reviewed.
"""
import importlib

import pytest

route = importlib.import_module("core.router").route

CASES = [
    ('voice status', 'system'),
    ('voice speak привет', 'system'),
    ('voice test', 'system'),
    ('gpt browser', 'gpt_browser'),
    ('закрой чатгпт браузер', 'gpt_browser'),
    ('chatgpt browser', 'gpt_browser'),
    ('browser autopilot', 'browser'),
    ('браузер план', 'browser'),
    ('browser research', 'browser'),
    ('browser page audit', 'browser'),
    ('аудит страницы', 'browser'),
    ('тильда', 'browser'),
    ('dev task', 'automation'),
    ('pc task', 'automation'),
    ('after patch', 'automation'),
    ('центр автоматизации', 'automation'),
    ('stability test', 'stability'),
    ('тест стабильности', 'stability'),
    ('автотест', 'stability'),
    ('help', 'system'),
    ('статус', 'system'),
    ('память', 'system'),
    ('project health', 'system'),
    ('какая модель', 'system'),
    ('rollback', 'system'),
    ('что ты умеешь', 'system'),
    ('калькулятор', 'windows'),
    ('notepad', 'windows'),
    ('открой хром', 'windows'),
    ('запусти приложение', 'windows'),
    ('paint', 'windows'),
    ('выбери лучший', 'operator'),
    ('топ 5 моделей', 'operator'),
    ('что лучше', 'operator'),
    ('покажи последний отчет', 'browser'),
    ('последний отчет', 'browser'),
    ('сделай отчет', 'browser'),
    ('изучи тему', 'browser'),
    ('проанализируй данные', 'research'),
    ('найди информацию', 'research'),
    ('создай современный сайт', 'project'),
    ('сайт компании', 'project'),
    ('проверь и улучши', 'project'),
    ('создай сайт', 'codegen'),
    ('лендинг', 'codegen'),
    ('визитку', 'codegen'),
    ('редизайн', 'codegen'),
    ('создай папку', 'files'),
    ('создай файл', 'files'),
    ('покажи файлы', 'files'),
    ('удали файл', 'files'),
    ('найди кофе', 'browser'),
    ('поиск погоды', 'browser'),
    ('youtube', 'browser'),
    ('открой сайт', 'browser'),
    ('прочитай страницу', 'browser'),
    ('привет', 'unknown'),
    ('как дела сегодня', 'unknown'),
    ('расскажи анекдот', 'unknown'),
    ('', 'unknown'),
    ('  СТАТУС  ', 'system'),
    ('HELP', 'system'),
]


@pytest.mark.parametrize("text,expected", CASES)
def test_route_characterization(text, expected):
    assert route(text) == expected


def test_windows_type_ignored_without_last_windows_app(monkeypatch):
    import core.router as r
    monkeypatch.setattr(r, "get_value", lambda key, default=None: None)
    assert r.route("напечатай привет всем") == "unknown"


def test_windows_type_routes_to_windows_with_last_windows_app(monkeypatch):
    import core.router as r
    monkeypatch.setattr(r, "get_value", lambda key, default=None: "notepad")
    assert r.route("напечатай привет всем") == "windows"


def test_windows_type_second_verb_with_last_windows_app(monkeypatch):
    import core.router as r
    monkeypatch.setattr(r, "get_value", lambda key, default=None: "notepad")
    assert r.route("введи текст") == "windows"
