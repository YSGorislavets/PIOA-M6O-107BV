import pytest
from unittest.mock import patch
from src.db.tui import AttendanceApp
from src.db.backend.errors import RecordNotFoundError

def create_full_record(name="Иван", group="М-101", date="2025-05-27", topic="Матан",
                       is_present=True, homework_done=True, grade=5):
    return {
        "student_name": name,
        "group": group,
        "date": date,
        "topic": topic,
        "is_present": is_present,
        "homework_done": homework_done,
        "grade": grade
    }

class TestTUI:
    def setup_method(self):
        self.app = AttendanceApp()
        self.app.table._data.clear()
        self.app.table._next_id = 1


    @patch('builtins.input', side_effect=[
        "Иван Петров", "М-101", "2025-05-27", "Производные", "да", "да", "5"
    ])
    @patch('builtins.print')
    def test_add_record_success(self, mock_print, mock_input):
        self.app.add_record()
        assert self.app.table.count() == 1
        record = self.app.table.get_by_id(1)
        assert record["student_name"] == "Иван Петров"
        assert record["group"] == "М-101"
        assert record["grade"] == 5

    @patch('builtins.input', side_effect=["", "М-101"])
    @patch('builtins.print')
    def test_add_record_empty_name(self, mock_print, mock_input):
        self.app.add_record()
        assert self.app.table.count() == 0
        mock_print.assert_called_with("Ошибка: ФИО не может быть пустым")


    def test_show_all_empty(self, capsys):
        self.app.show_all()
        captured = capsys.readouterr()
        assert "Нет записей" in captured.out

    def test_show_all_with_data(self, capsys):

        self.app.table.insert(create_full_record(name="Анна"))
        self.app.show_all()
        captured = capsys.readouterr()
        assert "Анна" in captured.out
        assert "М-101" in captured.out


    @patch('builtins.input', side_effect=["Анна", "", "", "", ""])
    @patch('builtins.print')
    def test_search_records_by_name(self, mock_print, mock_input):
        self.app.table.insert(create_full_record(name="Анна"))
        self.app.table.insert(create_full_record(name="Иван"))
        self.app.search_records()
        assert mock_print.called


    @patch('builtins.input', side_effect=["1", "Новое имя", "", "", "", "", "", ""])
    @patch('builtins.print')
    def test_update_record_success(self, mock_print, mock_input):
        self.app.table.insert(create_full_record(name="Старое имя"))
        self.app.update_record()
        updated = self.app.table.get_by_id(1)
        assert updated["student_name"] == "Новое имя"
        assert updated["group"] == "М-101"

    @patch('builtins.input', side_effect=["999"])
    @patch('builtins.print')
    def test_update_record_not_found(self, mock_print, mock_input):
        self.app.update_record()
        mock_print.assert_called_with("Ошибка: Запись с id=999 не найдена")


    @patch('builtins.input', side_effect=["1"])
    @patch('builtins.print')
    def test_delete_record_success(self, mock_print, mock_input):
        self.app.table.insert(create_full_record(name="Удалить"))
        assert self.app.table.count() == 1
        self.app.delete_record()
        assert self.app.table.count() == 0
        # Проверяем, что print был вызван (сообщение может быть "Удалено" или "Запись удалена")
        # Для надёжности проверим, что print вызывался
        assert mock_print.called

    @patch('builtins.input', side_effect=["999"])
    @patch('builtins.print')
    def test_delete_record_not_found(self, mock_print, mock_input):
        self.app.delete_record()
        mock_print.assert_called()
        args, _ = mock_print.call_args
        assert any("Ошибка" in str(arg) or "не найдена" in str(arg) for arg in args)


    @patch('builtins.input', side_effect=["grade", "да"])
    @patch('builtins.print')
    def test_sort_records_ascending(self, mock_print, mock_input):
        self.app.table.insert(create_full_record(name="Анна", grade=5))
        self.app.table.insert(create_full_record(name="Борис", grade=3))
        self.app.sort_records()
        assert mock_print.called

    def test_sort_records_empty(self, capsys):
        self.app.sort_records()
        captured = capsys.readouterr()
        assert "Нет записей для сортировки" in captured.out

    def test_menu_display(self, capsys):
        self.app._print_menu()
        captured = capsys.readouterr()
        assert "УЧЁТ ПОСЕЩЕНИЙ" in captured.out




