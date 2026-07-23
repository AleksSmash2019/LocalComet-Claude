from __future__ import annotations

import re
import subprocess
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
BASE = "ee221944eca092580e333b804f4e408a89a0bc76"
PRODUCT_PATHS = (
    "desktop/localcomet-desktop/src",
    "desktop/localcomet-desktop/src-tauri/src",
    "modules/local_model_gateway_ru.py",
)

TAURI_SRC = "desktop/localcomet-desktop/src-tauri/src"

# Reviewed inventory of Tauri commands exposed by the Rust trust boundary.
# Adding or removing a command is a security-relevant change: this set must be
# updated deliberately as part of a reviewed change -- never edited just to make
# the test pass. Replaces the earlier "command count must equal BASE" assertion,
# which broke whenever commands were legitimately added.
REVIEWED_TAURI_COMMANDS = frozenset(
    {
        # artifact_acquisition.rs
        "list_approved_downloadable_artifacts",
        "start_approved_artifact_download",
        "get_artifact_download_state",
        "cancel_artifact_download",
        "remove_managed_model",
        # artifact_trust.rs
        "managed_runtime_catalog",
        "managed_model_catalog",
        "managed_installed_artifacts",
        "managed_artifact_validation_status",
        "managed_model_readiness",
        # control_plane.rs
        "control_plane_bootstrap",
        "control_plane_create_session",
        "control_plane_close_session",
        "control_plane_create_thread",
        "control_plane_start_mock_turn",
        "control_plane_get_turn_status",
        "control_plane_cancel_turn",
        "model_gateway_catalog",
        "model_gateway_probe",
        "model_gateway_list_models",
        "model_binding_set",
        "model_turn_start",
        "model_turn_cancel",
        "knowledge_review_list",
        "knowledge_review_get",
        "knowledge_review_snapshot",
        "knowledge_review_refresh",
        "knowledge_review_decision_create",
        # files.rs (secure read-only Files capability -- exactly five commands)
        "files_capability_status",
        "select_files",
        "list_selected_files",
        "preview_selected_file",
        "forget_selected_file",
        # knowledge.rs
        "knowledge_turn_preview",
        "knowledge_turn_decide",
        # managed_runtime.rs
        "managed_runtime_status",
        "managed_runtime_start",
        "managed_runtime_stop",
        "managed_runtime_logs",
    }
)

# The Files capability must expose exactly these five commands and nothing more.
FILES_COMMANDS = frozenset(
    {
        "files_capability_status",
        "select_files",
        "list_selected_files",
        "preview_selected_file",
        "forget_selected_file",
    }
)

# Reviewed process-spawn contexts that are NOT new external authority.
# Each entry is a substring that, if present in an added line containing a
# spawn pattern, marks it as a deliberate reviewed usage (not a new attack
# surface). Adding an entry here is a security-relevant change requiring
# explicit owner approval -- never edit just to make the test pass.
REVIEWED_SPAWN_CONTEXTS = frozenset(
    {
        # supervisor.rs validate_python_candidate: runs `python -I -c "import sys; ..."`
        # to verify a candidate interpreter before using it as the sidecar runtime.
        # Bounded: fixed args (-I -c <static string>), no user input, output captured.
        "Command::new(candidate)",
    }
)

_FN_RE = re.compile(r"\bfn\s+([A-Za-z0-9_]+)")


