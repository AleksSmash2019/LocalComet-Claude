import os
import subprocess
import sys
from pathlib import Path
from modules.project_paths import projects_dir

from core.state import get_value, set_value


PROJECTS_DIR = projects_dir()
REPORTS_DIR = PROJECTS_DIR / "Reports"


def _resolve_report_path(path: str):
    return (PROJECTS_DIR / path).resolve()


def remember_report(path: str):
    set_value("last_report", path)
    return f"Последний отчет запомнен: {path}"


def find_latest_report():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    reports = list(REPORTS_DIR.glob("*.md"))

    if not reports:
        return None

    latest = max(reports, key=lambda p: p.stat().st_mtime)
    relative = latest.relative_to(PROJECTS_DIR)

    return str(relative).replace("\\", "/")


def get_last_report_path():
    path = get_value("last_report")

    if path:
        report_path = _resolve_report_path(path)

        if report_path.exists():
            return path

    latest = find_latest_report()

    if latest:
        remember_report(latest)
        return latest

    return None


def open_report(path: str):
    report_path = _resolve_report_path(path)

    if not report_path.exists():
        return f"Отчет не найден: {report_path}"

    remember_report(path)

    if sys.platform == "win32":
        try:
            os.startfile(str(report_path))
            return f"Открыл отчет: {report_path}"
        except OSError:
            pass

    try:
        subprocess.Popen(["code", str(report_path)])
        return f"Открыл отчет в VS Code: {report_path}"
    except OSError:
        subprocess.Popen(["notepad", str(report_path)])
        return f"Открыл отчет в Блокноте: {report_path}"


def open_last_report():
    path = get_last_report_path()

    if not path:
        return "Последний отчет не найден. Сначала создай отчет."

    return open_report(path)


def read_last_report():
    path = get_last_report_path()

    if not path:
        return "Последний отчет не найден. Сначала создай отчет."

    report_path = _resolve_report_path(path)

    if not report_path.exists():
        return f"Отчет не найден: {report_path}"

    text = report_path.read_text(encoding="utf-8")

    return (
        "Последний отчет:\n"
        + path
        + "\n\n"
        + text
    )