"""GR-01 Phase 3 - characterization tests for core.llm.

Offline: pure helpers need nothing; ask_llm's requests.post is monkeypatched so no
network is touched (LM Studio is never contacted).
"""
import importlib

import pytest

llm = importlib.import_module("core.llm")


@pytest.mark.parametrize("text,expected", [
    ("hi", "hi\n\n/no_think"),
    ("  hi  ", "hi\n\n/no_think"),
    ("", "\n\n/no_think"),
    (None, "\n\n/no_think"),
    ("already /no_think here", "already /no_think here"),
    ("uses /think mode", "uses /think mode"),
    ("/NO_THINK", "/NO_THINK"),
])
def test_apply_no_think(text, expected):
    assert llm._apply_no_think(text) == expected


def test_offline_message_stable():
    assert llm.format_llm_offline_message() == (
        "LLM server is offline. Start LM Studio Local Server at "
        "http://127.0.0.1:1234 and try again."
    )


def test_offline_message_ignores_error_arg():
    assert llm.format_llm_offline_message(Exception("boom")) == llm.format_llm_offline_message()


@pytest.mark.parametrize("value,expected", [
    ("LLM_OFFLINE_ERROR: connection refused", True),
    ("random text", False),
    (None, False),
    ("", False),
])
def test_is_llm_offline_error(value, expected):
    assert llm.is_llm_offline_error(value) is expected


def test_is_llm_offline_error_matches_formatted_message():
    assert llm.is_llm_offline_error(llm.format_llm_offline_message()) is True


class _FakeResp:
    def __init__(self, content="HELLO"):
        self._content = content

    def raise_for_status(self):
        return None

    def json(self):
        return {"choices": [{"message": {"content": self._content}}]}


def test_ask_llm_returns_model_content(monkeypatch):
    monkeypatch.setattr(llm.requests, "post", lambda *a, **k: _FakeResp("ANSWER"))
    assert llm.ask_llm("system", "user") == "ANSWER"


def test_ask_llm_builds_expected_payload(monkeypatch):
    captured = {}

    def fake_post(url, json=None, timeout=None):
        captured["url"] = url
        captured["json"] = json
        captured["timeout"] = timeout
        return _FakeResp()

    monkeypatch.setattr(llm.requests, "post", fake_post)
    llm.ask_llm("SYS", "USER", max_tokens=123, temperature=0.5, timeout=42)
    body = captured["json"]
    assert body["model"] == llm.MODEL
    assert body["messages"][0] == {"role": "system", "content": "SYS"}
    assert body["messages"][1]["role"] == "user"
    assert body["messages"][1]["content"].endswith("/no_think")  # no_think default True
    assert body["temperature"] == 0.5
    assert body["max_tokens"] == 123
    assert captured["timeout"] == 42


def test_ask_llm_no_think_false_keeps_user(monkeypatch):
    captured = {}

    def fake_post(url, json=None, timeout=None):
        captured["json"] = json
        return _FakeResp()

    monkeypatch.setattr(llm.requests, "post", fake_post)
    llm.ask_llm("SYS", "USER", no_think=False)
    assert captured["json"]["messages"][1]["content"] == "USER"


def test_ask_llm_connection_error_is_offline(monkeypatch):
    def boom(*a, **k):
        raise llm.requests.exceptions.ConnectionError("refused")
    monkeypatch.setattr(llm.requests, "post", boom)
    assert llm.ask_llm("s", "u") == llm.format_llm_offline_message()


def test_ask_llm_timeout_is_offline(monkeypatch):
    def boom(*a, **k):
        raise llm.requests.exceptions.Timeout("slow")
    monkeypatch.setattr(llm.requests, "post", boom)
    assert llm.ask_llm("s", "u") == llm.format_llm_offline_message()


def test_ask_llm_request_exception_is_offline(monkeypatch):
    def boom(*a, **k):
        raise llm.requests.exceptions.RequestException("bad")
    monkeypatch.setattr(llm.requests, "post", boom)
    assert llm.ask_llm("s", "u") == llm.format_llm_offline_message()
