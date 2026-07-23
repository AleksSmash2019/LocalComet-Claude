import re
from pathlib import Path

import localcomet_version

ROOT = Path(__file__).resolve().parents[1]


def test_canonical_version_string():
    assert localcomet_version.VERSION == "v6.84.5.1"


def test_product_name():
    assert localcomet_version.PRODUCT_NAME == "LocalComet"


def test_control_panel_literal_matches_canonical():
    # Control Panel keeps a simple string literal parsed by ~10 modules + gate 4.
    src = (ROOT / "LocalComet_Control_Panel.py").read_text(encoding="utf-8")
    m = re.search(r'LOCALCOMET_VERSION\s*=\s*"([^"]+)"', src)
    assert m is not None
    assert m.group(1) == localcomet_version.VERSION


def test_app_v5_imports_canonical_version():
    src = (ROOT / "next" / "app_v5.py").read_text(encoding="utf-8")
    assert "from localcomet_version import" in src
    assert "VERSION" in src
