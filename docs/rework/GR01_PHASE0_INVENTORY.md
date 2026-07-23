# GR-01 Phase 0 — Repository Inventory

**Program:** GR-01 (Grand Rework) — re-execution on branch `hyperagent/gr01-redo`.
**Baseline:** `c0c57bf` (== `main`). Risk: `doc`.
**Why re-executed:** the original Phase 0–3 commits were produced in a prior agent
session that never pushed; they exist only in a Phase-3 git bundle. Per the owner's
standing authorization, Phases 0–3 are re-executed from the recorded journal decisions
(no new sign-off on already-settled questions). New commit SHAs differ from the
historical ones.

## Method

Import-graph analysis over the Python tree (AST import edges across `modules/`,
`core/`, `agents/`, `next/`, `tools/`), cross-checked against string-based dynamic
references (`__import__`-by-name, registry/manifest lookups) and manual inspection of
gate/manifest pins. Analysis scripts are not committed.

## Structure re-verified at c0c57bf (this session)

| Area | Count |
|---|---|
| Tracked `.py` files (total) | 225 |
| `modules/` | 140 |
| `tools/` | 45 |
| repository root | 10 |

## Key results (carried from the recorded Phase 0 analysis)

- **~137 ACTIVE modules**; **~30 import-orphans** in `modules/`; 3 old-generation files;
  ≈16 480 LOC of quarantine candidates.
- **Browser stack is LIVE** — all 12 browser modules are active (the "dead browser"
  hypothesis was disproven). Genuinely dead: `premium_ui_*`, old-generation `pc_*`,
  `codex_*`.
- **Pinned orphans:** some orphans are pinned by active gates/manifests; gate 5
  (`strict_project_stability_ru`) hard-pins `project_one_command_check_ru` — must not move.
- **Gate 1 (py_compile):** 179 OK / 1 FAIL — `modules/ai_patch_planner_ru.py` (backslash
  inside an f-string expression; legal only on Python ≥ 3.12, target runtime is 3.11).
  Pre-existing defect, not introduced by this program. Fixed in Phase 1 (safe, behavior-
  neutral hoist) to reach gate 1 = 180/180 on Python 3.11.

## Approved decisions (pre-settled — not re-litigated)

1. **Canonical product version = `v6.84.5.1`** (source of truth: Obsidian "Version
   Matrix"). Bring `next/app_v5.py` (was v6.02) and `LocalComet_Control_Panel.py`
   (was v6.82) banners to `v6.84.5.1`. **Component versions stay independent**
   (IPC v6.84.1, Sidecar v6.84.3, Model Gateway v6.84.5) — do **not** unify.
2. `core/loop.py` **stays in place** (contract-active); any future quarantine with
   `app.py` is a separate authorized task.
3. **Supported Python = 3.11.** The minimal behavior-neutral `ai_patch_planner_ru.py`
   fix is authorized as part of Phase 1.
4. **Pinned orphans stay in place** in Phase 2; editing gate 5 / manifests requires
   separate authorization (granted narrowly in Phase 2 only for adding `legacy/` to
   ignore-sets).

## Environment note

True GREEN for gates 3/4/5 is only observable on the owner's Windows build. The agent
sandbox is Linux (here: CPython 3.9), lacking `tkinter`, `pyautogui`/`pyperclip`, and
`json_repair` runtime — those produce known environmental REDs that are not regressions.
