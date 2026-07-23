import os
import sys
import types

if "playwright" not in sys.modules:
    _pw = types.ModuleType("playwright")
    _sync = types.ModuleType("playwright.sync_api")
    _sync.sync_playwright = lambda: None
    _pw.sync_api = _sync
    sys.modules["playwright"] = _pw
    sys.modules["playwright.sync_api"] = _sync

# Make the repository root importable for offline unit tests.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
