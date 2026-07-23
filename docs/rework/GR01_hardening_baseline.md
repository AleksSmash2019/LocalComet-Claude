# GR-01 Hardening Baseline

First increment of the Project Hardening Sprint. Scope of this PR: replace the
two stale assertions in `tools/test_up02_wp01_security_negative.py` with
semantic invariants, without weakening any security check.

## What changed

`tools/test_up02_wp01_security_negative.py`:

1. **Precise process-spawn detection.**
   The "shell plugin" pattern used `std::process`, which false-positively
   matched the benign `std::process::id()` (used for hashing/logging).
   It now matches actual process spawning only:
   `@tauri-apps/plugin-shell | Command::new | std::process::Command | tokio::process::Command`.
   `std::process::id()` is allowed; real spawns are still rejected.

2. **Reviewed command inventory instead of a raw count vs BASE.**
   The previous check asserted that the number of `#[tauri::command]`
   attributes equalled the count at BASE (`ee221944`). That broke as soon as
   commands were legitimately added (29 → 39). It now pins the exact reviewed
   inventory (`REVIEWED_TAURI_COMMANDS`, 39 names) and asserts the Files
   capability exposes exactly its five commands (`FILES_COMMANDS`). Adding or
   removing a command fails the test until the reviewed set is updated
   deliberately.

The `invoke_raw` / `generic_ipc` raw-IPC checks are unchanged.

## Verified findings (base commit c0c57bf)

- Tauri commands: **39** total (was 29 at BASE); `files.rs` exposes exactly **5**
  (`files_capability_status`, `select_files`, `list_selected_files`,
  `preview_selected_file`, `forget_selected_file`).
- `BASE ee221944` is an ancestor of HEAD, so the diff-based checks run.
- No real process spawns exist in `src-tauri/src` — all `std::process`
  occurrences are `std::process::id()`.
- Local result (Linux): `py_compile` OK; `python tools/test_up02_wp01_security_negative.py`
  → **5/5 OK** (was 2 failing).

## Not in this PR (proposed next, needs owner review)

- Deeper cross-layer consistency: Rust command defs ↔ invoke handler ↔
  `permissions/*.toml` ↔ `capabilities/main.json` ↔ frontend bridge.
- Windows-native GitHub Actions CI + portable Linux checks.

## Environment note

Rust/Tauri tests are `BLOCKED_BY_ENVIRONMENT` on Linux (missing GTK/WebKit,
`gdk-3.0`); that is not a Files defect. Authoritative native validation must run
on a Windows runner.

## Provenance

Authored on branch `hyperagent/hardening-baseline` via the Hyperagent GitHub
integration. Opened as a PR for review — not merged automatically.
