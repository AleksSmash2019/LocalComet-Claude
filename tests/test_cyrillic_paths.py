"""Phase 3 Scenario 8: Paths with Cyrillic characters and spaces.

Documents current behavior of state, files, and reports modules when
paths contain Cyrillic characters and spaces. All operations must work
correctly on Windows with non-ASCII paths.
"""
import json
import pytest
from pathlib import Path
from unittest.mock import patch


class TestCyrillicPaths:
    def test_state_roundtrip_with_cyrillic_keys(self, tmp_path):
        """state.json must handle Cyrillic keys and values."""
        state_file = tmp_path / "state.json"
        with patch("core.state.STATE_FILE", state_file):
            import core.state as st
            st.set_value("последний_запрос", "найди информацию о Москве")
            st.set_value("отчёт", "данные готовы")
            assert st.get_value("последний_запрос") == "найди информацию о Москве"
            assert st.get_value("отчёт") == "данные готовы"

    def test_state_file_content_is_utf8(self, tmp_path):
        """state.json must be written as UTF-8 with ensure_ascii=False."""
        state_file = tmp_path / "state.json"
        with patch("core.state.STATE_FILE", state_file):
            import core.state as st
            st.set_value("ключ", "значение")
        content = state_file.read_text(encoding="utf-8")
        assert "ключ" in content
        assert "значение" in content
        assert "\\u" not in content

    def test_files_write_read_cyrillic_filename(self, tmp_path):
        """files module must handle Cyrillic filenames."""
        projects = tmp_path / "Projects"
        projects.mkdir()
        with patch("modules.files.BASE_DIR", projects):
            from modules.files import write_file, read_file
            write_file("отчёт/данные.txt", "Привет мир")
            result = read_file("отчёт/данные.txt")
            assert result == "Привет мир"

    def test_files_write_read_spaces_in_filename(self, tmp_path):
        """files module must handle spaces in filenames."""
        projects = tmp_path / "Projects"
        projects.mkdir()
        with patch("modules.files.BASE_DIR", projects):
            from modules.files import write_file, read_file
            write_file("my reports/final report.txt", "content here")
            result = read_file("my reports/final report.txt")
            assert result == "content here"

    def test_files_list_cyrillic_directory(self, tmp_path):
        """list_files must show Cyrillic-named entries."""
        projects = tmp_path / "Projects"
        projects.mkdir()
        (projects / "Отчёты").mkdir()
        (projects / "файл с пробелом.txt").write_text("x", encoding="utf-8")
        with patch("modules.files.BASE_DIR", projects):
            from modules.files import list_files
            result = list_files("")
            assert "Отчёты" in result
            assert "файл с пробелом.txt" in result

    def test_files_delete_cyrillic_path(self, tmp_path):
        """delete_path must work with Cyrillic paths."""
        projects = tmp_path / "Projects"
        projects.mkdir()
        target = projects / "удалить меня.txt"
        target.write_text("temp", encoding="utf-8")
        with patch("modules.files.BASE_DIR", projects):
            from modules.files import delete_path
            result = delete_path("удалить меня.txt")
            assert "Удалено" in result
            assert not target.exists()

    def test_state_survives_reload_with_cyrillic(self, tmp_path):
        """State must persist across fresh load_state() with Cyrillic data."""
        state_file = tmp_path / "state.json"
        with patch("core.state.STATE_FILE", state_file):
            import core.state as st
            st.set_value("задача", "создай сайт кофейни")
            loaded = st.load_state()
            assert loaded.get("задача") == "создай сайт кофейни"
