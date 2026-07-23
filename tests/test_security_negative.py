"""GR-01 Phase 3 - semantic security-negative tests (pytest).

Reuses the reviewed helpers/constants from tools.test_up02_wp01_security_negative
(the semantic invariants originally from the hardening work) and asserts them as
pytest cases: precise process-spawn detection (allow std::process::id(), reject
real spawns), the reviewed Tauri command inventory, exactly five Files commands,
no generic/raw IPC, no new external-authority APIs, fail-closed capability
defaults, and no forbidden tracked executables. Offline (source + git only).
"""
import importlib
import re

sec = importlib.import_module("tools.test_up02_wp01_security_negative")

SPAWN = r"@tauri-apps/plugin-shell|Command::new|std::process::Command|tokio::process::Command"


def test_reviewed_command_inventory_matches_source():
    assert sec.tauri_command_names() == sec.REVIEWED_TAURI_COMMANDS


def test_reviewed_inventory_size_is_39():
    assert len(sec.REVIEWED_TAURI_COMMANDS) == 39


def test_exactly_five_files_commands():
    assert sec.files_command_names() == sec.FILES_COMMANDS
    assert len(sec.FILES_COMMANDS) == 5


def test_files_commands_subset_of_inventory():
    assert sec.FILES_COMMANDS <= sec.REVIEWED_TAURI_COMMANDS


def test_precise_spawn_detection_allows_process_id():
    # The whole point of the fix: std::process::id() is benign and must NOT match.
    assert re.search(SPAWN, "hasher.update(std::process::id().to_le_bytes());") is None


def test_precise_spawn_detection_flags_real_spawns():
    assert re.search(SPAWN, 'std::process::Command::new("x")') is not None
    assert re.search(SPAWN, 'tokio::process::Command::new("x")') is not None
    assert re.search(SPAWN, "let c = Command::new(bin);") is not None
    assert re.search(SPAWN, 'import { Command } from "@tauri-apps/plugin-shell"') is not None


def test_no_new_external_authority_apis_in_additions():
    additions = sec.added_product_lines()
    forbidden = {
        "browser network": r"\bfetch\s*\(|XMLHttpRequest|WebSocket|EventSource|sendBeacon",
        "filesystem plugin": r"@tauri-apps/plugin-fs|\b(readFile|writeFile|readDir)\s*\(",
        "shell/spawn": SPAWN,
        "python process": r"\bsubprocess\b|\bos\.system\s*\(",
        "external http": r"\brequests\.|\burllib\.|\bsmtplib\.|\bwebbrowser\.",
    }
    for label, pattern in forbidden.items():
        if label == "shell/spawn":
            filtered = "\n".join(
                line for line in additions.splitlines()
                if not any(ctx in line for ctx in sec.REVIEWED_SPAWN_CONTEXTS)
            )
            assert re.search(pattern, filtered, re.IGNORECASE) is None, label
        else:
            assert re.search(pattern, additions, re.IGNORECASE) is None, label


def test_no_generic_raw_ipc_in_additions():
    additions = sec.added_product_lines()
    assert "invoke_raw" not in additions
    assert "generic_ipc" not in additions


def test_capability_defaults_fail_closed():
    rust = (sec.ROOT / "desktop/localcomet-desktop/src-tauri/src/control_plane.rs").read_text(encoding="utf-8")
    for field in ("internet", "email", "browser", "filesystem", "vault", "computer_use", "shell"):
        assert f"{field}: false" in rust
    assert "tools: Vec::new()" in rust


def test_no_forbidden_executables_tracked():
    tracked = sec.git("ls-files").splitlines()
    bad = [p for p in tracked if p.lower().endswith((".gguf", ".exe", ".bat", ".ps1"))]
    assert bad == []
