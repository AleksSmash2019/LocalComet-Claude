# GR-01 Phase 5 - loop tests, exception policy, stale reconcile, dev deps

Branch `hyperagent/gr01-redo`. Risk: guarded. Behavior-preserving.

## 1. core.loop characterization tests (`tests/test_loop.py`, 11 tests)

Offline: `route`, `plan`, `execute`, `ask_llm` are monkeypatched; fake agent
modules are injected so `core.executor` (and thus `core.loop`) import without the
heavy Windows/browser deps. Cover: immediate/deferred done, default vs custom
message, code-fence stripping, no/empty `next_step`, max-steps, multi-step, and
the two broad `except Exception` paths (step failure and review failure) with a
`RuntimeError`.

## 2. Exception-narrowing decision: broad excepts in `core/loop.py` are LEFT AS-IS

`run_loop` has two broad `except Exception` blocks:
- around `route`/`plan`/`execute` (step failure -> error string),
- around `ask_llm`/`repair_json`/`json.loads` (review failure -> partial message).

The characterization tests show both blocks must catch **arbitrary** exception
types (e.g. `RuntimeError`) to preserve current behavior. Narrowing them to
json/parse-specific types would let other exceptions propagate, changing the
returned strings. That is **not byte-identical**, so per the GR-01 contract the
narrowing is intentionally NOT applied. (This mirrors the Phase 4 note that the
loop broad-excepts are not test-provably narrowable.)

## 3. Stale assertion reconcile: `modules/stability_test.py`

Two stale checks in the Windows desktop-shell stability check were reconciled to
the current, truthful values (canonical product version v6.84.5.1):
- version equality: `== "v6.02"` -> `== "v6.84.5.1"` (matches `LocalComet_Control_Panel.LOCALCOMET_VERSION`).
- label substring: `"Command Center Control Panel"` -> `"Explainable Task Planner"`
  (the former string is the app_v5 banner, never present in
  `LOCALCOMET_VERSION_LABEL`; the latter is actually in the label).

Both reconciled values are verified against the real Control Panel constants.
`stability_test.py` drives Tkinter, so its true GREEN must be confirmed on the
owner's Windows runner.

## 4. Dev/test dependencies: `requirements-dev.txt`

Pins pytest (dev tool) plus json_repair and requests (runtime deps the tests
import), to the versions validated for GR-01. Gate 6 command:
`python -m pip install -r requirements-dev.txt && python -m pytest tests/`.

## 5. Residual (backlog)

- `tools/test_v6*.py` are version-pinned unittest scripts still run standalone
  (not migrated into the pytest `tests/` suite). Optional future migration.
