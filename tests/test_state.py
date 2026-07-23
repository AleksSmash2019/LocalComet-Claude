"""GR-01 Phase 4 - characterization tests for core.state (written BEFORE the refactor).

Lock the observable behavior of load_state/save_state/set_value/get_value,
especially the corrupt-JSON -> {} fallback, so the bare-except -> except Exception
narrowing in Phase 4 is provably behavior-preserving. STATE_FILE is monkeypatched
to a tmp file (no touching real memory/state.json).
"""
import importlib

import pytest

state = importlib.import_module("core.state")


@pytest.fixture
def tmp_state(tmp_path, monkeypatch):
    f = tmp_path / "state.json"
    monkeypatch.setattr(state, "STATE_FILE", f)
    return f


def test_load_state_missing_returns_empty(tmp_state):
    assert not tmp_state.exists()
    assert state.load_state() == {}


def test_load_state_valid_json(tmp_state):
    tmp_state.write_text('{"a": 1, "b": "x"}', encoding="utf-8")
    assert state.load_state() == {"a": 1, "b": "x"}


def test_load_state_corrupt_json_returns_empty(tmp_state):
    tmp_state.write_text("{not valid json", encoding="utf-8")
    assert state.load_state() == {}


def test_load_state_empty_file_returns_empty(tmp_state):
    tmp_state.write_text("", encoding="utf-8")
    assert state.load_state() == {}


def test_set_and_get_roundtrip(tmp_state):
    state.set_value("k", "v")
    assert state.get_value("k") == "v"


def test_get_value_default_when_missing(tmp_state):
    assert state.get_value("nope", "fallback") == "fallback"


def test_get_value_none_default(tmp_state):
    assert state.get_value("missing") is None


def test_save_state_then_load(tmp_state):
    state.save_state({"x": [1, 2, 3]})
    assert state.load_state() == {"x": [1, 2, 3]}


def test_set_value_persists_unicode(tmp_state):
    state.set_value("рус", "привет")
    assert state.get_value("рус") == "привет"
    assert "привет" in tmp_state.read_text(encoding="utf-8")
