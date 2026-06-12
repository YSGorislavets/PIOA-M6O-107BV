import pytest
from unittest.mock import patch
from src.db.tui import AttendanceApp, select_database_type


class TestTUI:
    def setup_method(self):
        self.app = AttendanceApp(db_type="memory")

    def test_init_creates_table(self):
        assert self.app._current_table == "attendance"
        assert self.app.db.table_exists("attendance")

    def test_get_db_type_name_memory(self):
        assert self.app._get_db_type_name() == "In-Memory"

    @patch('builtins.input', side_effect=[
        "Иван", "М-101", "2025-05-27", "Матан", "да", "да", "5"
    ])
    def test_add_record_success(self, mock_input):
        self.app.add_record()
        records = self.app.db.select_records("attendance")
        assert len(records) == 1

    def test_show_all_empty(self, capsys):
        self.app.show_all()
        captured = capsys.readouterr()
        assert "Нет записей" in captured.out

    def test_menu_display(self, capsys):
        self.app._print_menu()
        captured = capsys.readouterr()
        assert "УЧЁТ ПОСЕЩЕНИЙ" in captured.out

    def test_select_database_type_memory(self, monkeypatch):
        monkeypatch.setattr('builtins.input', lambda _: "1")
        assert select_database_type() == "memory"

    def test_select_database_type_file(self, monkeypatch):
        monkeypatch.setattr('builtins.input', lambda _: "2")
        assert select_database_type() == "file"
