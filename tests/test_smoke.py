import importlib


def test_core_modules_import_offline():
    for name in ("localcomet_version", "core.state", "core.router", "core.llm"):
        importlib.import_module(name)


def test_router_route_returns_str_offline():
    from core.router import route
    assert isinstance(route("статус"), str)
    assert isinstance(route(""), str)


def test_llm_offline_helpers():
    from core.llm import format_llm_offline_message, is_llm_offline_error
    msg = format_llm_offline_message()
    assert isinstance(msg, str) and msg
    assert is_llm_offline_error(msg) is True
    assert is_llm_offline_error("some unrelated text") is False
