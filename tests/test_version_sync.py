"""Version synchronization test: tauri.conf.json vs localcomet_version.py.

Ensures the semver in tauri.conf.json matches the first three segments of
VERSION in localcomet_version.py. Prevents version drift on future bumps.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_tauri_conf_version_matches_product_version():
    """tauri.conf.json version must equal first 3 segments of VERSION."""
    version_py = (ROOT / "localcomet_version.py").read_text(encoding="utf-8")
    ns = {}
    exec(version_py, ns)
    product_version = ns["VERSION"].lstrip("v")
    product_semver = ".".join(product_version.split(".")[:3])

    tauri_conf_path = ROOT / "desktop" / "localcomet-desktop" / "src-tauri" / "tauri.conf.json"
    tauri_conf = json.loads(tauri_conf_path.read_text(encoding="utf-8"))
    tauri_version = tauri_conf["version"]

    assert tauri_version == product_semver, (
        f"Version drift: tauri.conf.json has '{tauri_version}' "
        f"but localcomet_version.py VERSION implies '{product_semver}'. "
        f"Update both together."
    )


def test_product_version_has_four_segments():
    """VERSION in localcomet_version.py must have exactly 4 segments."""
    version_py = (ROOT / "localcomet_version.py").read_text(encoding="utf-8")
    ns = {}
    exec(version_py, ns)
    product_version = ns["VERSION"].lstrip("v")
    segments = product_version.split(".")
    assert len(segments) == 4, (
        f"VERSION must have 4 segments (MAJOR.MINOR.PATCH.BUILD), got {len(segments)}: {product_version}"
    )
    for seg in segments:
        assert seg.isdigit(), f"Non-numeric version segment: '{seg}' in {product_version}"
