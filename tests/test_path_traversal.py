"""Phase 3 Scenario 5: Path traversal in file_agent / modules.files.

Tests that safe_path() rejects traversal attempts and constrains all
operations to the Projects directory. Documents current behavior.
"""
import pytest
from pathlib import Path
from unittest.mock import patch


@pytest.fixture
def fake_projects(tmp_path):
    projects = tmp_path / "Projects"
    projects.mkdir()
    (projects / "existing.txt").write_text("hello", encoding="utf-8")
    (projects / "subdir").mkdir()
    return projects


class TestPathTraversal:
    def test_dotdot_traversal_rejected(self, fake_projects):
        with patch("modules.files.BASE_DIR", fake_projects):
            from modules.files import safe_path
            with pytest.raises(ValueError, match="Запрещенный путь"):
                safe_path("../../etc/passwd")

    def test_absolute_path_outside_rejected(self, fake_projects):
        with patch("modules.files.BASE_DIR", fake_projects):
            from modules.files import safe_path
            with pytest.raises(ValueError, match="Запрещенный путь"):
                safe_path("C:/Windows/System32/cmd.exe")

    def test_dotdot_in_middle_rejected(self, fake_projects):
        with patch("modules.files.BASE_DIR", fake_projects):
            from modules.files import safe_path
            with pytest.raises(ValueError, match="Запрещенный путь"):
                safe_path("subdir/../../secret.txt")

    def test_normal_path_allowed(self, fake_projects):
        with patch("modules.files.BASE_DIR", fake_projects):
            from modules.files import safe_path
            result = safe_path("subdir/file.txt")
            assert str(result).startswith(str(fake_projects.resolve()))

    def test_read_file_traversal_rejected(self, fake_projects):
        with patch("modules.files.BASE_DIR", fake_projects):
            from modules.files import read_file
            with pytest.raises(ValueError, match="Запрещенный путь"):
                read_file("../../../etc/passwd")

    def test_write_file_traversal_rejected(self, fake_projects):
        with patch("modules.files.BASE_DIR", fake_projects):
            from modules.files import write_file
            with pytest.raises(ValueError, match="Запрещенный путь"):
                write_file("../../evil.py", "import os; os.system('calc')")

    def test_delete_path_traversal_rejected(self, fake_projects):
        with patch("modules.files.BASE_DIR", fake_projects):
            from modules.files import delete_path
            with pytest.raises(ValueError, match="Запрещенный путь"):
                delete_path("../../important_file")

    def test_create_folder_traversal_rejected(self, fake_projects):
        with patch("modules.files.BASE_DIR", fake_projects):
            from modules.files import create_folder
            with pytest.raises(ValueError, match="Запрещенный путь"):
                create_folder("../../evil_dir")

    def test_list_files_traversal_rejected(self, fake_projects):
        with patch("modules.files.BASE_DIR", fake_projects):
            from modules.files import list_files
            with pytest.raises(ValueError, match="Запрещенный путь"):
                list_files("../../")

    def test_empty_path_resolves_to_base(self, fake_projects):
        with patch("modules.files.BASE_DIR", fake_projects):
            from modules.files import safe_path
            result = safe_path("")
            assert result == fake_projects.resolve()
