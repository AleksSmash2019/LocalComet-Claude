import json
import sys
from pathlib import Path
from typing import Any, Dict

from modules.project_paths import get_project_root

STATE_FILE = get_project_root() / "memory" / "state.json"
STATE_FILE.parent.mkdir(parents=True, exist_ok=True)


def load_state() -> Dict[str, Any]:
    if not STATE_FILE.exists():
        return {}

    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}

    if not isinstance(data, dict):
        return {}

    return data


def save_state(data: Dict[str, Any]) -> None:
    try:
        STATE_FILE.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
    except OSError as e:
        print(f"[state] Не удалось сохранить state.json: {e}", file=sys.stderr)


def set_value(key: str, value: Any) -> None:
    state = load_state()
    state[key] = value
    save_state(state)


def get_value(key: str, default: Any = None) -> Any:
    state = load_state()
    return state.get(key, default)