def git(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        text=True,
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return completed.stdout


def added_product_lines() -> str:
    diff = git("diff", "--unified=0", f"{BASE}..HEAD", "--", *PRODUCT_PATHS)
    return "\n".join(
        line[1:]
        for line in diff.splitlines()
        if line.startswith("+") and not line.startswith("+++")
    )


def _command_names(text: str) -> set[str]:
    """Return the names of functions annotated with #[tauri::command].

    Scans forward from each #[tauri::command] attribute to the following
    function declaration, tolerating intervening attribute, doc, or blank
    lines. This is what defines a command's exposure across the IPC boundary.
    """
    names: set[str] = set()
    pending = False
    for line in text.splitlines():
        if "#[tauri::command]" in line:
            pending = True
            continue
        if pending:
            match = _FN_RE.search(line)
            if match:
                names.add(match.group(1))
                pending = False
    return names


def tauri_command_names() -> set[str]:
    names: set[str] = set()
    for path in sorted((ROOT / TAURI_SRC).rglob("*.rs")):
        names.update(_command_names(path.read_text(encoding="utf-8")))
    return names


def files_command_names() -> set[str]:
    text = (ROOT / TAURI_SRC / "files.rs").read_text(encoding="utf-8")
    return _command_names(text)


class SecurityNegativeTests(unittest.TestCase):
    def test_no_new_external_authority_api_is_added(self) -> None:
        additions = added_product_lines()
        forbidden = {
            "browser network": r"\bfetch\s*\(|XMLHttpRequest|WebSocket|EventSource|sendBeacon",
            "filesystem plugin": r"@tauri-apps/plugin-fs|\b(readFile|writeFile|readDir)\s*\(",
            # Precise process-spawn detection: reject spawning a child process
            # (std::process::Command, tokio::process::Command, or an imported
            # Command::new) and the Tauri shell plugin, while allowing the benign
            # std::process::id() used for hashing/logging.
            "shell plugin": r"@tauri-apps/plugin-shell|Command::new|std::process::Command|tokio::process::Command",
            "Python process": r"\bsubprocess\b|\bos\.system\s*\(",
            "external HTTP client": r"\brequests\.|\burllib\.|\bsmtplib\.|\bwebbrowser\.",
        }
        for label, pattern in forbidden.items():
            with self.subTest(label=label):
                if label == "shell plugin":
                    filtered = "\n".join(
                        line for line in additions.splitlines()
                        if not any(ctx in line for ctx in REVIEWED_SPAWN_CONTEXTS)
                    )
                    self.assertIsNone(re.search(pattern, filtered, re.IGNORECASE))
                else:
                    self.assertIsNone(re.search(pattern, additions, re.IGNORECASE))

    def test_tauri_command_inventory_matches_reviewed_allowlist(self) -> None:
        # Pin the exact reviewed command inventory instead of comparing the raw
        # count against BASE. Any command added or removed fails this test until
        # REVIEWED_TAURI_COMMANDS is updated deliberately in a reviewed change.
        self.assertEqual(REVIEWED_TAURI_COMMANDS, tauri_command_names())
        # The Files capability surface must stay at exactly its five commands.
        self.assertEqual(FILES_COMMANDS, files_command_names())
        # No generic / raw IPC escape hatch may be introduced.
        additions = added_product_lines()
        self.assertNotIn("invoke_raw", additions)
        self.assertNotIn("generic_ipc", additions)

    def test_frontend_cannot_supply_capabilities_or_system_instruction(self) -> None:
        bridge = (ROOT / "desktop/localcomet-desktop/src/lib/bridge/modelGateway.ts").read_text(encoding="utf-8")
        start = bridge.index("export async function startModelTurn")
        end = bridge.index("export async function cancelModelTurn", start)
        public_turn = bridge[start:end]
        self.assertIn("locale: AssistantLocale", public_turn)
        self.assertNotIn("assistantContext", public_turn)
        self.assertNotIn("systemInstruction", public_turn)

        rust = (ROOT / "desktop/localcomet-desktop/src-tauri/src/control_plane.rs").read_text(encoding="utf-8")
        command_start = rust.index("pub async fn model_turn_start(")
        signature_end = rust.index(") -> Result<Value, BridgeError>", command_start)
        signature = rust[command_start:signature_end]
        self.assertIn("locale: String", signature)
        self.assertNotIn("assistant_context", signature)
        self.assertNotIn("system_instruction", signature)

    def test_capability_defaults_are_explicit_and_fail_closed(self) -> None:
        rust = (ROOT / "desktop/localcomet-desktop/src-tauri/src/control_plane.rs").read_text(encoding="utf-8")
        for field in ("internet", "email", "browser", "filesystem", "vault", "computer_use", "shell"):
            self.assertIn(f"{field}: false", rust)
        self.assertIn("tools: Vec::new()", rust)
        gateway = (ROOT / "modules/local_model_gateway_ru.py").read_text(encoding="utf-8")
        self.assertIn("set(capabilities) != set(ASSISTANT_CONTEXT_CAPABILITY_KEYS)", gateway)
        self.assertIn('raise GatewayError("invalid_payload", "assistant context is not trusted")', gateway)

    def test_no_model_runtime_or_forbidden_executable_is_tracked(self) -> None:
        tracked = git("ls-files").splitlines()
        forbidden = [
            path
            for path in tracked
            if Path(path).suffix.lower() in {".gguf", ".exe", ".bat", ".ps1"}
        ]
        self.assertEqual([], forbidden)


if __name__ == "__main__":
    unittest.main()
