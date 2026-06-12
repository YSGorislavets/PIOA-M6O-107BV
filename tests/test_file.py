import tempfile
import pytest
import json
from pathlib import Path
from src.db.backend.file import FileDatabase
from src.db.backend.errors import (
    TableNotFoundError,
    DuplicateTableError,
    EmptyTableNameError,
    EmptyColumnsError,
    InvalidRecordLengthError,
    ColumnNotFoundError,
    FileOperationError,
)


class TestFileDatabase:
    def setup_method(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db = FileDatabase(directory=self.temp_dir.name)

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

    def test_select_records_with_multiple_filters(self):
        self.db.create_table("students", ["id", "name", "age"])
        self.db.insert_record("students", (1, "Иван", 20))
        self.db.insert_record("students", (2, "Иван", 25))
        records = self.db.select_records("students", name="Иван", age=25)
        assert len(records) == 1
        assert records[0] == (2, "Иван", 25)

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

    def test_update_records_invalid_column(self):
        self.db.create_table("students", ["id", "name"])
        self.db.insert_record("students", (1, "Иван"))
        with pytest.raises(ColumnNotFoundError):
            self.db.update_records("students", {"age": 30})

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

    def test_rename_table_success(self):
        self.db.create_table("old", ["id"])
        self.db.rename_table("old", "new")
        assert self.db.table_exists("new")
        assert not self.db.table_exists("old")

    def test_rename_column_success(self):
        self.db.create_table("students", ["old_name", "age"])
        self.db.insert_record("students", ("Иван", 20))
        self.db.rename_column("students", "old_name", "new_name")
        columns = self.db.get_columns("students")
        assert "new_name" in columns
        assert "old_name" not in columns

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

    def test_sort_records_column_not_found(self):
        self.db.create_table("students", ["id", "name"])
        with pytest.raises(ColumnNotFoundError):
            self.db.sort_records("students", "ghost")

    def test_data_persists_between_instances(self):
        db1 = FileDatabase(directory=self.temp_dir.name)
        db1.create_table("students", ["id", "name"])
        db1.insert_record("students", (1, "Иван"))

        db2 = FileDatabase(directory=self.temp_dir.name)
        assert db2.table_exists("students")
        records = db2.select_records("students")
        assert len(records) == 1
        assert records[0] == (1, "Иван")
