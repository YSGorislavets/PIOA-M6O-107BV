import tempfile
import pytest
import csv
from pathlib import Path
from src.db.backend.csv import CSVDatabase
from src.db.backend.errors import (
    TableNotFoundError,
    DuplicateTableError,
    EmptyTableNameError,
    EmptyColumnsError,
    InvalidRecordLengthError,
    ColumnNotFoundError,
    FileOperationError,
    InvalidColumnNameError,
)


class TestCSVDatabase:
    def setup_method(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db = CSVDatabase(directory=self.temp_dir.name)

    def teardown_method(self):
        self.temp_dir.cleanup()

    def test_create_table_success(self):
        self.db.create_table("students", ["id", "name", "age"])
        assert self.db.table_exists("students")
        assert self.db.get_columns("students") == ["id", "name", "age"]
        assert "students" in self.db.list_tables()

    def test_create_table_duplicate(self):
        self.db.create_table("students", ["id", "name"])
        with pytest.raises(DuplicateTableError):
            self.db.create_table("students", ["id", "name", "age"])

    def test_create_table_empty_name(self):
        with pytest.raises(EmptyTableNameError):
            self.db.create_table("", ["id"])

    def test_create_table_no_columns(self):
        with pytest.raises(EmptyColumnsError):
            self.db.create_table("test", [])

    def test_create_table_duplicate_columns(self):
        with pytest.raises(InvalidColumnNameError) as exc_info:
            self.db.create_table("students", ["id", "name", "id"])
        assert "Названия колонок не должны повторяться" in str(exc_info.value)

    def test_insert_record_success(self):
        self.db.create_table("students", ["id", "name"])
        self.db.insert_record("students", (1, "Иван"))
        records = self.db.select_records("students")
        assert len(records) == 1
        assert records[0] == (1, "Иван")

    def test_insert_record_wrong_length(self):
        self.db.create_table("students", ["id", "name"])
        with pytest.raises(InvalidRecordLengthError):
            self.db.insert_record("students", (1,))

    def test_insert_record_table_not_found(self):
        with pytest.raises(TableNotFoundError):
            self.db.insert_record("ghost", (1, "test"))

    def test_insert_multiple_records(self):
        self.db.create_table("students", ["id", "name"])
        self.db.insert_record("students", (1, "Иван"))
        self.db.insert_record("students", (2, "Пётр"))
        self.db.insert_record("students", (3, "Анна"))
        records = self.db.select_records("students")
        assert len(records) == 3

    def test_select_records_no_filters(self):
        self.db.create_table("students", ["id", "name"])
        self.db.insert_record("students", (1, "Иван"))
        self.db.insert_record("students", (2, "Пётр"))
        records = self.db.select_records("students")
        assert len(records) == 2

    def test_select_records_with_filter(self):
        self.db.create_table("students", ["id", "name"])
        self.db.insert_record("students", (1, "Иван"))
        self.db.insert_record("students", (2, "Пётр"))
        self.db.insert_record("students", (3, "Иван"))
        records = self.db.select_records("students", name="Иван")
        assert len(records) == 2
        assert records[0][1] == "Иван"
        assert records[1][1] == "Иван"

    def test_select_records_with_multiple_filters(self):
        self.db.create_table("students", ["id", "name", "age"])
        self.db.insert_record("students", (1, "Иван", 20))
        self.db.insert_record("students", (2, "Иван", 25))
        self.db.insert_record("students", (3, "Пётр", 20))
        records = self.db.select_records("students", name="Иван", age=25)
        assert len(records) == 1
        assert records[0] == (2, "Иван", 25)

    def test_select_records_filter_not_found(self):
        self.db.create_table("students", ["id", "name"])
        self.db.insert_record("students", (1, "Иван"))
        records = self.db.select_records("students", name="Анна")
        assert len(records) == 0

    def test_update_records_no_filters(self):
        self.db.create_table("students", ["id", "name"])
        self.db.insert_record("students", (1, "Иван"))
        self.db.insert_record("students", (2, "Пётр"))
        updated = self.db.update_records("students", {"name": "Анна"})
        assert updated == 2
        records = self.db.select_records("students")
        assert records[0][1] == "Анна"
        assert records[1][1] == "Анна"

    def test_update_records_with_filter(self):
        self.db.create_table("students", ["id", "name"])
        self.db.insert_record("students", (1, "Иван"))
        self.db.insert_record("students", (2, "Пётр"))
        updated = self.db.update_records("students", {"name": "Анна"}, name="Иван")
        assert updated == 1
        records = self.db.select_records("students", name="Анна")
        assert len(records) == 1
        assert records[0][1] == "Анна"

    def test_update_records_invalid_column(self):
        self.db.create_table("students", ["id", "name"])
        self.db.insert_record("students", (1, "Иван"))
        with pytest.raises(ColumnNotFoundError):
            self.db.update_records("students", {"age": 30})

    def test_update_records_no_matches(self):
        self.db.create_table("students", ["id", "name"])
        self.db.insert_record("students", (1, "Иван"))
        updated = self.db.update_records("students", {"name": "Анна"}, name="Ghost")
        assert updated == 0
        records = self.db.select_records("students")
        assert records[0][1] == "Иван"

    def test_delete_records_no_filters(self):
        self.db.create_table("students", ["id", "name"])
        self.db.insert_record("students", (1, "Иван"))
        self.db.insert_record("students", (2, "Пётр"))
        deleted = self.db.delete_records("students")
        assert deleted == 2
        assert len(self.db.select_records("students")) == 0

    def test_delete_records_with_filter(self):
        self.db.create_table("students", ["id", "name"])
        self.db.insert_record("students", (1, "Иван"))
        self.db.insert_record("students", (2, "Пётр"))
        deleted = self.db.delete_records("students", name="Иван")
        assert deleted == 1
        records = self.db.select_records("students")
        assert len(records) == 1
        assert records[0][1] == "Пётр"

    def test_delete_records_no_matches(self):
        self.db.create_table("students", ["id", "name"])
        self.db.insert_record("students", (1, "Иван"))
        deleted = self.db.delete_records("students", name="Ghost")
        assert deleted == 0
        assert len(self.db.select_records("students")) == 1

    def test_delete_records_with_multiple_filters(self):
        self.db.create_table("students", ["id", "name", "age"])
        self.db.insert_record("students", (1, "Иван", 20))
        self.db.insert_record("students", (2, "Иван", 25))
        self.db.insert_record("students", (3, "Пётр", 20))
        deleted = self.db.delete_records("students", name="Иван", age=25)
        assert deleted == 1
        records = self.db.select_records("students")
        assert len(records) == 2
        assert (1, "Иван", 20) in records
        assert (3, "Пётр", 20) in records

    def test_delete_table_success(self):
        self.db.create_table("students", ["id"])
        self.db.delete_table("students")
        assert not self.db.table_exists("students")

    def test_delete_table_not_found(self):
        with pytest.raises(TableNotFoundError):
            self.db.delete_table("ghost")

    def test_clear_table(self):
        self.db.create_table("students", ["id"])
        self.db.insert_record("students", (1,))
        self.db.insert_record("students", (2,))
        self.db.clear_table("students")
        assert len(self.db.select_records("students")) == 0

    def test_clear_table_empty(self):
        self.db.create_table("students", ["id"])
        self.db.clear_table("students")
        assert len(self.db.select_records("students")) == 0

    def test_rename_table_success(self):
        self.db.create_table("old", ["id"])
        self.db.rename_table("old", "new")
        assert self.db.table_exists("new")
        assert not self.db.table_exists("old")
        self.db.insert_record("new", (1,))
        records = self.db.select_records("new")
        assert len(records) == 1

    def test_rename_table_not_found(self):
        with pytest.raises(TableNotFoundError):
            self.db.rename_table("ghost", "new")

    def test_rename_table_duplicate(self):
        self.db.create_table("t1", ["id"])
        self.db.create_table("t2", ["id"])
        with pytest.raises(DuplicateTableError):
            self.db.rename_table("t1", "t2")

    def test_rename_column_success(self):
        self.db.create_table("students", ["old_name", "age"])
        self.db.insert_record("students", ("Иван", 20))
        self.db.rename_column("students", "old_name", "new_name")
        columns = self.db.get_columns("students")
        assert "new_name" in columns
        assert "old_name" not in columns
        records = self.db.select_records("students")
        assert records[0][0] == "Иван"

    def test_rename_column_not_found(self):
        self.db.create_table("students", ["name"])
        with pytest.raises(ColumnNotFoundError):
            self.db.rename_column("students", "ghost", "new")

    def test_rename_column_duplicate(self):
        self.db.create_table("students", ["name", "age"])
        with pytest.raises(ColumnNotFoundError):
            self.db.rename_column("students", "name", "age")

    def test_sort_records_ascending(self):
        self.db.create_table("students", ["id", "name"])
        self.db.insert_record("students", (1, "Иван"))
        self.db.insert_record("students", (2, "Анна"))
        self.db.insert_record("students", (3, "Борис"))
        sorted_records = self.db.sort_records("students", "name", reverse=False)
        names = [r[1] for r in sorted_records]
        assert names == ["Анна", "Борис", "Иван"]

    def test_sort_records_descending(self):
        self.db.create_table("students", ["id", "name"])
        self.db.insert_record("students", (1, "Иван"))
        self.db.insert_record("students", (2, "Анна"))
        self.db.insert_record("students", (3, "Борис"))
        sorted_records = self.db.sort_records("students", "name", reverse=True)
        names = [r[1] for r in sorted_records]
        assert names == ["Иван", "Борис", "Анна"]

    def test_sort_records_by_integer(self):
        self.db.create_table("students", ["id", "age"])
        self.db.insert_record("students", (1, 25))
        self.db.insert_record("students", (2, 20))
        self.db.insert_record("students", (3, 30))
        sorted_records = self.db.sort_records("students", "age", reverse=False)
        ages = [r[1] for r in sorted_records]
        assert ages == [20, 25, 30]

    def test_sort_records_column_not_found(self):
        self.db.create_table("students", ["id", "name"])
        with pytest.raises(ColumnNotFoundError):
            self.db.sort_records("students", "ghost")

    def test_sort_records_empty_table(self):
        self.db.create_table("students", ["id", "name"])
        sorted_records = self.db.sort_records("students", "name", reverse=False)
        assert sorted_records == []

    def test_data_persists_between_instances(self):
        db1 = CSVDatabase(directory=self.temp_dir.name)
        db1.create_table("students", ["id", "name"])
        db1.insert_record("students", (1, "Иван"))
        db1.insert_record("students", (2, "Пётр"))

        db2 = CSVDatabase(directory=self.temp_dir.name)
        assert db2.table_exists("students")
        records = db2.select_records("students")
        assert len(records) == 2
        assert (1, "Иван") in records
        assert (2, "Пётр") in records

    def test_list_tables_empty(self):
        assert self.db.list_tables() == []

    def test_list_tables_with_data(self):
        self.db.create_table("students", ["id"])
        self.db.create_table("teachers", ["id"])
        tables = self.db.list_tables()
        assert len(tables) == 2
        assert "students" in tables
        assert "teachers" in tables

    def test_get_all_info(self):
        self.db.create_table("students", ["id", "name"])
        self.db.insert_record("students", (1, "Иван"))
        self.db.create_table("teachers", ["id"])
        info = self.db.get_all_info()
        assert "students" in info
        assert "teachers" in info
        columns_students, count_students = info["students"]
        assert columns_students == ["id", "name"]
        assert count_students == 1
        columns_teachers, count_teachers = info["teachers"]
        assert columns_teachers == ["id"]
        assert count_teachers == 0

    def test_table_exists_true(self):
        self.db.create_table("students", ["id"])
        assert self.db.table_exists("students") is True

    def test_table_exists_false(self):
        assert self.db.table_exists("ghost") is False

