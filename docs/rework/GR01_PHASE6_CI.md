# GR-01 Phase 6 - CI, EOL policy, documentation

Branch `hyperagent/gr01-redo`. Risk: config/doc.

## CI (.github/workflows/validation.yml)

- **linux-offline** (portable, must be GREEN): install requirements-dev, compile
  active Python (excluding legacy/), EOL check (no CRLF in tracked .py), offline
  `pytest tests/` (185 tests).
- **windows-authoritative**: offline pytest + Control Panel compile; verification
  gates 3/4/5 as informational (`continue-on-error`, because they have known
  non-zero baseline states - gate3 missing=1, gate4 72/80, gate5 tkinter - and
  parity-vs-baseline is the criterion, not absolute zero); desktop `npm run check`
  + `npm run test`; Rust `cargo test`. Windows is the authoritative environment
  for the Tauri/Windows suites.

## Validation matrix

| Check | Linux CI | Windows CI | Authoritative on |
|---|---|---|---|
| py compile (active) | yes | control panel | both |
| EOL (no CRLF in .py) | yes | - | Linux |
| pytest tests/ (offline) | yes | yes | both |
| gates 3/4/5 | - | informational | Windows (owner) |
| svelte-check / vitest | - | yes | Windows |
| cargo test (Tauri) | - | yes | Windows |

## EOL policy (.gitattributes)

Source code (`*.py`, `*.rs`, `*.ts`, `*.svelte`, `*.toml`) is pinned to `eol=lf`
in addition to the existing hash-sensitive pins. This prevents the CRLF drift that
recurred in Phases 0-1 on Windows `core.autocrlf` checkouts. Existing committed
blobs are already LF; new checkouts/commits stay LF. Owner may run
`git add --renormalize .` on Windows if the working tree shows EOL-only changes.

## Doc drift fixed

`docs/agent_operating_layer.md` referenced a non-existent
`--include-tools` flag for `tools/localcomet_preflight_audit.py` (the parser only
has `--root/--json/--output`; the audit always scans `tools/`). Removed.
