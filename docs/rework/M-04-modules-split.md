# M-04: План распила modules/ на подпакеты

Статус: ПЛАН (не реализован, требует ревью)
Дата: 2026-07-23

## Текущее состояние

modules/ содержит ~140 файлов, ~70K строк. Все файлы в одном плоском пространстве имён.
Импорты: `from modules.browser import ...`, `from modules.files import ...` и т.д.

## Предлагаемые домены

| Подпакет | Файлов | Файлы |
|----------|--------|-------|
| `modules/browser/` | 8 | browser.py, browser_actions.py, browser_autopilot.py, browser_direct.py, browser_operator.py, browser_super.py, browser_task_runner.py, browser_harness_ru.py |
| `modules/computer_use/` | 18 | computer_use_*.py (все 18 файлов) |
| `modules/knowledge/` | 7 | knowledge_*.py (все 7 файлов) |
| `modules/pc_agent/` | 10 | pc_*.py (все 10 файлов) |
| `modules/desktop/` | 5 | desktop_*.py (все 5 файлов) |
| `modules/screenshot/` | 4 | screenshot_*.py (все 4 файла) |
| `modules/patch/` | 3 | patch_*.py, patch_registry.py |
| `modules/task/` | 3 | task_*.py |
| `modules/chatgpt/` | 2 | chatgpt_desktop_bridge.py, chatgpt_relay.py |
| `modules/gpt/` | 2 | gpt_browser_bridge.py, gpt_client.py |
| `modules/autonomous/` | 2 | autonomous_*.py |
| `modules/repo/` | 2 | repo_*.py |
| `modules/local/` | 2 | local_*.py |
| `modules/command/` | 2 | command_*.py |
| `modules/ai/` | 4 | ai_*.py |
| `modules/project/` | 4 | project_*.py |
| `modules/localcomet/` | 3 | localcomet_*.py |
| `modules/core_modules/` | ~20 | Остальные одиночные: files.py, workspace.py, windows.py, voice.py, voice_control.py, diagnostics.py, maintenance.py, research.py, codegen.py, self_edit.py, stability_test.py, history_log.py, git_status.py, report_opener.py, llm_provider.py, natural_command_intents.py, russian_command_context.py, config-related |

## Порядок миграции (по одному подпакету за коммит)

1. Создать `modules/<domain>/__init__.py` с re-export всех публичных имён.
2. Переместить файлы в подпакет.
3. Обновить импорты в `agents/`, `core/`, `next/` (find-replace `from modules.X` → `from modules.<domain>.X`).
4. Прогнать pytest + py_compile.
5. Один коммит на домен.

## Ограничения

- НЕ менять публичные API (имена функций, сигнатуры).
- `__init__.py` должен re-export все публичные имена для обратной совместимости.
- legacy/ не трогать.
- Один домен = один коммит.

## Оценка трудозатрат

~140 файлов / ~18 доменов = ~18 коммитов. Каждый ~15-30 мин.
Итого: ~6-9 часов чистой работы + тестирование.
